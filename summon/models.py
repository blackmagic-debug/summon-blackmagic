# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry, relationship
from pathlib import Path
from typing import NewType

from .types import Probe, TargetOS, TargetArch, UnicodePath, intEnumMapper

__all__ = (
	'db',
	'Release',
	'ReleaseProbe',
	'FirmwareDownload',
	'BMDABinary',
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
			Probe: intEnumMapper(type = Probe),
			TargetOS: intEnumMapper(type = TargetOS),
			TargetArch: intEnumMapper(type = TargetArch),
		}
	)

# Build the Flask SQLAlchemy object, making use of the model mappings
db = SQLAlchemy(model_class = Model)

# Releases of BMD that have been made
class Release(db.Model):
	id: Mapped[i32] = mapped_column(primary_key = True, autoincrement = True, unique = True)
	version: Mapped[str]

	probeFirmware: Mapped[list['ReleaseProbe']] = relationship(back_populates = 'release')
	bmdaDownloads: Mapped[list['BMDABinary']] = relationship(back_populates = 'release')

	def __init__(self, version: str):
		self.version = version

	def __repr__(self) -> str:
		return f'<Release: {self.version}>'

# Firmware in a release by probe platform
class ReleaseProbe(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True, autoincrement = True, unique = True)
	releaseID: Mapped[i32] = mapped_column(ForeignKey(Release.id))
	probe: Mapped[Probe]

	release: Mapped[Release] = relationship(back_populates = 'probeFirmware')
	variants: Mapped[list['FirmwareDownload']] = relationship(back_populates = 'probe')

	def __init__(self, release: Release, probe: Probe | str):
		self.release = release
		if isinstance(probe, Probe):
			self.probe = probe
		else:
			self.probe = Probe.fromString(probe)

	def __repr__(self) -> str:
		return f'<ReleaseProbe: {self.probe.name} for {self.release.version}>'

# Downloads for firmware available for a probe
class FirmwareDownload(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True, autoincrement = True, unique = True)
	releaseFirmwareID: Mapped[i64] = mapped_column(ForeignKey(ReleaseProbe.id))
	friendlyName: Mapped[str]
	# This fileName is the name of the file the firmware is to be written into on the
	# user's system as part of the firmware cache to uniquely identify the firmware
	fileName: Mapped[Path]
	uri: Mapped[str]
	# If there are multiple firmware downloads for one probe in one release, this
	# provides a name to which variant this download is for
	variantName: Mapped[str]

	probe: Mapped[ReleaseProbe] = relationship(back_populates = 'variants')

	def __init__(self, probe: ReleaseProbe):
		self.probe = probe

	def __repr__(self) -> str:
		return f'<FirmwareDownload: {self.friendlyName} for {self.probe.release.version}>'

# Downloads for zip files containing BMDA binaries
class BMDABinary(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True, autoincrement = True, unique = True)
	releaseID: Mapped[i32] = mapped_column(ForeignKey(Release.id))
	targetOS: Mapped[TargetOS]
	targetArch: Mapped[TargetArch]
	# This fileName is not the one above - this names the file in the archive that contains a BMDA
	# binary, as the binary can be named different things for different platforms (eg, having .exe on the end)
	fileName: Mapped[Path]
	uri: Mapped[str]

	release: Mapped[Release] = relationship(back_populates = 'bmdaDownloads')

	def __init__(self, release: Release, targetOS: TargetOS, targetArch: TargetArch):
		self.release = release
		self.targetOS = targetOS
		self.targetArch = targetArch

	def __repr__(self) -> str:
		return f'<BMDABinary: runs on {self.targetOS!r} ({self.targetArch!r}) for {self.release.version}>'
