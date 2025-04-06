# SPDX-License-Identifier: BSD-3-Clause
from flask import Flask, render_template

# Initialise Flask for summon
app = Flask(__name__)
# Configure Flask from the config.py in this directory
app.config.from_pyfile('config.py')

@app.route('/')
def index():
	return render_template('index.html')
