"""
ClinicalNote model - FHIR DocumentReference/DiagnosticReport.
Clinical documentation with auto-save functionality.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class ClinicalNote(Base, UUIDMixin, TimestampMixin):
    """
    Clinical documentation model.
    Represents SOAP notes, progress notes, intake assessments, etc.
    Includes auto-save functionality to prevent data loss.
    """

    __tablename__ = "clinical_notes"

    # Encounter reference
    encounter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("encounters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Encounter reference"
    )

    # Patient reference (denormalized for quick access)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient reference"
    )

    # Author
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="Note author"
    )

    # Note type
    note_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="SOAP/Progress/Intake/Discharge/Assessment"
    )

    # Status
    status = Column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
        comment="draft/final/amended/entered-in-error"
    )

    # Title
    title = Column(
        String(255),
        nullable=False,
        comment="Note title"
    )

    # Content (encrypted)
    content = Column(
        Text,
        nullable=False,
        comment="Note content (may be encrypted)"
    )

    content_encrypted = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Encryption flag"
    )

    # Auto-save tracking
    autosave_version = Column(
        Integer,
        default=1,
        nullable=False,
        comment="Auto-save version counter"
    )

    last_autosave_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last auto-save timestamp"
    )

    # Finalization
    finalized_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When note was marked final"
    )

    # AI-generated content flags
    ai_generated = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="AI-assisted flag"
    )

    ai_summary = Column(
        Text,
        nullable=True,
        comment="AI-generated summary"
    )

    ai_summary_evidence = Column(
        JSONB,
        nullable=True,
        comment="Evidence links to transcript segments"
    )

    # Relationships
    encounter = relationship("Encounter", back_populates="clinical_notes")
    patient = relationship("Patient", back_populates="clinical_notes")
    author = relationship("Practitioner", foreign_keys=[author_id])
    versions = relationship("ClinicalNoteVersion", back_populates="clinical_note", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ClinicalNote(id={self.id}, type={self.note_type}, status={self.status})>"

    @property
    def is_draft(self) -> bool:
        """Check if note is still in draft status."""
        return self.status == "draft"

    @property
    def is_final(self) -> bool:
        """Check if note has been finalized."""
        return self.status == "final"

    @property
    def can_edit(self) -> bool:
        """Check if note can be edited (only drafts)."""
        return self.is_draft


class ClinicalNoteVersion(Base, UUIDMixin):
    """
    Version history for clinical notes.
    Maintains audit trail of all changes.
    """

    __tablename__ = "clinical_note_versions"

    # Parent note
    clinical_note_id = Column(
        UUID(as_uuid=True),
        ForeignKey("clinical_notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent clinical note"
    )

    # Version number
    version_number = Column(
        Integer,
        nullable=False,
        comment="Incremental version number"
    )

    # Content snapshot
    content = Column(
        Text,
        nullable=False,
        comment="Content at this version"
    )

    # Who changed
    changed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=False,
        comment="Who made the change"
    )

    # Change metadata
    change_reason = Column(
        Text,
        nullable=True,
        comment="Reason for amendment (if status=amended)"
    )

    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Change timestamp"
    )

    # Relationships
    clinical_note = relationship("ClinicalNote", back_populates="versions")
    practitioner = relationship("Practitioner", foreign_keys=[changed_by])

    def __repr__(self) -> str:
        return f"<ClinicalNoteVersion(note_id={self.clinical_note_id}, version={self.version_number})>"
