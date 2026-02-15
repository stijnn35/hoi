"""
Location model - FHIR Location resource.
Physical therapy rooms and consultation spaces.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Location(Base, UUIDMixin, TimestampMixin):
    """
    FHIR Location resource.
    Represents physical therapy rooms and consultation spaces.
    """

    __tablename__ = "locations"

    # FHIR identifier
    identifier = Column(
        JSONB,
        nullable=True,
        comment="FHIR Identifier[] (business identifiers)"
    )

    # FHIR status
    status = Column(
        String(20),
        nullable=False,
        default="active",
        comment="active/suspended/inactive"
    )

    # Location name
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Location name (e.g., 'Therapy Room 1')"
    )

    # Alias names
    alias = Column(
        JSONB,
        nullable=True,
        comment="Alternative names"
    )

    # Description
    description = Column(
        Text,
        nullable=True,
        comment="Location description"
    )

    # FHIR mode
    mode = Column(
        String(20),
        nullable=False,
        default="instance",
        comment="instance/kind"
    )

    # FHIR type
    type = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept[] (room type)"
    )

    # FHIR ContactPoint
    telecom = Column(
        JSONB,
        nullable=True,
        comment="FHIR ContactPoint[] (phone, etc.)"
    )

    # FHIR Address
    address = Column(
        JSONB,
        nullable=True,
        comment="FHIR Address"
    )

    # Managing organization
    managing_organization = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Owner organization"
    )

    # Relationships
    organization = relationship("Organization", foreign_keys=[managing_organization])

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, name={self.name})>"
