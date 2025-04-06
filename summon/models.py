# SPDX-License-Identifier: BSD-3-Clause
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Mapped, mapped_column

db = SQLAlchemy()

class Release(db.Model):
	id: Mapped[int] = mapped_column(primary_key = True)
	version: Mapped[str]
