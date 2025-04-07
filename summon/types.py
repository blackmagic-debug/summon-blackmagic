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

	@staticmethod
	def fromString(name: str) -> 'Probe':
		match name:
			case '96b_carbon':
				return Probe._96bCarbon
			case 'blackpill-f401cc':
				return Probe.blackpillF401CC
			case 'blackpill-f401ce':
				return Probe.blackpillF401CE
			case 'blackpill-f411ce':
				return Probe.blackpillF411CE
			case 'bluepill':
				return Probe.bluepill
			case 'ctxlink':
				return Probe.ctxLink
			case 'f072':
				return Probe.f072
			case 'f3':
				return Probe.f3
			case 'f4discovery':
				return Probe.f4Discovery
			case 'hydrabus':
				return Probe.hydraBus
			case 'launchpad-icdi':
				return Probe.launchpadICDI
			case 'native':
				return Probe.native
			case 'stlink' | 'stlinkv2':
				return Probe.stlink
			case 'stlinkv3':
				return Probe.stlinkv3
			case 'swlink':
				return Probe.swlink
			case _:
				raise ValueError(f'Invalid probe name {name}')
