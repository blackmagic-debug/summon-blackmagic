# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import sql
import requests

from .models import Release
from .githubTypes import GitHubRelease, GitHubAsset

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
		releases: list[Release] = []

		# Iterate through all the release descriptors that GitHub has returned
		for releaseFragment in releaseFragments:
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
					self.indexAsset(asset, release.id)

		# Make sure any additions made by this function to the databse stick
		db.session.commit()
		return releases

	# Process an asset from a release, and turn it into a firmware download in the database
	def indexAsset(self, asset: GitHubAsset, releaseID: int):
		# Determine if this is firmware or BMDA
		if asset['name'].endswith('.elf'):
			self.indexFirmware(asset, releaseID)
		# Otherwise it's BMDA
		else:
			self.indexBMDA(asset, releaseID)

	# Index a firmware build into the database against a release
	def indexFirmware(self, asset: GitHubAsset, releaseID: int):
		pass

	def indexBMDA(self, asset: GitHubAsset, releaseID: int):
		pass
