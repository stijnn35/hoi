"""
SessionTranscript model - Audio transcription storage.
Stores STT results with pgvector embeddings for RAG.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class SessionTranscript(Base, UUIDMixin, TimestampMixin):
    """
    Audio transcription storage for therapy sessions.
    Includes pgvector embeddings for RAG similarity search.
    """

    __tablename__ = "session_transcripts"

    # Encounter reference (one-to-one relationship)
    encounter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("encounters.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Session/encounter reference"
    )

    # Patient reference (denormalized)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient reference"
    )

    # Consent verification
    consent_verified = Column(
        Boolean,
        nullable=False,
        comment="Consent check passed before processing"
    )

    consent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("consents.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to consent record"
    )

    # Audio file metadata
    audio_file_path = Column(
        String(500),
        nullable=True,
        comment="Encrypted audio storage path"
    )

    audio_duration_seconds = Column(
        Integer,
        nullable=True,
        comment="Audio length in seconds"
    )

    # Transcription data
    transcript_text = Column(
        Text,
        nullable=True,
        comment="Full transcription text"
    )

    transcript_segments = Column(
        JSONB,
        nullable=True,
        comment="Time-stamped segments with speaker labels"
    )

    speaker_labels = Column(
        JSONB,
        nullable=True,
        comment="Speaker diarization results"
    )

    # Processing status
    processing_status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="pending/processing/completed/failed"
    )

    # AI model metadata
    ai_model_used = Column(
        String(100),
        nullable=True,
        comment="STT model identifier (e.g., whisper-1)"
    )

    confidence_score = Column(
        Float,
        nullable=True,
        comment="Average confidence score"
    )

    processed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Processing completion timestamp"
    )

    # Vector embedding for RAG (pgvector)
    embedding_vector = Column(
        Vector(1536),  # OpenAI text-embedding-3-small dimension
        nullable=True,
        comment="Vector embedding for similarity search"
    )

    # Relationships
    encounter = relationship("Encounter", back_populates="session_transcript")
    patient = relationship("Patient", back_populates="session_transcripts")
    consent = relationship("Consent", foreign_keys=[consent_id])

    def __repr__(self) -> str:
        return f"<SessionTranscript(id={self.id}, encounter_id={self.encounter_id}, status={self.processing_status})>"

    @property
    def is_completed(self) -> bool:
        """Check if transcription is completed."""
        return self.processing_status == "completed"

    @property
    def has_embedding(self) -> bool:
        """Check if vector embedding exists."""
        return self.embedding_vector is not None

    @property
    def duration_formatted(self) -> str:
        """Format duration as HH:MM:SS."""
        if not self.audio_duration_seconds:
            return "00:00:00"

        hours, remainder = divmod(self.audio_duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
