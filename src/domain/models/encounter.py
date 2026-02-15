"""
Encounter model - FHIR Encounter resource.
Therapy sessions and clinical interactions.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Encounter(Base, UUIDMixin, TimestampMixin):
    """
    FHIR Encounter resource.
    Represents therapy sessions, consultations, and clinical interactions.
    """

    __tablename__ = "encounters"

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
        index=True,
        comment="planned/arrived/in-progress/finished/cancelled"
    )

    # FHIR class (encounter type)
    class_ = Column(
        "class",
        JSONB,
        nullable=False,
        comment="FHIR Coding (AMB=ambulatory, IMP=inpatient, VR=virtual)"
    )

    # Encounter type
    type = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept[] (intake, therapy session, crisis)"
    )

    # Service type
    service_type = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept (specific service type)"
    )

    # Priority
    priority = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept (urgency level)"
    )

    # Patient (subject)
    subject = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient reference"
    )

    # Participant - array of practitioners and related persons
    participant = Column(
        JSONB,
        nullable=False,
        comment="FHIR Encounter.participant[] (practitioners, interpreters, etc.)"
    )

    # Appointment reference
    appointment_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Link to appointment/scheduling system"
    )

    # Period
    period_start = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Session start time"
    )

    period_end = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Session end time"
    )

    # Length in minutes
    length_minutes = Column(
        Integer,
        nullable=True,
        comment="Duration in minutes"
    )

    # Reason codes
    reason_code = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept[] (reason for encounter)"
    )

    # Diagnosis
    diagnosis = Column(
        JSONB,
        nullable=True,
        comment="FHIR Encounter.diagnosis[] (condition references)"
    )

    # Location
    location = Column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Physical location reference"
    )

    # Service provider
    service_provider = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Organization providing service"
    )

    # Audio recording flags
    has_audio_recording = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Audio file exists for this session"
    )

    audio_consent_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Consent verified for AI processing"
    )

    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    location_ref = relationship("Location", foreign_keys=[location])
    organization = relationship("Organization", foreign_keys=[service_provider])
    observations = relationship("Observation", back_populates="encounter", cascade="all, delete-orphan")
    clinical_notes = relationship("ClinicalNote", back_populates="encounter", cascade="all, delete-orphan")
    session_transcript = relationship("SessionTranscript", back_populates="encounter", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Encounter(id={self.id}, patient_id={self.subject}, status={self.status})>"

    @property
    def is_finished(self) -> bool:
        """Check if encounter is completed."""
        return self.status == "finished"

    @property
    def primary_practitioner(self) -> dict | None:
        """Get primary practitioner from participant array."""
        if not self.participant:
            return None

        for participant in self.participant:
            if participant.get("type", [{}])[0].get("text") == "primary":
                return participant

        # Return first participant if no primary found
        return self.participant[0] if self.participant else None

    @property
    def duration_minutes(self) -> int | None:
        """Calculate duration if not explicitly set."""
        if self.length_minutes:
            return self.length_minutes

        if self.period_start and self.period_end:
            delta = self.period_end - self.period_start
            return int(delta.total_seconds() / 60)

        return None
