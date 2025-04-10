# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import sql
from pathlib import Path
from zipfile import ZipFile, ZipInfo
import requests
import magic

from .models import Release, ReleaseProbe, FirmwareDownload, BMDABinary
from .githubTypes import GitHubRelease, GitHubAsset
from .types import Probe, variantFriendlyName, TargetOS, TargetArch

# All valid release files start with this prefix
fileNamePrefix = 'blackmagic-'

# Represents our bindings to the GitHub API as much as we care to have
class GitHubAPI:
	# Initialise a connection to the API using the API token from the config
	def __init__(self, token: str) -> None:
		self.apiToken = token
		# For now, we conform to the API version from 2022-11-28
		self.apiVersion = '2022-11-28'

	# Extract a list of current releases off the BMD repo, and update the DB with it
	def updateReleases(self, db: SQLAlchemy):
		# Fire off the request with the API token and version specified
		response = requests.get(
			'https://api.github.com/repos/blackmagic-debug/blackmagic/releases',
			headers = {
				'Authorization': f'Bearer {self.apiToken}',
				'X-GitHub-Api-Version': self.apiVersion,
			}
		)
		# We expect the response to be encoded as JSON
		# XXX: Need to deal with the fact this response is pagenated to 30 results per request
		releaseFragments: list[GitHubRelease] = response.json()

		# Iterate through all the release descriptors that GitHub has returned
		for releaseFragment in releaseFragments:
			# Try to index each one
			self.indexRelease(db, releaseFragment)

		# Make sure any additions made by this function to the databse stick
		db.session.commit()

	# Process the details of a specific release and try to index it
	def indexRelease(self, db: SQLAlchemy, releaseFragment: GitHubRelease):
		# Check and make sure this is an actually published release
		if releaseFragment['draft']:
			return

		# See if the release is already present in the database
		releaseVersion = releaseFragment['tag_name']
		release = db.session.scalar(sql.select(Release).where(Release.version == releaseVersion))
		# If there is one present, we've already cached this one so skip it
		if release is not None:
			return

		# Otherwise, build a new Release object and add it to the database
		release = Release(releaseVersion)
		db.session.add(release)

		# Now loop through the release assets
		for asset in releaseFragment['assets']:
			# If the asset is a build of BMDA or the firmware, we want to index that
			name = asset['name']
			# Firmware ends with .elf, BMDA with .zip and when the asset name does not contain 'source' in the name
			if name.endswith('.elf') or (name.endswith('.zip') and 'source' not in name):
				self.indexAsset(db, asset, release)

		# Having built a list of all the assets by probe, go through and make sure the variant names,
		# file names and friendly names are set appropriately (fixup for full -> common)
		self.harmoniseDownloadNames(release)

	# Process an asset from a release, and turn it into a firmware download in the database
	def indexAsset(self, db: SQLAlchemy, asset: GitHubAsset, release: Release):
		# Determine if this is firmware or BMDA
		if asset['name'].endswith('.elf'):
			self.indexFirmware(db, asset, release)
		# Otherwise it's BMDA
		else:
			self.indexBMDA(db, asset, release)

	# Index a firmware build into the database against a release
	def indexFirmware(self, db: SQLAlchemy, asset: GitHubAsset, release: Release):
		# Firmware ELF files have the general name form of:
		# blackmagic-<probe>-<variant>-<release>.elf
		# or blackmagic-<probe>-<release>.elf
		# Check that the end of the file name is actually the release name, and the start 'blackmagic-'
		releaseName = release.version.replace('.', '_')
		fileNameSuffix = f'-{releaseName}.elf'
		fileName = asset['name']
		# If it does not, then we're done here..
		if not fileName.startswith(fileNamePrefix) or not fileName.endswith(fileNameSuffix):
			return

		# Grab only the middle part of the file name and tear it apart
		nameParts = fileName[len(fileNamePrefix):-len(fileNameSuffix)].split('-')
		# Now extract which probe this is for
		probeName = nameParts.pop(0).lower()
		# If there are now only 1 part left, the next is the variant
		if len(nameParts) != 0:
			variant = '-'.join(nameParts).lower()
		else:
			# Otherwise this ia a full firmware build for this platform, not a variant
			variant = 'full'

		# With the probe and variant established, try to find the probe in the
		# database for the release (and add it if it's not)
		releaseProbe = self.findProbe(db, release, Probe.fromString(probeName))
		probe = releaseProbe.probe

		# Now build a description of this firwmare download for that probe
		firmwareDownload = FirmwareDownload(releaseProbe)
		firmwareDownload.uri = asset['browser_download_url']
		firmwareDownload.variantName = variant
		# Build a new file name that we can guarantee to be unique on the user's system
		firmwareDownload.fileName = Path(f'blackmagic-{probe.toString()}-{variant}-{release.version}.elf')
		# Build a friendly name for this download
		probeFriendlyName = 'BMP' if probe == Probe.native else probe.toString()
		firmwareDownload.friendlyName = f'Black Magic Debug for {probeFriendlyName} ({variantFriendlyName(variant)})'

		# Finally, add it to the database now we're done defining it
		db.session.add(firmwareDownload)

	def indexBMDA(self, db: SQLAlchemy, asset: GitHubAsset, release: Release):
		# BMDA release files have the general name form of:
		# blackmagic-<os>-<os-ver>-<arch>-<release>.zip
		# Where the architecture and OS version are both optional and omitable.
		# So, disecting these is a bit of a pain.. but here goes:
		# Check that the end of the file name is actually the release name, and the start 'blackmagic-'
		releaseName = release.version.replace('.', '_')
		fileNameSuffix = f'-{releaseName}.zip'
		fileName = asset['name']
		# If it does not, then we're done here..
		if not fileName.startswith(fileNamePrefix) or not fileName.endswith(fileNameSuffix):
			return

		# Now grab only the middle part of the file name, and tear it apart
		nameParts = fileName[len(fileNamePrefix):-len(fileNameSuffix)].split('-')
		# The first part is the OS on which this is to be run on, so convert that to a TargetOS enum value
		targetOS = TargetOS.fromString(nameParts.pop(0).lower())

		# We now have a few options here.. the first is that the file name contains an OS version.. but
		# it's actually easier to see if there's an architecture present, and pop that out till we run out
		# of components - if we don't recover one, we have to download the zip file to temporary storage and
		# tear the archive apart to figure out what it can be run on.
		targetArch: TargetArch | None = None
		for idx, part in enumerate(nameParts):
			arch = TargetArch.fromString(part.lower())
			if arch is not None:
				targetArch = arch
				nameParts.pop(idx)
				break

		# We have to download the file anyway to identify the BMDA executable, so get that done
		archivePath = self.downloadBMDA(asset['browser_download_url'])
		# Turn the archive into a ZipFile resource so we can read out the contents and figure out what the
		# BMDA binary is actually named - which we have to do before we can further determine architecture
		archive = ZipFile(archivePath, mode = 'r')
		bmdaFileName = self.determineBMDAFileName(archive.infolist())
		# If we could not find a valid name for the BMDA binary, we're done here..
		if bmdaFileName is None:
			archive.close()
			archivePath.unlink(missing_ok = True)
			return

		# Now handle if we still don't know the target architecture of the binary
		if targetArch is None:
			# Extract the BMDA binary from the archive to be able to futz with it
			bmdaFile = Path(archive.extract(bmdaFileName, path = '/tmp'))
			# Get the file magic for it and figure out what architecture is represented
			targetArch = self.determineBMDAArch(magic.from_file(bmdaFile).lower())
			bmdaFile.unlink()
			# If we did not get a supported architecture, we're done!
			if targetArch is None:
				archive.close()
				archivePath.unlink(missing_ok = True)
				return

		# We now have all the moving pieces - turn the information we have into an entry in the database
		binary = BMDABinary(release, targetOS, targetArch)
		binary.uri = asset['browser_download_url']
		binary.fileName = Path(bmdaFileName.filename)

		# When we get done, make sure to clean up the archive we downloaded
		archive.close()
		archivePath.unlink(missing_ok = True)
		# Finally, add it to the database now we're done defining it
		db.session.add(binary)

	def findProbe(self, db: SQLAlchemy, release: Release, probe: Probe) -> ReleaseProbe:
		# Check and see if this probe is already in the database for this release
		releaseProbe = db.session.scalar(
			sql.select(ReleaseProbe).where(ReleaseProbe.releaseID == release.id, ReleaseProbe.probe == probe)
		)

		# If it is, then return that
		if releaseProbe is not None:
			return releaseProbe

		# It was not, so make a new one, add it to the database and return
		releaseProbe = ReleaseProbe(release, probe)
		db.session.add(releaseProbe)
		return releaseProbe

	def harmoniseDownloadNames(self, release: Release):
		# Loop through all the probes in the release
		for releaseProbe in release.probeFirmware:
			# If the probe only has one variant or none, skip
			if len(releaseProbe.variants) <= 1:
				continue

			probe = releaseProbe.probe
			# Loop through the variants
			for variant in releaseProbe.variants:
				# See if the variant is named 'full', and skip if not
				if variant.variantName != 'full':
					continue

				# Ok, we've found a 'full' variant in a multi-variant set - fixup to 'common'
				variant.variantName = 'common'
				variant.fileName = Path(f'blackmagic-{probe.toString()}-{variant.variantName}-{release.version}.elf')
				probeFriendlyName = 'BMP' if probe == Probe.native else probe.toString()
				variant.friendlyName = f'Black Magic Debug for {probeFriendlyName} ({variantFriendlyName(variant.variantName)})'

	def downloadBMDA(self, uri: str) -> Path:
		# Figure out where stick this archive (use /tmp!)
		downloadPath = Path('/tmp/blackmagic-bmda.zip')
		# If it already exists, clean up - this means something went wrong in a previous run
		if downloadPath.exists():
			# TOCTOU: This could be cleaned up between the check and unlink, so allow it to have gone missing
			downloadPath.unlink(missing_ok = True)

		# Request the file from the GH servers streamed
		response = requests.get(uri, stream = True)
		with downloadPath.open('wb') as file:
			# Pull the file contents back in 4KiB chunks
			for chunk in response.iter_content(chunk_size = 4096):
				# Write the chunk out, however big it winds up being
				file.write(chunk)

		# When all's said and done, return where we stuck the downloaded file
		return downloadPath

	def determineBMDAFileName(self, files: list[ZipInfo]) -> ZipInfo | None:
		# Loop through each of the files in the zip file
		for file in files:
			# Skip entries which are directories, we don't care about those
			if file.is_dir():
				continue

			# Otherwise, check to see if the file is one of the recognised names for BMDAs
			filePath = Path(file.filename)
			fileName = filePath.stem
			fileExt = filePath.suffix
			# If there is a file extension, it needs to be '.exe' (for Windows)
			# and the file name component needs to be one of 'blackmagic-bmda' or 'blackmagic'
			# to be recognised. Ignore anything else.
			if (
				(fileExt == '' or fileExt == '.exe') and
				(fileName == 'blackmagic-bmda' or fileName == 'blackmagic')
			):
				return file

		# If we didn't find one, indicate that by returning None
		return None

	def determineBMDAArch(self, magic: str) -> TargetArch | None:
		# If the file magic contains one of these substrings somewhere in it, we have an AMD64 binary (probably)
		if 'x86-64' in magic or 'x86_64' in magic:
			return TargetArch.amd64
		# If the file magic contains i*86, we have an i386 binary (probably)
		if 'i386' in magic or 'i486' in magic or 'i586' in magic or 'i686' in magic:
			return TargetArch.i386
		# If the file contains one of these substrings, we have an AArch64 binary for sure
		if 'aarch64' in magic or 'arm64' in magic:
			return TargetArch.aarch64

		return None
