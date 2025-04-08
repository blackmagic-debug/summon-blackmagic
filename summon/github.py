# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import sql
from pathlib import Path
import requests

from .models import Release, ReleaseProbe, FirmwareDownload
from .githubTypes import GitHubRelease, GitHubAsset
from .types import Probe, variantFriendlyName

# Represents our bindings to the GitHub API as much as we care to have
class GitHubAPI:
	# Initialise a connection to the API using the API token from the config
	def __init__(self, token: str) -> None:
		self.apiToken = token
		# For now, we conform to the API version from 2022-11-28
		self.apiVersion = '2022-11-28'

	# Extract a list of current releases off the BMD repo, and update the DB with it
	def updateReleases(self, db: SQLAlchemy) -> list[Release]:
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
		releases: list[Release] = []

		# Iterate through all the release descriptors that GitHub has returned
		for releaseFragment in releaseFragments:
			# Check and make sure this is an actually published release
			if releaseFragment['draft']:
				continue

			# See if the release is already present in the database
			releaseVersion = releaseFragment['tag_name']
			release = db.session.execute(sql.select(Release).filter_by(version = releaseVersion)).scalar()
			# If there is one present, we've already cached this one so skip it
			if release is not None:
				continue

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

		# Make sure any additions made by this function to the databse stick
		db.session.commit()
		return releases

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
		# Check that the end of the file name is actually the release name
		releaseName = release.version.replace('.', '_')
		fileNameSuffix = f'-{releaseName}.elf'
		fileName = asset['name']
		# If it does not, then we're done here..
		if not fileName.endswith(fileNameSuffix):
			return

		# Grab only the front of the file name and tear it apart
		nameParts = fileName[:-len(fileNameSuffix)].split('-')
		# Remove the 'blackmagic' part, we don't want to be having to deal with that
		nameParts.pop(0)
		# Now extract which probe this is for
		probe = nameParts.pop(0).lower()
		# If there are now only 1 part left, the next is the variant
		if len(nameParts) != 0:
			variant = '-'.join(nameParts).lower()
		else:
			# Otherwise this ia a full firmware build for this platform, not a variant
			variant = 'full'

		# With the probe and variant established, try to find the probe in the
		# database for the release (and add it if it's not)
		releaseProbe = self.findProbe(db, release, probe)

		# Now build a description of this firwmare download for that probe
		firmwareDownload = FirmwareDownload(releaseProbe)
		firmwareDownload.uri = asset['browser_download_url']
		firmwareDownload.variantName = variant
		# Build a new file name that we can guarantee to be unique on the user's system
		firmwareDownload.fileName = Path(f'blackmagic-{probe}-{variant}-{release.version}.elf')
		# Build a friendly name for this download
		probeFriendlyName = 'BMP' if releaseProbe.probe == Probe.native else probe
		firmwareDownload.friendlyName = f'Black Magic Debug for {probeFriendlyName} ({variantFriendlyName(variant)})'

		# Finally, add it to the database now we're done defining it
		db.session.add(firmwareDownload)

	def indexBMDA(self, db: SQLAlchemy, asset: GitHubAsset, release: Release):
		pass

	def findProbe(self, db: SQLAlchemy, release: Release, probe: str) -> ReleaseProbe:
		# Check and see if this probe is already in the database for this release
		releaseProbe = db.session.execute(
			sql.select(ReleaseProbe).filter_by(releaseID = release.id, probe = probe)
		).scalar()

		# If it is, then return that
		if releaseProbe is not None:
			return releaseProbe

		# It was not, so make a new one, add it to the database and return
		releaseProbe = ReleaseProbe(release, probe)
		db.session.add(releaseProbe)
		return releaseProbe
