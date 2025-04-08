# SPDX-License-Identifier: BSD-3-Clause
from enum import IntEnum, unique
from pathlib import Path
from sqlalchemy.types import Concatenable, TypeEngine
from sqlalchemy.sql import type_api
from sqlalchemy.engine.interfaces import Dialect
from typing import Generic, TypeVar
from types import ModuleType

__all__ = (
	'Probe',
	'variantFriendlyName',
	'UnicodePath',
	'',
)

IntEnumT = TypeVar('IntEnumT', bound = IntEnum)

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

	# Construct a Probe from a string name for the probe
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

# Translate a firmware variant to its friendly name
def variantFriendlyName(variant: str) -> str:
	match variant:
		case 'common':
			return 'common targets'
		case 'riscv':
			return 'RISC-V targets'
		case 'st-clones':
			return 'ST and ST-clones targets'
		case 'uncommon':
			return 'uncommon targets'
		# If we don't have a specific translation for this, just use the variant name itself
		case _:
			return variant

# SQLAlchemy unicode string type for holding file paths
class UnicodePath(Concatenable, TypeEngine[Path]):
	__visit_name__ = "unicode"
	length: int | None = None

	# When a new one of these is created (for the mapping system), automatically
	# include a variant so it behaves correctly for SQLite
	def __init__(self, *, dialect: str | None = None):
		if dialect == 'sqlite':
			self.collation = None
		else:
			self.collation = 'utf8'
			self._variant_mapping = self._variant_mapping.union(
				{'sqlite': UnicodePath(dialect = 'sqlite')}
			)

	# Disallow path literals to be processed into the query, only allow binds/unbinds
	def literal_processor(self, dialect: Dialect) -> None:
		return None

	# Define how to convert a Path value into something that can be bound into the query
	def bind_processor(self, dialect: Dialect) -> type_api._BindProcessorType[Path]:
		def process(value: Path | None) -> str | None:
			if value is not None:
				return str(value)
			return None
		return process

	# Define how to convert a value from a result set back into a Path from a query
	def result_processor(self, dialect: Dialect, coltype: object) -> type_api._ResultProcessorType[Path]:
		def process(value: str) -> Path:
			return Path(value)
		return process

	@property
	def python_type(self):
		return Path

	def get_dbapi_type(self, dbapi: ModuleType):
		return dbapi.STRING

# SQLAlchemy integer type for IntEnum storage and unmapping
def intEnumMapper(*, type: type[IntEnumT]):
	class IntEnumMapper(TypeEngine[IntEnumT]):
		__visit_name__ = "integer"

		# Define how to convert a literal of the mapped IntEnum to a string for use immediately in a query
		def literal_processor(self, dialect: Dialect) -> type_api._LiteralProcessorType[IntEnumT]:
			def process(value: IntEnumT) -> str:
				return str(value.value)
			return process

		# Define how to convert a value of the mapped enum into something that can be bound into the query
		def bind_processor(self, dialect: Dialect) -> type_api._BindProcessorType[IntEnumT]:
			def process(value: IntEnumT | None) -> int | None:
				if value is not None:
					return value.value
				return None
			return process

		# Define how to convert a value from a result set back into a value of the mapped enum type from a query
		def result_processor(self, dialect: Dialect, coltype: object) -> type_api._ResultProcessorType[IntEnumT]:
			def process(value: int) -> IntEnumT:
				return type(value)
			return process

		@property
		def python_type(self):
			return type

		def get_dbapi_type(self, dbapi: ModuleType):
			return dbapi.NUMBER

	return IntEnumMapper
