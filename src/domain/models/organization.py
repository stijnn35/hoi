"""
Organization model - FHIR Organization resource.
Healthcare organizations, clinics, and practices.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    """
    FHIR Organization resource.
    Represents clinics, practices, hospitals, and other healthcare organizations.
    """

    __tablename__ = "organizations"

    # FHIR identifier - array of identifiers (KVK, AGB code, etc.)
    identifier = Column(
        JSONB,
        nullable=False,
        comment="FHIR Identifier[] (KVK, AGB codes)"
    )

    # FHIR active status
    active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Organization active status"
    )

    # FHIR type - array of organization types
    type = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept[] (clinic, hospital, etc.)"
    )

    # Organization name
    name = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Organization name"
    )

    # Alias names
    alias = Column(
        JSONB,
        nullable=True,
        comment="Alternative names"
    )

    # FHIR ContactPoint - array of telecom info
    telecom = Column(
        JSONB,
        nullable=True,
        comment="FHIR ContactPoint[] (phone, email, etc.)"
    )

    # FHIR Address - array of addresses
    address = Column(
        JSONB,
        nullable=True,
        comment="FHIR Address[]"
    )

    # Part of (parent organization)
    part_of = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent organization reference"
    )

    # Relationships
    parent_organization = relationship(
        "Organization",
        remote_side="Organization.id",
        backref="sub_organizations"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"

    @property
    def primary_identifier(self) -> dict:
        """Get primary identifier (KVK number)."""
        if not self.identifier:
            return {}

        for ident in self.identifier:
            if ident.get("system") == "urn:oid:2.16.528.1.1007.99.101":  # KVK
                return ident

        return self.identifier[0] if self.identifier else {}
