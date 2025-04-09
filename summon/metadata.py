# SPDX-License-Identifier: BSD-3-Clause
from sqlalchemy import sql

from .models import SQLAlchemy, Release, ReleaseProbe, FirmwareDownload, BMDABinary

__all__ = (
	'releasesToJSON'
)

def releasesToJSON(db: SQLAlchemy) -> dict:
	# Extract all the releases we have indexed in the database
	releases = db.session.scalars(
		sql.select(Release)
	)

	# Construct a new dictionary for holding releases in
	result = {}
	# Now iterate through the releases, filling in an entry for each in the dict
	for release in releases:
		# Filter out releases that contain no firmware
		if len(release.probeFirmware) == 0:
			continue

		# Otherwise, convert the firwmare entry list into a suitable JSON object
		firmwareDict = probeFirmwareToJSON(release.probeFirmware)
		includesBMDA = len(release.bmdaDownloads) != 0
		bmdaDict = bmdaDownloadsToJSON(release.bmdaDownloads)

		# Add the release to the result set
		result[release.version] = {
			"includesBMDA": includesBMDA,
			"firmware": firmwareDict,
		}

		# If this release includes BMDAs, then add the entry for that to the result dict
		if includesBMDA:
			result[release.version]['bmda'] = bmdaDict

	return result

def probeFirmwareToJSON(probeFirmware: list[ReleaseProbe]) -> dict:
	# Construct a new dictionary for holding firmware downloads by probe in
	result = {}
	# Iterate through all the probes with firmware in this release
	for probeRelease in probeFirmware:
		# Build a new dictionary holding all the variants for this probe
		result[probeRelease.probe.toString()] = firmwareVariantsToJSON(probeRelease.variants)

	return result

def firmwareVariantsToJSON(variants: list[FirmwareDownload]) -> dict:
	# Construct a new dictionary for holding firmware variants for a probe
	result = {}
	# Iterate through all the variants for this probe
	for variant in variants:
		# Build an object that describes this variant
		result[variant.variantName] = {
			"friendlyName": variant.friendlyName,
			"fileName": str(variant.fileName),
			"uri": variant.uri,
		}

	return result

def bmdaDownloadsToJSON(bmdaDownloads: list[BMDABinary]) -> dict:
	# Construct a new dictionary for holding the BMDA binaries in this release
	result = {}
	# Iterate through all the downloads available
	for bmdaBinary in bmdaDownloads:
		# Convert the target OS to a string and if that string does not yet exist in the result dictionary,
		# make a new dictionary to hold the binaries for this OS
		targetOS = bmdaBinary.targetOS.toString()
		targetOSDict = result.setdefault(targetOS, {})

		# Build a new dictionary holding an entry for the architecture of this BMDA binary
		targetOSDict[bmdaBinary.targetArch.toString()] = bmdaBinaryToJSON(bmdaBinary)

	return result

def bmdaBinaryToJSON(binary: BMDABinary) -> dict:
	# Construct a dictionary holding the information required for this BMDA binary to be downloaded
	# and utilised successfully on a user's machine
	return {
		'fileName': str(binary.fileName),
		'uri': binary.uri
	}
