# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, types
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pathlib import Path
from typing import NewType

from .types import Probe

# Define types for mapping things in and out of the database cleanly
i32 = NewType("i32", int)
i64 = NewType("i64", int)

# Define the type mappings from Python to the DBMS
class Model(DeclarativeBase):
	type_annotation_map = {
		Path: types.String,
		i32: types.Integer,
		i64: types.BigInteger,
		Probe: types.Integer,
	}

# Build the Flask SQLAlchemy object, making use of the model mappings
db = SQLAlchemy(model_class = Model)

# Releases of BMD that have been made
class Release(db.Model):
	id: Mapped[i32] = mapped_column(primary_key = True)
	version: Mapped[str]

# Downloads for firmware available by probe platform
class FirmwareDownload(db.Model):
	id: Mapped[i64] = mapped_column(primary_key = True)
	releaseID: Mapped[i32] = mapped_column(ForeignKey('Release.id'))
	friendlyName: Mapped[str]
	fileName: Mapped[Path]
	uri: Mapped[str]
	probe: Mapped[Probe]
	# If there are multiple firmware downloads for one probe in one release, this
	# provides a name to which variant this download is for
	variantName: Mapped[str]
