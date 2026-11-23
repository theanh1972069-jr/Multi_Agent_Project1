from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared SQLAlchemy 2.x declarative base for PostgreSQL and SQLite models."""


def new_uuid() -> str:
    """Return a string UUID4 suitable for portable `String(36)` primary keys."""
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)
