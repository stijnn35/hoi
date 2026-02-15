"""
AISummary model - AI-generated summaries with evidence links.
Stores LLM-generated summaries with citations and pgvector embeddings.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class AISummary(Base, UUIDMixin, TimestampMixin):
    """
    AI-generated summaries with evidence links.
    Ensures all AI-generated content has traceable citations.
    """

    __tablename__ = "ai_summaries"

    # Source reference (polymorphic)
    source_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="transcript/note/encounter/longitudinal"
    )

    source_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="Reference to source entity"
    )

    # Patient reference (denormalized)
    patient_id = Column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Patient reference"
    )

    # Summary type
    summary_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="session/longitudinal/crisis/progress"
    )

    # Summary content
    summary_text = Column(
        Text,
        nullable=False,
        comment="Generated summary text"
    )

    # Evidence links (citations to source)
    evidence_links = Column(
        JSONB,
        nullable=False,
        comment="Citations to source segments with timestamps/line numbers"
    )

    # Extracted insights
    key_themes = Column(
        JSONB,
        nullable=True,
        comment="Extracted themes and topics"
    )

    risk_flags = Column(
        JSONB,
        nullable=True,
        comment="Identified risk factors (suicide, harm, etc.)"
    )

    # AI model metadata
    ai_model_used = Column(
        String(100),
        nullable=False,
        comment="Model identifier (e.g., gpt-4-turbo)"
    )

    # Who requested the summary
    generated_by = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=False,
        comment="Requesting practitioner"
    )

    # Human review status
    reviewed = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Human review completed flag"
    )

    reviewed_by = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reviewer"
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Review timestamp"
    )

    # Vector embedding for RAG (pgvector)
    embedding_vector = Column(
        Vector(1536),  # OpenAI text-embedding-3-small dimension
        nullable=True,
        comment="Vector embedding for similarity search"
    )

    # Relationships
    patient = relationship("Patient", foreign_keys=[patient_id])
    generator = relationship("Practitioner", foreign_keys=[generated_by])
    reviewer = relationship("Practitioner", foreign_keys=[reviewed_by])

    def __repr__(self) -> str:
        return f"<AISummary(id={self.id}, type={self.summary_type}, reviewed={self.reviewed})>"

    @property
    def is_reviewed(self) -> bool:
        """Check if summary has been reviewed by a human."""
        return self.reviewed

    @property
    def has_evidence(self) -> bool:
        """Check if evidence links exist."""
        return bool(self.evidence_links)

    @property
    def evidence_count(self) -> int:
        """Count number of evidence citations."""
        if not self.evidence_links:
            return 0
        if isinstance(self.evidence_links, list):
            return len(self.evidence_links)
        return 0


class RAGQueryLog(Base, UUIDMixin):
    """
    RAG chatbot query tracking.
    Audit trail for all RAG queries with RBAC scope enforcement.
    """

    __tablename__ = "rag_query_logs"

    # Who queried
    practitioner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("practitioners.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
        comment="Querying practitioner"
    )

    # Query details
    query_text = Column(
        Text,
        nullable=False,
        comment="User question"
    )

    query_embedding = Column(
        Vector(1536),
        nullable=False,
        comment="Query vector for similarity search"
    )

    # RBAC scope filter applied
    rbac_scope_filter = Column(
        JSONB,
        nullable=False,
        comment="RLS filters applied to the query"
    )

    # Retrieved documents
    retrieved_documents = Column(
        JSONB,
        nullable=False,
        comment="Retrieved context document IDs and scores"
    )

    # LLM response
    llm_response = Column(
        Text,
        nullable=False,
        comment="Generated answer"
    )

    # Sources cited
    sources_cited = Column(
        JSONB,
        nullable=False,
        comment="Source references in response"
    )

    # Patient data accessed
    patient_ids_accessed = Column(
        JSONB,
        nullable=False,
        comment="Patient IDs whose data was retrieved"
    )

    # Quality metrics
    confidence_score = Column(
        Float,
        nullable=True,
        comment="Response confidence score"
    )

    feedback_rating = Column(
        Integer,
        nullable=True,
        comment="User rating 1-5"
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        index=True,
        comment="Query timestamp"
    )

    # Relationships
    practitioner = relationship("Practitioner", foreign_keys=[practitioner_id])

    def __repr__(self) -> str:
        return f"<RAGQueryLog(id={self.id}, practitioner_id={self.practitioner_id})>"
