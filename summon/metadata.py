# SPDX-License-Identifier: BSD-3-Clause
from sqlalchemy import sql

from .models import SQLAlchemy, Release, ReleaseProbe, FirmwareDownload

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

		# Add the release to the result set
		result[release.version] = {
			"includesBMDA": False, # XXX: Should be determined by the presence of any BMDA entries
			"firmware": firmwareDict,
		}

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
