"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables for the psychiatric EHR system."""

    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')

    # ============================================================================
    # Authentication & Authorization Tables
    # ============================================================================

    # users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('mfa_secret', sa.String(255), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_token', sa.String(255), nullable=True),
        sa.Column('verification_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # roles table
    op.create_table(
        'roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role'),
    )

    # ============================================================================
    # FHIR Resource Tables
    # ============================================================================

    # organizations table
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('identifier', postgresql.JSONB(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('type', postgresql.JSONB(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('alias', postgresql.JSONB(), nullable=True),
        sa.Column('telecom', postgresql.JSONB(), nullable=True),
        sa.Column('address', postgresql.JSONB(), nullable=True),
        sa.Column('part_of', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['part_of'], ['organizations.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_organizations_identifier', 'organizations', ['identifier'], postgresql_using='gin')

    # practitioners table
    op.create_table(
        'practitioners',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('identifier', postgresql.JSONB(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('name', postgresql.JSONB(), nullable=False),
        sa.Column('telecom', postgresql.JSONB(), nullable=True),
        sa.Column('address', postgresql.JSONB(), nullable=True),
        sa.Column('gender', sa.String(20), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('qualification', postgresql.JSONB(), nullable=True),
        sa.Column('communication', postgresql.JSONB(), nullable=True),
        sa.Column('specialty_codes', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_practitioners_identifier', 'practitioners', ['identifier'], postgresql_using='gin')

    # patients table
    op.create_table(
        'patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, unique=True, index=True),
        sa.Column('identifier', postgresql.JSONB(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('name', postgresql.JSONB(), nullable=False),
        sa.Column('telecom', postgresql.JSONB(), nullable=True),
        sa.Column('gender', sa.String(20), nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False, index=True),
        sa.Column('deceased_boolean', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deceased_datetime', sa.DateTime(timezone=True), nullable=True),
        sa.Column('address', postgresql.JSONB(), nullable=True),
        sa.Column('marital_status', postgresql.JSONB(), nullable=True),
        sa.Column('contact', postgresql.JSONB(), nullable=True),
        sa.Column('communication', postgresql.JSONB(), nullable=True),
        sa.Column('general_practitioner', postgresql.JSONB(), nullable=True),
        sa.Column('managing_organization', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['managing_organization'], ['organizations.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_patients_identifier', 'patients', ['identifier'], postgresql_using='gin')

    # locations table
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('identifier', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('alias', postgresql.JSONB(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('mode', sa.String(20), nullable=False, server_default='instance'),
        sa.Column('type', postgresql.JSONB(), nullable=True),
        sa.Column('telecom', postgresql.JSONB(), nullable=True),
        sa.Column('address', postgresql.JSONB(), nullable=True),
        sa.Column('managing_organization', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['managing_organization'], ['organizations.id'], ondelete='SET NULL'),
    )

    # ============================================================================
    # Clinical Data Tables
    # ============================================================================

    # consents table
    op.create_table(
        'consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('scope', sa.String(50), nullable=False),
        sa.Column('category', postgresql.JSONB(), nullable=False),
        sa.Column('date_time', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('performer', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('organization', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('policy_rule', sa.String(100), nullable=False),
        sa.Column('provision_type', sa.String(20), nullable=False, server_default='permit'),
        sa.Column('provision_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provision_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provision_purpose', postgresql.JSONB(), nullable=False),
        sa.Column('provision_data_scope', postgresql.JSONB(), nullable=False),
        sa.Column('ai_processing_allowed', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('rag_chatbot_allowed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('research_allowed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('signature_blob', sa.LargeBinary(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['performer'], ['practitioners.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization'], ['organizations.id'], ondelete='SET NULL'),
    )

    # encounters table
    op.create_table(
        'encounters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('identifier', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('class', postgresql.JSONB(), nullable=False),
        sa.Column('type', postgresql.JSONB(), nullable=True),
        sa.Column('service_type', postgresql.JSONB(), nullable=True),
        sa.Column('priority', postgresql.JSONB(), nullable=True),
        sa.Column('subject', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('participant', postgresql.JSONB(), nullable=False),
        sa.Column('appointment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('length_minutes', sa.Integer(), nullable=True),
        sa.Column('reason_code', postgresql.JSONB(), nullable=True),
        sa.Column('diagnosis', postgresql.JSONB(), nullable=True),
        sa.Column('location', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('service_provider', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('has_audio_recording', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('audio_consent_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['subject'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location'], ['locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['service_provider'], ['organizations.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_encounters_participant', 'encounters', ['participant'], postgresql_using='gin')

    # observations table
    op.create_table(
        'observations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('identifier', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, index=True),
        sa.Column('category', postgresql.JSONB(), nullable=False),
        sa.Column('code', postgresql.JSONB(), nullable=False),
        sa.Column('subject', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('encounter', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('effective_datetime', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('issued', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('performer', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('value_quantity', postgresql.JSONB(), nullable=True),
        sa.Column('value_codeable_concept', postgresql.JSONB(), nullable=True),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('data_absent_reason', postgresql.JSONB(), nullable=True),
        sa.Column('interpretation', postgresql.JSONB(), nullable=True),
        sa.Column('note', postgresql.JSONB(), nullable=True),
        sa.Column('body_site', postgresql.JSONB(), nullable=True),
        sa.Column('method', postgresql.JSONB(), nullable=True),
        sa.Column('reference_range', postgresql.JSONB(), nullable=True),
        sa.Column('has_member', postgresql.JSONB(), nullable=True),
        sa.Column('component', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['subject'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['encounter'], ['encounters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['performer'], ['practitioners.id'], ondelete='SET NULL'),
    )
    op.create_index('idx_observations_code', 'observations', ['code'], postgresql_using='gin')
    op.create_index('idx_observations_subject_date', 'observations', ['subject', 'effective_datetime'])

    # clinical_notes table
    op.create_table(
        'clinical_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('note_type', sa.String(50), nullable=False, index=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft', index=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_encrypted', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('autosave_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_autosave_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ai_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('ai_summary_evidence', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['practitioners.id'], ondelete='SET NULL'),
    )

    # clinical_note_versions table
    op.create_table(
        'clinical_note_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('clinical_note_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['clinical_note_id'], ['clinical_notes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['practitioners.id'], ondelete='SET NULL'),
        sa.UniqueConstraint('clinical_note_id', 'version_number', name='uq_note_version'),
    )

    # ============================================================================
    # AI Integration Tables
    # ============================================================================

    # session_transcripts table
    op.create_table(
        'session_transcripts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('consent_verified', sa.Boolean(), nullable=False),
        sa.Column('consent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('audio_file_path', sa.String(500), nullable=True),
        sa.Column('audio_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('transcript_text', sa.Text(), nullable=True),
        sa.Column('transcript_segments', postgresql.JSONB(), nullable=True),
        sa.Column('speaker_labels', postgresql.JSONB(), nullable=True),
        sa.Column('processing_status', sa.String(20), nullable=False, server_default='pending', index=True),
        sa.Column('ai_model_used', sa.String(100), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('embedding_vector', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['consent_id'], ['consents.id'], ondelete='SET NULL'),
    )

    # Create HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX idx_transcripts_embedding
        ON session_transcripts
        USING hnsw (embedding_vector vector_cosine_ops)
    """)

    # ai_summaries table
    op.create_table(
        'ai_summaries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_type', sa.String(50), nullable=False, index=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('summary_type', sa.String(50), nullable=False, index=True),
        sa.Column('summary_text', sa.Text(), nullable=False),
        sa.Column('evidence_links', postgresql.JSONB(), nullable=False),
        sa.Column('key_themes', postgresql.JSONB(), nullable=True),
        sa.Column('risk_flags', postgresql.JSONB(), nullable=True),
        sa.Column('ai_model_used', sa.String(100), nullable=False),
        sa.Column('generated_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reviewed', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('embedding_vector', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_by'], ['practitioners.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['practitioners.id'], ondelete='SET NULL'),
    )

    # Create HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX idx_summaries_embedding
        ON ai_summaries
        USING hnsw (embedding_vector vector_cosine_ops)
    """)

    # rag_query_logs table
    op.create_table(
        'rag_query_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('practitioner_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_embedding', Vector(1536), nullable=False),
        sa.Column('rbac_scope_filter', postgresql.JSONB(), nullable=False),
        sa.Column('retrieved_documents', postgresql.JSONB(), nullable=False),
        sa.Column('llm_response', sa.Text(), nullable=False),
        sa.Column('sources_cited', postgresql.JSONB(), nullable=False),
        sa.Column('patient_ids_accessed', postgresql.JSONB(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('feedback_rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.ForeignKeyConstraint(['practitioner_id'], ['practitioners.id'], ondelete='SET NULL'),
    )

    # ============================================================================
    # Audit & Compliance Tables
    # ============================================================================

    # audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('actor_ip_address', postgresql.INET(), nullable=True),
        sa.Column('actor_user_agent', sa.Text(), nullable=True),
        sa.Column('action_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_type', sa.String(100), nullable=False, index=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('changes', postgresql.JSONB(), nullable=True),
        sa.Column('query_text', sa.Text(), nullable=True),
        sa.Column('access_granted', sa.Boolean(), nullable=False),
        sa.Column('denial_reason', sa.Text(), nullable=True),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='SET NULL'),
    )

    # anonymization_logs table
    op.create_table(
        'anonymization_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('original_resource_type', sa.String(100), nullable=False, index=True),
        sa.Column('original_resource_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('anonymization_method', sa.String(50), nullable=False),
        sa.Column('pii_entities_detected', postgresql.JSONB(), nullable=False),
        sa.Column('anonymized_data', postgresql.JSONB(), nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('purpose', sa.String(100), nullable=False),
        sa.Column('consent_verified', sa.Boolean(), nullable=False),
        sa.Column('consent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['consent_id'], ['consents.id'], ondelete='SET NULL'),
    )

    # ============================================================================
    # ROM Tables
    # ============================================================================

    # rom_questionnaires table
    op.create_table(
        'rom_questionnaires',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('code', sa.String(50), nullable=False, unique=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('loinc_code', sa.String(20), nullable=True),
        sa.Column('items', postgresql.JSONB(), nullable=False),
        sa.Column('scoring_algorithm', postgresql.JSONB(), nullable=False),
        sa.Column('interpretation_ranges', postgresql.JSONB(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # rom_responses table
    op.create_table(
        'rom_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('questionnaire_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('encounter_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('practitioner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('authored_datetime', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('responses', postgresql.JSONB(), nullable=False),
        sa.Column('calculated_scores', postgresql.JSONB(), nullable=False),
        sa.Column('interpretation', postgresql.JSONB(), nullable=True),
        sa.Column('observation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['questionnaire_id'], ['rom_questionnaires.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['practitioner_id'], ['practitioners.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['observation_id'], ['observations.id'], ondelete='SET NULL'),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('rom_responses')
    op.drop_table('rom_questionnaires')
    op.drop_table('anonymization_logs')
    op.drop_table('audit_logs')
    op.drop_table('rag_query_logs')
    op.drop_table('ai_summaries')
    op.drop_table('session_transcripts')
    op.drop_table('clinical_note_versions')
    op.drop_table('clinical_notes')
    op.drop_table('observations')
    op.drop_table('encounters')
    op.drop_table('consents')
    op.drop_table('locations')
    op.drop_table('patients')
    op.drop_table('practitioners')
    op.drop_table('organizations')
    op.drop_table('user_roles')
    op.drop_table('roles')
    op.drop_table('users')
