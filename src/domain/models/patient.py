"""
Patient model - FHIR Patient resource.
Individuals receiving psychiatric care.
"""

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Patient(Base, UUIDMixin, TimestampMixin):
    """
    FHIR Patient resource.
    Represents individuals receiving psychiatric care.
    """

    __tablename__ = "patients"

    # Optional link to user account (for patient portal access)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        index=True,
        comment="Optional patient portal user account"
    )

    # FHIR identifier - array of identifiers (BSN must be encrypted)
    identifier = Column(
        JSONB,
        nullable=False,
        comment="FHIR Identifier[] (BSN encrypted, MRN, etc.)"
    )

    # FHIR active status
    active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Patient active status"
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

    # FHIR gender (administrative)
    gender = Column(
        String(20),
        nullable=False,
        comment="FHIR gender (male/female/other/unknown)"
    )

    # Birth date
    birth_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date of birth"
    )

    # Deceased status
    deceased_boolean = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Deceased flag"
    )

    deceased_datetime = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Date/time of death"
    )

    # FHIR Address - array of addresses
    address = Column(
        JSONB,
        nullable=True,
        comment="FHIR Address[]"
    )

    # FHIR marital status
    marital_status = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept for marital status"
    )

    # FHIR contact - emergency contacts and next of kin
    contact = Column(
        JSONB,
        nullable=True,
        comment="FHIR Patient.contact[] (emergency contacts)"
    )

    # Communication - language preferences
    communication = Column(
        JSONB,
        nullable=True,
        comment="FHIR Communication[] (language preferences)"
    )

    # General practitioner references
    general_practitioner = Column(
        JSONB,
        nullable=True,
        comment="FHIR Reference[] to general practitioners"
    )

    # Managing organization
    managing_organization = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Managing organization reference"
    )

    # Relationships
    user = relationship("User", back_populates="patient")
    organization = relationship("Organization", foreign_keys=[managing_organization])
    encounters = relationship("Encounter", back_populates="patient", cascade="all, delete-orphan")
    observations = relationship("Observation", back_populates="patient", cascade="all, delete-orphan")
    clinical_notes = relationship("ClinicalNote", back_populates="patient", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="patient", cascade="all, delete-orphan")
    session_transcripts = relationship("SessionTranscript", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, name={self.full_name})>"

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
    def bsn(self) -> str | None:
        """Get BSN (Dutch national ID) if present."""
        if not self.identifier:
            return None

        for ident in self.identifier:
            if ident.get("system") == "urn:oid:2.16.840.1.113883.2.4.6.3":  # BSN OID
                return ident.get("value")

        return None

    @property
    def age(self) -> int | None:
        """Calculate age from birth_date."""
        if not self.birth_date:
            return None

        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )
