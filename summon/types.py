# SPDX-License-Identifier: BSD-3-Clause
from enum import IntEnum, unique

__all__ = (
	'Probe',
)

# Enumeration of the available valid probe platforms
@unique
class Probe(IntEnum):
	_96bCarbon = 0
	blackpillF401CC = 1
	blackpillF401CE = 2
	blackpillF411CE = 3
	bluepill = 4
	ctxLink = 5
	f072 = 6
	f3 = 7
	f4Discovery = 8
	hydraBus = 9
	launchpadICDI = 10
	native = 11
	stlink = 12
	stlinkv3 = 13
	swlink = 14
