# app/database/base.py
# Declares the shared SQLAlchemy DeclarativeBase used by all models.

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models in CampusHire."""
    pass
