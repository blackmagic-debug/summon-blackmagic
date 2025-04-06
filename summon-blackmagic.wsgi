#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause

from sys import argv, path
from pathlib import Path

# Locate where we are deployed, and try to add the summon package onto the path
summonPath = Path(argv[0]).resolve().parent
if (summonPath / 'summon').is_dir():
	path.insert(0, str(summonPath))
else:
	raise ImportError('Could not summon blackmagic - elixirs not found')
# Now see if we have a virtual environment available, and activate it if we do
activateThis = summonPath / '.env' / 'bin' / 'activate_this.py'
if activateThis.exists() and activateThis.is_file():
	# Read out the contents of the file and exec it
	with activateThis.open('r') as activateFile:
		exec(activateFile.read(), {'__file__': activateThis})

from summon import app as application
