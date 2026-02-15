"""
Observation model - FHIR Observation resource.
ROM scores, vital signs, and clinical assessments.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Observation(Base, UUIDMixin, TimestampMixin):
    """
    FHIR Observation resource.
    Represents ROM scores (BSI, GAF), vital signs, and clinical assessments.
    """

    __tablename__ = "observations"

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
        comment="registered/preliminary/final/amended/cancelled"
    )

    # Category
    category = Column(
        JSONB,
        nullable=False,
        comment="FHIR CodeableConcept[] (vital-signs/social-history/survey)"
    )

    # Code (what was observed)
    code = Column(
        JSONB,
        nullable=False,
        comment="FHIR CodeableConcept (LOINC/SNOMED code for BSI, GAF, etc.)"
    )

    # Patient (subject)
    subject = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient reference"
    )

    # Encounter context
    encounter = Column(
        UUID(as_uuid=True),
        ForeignKey("encounters.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Encounter context"
    )

    # Effective datetime
    effective_datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When observation was made"
    )

    # Issued timestamp
    issued = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        comment="When result was published"
    )

    # Performer (who observed)
    performer = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=True,
        comment="Who performed observation"
    )

    # Value types (only one should be populated)
    value_quantity = Column(
        JSONB,
        nullable=True,
        comment="FHIR Quantity (numeric value + unit)"
    )

    value_codeable_concept = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept (coded value)"
    )

    value_string = Column(
        Text,
        nullable=True,
        comment="String value"
    )

    value_boolean = Column(
        Boolean,
        nullable=True,
        comment="Boolean value"
    )

    value_integer = Column(
        Integer,
        nullable=True,
        comment="Integer value"
    )

    # Data absent reason
    data_absent_reason = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept (why no value)"
    )

    # Interpretation
    interpretation = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept[] (High/Low/Normal)"
    )

    # Note
    note = Column(
        JSONB,
        nullable=True,
        comment="FHIR Annotation[] (comments)"
    )

    # Body site
    body_site = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept (body location)"
    )

    # Method
    method = Column(
        JSONB,
        nullable=True,
        comment="FHIR CodeableConcept (how performed)"
    )

    # Reference range
    reference_range = Column(
        JSONB,
        nullable=True,
        comment="FHIR Observation.referenceRange[]"
    )

    # Has member (for observation groups/panels)
    has_member = Column(
        JSONB,
        nullable=True,
        comment="FHIR Reference[] to related observations"
    )

    # Component (multi-component observations)
    component = Column(
        JSONB,
        nullable=True,
        comment="FHIR Observation.component[] (e.g., BP systolic/diastolic)"
    )

    # Relationships
    patient = relationship("Patient", back_populates="observations")
    encounter_ref = relationship("Encounter", back_populates="observations")
    practitioner = relationship("Practitioner", foreign_keys=[performer])

    def __repr__(self) -> str:
        return f"<Observation(id={self.id}, patient_id={self.subject}, code={self.code})>"

    @property
    def numeric_value(self) -> float | None:
        """Extract numeric value from value_quantity."""
        if self.value_quantity and isinstance(self.value_quantity, dict):
            return self.value_quantity.get("value")
        if self.value_integer is not None:
            return float(self.value_integer)
        return None

    @property
    def is_rom(self) -> bool:
        """Check if this is a ROM observation."""
        if not self.code:
            return False

        rom_codes = ["BSI", "GAF", "PHQ-9", "GAD-7", "44249-1", "69737-5", "68473-8"]
        code_value = self.code.get("coding", [{}])[0].get("code", "")

        return code_value in rom_codes
