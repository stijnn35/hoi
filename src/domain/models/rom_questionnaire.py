"""
ROM Questionnaire models - Routine Outcome Monitoring.
Psychology-specific questionnaires (BSI, GAF, PHQ-9, GAD-7).
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class ROMQuestionnaire(Base, UUIDMixin, TimestampMixin):
    """
    ROM questionnaire definition.
    Defines the structure and scoring algorithm for ROM instruments.
    """

    __tablename__ = "rom_questionnaires"

    # Questionnaire code
    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Questionnaire code (BSI, GAF, PHQ9, GAD7)"
    )

    # Name and description
    name = Column(
        String(255),
        nullable=False,
        comment="Full questionnaire name"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Questionnaire description"
    )

    # Version
    version = Column(
        String(20),
        nullable=False,
        comment="Questionnaire version"
    )

    # LOINC code
    loinc_code = Column(
        String(20),
        nullable=True,
        comment="LOINC code for standardization"
    )

    # Questionnaire structure
    items = Column(
        JSONB,
        nullable=False,
        comment="Question items with response options"
    )

    # Scoring algorithm (Pandas-compatible)
    scoring_algorithm = Column(
        JSONB,
        nullable=False,
        comment="Pandas calculation rules for scoring"
    )

    # Interpretation ranges
    interpretation_ranges = Column(
        JSONB,
        nullable=False,
        comment="Score interpretation (normal/mild/moderate/severe)"
    )

    # Active status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Active status"
    )

    # Relationships
    responses = relationship("ROMResponse", back_populates="questionnaire", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ROMQuestionnaire(id={self.id}, code={self.code}, version={self.version})>"

    @property
    def item_count(self) -> int:
        """Get number of items in questionnaire."""
        if not self.items or not isinstance(self.items, list):
            return 0
        return len(self.items)


class ROMResponse(Base, UUIDMixin, TimestampMixin):
    """
    Patient responses to ROM questionnaires.
    Stores answers and calculated scores.
    """

    __tablename__ = "rom_responses"

    # Questionnaire reference
    questionnaire_id = Column(
        UUID(as_uuid=True),
        ForeignKey("rom_questionnaires.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Questionnaire reference"
    )

    # Patient reference
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient who completed questionnaire"
    )

    # Encounter context
    encounter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("encounters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Encounter context"
    )

    # Practitioner who administered
    practitioner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=False,
        comment="Administering practitioner"
    )

    # When completed
    authored_datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Completion timestamp"
    )

    # Responses
    responses = Column(
        JSONB,
        nullable=False,
        comment="Answer values (item_id: value)"
    )

    # Calculated scores (using Pandas)
    calculated_scores = Column(
        JSONB,
        nullable=False,
        comment="Computed scores and subscales"
    )

    # Interpretation
    interpretation = Column(
        JSONB,
        nullable=True,
        comment="Automated interpretation based on ranges"
    )

    # Linked FHIR Observation
    observation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("observations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Linked FHIR Observation resource"
    )

    # Relationships
    questionnaire = relationship("ROMQuestionnaire", back_populates="responses")
    patient = relationship("Patient", foreign_keys=[patient_id])
    encounter = relationship("Encounter", foreign_keys=[encounter_id])
    practitioner = relationship("Practitioner", foreign_keys=[practitioner_id])
    observation = relationship("Observation", foreign_keys=[observation_id])

    def __repr__(self) -> str:
        return f"<ROMResponse(id={self.id}, questionnaire={self.questionnaire.code if self.questionnaire else 'Unknown'}, patient_id={self.patient_id})>"

    @property
    def total_score(self) -> float | None:
        """Get total/global score if available."""
        if not self.calculated_scores:
            return None
        return self.calculated_scores.get("total_score") or self.calculated_scores.get("global_score")

    @property
    def severity_level(self) -> str | None:
        """Get severity interpretation."""
        if not self.interpretation:
            return None
        return self.interpretation.get("severity")
