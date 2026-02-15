"""
Practitioner model - FHIR Practitioner resource.
Healthcare professionals providing care.
"""

from sqlalchemy import Boolean, Column, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Practitioner(Base, UUIDMixin, TimestampMixin):
    """
    FHIR Practitioner resource.
    Represents healthcare professionals (psychologists, psychiatrists, therapists).
    """

    __tablename__ = "practitioners"

    # Link to user account
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Reference to user account"
    )

    # FHIR identifier - array of identifiers (BIG number, AGB code, etc.)
    identifier = Column(
        JSONB,
        nullable=False,
        comment="FHIR Identifier[] (BIG, AGB codes)"
    )

    # FHIR active status
    active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Practitioner active status"
    )

    # FHIR HumanName - array of names
    name = Column(
        JSONB,
        nullable=False,
        comment="FHIR HumanName[] (official, nickname, etc.)"
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

    # FHIR gender
    gender = Column(
        String(20),
        nullable=True,
        comment="FHIR gender (male/female/other/unknown)"
    )

    # Birth date
    birth_date = Column(
        Date,
        nullable=True,
        comment="Date of birth"
    )

    # FHIR Qualification - array of qualifications
    qualification = Column(
        JSONB,
        nullable=True,
        comment="FHIR Qualification[] (degrees, licenses, certifications)"
    )

    # Communication - languages spoken
    communication = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept[] of languages"
    )

    # Specialty codes (SNOMED CT)
    specialty_codes = Column(
        JSONB,
        nullable=True,
        comment="SNOMED CT specialty codes"
    )

    # Relationships
    user = relationship("User", back_populates="practitioner")

    # Note: encounters, observations, etc. will reference this via JSONB participant field

    def __repr__(self) -> str:
        return f"<Practitioner(id={self.id}, user_id={self.user_id})>"

    @property
    def official_name(self) -> dict:
        """Get the official name from the name array."""
        if not self.name:
            return {}

        for name_item in self.name:
            if name_item.get("use") == "official":
                return name_item

        # Return first name if no official name found
        return self.name[0] if self.name else {}

    @property
    def full_name(self) -> str:
        """Get formatted full name."""
        official = self.official_name
        if not official:
            return "Unknown"

        given = " ".join(official.get("given", []))
        family = official.get("family", "")
        prefix = " ".join(official.get("prefix", []))

        parts = [prefix, given, family]
        return " ".join(part for part in parts if part).strip()

    @property
    def primary_identifier(self) -> dict:
        """Get primary identifier (BIG number)."""
        if not self.identifier:
            return {}

        for ident in self.identifier:
            if ident.get("use") == "official" or ident.get("system") == "urn:oid:2.16.528.1.1007.3.1":
                return ident

        return self.identifier[0] if self.identifier else {}
