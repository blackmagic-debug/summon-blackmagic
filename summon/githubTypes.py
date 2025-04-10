# SPDX-License-Identifier: BSD-3-Clause
from typing import TypedDict

__all__ = (
	'GitHubUser',
	'GitHubAsset',
	'GitHubRelease',
)

class GitHubUser(TypedDict):
	id: int
	node_id: str
	type: str
	url: str
	html_url: str
	login: str
	avatar_url: str
	gravatar_id: str
	followers_url: str
	following_url: str
	gists_url: str
	starred_url: str
	subscriptions_url: str
	organizations_url: str
	repos_url: str
	events_url: str
	received_events_url: str
	site_admin: bool

class GitHubOrganisation(TypedDict):
	id: int
	node_id: str
	url: str
	login: str
	repos_url: str
	events_url: str
	hooks_url: str
	issues_url: str
	members_url: str
	public_members_url: str
	avatar_url: str
	description: str

class GitHubAsset(TypedDict):
	id: int
	node_id: str
	type: str
	url: str
	name: str
	browser_download_url: str
	label: str
	state: str
	content_type: str
	size: int
	download_count: int
	created_at: str
	updated_at: str
	uploader: GitHubUser

class GitHubRelease(TypedDict):
	id: int
	node_id: str
	url: str
	name: str
	html_url: str
	assets_url: str
	upload_url: str
	tarball_url: str
	zipball_url: str
	tag_name: str
	target_commitish: str
	body: str
	draft: bool
	prerelease: bool
	created_at: str
	published_at: str
	author: GitHubUser
	assets: list[GitHubAsset]
