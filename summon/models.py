# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry, relationship
from pathlib import Path
from typing import NewType

from .types import Probe, UnicodePath

__all__ = (
	'db',
	'Release',
	'ReleaseProbe',
	'FirmwareDownload',
)

# Define types for mapping things in and out of the database cleanly
i32 = NewType("i32", int)
i64 = NewType("i64", int)

# Define the type mappings from Python to the DBMS
class Model(DeclarativeBase):
	registry = registry(
		type_annotation_map = {
			Path: UnicodePath(),
			i32: types.Integer(),
			# SQLite is stupid and needs our primary key fields to be i32 to be autoincrement 🙃
			i64: types.BigInteger().with_variant(types.Integer(), 'sqlite'),
			Probe: types.Integer(),
		}
	)

# Build the Flask SQLAlchemy object, making use of the model mappings
db = SQLAlchemy(model_class = Model)

# Releases of BMD that have been made
class Release(db.Model):
	id: Mapped[i32] = mapped_column(primary_key = True, autoincrement = True, unique = True)
	version: Mapped[str]

	firmware: Mapped[list['ReleaseProbe']] = relationship(back_populates = 'release')

	def __init__(self, version: str):
		self.version = version

# Firmware in a release by probe platform
class ReleaseProbe(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True, autoincrement = True, unique = True)
	releaseID: Mapped[i32] = mapped_column(ForeignKey(Release.id))
	probe: Mapped[Probe]

	release: Mapped[Release] = relationship(back_populates = 'firmware')
	variants: Mapped[list['FirmwareDownload']] = relationship(back_populates = 'probe')

	def __init__(self, release: Release, probe: str):
		self.release = release
		self.probe = Probe.fromString(probe)

# Downloads for firmware available for a probe
class FirmwareDownload(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True, autoincrement = True, unique = True)
	releaseFirmwareID: Mapped[i64] = mapped_column(ForeignKey(ReleaseProbe.id))
	friendlyName: Mapped[str]
	fileName: Mapped[Path]
	uri: Mapped[str]
	# If there are multiple firmware downloads for one probe in one release, this
	# provides a name to which variant this download is for
	variantName: Mapped[str]

	probe: Mapped[ReleaseProbe] = relationship(back_populates = 'variants')

	def __init__(self, probe: ReleaseProbe):
		self.probe = probe
