# SPDX-License-Identifier: BSD-3-Clause
from flask import Flask, render_template, request

from .models import db
from .metadata import releasesToJSON
from .github import GitHubAPI

__all__ = (
	'app',
)

# Initialise Flask for summon
app = Flask(__name__, instance_relative_config = True)
# Configure Flask from the config.py in this directory
app.config.from_pyfile('config.py')
# Now initialise the database engine
db.init_app(app)

# And make sure that all tables are properly defined in the database
with app.app_context():
	db.create_all()

# Register `db` to the Flask globals context for use in templates etc
@app.before_request
def build_up():
	from flask import g
	g.db = db

# Create an instance of the GitHub API interactor
gitHubAPI = GitHubAPI(app.config['GITHUB_API_TOKEN'])

# Handler for '/' so people trying to access the server don't get a 404
@app.route('/')
def index():
	return render_template('index.html')

# Handler for the release downloads metadata using the database index of the releases
@app.route('/metadata.json')
def metadata():
	# Construct a schema-conforming JSON object from the releases in the database
	return {
		"$schema": "https://raw.githubusercontent.com/blackmagic-debug/bmputil/refs/heads/main/src/metadata/metadata.schema.json",
		"version": 1,
		"releases": releasesToJSON(db)
	}

@app.post('/releaseUpdate')
def releaseUpdate():
	# Before we hand the request off to the webhook handler, make sure it's not insanely big -
	# releases should not be more than a couple of MiB, so check for the request being not larger
	# than 5MiB (that's a lot of JSON!!)
	if request.content_length > (5 * 1024 * 1024):
		return 'Request too large', 413
	return gitHubAPI.processReleaseWebhook(db, request, app.config['GITHUB_SECRET'].encode('utf8'))
