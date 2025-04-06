# SPDX-License-Identifier: BSD-3-Clause
from flask import Flask, render_template

from .models import db

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

@app.route('/')
def index():
	return render_template('index.html')
