"""
Consent model - FHIR Consent resource.
Granular consent tracking for GDPR/AVG compliance and AI processing.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Consent(Base, UUIDMixin, TimestampMixin):
    """
    FHIR Consent resource.
    Tracks patient consent for treatment, AI processing, and research.
    Critical for GDPR/AVG Article 9.2(a) compliance.
    """

    __tablename__ = "consents"

    # Patient reference
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient who gave consent"
    )

    # FHIR status
    status = Column(
        String(20),
        nullable=False,
        index=True,
        comment="active/inactive/rejected/proposed"
    )

    # FHIR scope
    scope = Column(
        String(50),
        nullable=False,
        comment="patient-privacy/research/treatment"
    )

    # FHIR category - array of categories
    category = Column(
        JSONB,
        nullable=False,
        comment="FHIR CodeableConcept[] (consent category)"
    )

    # When consent was given
    date_time = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When consent was given"
    )

    # Who obtained the consent
    performer = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=True,
        comment="Practitioner who obtained consent"
    )

    # Organization context
    organization = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Organization reference"
    )

    # Legal basis (AVG/GDPR)
    policy_rule = Column(
        String(100),
        nullable=False,
        comment="Legal basis (e.g., AVG Art. 9.2a)"
    )

    # FHIR provision type
    provision_type = Column(
        String(20),
        nullable=False,
        default="permit",
        comment="permit/deny"
    )

    # Provision period
    provision_period_start = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Consent valid from"
    )

    provision_period_end = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Consent valid until"
    )

    # Purpose of consent
    provision_purpose = Column(
        JSONB,
        nullable=False,
        comment="FHIR Coding[] (treatment/AI/research purposes)"
    )

    # Data scope
    provision_data_scope = Column(
        JSONB,
        nullable=False,
        comment="What data types are consented"
    )

    # Psychology-specific AI consent flags
    ai_processing_allowed = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="AI STT/Summarization consent flag"
    )

    rag_chatbot_allowed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="RAG query inclusion consent"
    )

    research_allowed = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Anonymized research consent"
    )

    # Digital signature
    signature_blob = Column(
        LargeBinary,
        nullable=True,
        comment="Digital signature (PDF/image)"
    )

    # Relationships
    patient = relationship("Patient", back_populates="consents")
    practitioner = relationship("Practitioner", foreign_keys=[performer])
    organization_ref = relationship("Organization", foreign_keys=[organization])

    def __repr__(self) -> str:
        return f"<Consent(id={self.id}, patient_id={self.patient_id}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if consent is currently active."""
        if self.status != "active":
            return False

        from datetime import datetime
        now = datetime.utcnow()

        if self.provision_period_start and now < self.provision_period_start:
            return False

        if self.provision_period_end and now > self.provision_period_end:
            return False

        return True

    @property
    def allows_ai_processing(self) -> bool:
        """Check if AI processing is allowed and consent is active."""
        return self.is_active and self.ai_processing_allowed

    @property
    def allows_rag(self) -> bool:
        """Check if RAG chatbot access is allowed and consent is active."""
        return self.is_active and self.rag_chatbot_allowed
