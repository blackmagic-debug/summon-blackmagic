# SPDX-License-Identifier: BSD-3-Clause
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
	return render_template('index.html')
