# Psychiatric EHR Database Schema (FHIR-Compliant)

## Overview
This database schema is designed for a psychiatric Electronic Patient Dossier (EPD) system with strict FHIR compliance, GDPR/AVG requirements, and AI integration capabilities.

## Core Principles
- **FHIR Compliance**: All clinical entities mapped to HL7 FHIR resources
- **Security**: Row-Level Security (RLS) for multi-tenant isolation
- **Audit**: Immutable audit trail for all operations
- **AI-Ready**: pgvector extension for RAG capabilities
- **GDPR**: Consent management and PII anonymization support

---

## Entity Relationship Diagram

### 1. AUTHENTICATION & AUTHORIZATION

#### users
Primary authentication table for all system users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email (login) |
| username | VARCHAR(100) | UNIQUE, NOT NULL | Username |
| hashed_password | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| is_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| mfa_enabled | BOOLEAN | DEFAULT FALSE | MFA activation flag |
| mfa_secret | VARCHAR(255) | NULLABLE | TOTP secret for MFA |
| created_at | TIMESTAMP | NOT NULL | Account creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| last_login | TIMESTAMP | NULLABLE | Last successful login |
| failed_login_attempts | INTEGER | DEFAULT 0 | Failed login counter |
| locked_until | TIMESTAMP | NULLABLE | Account lock expiry |

**Indexes**: email, username, is_active

---

#### roles
RBAC role definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Role identifier |
| name | VARCHAR(50) | UNIQUE, NOT NULL | Role name (e.g., PSYCHOLOGIST, ADMIN) |
| description | TEXT | NULLABLE | Role description |
| permissions | JSONB | NOT NULL | Permission matrix |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Standard Roles**:
- `SUPER_ADMIN`: Full system access
- `PSYCHOLOGIST`: Clinical practitioner
- `PSYCHIATRIST`: Medical practitioner
- `THERAPIST`: Therapy practitioner
- `ADMIN_STAFF`: Administrative support
- `PATIENT`: Patient portal access
- `RESEARCHER`: Anonymized data access

---

#### user_roles
Many-to-many relationship between users and roles.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Assignment identifier |
| user_id | UUID | FK(users.id), NOT NULL | Reference to user |
| role_id | UUID | FK(roles.id), NOT NULL | Reference to role |
| assigned_at | TIMESTAMP | NOT NULL | Assignment timestamp |
| assigned_by | UUID | FK(users.id), NULLABLE | Who assigned the role |

**Unique Constraint**: (user_id, role_id)

---

### 2. FHIR RESOURCES: PRACTITIONERS & ORGANIZATIONS

#### practitioners
FHIR Practitioner resource - healthcare professionals.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | FHIR Practitioner.id |
| user_id | UUID | FK(users.id), UNIQUE | Link to user account |
| identifier | JSONB | NOT NULL | FHIR Identifier[] (BIG, AGB codes) |
| active | BOOLEAN | DEFAULT TRUE | FHIR active status |
| name | JSONB | NOT NULL | FHIR HumanName[] |
| telecom | JSONB | NULLABLE | FHIR ContactPoint[] |
| address | JSONB | NULLABLE | FHIR Address[] |
| gender | VARCHAR(20) | NULLABLE | FHIR gender (male/female/other) |
| birth_date | DATE | NULLABLE | Date of birth |
| qualification | JSONB | NULLABLE | FHIR Qualification[] (degrees, licenses) |
| communication | JSONB | NULLABLE | Languages spoken |
| specialty_codes | JSONB | NULLABLE | SNOMED CT specialty codes |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: user_id, identifier (GIN), active

---

#### organizations
FHIR Organization resource - clinics/practices.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | FHIR Organization.id |
| identifier | JSONB | NOT NULL | FHIR Identifier[] (KVK, AGB) |
| active | BOOLEAN | DEFAULT TRUE | Organization status |
| type | JSONB | NULLABLE | FHIR CodeableConcept[] |
| name | VARCHAR(255) | NOT NULL | Organization name |
| alias | JSONB | NULLABLE | Alternative names |
| telecom | JSONB | NULLABLE | Contact details |
| address | JSONB | NULLABLE | Physical addresses |
| part_of | UUID | FK(organizations.id), NULLABLE | Parent organization |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: name, active, part_of

---

### 3. FHIR RESOURCES: PATIENTS

#### patients
FHIR Patient resource - individuals receiving care.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | FHIR Patient.id |
| user_id | UUID | FK(users.id), NULLABLE | Optional patient portal access |
| identifier | JSONB | NOT NULL | FHIR Identifier[] (BSN encrypted) |
| active | BOOLEAN | DEFAULT TRUE | Patient status |
| name | JSONB | NOT NULL | FHIR HumanName[] |
| telecom | JSONB | NULLABLE | Contact information |
| gender | VARCHAR(20) | NOT NULL | Administrative gender |
| birth_date | DATE | NOT NULL | Date of birth |
| deceased_boolean | BOOLEAN | DEFAULT FALSE | Deceased flag |
| deceased_datetime | TIMESTAMP | NULLABLE | Date/time of death |
| address | JSONB | NULLABLE | FHIR Address[] |
| marital_status | JSONB | NULLABLE | FHIR CodeableConcept |
| contact | JSONB | NULLABLE | Emergency contacts |
| communication | JSONB | NULLABLE | Language preferences |
| general_practitioner | JSONB | NULLABLE | Reference to GP |
| managing_organization | UUID | FK(organizations.id), NULLABLE | Managing organization |
| created_at | TIMESTAMP | NOT NULL | Registration timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: user_id, identifier (GIN), managing_organization, active
**RLS Policy**: Practitioners can only access patients they have encounters with

---

### 4. CONSENT MANAGEMENT

#### consents
FHIR Consent resource - granular consent tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | FHIR Consent.id |
| patient_id | UUID | FK(patients.id), NOT NULL | Patient reference |
| status | VARCHAR(20) | NOT NULL | active/inactive/rejected |
| scope | VARCHAR(50) | NOT NULL | patient-privacy/research/treatment |
| category | JSONB | NOT NULL | FHIR CodeableConcept[] |
| date_time | TIMESTAMP | NOT NULL | When consent given |
| performer | UUID | FK(practitioners.id), NULLABLE | Who obtained consent |
| organization | UUID | FK(organizations.id), NULLABLE | Organization reference |
| policy_rule | VARCHAR(100) | NOT NULL | Legal basis (AVG Art. 9.2a) |
| provision_type | VARCHAR(20) | NOT NULL | permit/deny |
| provision_period_start | TIMESTAMP | NULLABLE | Consent valid from |
| provision_period_end | TIMESTAMP | NULLABLE | Consent valid until |
| provision_purpose | JSONB | NOT NULL | Purpose codes (treatment/AI/research) |
| provision_data_scope | JSONB | NOT NULL | What data is consented |
| ai_processing_allowed | BOOLEAN | DEFAULT FALSE | AI STT/Summarization consent |
| rag_chatbot_allowed | BOOLEAN | DEFAULT FALSE | RAG query consent |
| research_allowed | BOOLEAN | DEFAULT FALSE | Anonymized research consent |
| signature_blob | BYTEA | NULLABLE | Digital signature |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: patient_id, status, ai_processing_allowed
**RLS Policy**: Practitioners can only view consents for their patients

---

### 5. CLINICAL ENCOUNTERS

#### encounters
FHIR Encounter resource - therapy sessions/appointments.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | FHIR Encounter.id |
| identifier | JSONB | NULLABLE | Business identifiers |
| status | VARCHAR(20) | NOT NULL | planned/in-progress/finished/cancelled |
| class | JSONB | NOT NULL | FHIR Coding (AMB, IMP, VR) |
| type | JSONB | NULLABLE | FHIR CodeableConcept[] (session type) |
| service_type | JSONB | NULLABLE | Specific service (intake, therapy) |
| priority | JSONB | NULLABLE | Urgency |
| subject | UUID | FK(patients.id), NOT NULL | Patient reference |
| participant | JSONB | NOT NULL | Practitioner/RelatedPerson array |
| appointment_id | UUID | NULLABLE | Link to scheduling system |
| period_start | TIMESTAMP | NOT NULL | Session start time |
| period_end | TIMESTAMP | NULLABLE | Session end time |
| length_minutes | INTEGER | NULLABLE | Duration in minutes |
| reason_code | JSONB | NULLABLE | FHIR CodeableConcept[] (diagnosis) |
| diagnosis | JSONB | NULLABLE | FHIR Diagnosis[] references |
| location | UUID | FK(locations.id), NULLABLE | Physical location |
| service_provider | UUID | FK(organizations.id), NULLABLE | Organization |
| has_audio_recording | BOOLEAN | DEFAULT FALSE | Audio file exists |
| audio_consent_verified | BOOLEAN | DEFAULT FALSE | Consent check for AI |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: subject, status, period_start, participant (GIN)
**RLS Policy**: Practitioners can only access encounters they participated in

---

#### locations
FHIR Location resource - physical therapy rooms.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | FHIR Location.id |
| identifier | JSONB | NULLABLE | Business identifiers |
| status | VARCHAR(20) | NOT NULL | active/suspended/inactive |
| name | VARCHAR(255) | NOT NULL | Location name |
| alias | JSONB | NULLABLE | Alternative names |
| description | TEXT | NULLABLE | Location description |
| mode | VARCHAR(20) | NOT NULL | instance/kind |
| type | JSONB | NULLABLE | FHIR CodeableConcept[] |
| telecom | JSONB | NULLABLE | Contact details |
| address | JSONB | NULLABLE | Physical address |
| managing_organization | UUID | FK(organizations.id), NULLABLE | Owner organization |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

---

### 6. CLINICAL OBSERVATIONS & ROM

#### observations
FHIR Observation resource - ROM scores, vital signs, assessments.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | FHIR Observation.id |
| identifier | JSONB | NULLABLE | Business identifiers |
| status | VARCHAR(20) | NOT NULL | registered/final/amended |
| category | JSONB | NOT NULL | vital-signs/social-history/survey |
| code | JSONB | NOT NULL | LOINC/SNOMED code (BSI, GAF, etc.) |
| subject | UUID | FK(patients.id), NOT NULL | Patient reference |
| encounter | UUID | FK(encounters.id), NULLABLE | Encounter context |
| effective_datetime | TIMESTAMP | NOT NULL | Observation date/time |
| issued | TIMESTAMP | NOT NULL | When result published |
| performer | UUID | FK(practitioners.id), NULLABLE | Who performed observation |
| value_quantity | JSONB | NULLABLE | Numeric value + unit |
| value_codeable_concept | JSONB | NULLABLE | Coded value |
| value_string | TEXT | NULLABLE | String value |
| value_boolean | BOOLEAN | NULLABLE | Boolean value |
| value_integer | INTEGER | NULLABLE | Integer value |
| data_absent_reason | JSONB | NULLABLE | Why no value |
| interpretation | JSONB | NULLABLE | High/Low/Normal |
| note | JSONB | NULLABLE | Comments |
| body_site | JSONB | NULLABLE | Body site |
| method | JSONB | NULLABLE | How performed |
| reference_range | JSONB | NULLABLE | Normal range |
| has_member | JSONB | NULLABLE | Related observations (for panels) |
| component | JSONB | NULLABLE | Multi-component results |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: subject, encounter, code (GIN), effective_datetime
**RLS Policy**: Practitioners can only view observations for their patients

**ROM Codes (LOINC/SNOMED)**:
- BSI (Brief Symptom Inventory): Custom LOINC code
- GAF (Global Assessment of Functioning): 68473-8
- PHQ-9: 44249-1
- GAD-7: 69737-5

---

#### rom_questionnaires
Psychology-specific ROM questionnaire definitions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Questionnaire identifier |
| code | VARCHAR(50) | UNIQUE, NOT NULL | BSI/GAF/PHQ9/GAD7 |
| name | VARCHAR(255) | NOT NULL | Full name |
| description | TEXT | NULLABLE | Description |
| version | VARCHAR(20) | NOT NULL | Questionnaire version |
| loinc_code | VARCHAR(20) | NULLABLE | LOINC code |
| items | JSONB | NOT NULL | Question items structure |
| scoring_algorithm | JSONB | NOT NULL | Pandas calculation rules |
| interpretation_ranges | JSONB | NOT NULL | Score interpretation |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

---

#### rom_responses
Patient responses to ROM questionnaires.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Response identifier |
| questionnaire_id | UUID | FK(rom_questionnaires.id), NOT NULL | Questionnaire reference |
| patient_id | UUID | FK(patients.id), NOT NULL | Patient reference |
| encounter_id | UUID | FK(encounters.id), NULLABLE | Encounter context |
| practitioner_id | UUID | FK(practitioners.id), NOT NULL | Administering practitioner |
| authored_datetime | TIMESTAMP | NOT NULL | When completed |
| responses | JSONB | NOT NULL | Answer values |
| calculated_scores | JSONB | NOT NULL | Computed scores (Pandas) |
| interpretation | JSONB | NULLABLE | Automated interpretation |
| observation_id | UUID | FK(observations.id), NULLABLE | Linked FHIR Observation |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**: patient_id, questionnaire_id, authored_datetime

---

### 7. CLINICAL DOCUMENTATION

#### clinical_notes
FHIR DocumentReference/DiagnosticReport - clinical notes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Note identifier |
| encounter_id | UUID | FK(encounters.id), NOT NULL | Encounter reference |
| patient_id | UUID | FK(patients.id), NOT NULL | Patient reference |
| author_id | UUID | FK(practitioners.id), NOT NULL | Note author |
| note_type | VARCHAR(50) | NOT NULL | SOAP/Progress/Intake/Discharge |
| status | VARCHAR(20) | NOT NULL | draft/final/amended |
| title | VARCHAR(255) | NOT NULL | Note title |
| content | TEXT | NOT NULL | Note content (encrypted) |
| content_encrypted | BOOLEAN | DEFAULT TRUE | Encryption flag |
| autosave_version | INTEGER | DEFAULT 1 | Auto-save version counter |
| last_autosave_at | TIMESTAMP | NULLABLE | Last auto-save timestamp |
| finalized_at | TIMESTAMP | NULLABLE | When marked final |
| ai_generated | BOOLEAN | DEFAULT FALSE | AI-assisted flag |
| ai_summary | TEXT | NULLABLE | AI-generated summary |
| ai_summary_evidence | JSONB | NULLABLE | Evidence links to transcript |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: encounter_id, patient_id, author_id, note_type, status
**RLS Policy**: Authors can edit drafts; all practitioners can read final notes for their patients

---

#### clinical_note_versions
Version history for clinical notes (audit trail).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Version identifier |
| clinical_note_id | UUID | FK(clinical_notes.id), NOT NULL | Parent note |
| version_number | INTEGER | NOT NULL | Incremental version |
| content | TEXT | NOT NULL | Snapshot of content |
| changed_by | UUID | FK(practitioners.id), NOT NULL | Who made the change |
| change_reason | TEXT | NULLABLE | Reason for amendment |
| changed_at | TIMESTAMP | NOT NULL | Change timestamp |

**Unique Constraint**: (clinical_note_id, version_number)

---

### 8. AI INTEGRATION

#### session_transcripts
Audio transcription storage for therapy sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Transcript identifier |
| encounter_id | UUID | FK(encounters.id), UNIQUE, NOT NULL | Session reference |
| patient_id | UUID | FK(patients.id), NOT NULL | Patient reference |
| consent_verified | BOOLEAN | NOT NULL | Consent check passed |
| consent_id | UUID | FK(consents.id), NULLABLE | Reference to consent |
| audio_file_path | VARCHAR(500) | NULLABLE | Encrypted audio storage path |
| audio_duration_seconds | INTEGER | NULLABLE | Audio length |
| transcript_text | TEXT | NULLABLE | Full transcription |
| transcript_segments | JSONB | NULLABLE | Time-stamped segments |
| speaker_labels | JSONB | NULLABLE | Speaker diarization |
| processing_status | VARCHAR(20) | NOT NULL | pending/processing/completed/failed |
| ai_model_used | VARCHAR(100) | NULLABLE | STT model identifier |
| confidence_score | FLOAT | NULLABLE | Average confidence |
| processed_at | TIMESTAMP | NULLABLE | Processing completion time |
| embedding_vector | vector(1536) | NULLABLE | pgvector for RAG |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: encounter_id, patient_id, processing_status
**Vector Index**: HNSW index on embedding_vector for similarity search
**RLS Policy**: Only practitioners involved in the encounter can access

---

#### ai_summaries
AI-generated summaries with evidence links.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Summary identifier |
| source_type | VARCHAR(50) | NOT NULL | transcript/note/encounter |
| source_id | UUID | NOT NULL | Reference to source |
| patient_id | UUID | FK(patients.id), NOT NULL | Patient reference |
| summary_type | VARCHAR(50) | NOT NULL | session/longitudinal/crisis |
| summary_text | TEXT | NOT NULL | Generated summary |
| evidence_links | JSONB | NOT NULL | Citations to source segments |
| key_themes | JSONB | NULLABLE | Extracted themes |
| risk_flags | JSONB | NULLABLE | Identified risk factors |
| ai_model_used | VARCHAR(100) | NOT NULL | Model identifier |
| generated_by | UUID | FK(practitioners.id), NOT NULL | Requesting practitioner |
| reviewed | BOOLEAN | DEFAULT FALSE | Human review flag |
| reviewed_by | UUID | FK(practitioners.id), NULLABLE | Reviewer |
| reviewed_at | TIMESTAMP | NULLABLE | Review timestamp |
| embedding_vector | vector(1536) | NULLABLE | pgvector for RAG |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**: source_id, patient_id, summary_type
**Vector Index**: HNSW index on embedding_vector

---

#### rag_query_logs
RAG chatbot query tracking for audit and scope enforcement.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Query identifier |
| practitioner_id | UUID | FK(practitioners.id), NOT NULL | Querying user |
| query_text | TEXT | NOT NULL | User question |
| query_embedding | vector(1536) | NOT NULL | Query vector |
| rbac_scope_filter | JSONB | NOT NULL | Applied RLS filters |
| retrieved_documents | JSONB | NOT NULL | Retrieved context IDs |
| llm_response | TEXT | NOT NULL | Generated answer |
| sources_cited | JSONB | NOT NULL | Source references |
| patient_ids_accessed | UUID[] | NOT NULL | Patients whose data was retrieved |
| confidence_score | FLOAT | NULLABLE | Response confidence |
| feedback_rating | INTEGER | NULLABLE | User rating (1-5) |
| created_at | TIMESTAMP | NOT NULL | Query timestamp |

**Indexes**: practitioner_id, created_at, patient_ids_accessed (GIN)

---

### 9. AUDIT & SECURITY

#### audit_logs
Immutable audit trail for all data operations (GDPR Article 30).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Audit record identifier |
| timestamp | TIMESTAMP | NOT NULL | Operation timestamp |
| actor_user_id | UUID | FK(users.id), NULLABLE | User who performed action |
| actor_ip_address | INET | NULLABLE | Source IP address |
| actor_user_agent | TEXT | NULLABLE | Browser/client info |
| action_type | VARCHAR(50) | NOT NULL | CREATE/READ/UPDATE/DELETE/LOGIN |
| resource_type | VARCHAR(100) | NOT NULL | Table/entity name |
| resource_id | UUID | NULLABLE | Affected record ID |
| patient_id | UUID | FK(patients.id), NULLABLE | Patient context |
| changes | JSONB | NULLABLE | Before/after values (PII-stripped) |
| query_text | TEXT | NULLABLE | AI query text |
| access_granted | BOOLEAN | NOT NULL | Authorization result |
| denial_reason | TEXT | NULLABLE | Why access denied |
| session_id | UUID | NULLABLE | Session identifier |
| request_id | UUID | NULLABLE | Request trace ID |

**Indexes**: timestamp DESC, actor_user_id, resource_type, patient_id, action_type
**Table Settings**: `ALTER TABLE audit_logs SET (autovacuum_enabled = false);` (prevent deletion)
**RLS Policy**: Only SUPER_ADMIN can read; triggers insert for all users

---

#### anonymization_logs
Track PII anonymization operations (Presidio).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Anonymization record ID |
| original_resource_type | VARCHAR(100) | NOT NULL | Source entity |
| original_resource_id | UUID | NOT NULL | Source record ID |
| anonymization_method | VARCHAR(50) | NOT NULL | replace/redact/hash/mask |
| pii_entities_detected | JSONB | NOT NULL | Entity types found |
| anonymized_data | JSONB | NOT NULL | Anonymized output |
| requested_by | UUID | FK(users.id), NOT NULL | Requester |
| purpose | VARCHAR(100) | NOT NULL | research/export/analytics |
| consent_verified | BOOLEAN | NOT NULL | Consent check |
| created_at | TIMESTAMP | NOT NULL | Operation timestamp |

**Indexes**: original_resource_id, requested_by, created_at

---

### 10. REFERENCE DATA

#### codeable_concepts
Shared terminology storage (SNOMED CT, LOINC, ICD-10).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Concept identifier |
| system | VARCHAR(255) | NOT NULL | Coding system URI |
| code | VARCHAR(100) | NOT NULL | Code value |
| display | VARCHAR(500) | NOT NULL | Human-readable name |
| definition | TEXT | NULLABLE | Full definition |
| designation | JSONB | NULLABLE | Alternative names |
| property | JSONB | NULLABLE | Additional properties |
| is_active | BOOLEAN | DEFAULT TRUE | Active status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Unique Constraint**: (system, code)
**Indexes**: system, code, display

---

## Database Extensions

```sql
-- Vector similarity search for RAG
CREATE EXTENSION IF NOT EXISTS vector;

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptography functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

---

## Row-Level Security (RLS) Policies

### General Principle
All tables with patient data MUST have RLS enabled:
```sql
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
```

### Example Policy: Practitioners Access Own Patients
```sql
CREATE POLICY practitioner_patient_access ON patients
FOR SELECT
TO authenticated_user
USING (
  id IN (
    SELECT DISTINCT subject FROM encounters
    WHERE participant @> jsonb_build_array(
      jsonb_build_object('actor', jsonb_build_object('reference', 'Practitioner/' || current_setting('app.current_practitioner_id')))
    )
  )
);
```

### Example Policy: Audit Logs (Write-Only for Users)
```sql
CREATE POLICY audit_insert_only ON audit_logs
FOR INSERT
TO authenticated_user
WITH CHECK (actor_user_id = current_setting('app.current_user_id')::uuid);

CREATE POLICY audit_admin_read ON audit_logs
FOR SELECT
TO authenticated_user
USING (
  EXISTS (
    SELECT 1 FROM user_roles ur
    JOIN roles r ON ur.role_id = r.id
    WHERE ur.user_id = current_setting('app.current_user_id')::uuid
    AND r.name = 'SUPER_ADMIN'
  )
);
```

---

## Encryption Strategy

### Data at Rest
- **BSN (National ID)**: AES-256 encryption using pgcrypto
- **Clinical Notes**: Application-level encryption before storage
- **Audio Files**: Encrypted files on disk (not in DB)

### Data in Transit
- TLS 1.3 for all API connections
- mTLS for inter-service communication

---

## Indexes for Performance

### Vector Indexes (AI/RAG)
```sql
CREATE INDEX idx_transcripts_embedding ON session_transcripts
USING hnsw (embedding_vector vector_cosine_ops);

CREATE INDEX idx_summaries_embedding ON ai_summaries
USING hnsw (embedding_vector vector_cosine_ops);
```

### JSONB Indexes
```sql
CREATE INDEX idx_patients_identifier ON patients USING GIN (identifier);
CREATE INDEX idx_observations_code ON observations USING GIN (code);
CREATE INDEX idx_encounters_participant ON encounters USING GIN (participant);
```

### Composite Indexes
```sql
CREATE INDEX idx_observations_patient_date ON observations(subject, effective_datetime DESC);
CREATE INDEX idx_encounters_patient_status ON encounters(subject, status, period_start DESC);
```

---

## Migration Strategy

1. **Phase 1**: Core authentication, users, roles
2. **Phase 2**: FHIR resources (Practitioners, Organizations, Patients)
3. **Phase 3**: Clinical entities (Encounters, Observations, Notes)
4. **Phase 4**: Consent management
5. **Phase 5**: AI integration (Transcripts, Summaries, RAG)
6. **Phase 6**: Audit logs and RLS policies

---

## GDPR Compliance Checklist

- [x] Consent tracking (consents table)
- [x] Right to access (audit_logs)
- [x] Right to rectification (clinical_note_versions)
- [x] Right to erasure (soft delete with `active` flags)
- [x] Data portability (FHIR-compliant export)
- [x] Processing records (anonymization_logs)
- [x] Breach notification (audit_logs monitoring)
- [x] Data minimization (RLS policies)
- [x] Storage limitation (retention policies via created_at)

---

## Performance Targets

- Patient record retrieval: < 100ms
- ROM score calculation: < 50ms
- Vector similarity search: < 200ms (top 10 results)
- Audit log insertion: < 10ms (async trigger)

---

## Backup & Disaster Recovery

- **Daily**: Full database backup
- **Hourly**: Transaction log backup
- **Continuous**: Write-ahead log (WAL) archiving
- **Retention**: 7 years (Dutch healthcare law)
