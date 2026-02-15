"""
SQLAlchemy declarative base and common model mixins.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr


class Base:
    """Base class for all database models."""

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name (snake_case)."""
        name = cls.__name__
        return "".join(
            ["_" + c.lower() if c.isupper() else c for c in name]
        ).lstrip("_") + "s"


# Create declarative base
Base = declarative_base(cls=Base)


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Record creation timestamp"
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp"
    )


class UUIDMixin:
    """Mixin for UUID primary key."""

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique identifier"
    )


class AuditMixin:
    """Mixin for audit fields (who created/updated)."""

    created_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who created this record"
    )

    updated_by = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User who last updated this record"
    )


def generate_uuid() -> uuid.UUID:
    """Generate a new UUID4."""
    return uuid.uuid4()
