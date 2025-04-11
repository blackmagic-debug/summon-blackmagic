# SPDX-License-Identifier: BSD-3-Clause
from flask import Flask, render_template, request

from .models import db
from .metadata import releasesToJSON
from .github import GitHubAPI
from .etag import ETagCache

__all__ = (
	'app',
)

# Initialise Flask for summon
app = Flask(__name__, instance_relative_config = True)
# Configure Flask from the config.py in this directory
app.config.from_pyfile('config.py')
# Now initialise the database engine
db.init_app(app)

# Create an instance of the GitHub API interactor
gitHubAPI = GitHubAPI(app.config['GITHUB_API_TOKEN'])
# Create an instance of the ETag cache
cache = ETagCache()

# And make sure that all tables are properly defined in the database
with app.app_context():
	db.create_all()
	# Having done this, also go poke the releases and populate the database with any changes
	# that may have happened while we were down
	gitHubAPI.updateReleases(db)

# Register `db` to the Flask globals context for use in templates etc
@app.before_request
def build_up():
	from flask import g
	g.db = db

# Handler for '/' so people trying to access the server don't get a 404
@app.route('/')
def index():
	return render_template('index.html')

# Handler for the release downloads metadata using the database index of the releases
@app.route('/metadata.json')
@cache.json
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
	# Determine which kind of webhook request this is
	event = request.headers.get('X-GitHub-Event')
	match event:
		# For ping requests, just say we were successfull.. we don't care about anything else
		case 'ping':
			return 'Success', 200
		# For release requests, dispatch to the release webhook handler
		case 'release':
			return gitHubAPI.processReleaseWebhook(db, request, app.config['GITHUB_SECRET'].encode('utf8'))
		# For everything else, including None, say we're not here
		case _:
			return 'Not Found', 404
