#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
from summon import app, db
from summon.github import GitHubAPI

github = GitHubAPI(app.config['GITHUB_API_TOKEN'])
with app.app_context():
		github.updateReleases(db)
