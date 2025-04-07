# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry, relationship
from pathlib import Path
from typing import NewType

from .types import Probe

__all__ = (
	'db',
	'Release',
	'ReleaseFirmware',
	'FirmwareDownload',
)

# Define types for mapping things in and out of the database cleanly
i32 = NewType("i32", int)
i64 = NewType("i64", int)

# Define the type mappings from Python to the DBMS
class Model(DeclarativeBase):
	registry = registry(
		type_annotation_map = {
			Path: types.String,
			i32: types.Integer,
			i64: types.BigInteger,
			Probe: types.Integer,
		}
	)

# Build the Flask SQLAlchemy object, making use of the model mappings
db = SQLAlchemy(model_class = Model)

# Releases of BMD that have been made
class Release(db.Model):
	id: Mapped[i32] = mapped_column(primary_key = True)
	version: Mapped[str]

	firmware: Mapped[list['ReleaseFirmware']] = relationship(back_populates = 'release')

	def __init__(self, version: str):
		self.version = version

# Firmware in a release by probe platform
class ReleaseFirmware(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True)
	releaseID: Mapped[i32] = mapped_column(ForeignKey(Release.id))
	probe: Mapped[Probe]

	release: Mapped[Release] = relationship(back_populates = 'firmware')
	variants: Mapped[list['FirmwareDownload']] = relationship()

# Downloads for firmware available for a probe
class FirmwareDownload(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True)
	releaseFirmwareID: Mapped[i64] = mapped_column(ForeignKey(ReleaseFirmware.id))
	friendlyName: Mapped[str]
	fileName: Mapped[Path]
	uri: Mapped[str]
	# If there are multiple firmware downloads for one probe in one release, this
	# provides a name to which variant this download is for
	variantName: Mapped[str]
