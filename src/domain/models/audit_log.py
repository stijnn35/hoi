"""
AuditLog model - Immutable audit trail.
GDPR Article 30 compliant audit logging for all data operations.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID

from src.infrastructure.database.base import Base, UUIDMixin


class AuditLog(Base, UUIDMixin):
    """
    Immutable audit trail for GDPR Article 30 compliance.
    Tracks all data access, modifications, and AI queries.

    CRITICAL: This table should have:
    - No update/delete permissions (immutable)
    - Automatic archiving after retention period
    - RLS policy: Only SUPER_ADMIN can read; all users can insert via triggers
    """

    __tablename__ = "audit_logs"

    # Timestamp (indexed for time-based queries)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Operation timestamp"
    )

    # Actor information
    actor_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed action"
    )

    actor_ip_address = Column(
        INET,
        nullable=True,
        comment="Source IP address"
    )

    actor_user_agent = Column(
        Text,
        nullable=True,
        comment="Browser/client user agent"
    )

    # Action details
    action_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="CREATE/READ/UPDATE/DELETE/LOGIN/LOGOUT/AI_QUERY"
    )

    # Resource information
    resource_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Table/entity name (e.g., 'patient', 'clinical_note')"
    )

    resource_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Affected record ID"
    )

    # Patient context (for healthcare-specific filtering)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Patient context if applicable"
    )

    # Change details
    changes = Column(
        JSONB,
        nullable=True,
        comment="Before/after values (PII-stripped for non-admins)"
    )

    # AI query tracking
    query_text = Column(
        Text,
        nullable=True,
        comment="AI/RAG query text if action_type=AI_QUERY"
    )

    # Authorization result
    access_granted = Column(
        Boolean,
        nullable=False,
        comment="Whether access was granted"
    )

    denial_reason = Column(
        Text,
        nullable=True,
        comment="Reason for access denial"
    )

    # Session tracking
    session_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Session identifier"
    )

    request_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Request trace ID for distributed tracing"
    )

    # Additional metadata
    metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional context (endpoint, method, etc.)"
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action_type}, resource={self.resource_type})>"

    @property
    def is_success(self) -> bool:
        """Check if action was successful."""
        return self.access_granted

    @property
    def is_failed(self) -> bool:
        """Check if action failed."""
        return not self.access_granted


class AnonymizationLog(Base, UUIDMixin, TimestampMixin):
    """
    Track PII anonymization operations.
    Required for GDPR Article 30 processing records.
    """

    __tablename__ = "anonymization_logs"

    # Source data
    original_resource_type = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Source entity type"
    )

    original_resource_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Source record ID"
    )

    # Anonymization method
    anonymization_method = Column(
        String(50),
        nullable=False,
        comment="replace/redact/hash/mask/synthetic"
    )

    # PII entities detected
    pii_entities_detected = Column(
        JSONB,
        nullable=False,
        comment="Entity types found by Presidio (PERSON, EMAIL, etc.)"
    )

    # Anonymized output
    anonymized_data = Column(
        JSONB,
        nullable=False,
        comment="Anonymized result"
    )

    # Who requested
    requested_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="User who requested anonymization"
    )

    # Purpose
    purpose = Column(
        String(100),
        nullable=False,
        comment="research/export/analytics/transfer"
    )

    # Consent verification
    consent_verified = Column(
        Boolean,
        nullable=False,
        comment="Consent check passed"
    )

    consent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("consents.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to consent record"
    )

    # Relationships
    user = relationship("User", foreign_keys=[requested_by])
    consent = relationship("Consent", foreign_keys=[consent_id])

    def __repr__(self) -> str:
        return f"<AnonymizationLog(id={self.id}, resource={self.original_resource_type}, method={self.anonymization_method})>"


# Import TimestampMixin for AnonymizationLog
from src.infrastructure.database.base import TimestampMixin
from sqlalchemy.orm import relationship
from sqlalchemy import Float
