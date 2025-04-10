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

class GitHubLicense(TypedDict):
	node_id: str
	url: str
	key: str
	name: str
	spdx_id: str

class GitHubRepository(TypedDict):
	id: int
	node_id: str
	url: str
	html_url: str
	name: str
	full_name: str
	private: bool
	owner: GitHubUser
	description: str
	fork: bool
	forks_url: str
	keys_url: str
	collaborators_url: str
	teams_url: str
	hooks_url: str
	issue_events_url: str
	events_url: str
	assignees_url: str
	branches_url: str
	tags_url: str
	blobs_url: str
	git_tags_url: str
	git_refs_url: str
	tress_url: str
	statuses_url: str
	languages_url: str
	stargazers_url: str
	contributors_url: str
	subscribers_url: str
	subscription_url: str
	commits_url: str
	git_commits_url: str
	comments_url: str
	issue_comment_url: str
	contents_url: str
	compare_url: str
	merges_url: str
	archive_url: str
	downloads_url: str
	issues_url: str
	pulls_url: str
	milestones_url: str
	notifications_url: str
	labels_url: str
	releases_url: str
	deployments_url: str
	created_at: str
	updated_at: str
	pushed_at: str
	git_url: str
	ssh_url: str
	clone_url: str
	svn_url: str
	homepage: str
	size: int
	stargazers_count: int
	watchers_count: int
	language: str
	has_issues: bool
	has_projects: bool
	has_downloads: bool
	has_wiki: bool
	has_pages: bool
	has_discussions: bool
	forks_count: int
	mirror_url: str | None
	archived: bool
	disabled: bool
	open_issues_count: int
	license: GitHubLicense
	allow_forking: bool
	is_template: bool
	web_commit_signoff_required: bool
	topics: list[dict]
	visibility: str
	forks: int
	open_issues: int
	watchers: int
	default_branch: str
	custom_properties: dict

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

GitHubReleaseChange = TypedDict('GitHubReleaseChange', {'from': str})

class GitHubReleaseChanges(TypedDict):
	body: GitHubReleaseChange | None
	name: GitHubReleaseChange | None
	tag_name: GitHubReleaseChange | None
	make_latest: dict

class GitHubReleaseWebhook(TypedDict):
	action: str
	changes: GitHubReleaseChanges | None
	release: GitHubRelease
	repostiory: GitHubRepository
	organization: GitHubOrganisation
	sender: GitHubUser
