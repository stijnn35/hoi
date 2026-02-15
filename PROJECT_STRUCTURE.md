# Psychiatric EHR - Clean Architecture Project Structure

## Overview
This project follows **Clean Architecture** (also known as Hexagonal/Onion Architecture) with **Domain-Driven Design (DDD)** principles. The architecture ensures separation of concerns, testability, and maintainability.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                  │
│            (Routes, Controllers, Middleware)            │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                  Application Layer                      │
│         (Use Cases, Services, Business Logic)           │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    Domain Layer                         │
│        (Entities, Value Objects, Domain Events)         │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│               Infrastructure Layer                      │
│    (Database, External APIs, Security, File Storage)    │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
psychiatric-ehr/
├── src/                          # Main application source code
│   ├── api/                      # API Layer (Presentation)
│   │   ├── routes/               # API route definitions
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── patients.py      # Patient CRUD operations
│   │   │   ├── practitioners.py # Practitioner management
│   │   │   ├── encounters.py    # Encounter/session management
│   │   │   ├── observations.py  # Observations & ROM
│   │   │   ├── clinical_notes.py # Clinical documentation
│   │   │   ├── consents.py      # Consent management
│   │   │   ├── ai.py            # AI services (STT, summarization)
│   │   │   └── rag.py           # RAG chatbot endpoints
│   │   ├── dependencies/         # FastAPI dependency injection
│   │   │   ├── auth.py          # Current user/practitioner dependencies
│   │   │   ├── database.py      # Database session dependencies
│   │   │   └── rbac.py          # Authorization dependencies
│   │   ├── middleware/           # API middleware
│   │   │   ├── auth_middleware.py    # JWT validation
│   │   │   ├── rbac_middleware.py    # Role-based access control
│   │   │   ├── audit_middleware.py   # Audit logging
│   │   │   └── cors_middleware.py    # CORS configuration
│   │   └── __init__.py
│   │
│   ├── domain/                   # Domain Layer (Business Entities)
│   │   ├── models/               # SQLAlchemy ORM models
│   │   │   ├── user.py          # User model
│   │   │   ├── role.py          # Role model
│   │   │   ├── practitioner.py  # Practitioner model
│   │   │   ├── patient.py       # Patient model
│   │   │   ├── encounter.py     # Encounter model
│   │   │   ├── observation.py   # Observation model
│   │   │   ├── clinical_note.py # Clinical note model
│   │   │   ├── consent.py       # Consent model
│   │   │   ├── audit_log.py     # Audit log model
│   │   │   ├── session_transcript.py # Transcript model
│   │   │   └── ai_summary.py    # AI summary model
│   │   ├── schemas/              # Pydantic schemas (DTOs)
│   │   │   ├── user_schema.py   # User request/response schemas
│   │   │   ├── patient_schema.py # Patient FHIR schemas
│   │   │   ├── practitioner_schema.py # Practitioner FHIR schemas
│   │   │   ├── encounter_schema.py # Encounter schemas
│   │   │   ├── observation_schema.py # Observation schemas
│   │   │   ├── clinical_note_schema.py # Note schemas
│   │   │   ├── consent_schema.py # Consent schemas
│   │   │   └── ai_schema.py     # AI request/response schemas
│   │   ├── enums/                # Business enumerations
│   │   │   ├── user_enums.py    # User-related enums
│   │   │   ├── fhir_enums.py    # FHIR value sets
│   │   │   ├── consent_enums.py # Consent types
│   │   │   └── ai_enums.py      # AI processing statuses
│   │   └── __init__.py
│   │
│   ├── application/              # Application Layer (Use Cases)
│   │   ├── services/             # Business logic services
│   │   │   ├── auth_service.py  # Authentication service (MFA, JWT)
│   │   │   ├── patient_service.py # Patient management
│   │   │   ├── encounter_service.py # Encounter management
│   │   │   ├── observation_service.py # Observation & ROM service
│   │   │   ├── clinical_note_service.py # Note CRUD & autosave
│   │   │   ├── consent_service.py # Consent verification
│   │   │   ├── ai_service.py    # AI orchestration
│   │   │   ├── stt_service.py   # Speech-to-text service
│   │   │   ├── summarization_service.py # AI summarization
│   │   │   ├── rag_service.py   # RAG chatbot service
│   │   │   ├── anonymization_service.py # PII stripping (Presidio)
│   │   │   └── rom_service.py   # ROM scoring (Pandas)
│   │   ├── use_cases/            # Specific use case implementations
│   │   │   ├── register_patient.py # Patient registration flow
│   │   │   ├── create_encounter.py # Encounter creation
│   │   │   ├── process_transcript.py # STT processing
│   │   │   ├── generate_summary.py # Summary generation
│   │   │   └── query_rag.py     # RAG query execution
│   │   └── __init__.py
│   │
│   ├── infrastructure/           # Infrastructure Layer
│   │   ├── database/             # Database infrastructure
│   │   │   ├── connection.py    # Database connection setup
│   │   │   ├── session.py       # Session management
│   │   │   ├── base.py          # SQLAlchemy declarative base
│   │   │   ├── repositories/    # Repository pattern implementations
│   │   │   │   ├── user_repository.py
│   │   │   │   ├── patient_repository.py
│   │   │   │   ├── practitioner_repository.py
│   │   │   │   ├── encounter_repository.py
│   │   │   │   ├── observation_repository.py
│   │   │   │   └── clinical_note_repository.py
│   │   │   └── rls_policies.py  # Row-Level Security setup
│   │   ├── security/             # Security infrastructure
│   │   │   ├── password.py      # Password hashing (passlib)
│   │   │   ├── jwt.py           # JWT token handling (python-jose)
│   │   │   ├── mfa.py           # MFA/TOTP implementation
│   │   │   ├── encryption.py    # Data encryption (pgcrypto)
│   │   │   └── rbac.py          # RBAC policy engine
│   │   ├── ai/                   # AI service integrations
│   │   │   ├── openai_client.py # OpenAI API client
│   │   │   ├── vector_store.py  # pgvector operations
│   │   │   ├── embeddings.py    # Text embedding generation
│   │   │   └── presidio_client.py # Presidio anonymization
│   │   ├── external/             # External service integrations
│   │   │   ├── fhir_validator.py # FHIR validation
│   │   │   └── audit_logger.py  # Audit trail implementation
│   │   └── __init__.py
│   │
│   ├── core/                     # Core shared utilities
│   │   ├── config/               # Configuration management
│   │   │   ├── settings.py      # Pydantic settings
│   │   │   └── logging.py       # Structlog configuration
│   │   ├── exceptions/           # Custom exceptions
│   │   │   ├── base.py          # Base exception classes
│   │   │   ├── auth_exceptions.py # Authentication errors
│   │   │   ├── fhir_exceptions.py # FHIR validation errors
│   │   │   └── ai_exceptions.py # AI processing errors
│   │   ├── utils/                # Utility functions
│   │   │   ├── datetime_utils.py # Date/time helpers
│   │   │   ├── fhir_utils.py    # FHIR resource helpers
│   │   │   └── validators.py    # Custom validators
│   │   └── __init__.py
│   │
│   └── main.py                   # FastAPI application entry point
│
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests (isolated)
│   │   ├── test_services/        # Service tests
│   │   ├── test_repositories/    # Repository tests
│   │   └── test_utils/           # Utility tests
│   ├── integration/              # Integration tests (with DB)
│   │   ├── test_api/             # API endpoint tests
│   │   ├── test_database/        # Database tests
│   │   └── test_ai/              # AI integration tests
│   ├── e2e/                      # End-to-end tests
│   │   └── test_workflows/       # Complete user workflows
│   ├── conftest.py               # Pytest fixtures
│   └── __init__.py
│
├── alembic/                      # Database migrations
│   ├── versions/                 # Migration files
│   ├── env.py                    # Alembic environment
│   └── script.py.mako            # Migration template
│
├── docs/                         # Documentation
│   ├── api/                      # API documentation
│   ├── architecture/             # Architecture diagrams
│   └── user_guide/               # User guides
│
├── scripts/                      # Utility scripts
│   ├── seed_data.py             # Database seeding
│   ├── create_admin.py          # Create admin user
│   └── check_compliance.py      # FHIR/GDPR compliance checks
│
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Python project metadata
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # Development dependencies
├── DATABASE_SCHEMA.md            # Database schema documentation
├── PROJECT_STRUCTURE.md          # This file
└── README.md                     # Project overview
```

## Layer Responsibilities

### 1. API Layer (`src/api/`)
**Purpose**: Handle HTTP requests, validation, and response formatting.

**Rules**:
- No business logic
- Only route definitions and request/response handling
- Depends on Application Layer services
- Uses Pydantic schemas for validation

**Example**:
```python
@router.post("/patients", response_model=PatientSchema)
async def create_patient(
    patient: PatientCreateSchema,
    current_user: User = Depends(get_current_practitioner),
    patient_service: PatientService = Depends(get_patient_service)
):
    return await patient_service.create_patient(patient, current_user)
```

### 2. Application Layer (`src/application/`)
**Purpose**: Orchestrate business workflows and use cases.

**Rules**:
- Contains business logic
- Orchestrates domain models and infrastructure services
- Transaction management
- Does NOT depend on API layer

**Example**:
```python
class PatientService:
    async def create_patient(self, patient_data: PatientCreateSchema, actor: User):
        # Validate FHIR compliance
        fhir_patient = self.fhir_validator.validate_patient(patient_data)

        # Check authorization
        await self.rbac_service.check_permission(actor, "patient:create")

        # Save to database
        patient = await self.patient_repository.create(fhir_patient)

        # Audit log
        await self.audit_service.log_create(patient, actor)

        return patient
```

### 3. Domain Layer (`src/domain/`)
**Purpose**: Define business entities, value objects, and validation rules.

**Rules**:
- Pure business entities (SQLAlchemy models)
- Pydantic schemas for data transfer
- Business enumerations
- No dependencies on other layers

**Example**:
```python
class Patient(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True)
    identifier = Column(JSONB, nullable=False)  # FHIR Identifier[]
    active = Column(Boolean, default=True)

    @validates('birth_date')
    def validate_birth_date(self, key, value):
        if value > date.today():
            raise ValueError("Birth date cannot be in the future")
        return value
```

### 4. Infrastructure Layer (`src/infrastructure/`)
**Purpose**: Implement technical capabilities (database, external APIs, security).

**Rules**:
- Database access (repositories)
- External service integrations
- Security implementations
- Can depend on Domain Layer

**Example**:
```python
class PatientRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create(self, patient: Patient) -> Patient:
        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)
        return patient

    async def find_by_id(self, patient_id: UUID) -> Patient:
        result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        return result.scalar_one_or_none()
```

### 5. Core Layer (`src/core/`)
**Purpose**: Shared utilities, configuration, and cross-cutting concerns.

**Rules**:
- Configuration management
- Logging setup
- Custom exceptions
- Utility functions
- Can be used by all layers

## Dependency Rules (Clean Architecture)

```
API → Application → Domain ← Infrastructure
                      ↑
                    Core
```

**Key Principle**: Dependencies point INWARD. Outer layers depend on inner layers, never the reverse.

- ✅ API can import from Application, Domain, Core
- ✅ Application can import from Domain, Core
- ✅ Infrastructure can import from Domain, Core
- ❌ Domain CANNOT import from Application, Infrastructure, API
- ❌ Application CANNOT import from API

## Dependency Injection

FastAPI's dependency injection system is used throughout:

```python
# dependencies/database.py
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_async_session() as session:
        yield session

# dependencies/services.py
async def get_patient_service(
    db: AsyncSession = Depends(get_db_session)
) -> PatientService:
    repository = PatientRepository(db)
    return PatientService(repository)

# routes/patients.py
@router.get("/patients/{patient_id}")
async def get_patient(
    patient_id: UUID,
    service: PatientService = Depends(get_patient_service),
    current_user: User = Depends(get_current_user)
):
    return await service.get_patient(patient_id, current_user)
```

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test services in isolation with mocked dependencies
- Test utility functions
- Fast execution (no database)

### Integration Tests (`tests/integration/`)
- Test with real database (test container)
- Test API endpoints
- Test AI service integrations

### E2E Tests (`tests/e2e/`)
- Complete user workflows
- Patient registration → Encounter → Note → ROM → AI Summary

## Configuration Management

Environment-based configuration using Pydantic Settings:

```python
# core/config/settings.py
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Security
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI
    OPENAI_API_KEY: str

    # FHIR
    FHIR_BASE_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

## Migration Workflow

1. Create models in `src/domain/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review migration in `alembic/versions/`
4. Apply migration: `alembic upgrade head`

## Security Considerations

### Row-Level Security (RLS)
Applied at database level AND application level:
```python
# Set session variables for RLS
await db.execute(
    text("SET LOCAL app.current_user_id = :user_id"),
    {"user_id": str(current_user.id)}
)
```

### Audit Logging
Automatic via middleware:
```python
# middleware/audit_middleware.py
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    # Log all requests with user context
    await audit_logger.log_request(request, user)
    response = await call_next(request)
    await audit_logger.log_response(response)
    return response
```

## Development Workflow

1. **Create Feature Branch**: `git checkout -b feature/rom-integration`
2. **Define Domain Model**: Add SQLAlchemy model in `domain/models/`
3. **Create Migration**: `alembic revision --autogenerate`
4. **Implement Repository**: Add repository in `infrastructure/database/repositories/`
5. **Create Service**: Add business logic in `application/services/`
6. **Add API Route**: Create endpoint in `api/routes/`
7. **Write Tests**: Add unit, integration, and E2E tests
8. **Commit**: Follow conventional commits (feat/fix/docs)

## Naming Conventions

- **Files**: snake_case (e.g., `patient_service.py`)
- **Classes**: PascalCase (e.g., `PatientService`)
- **Functions**: snake_case (e.g., `get_patient_by_id`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_UPLOAD_SIZE`)
- **Private**: Prefix with `_` (e.g., `_validate_consent`)

## Import Conventions

```python
# Standard library
import os
from datetime import datetime
from typing import Optional, List

# Third-party
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from pydantic import BaseModel

# Local - absolute imports from src root
from src.domain.models.patient import Patient
from src.domain.schemas.patient_schema import PatientSchema
from src.application.services.patient_service import PatientService
from src.core.exceptions.auth_exceptions import UnauthorizedException
```

## Performance Considerations

1. **Database Queries**:
   - Use async SQLAlchemy
   - Implement query result caching
   - Use select/join loading strategies

2. **API Responses**:
   - Pagination for list endpoints
   - Field filtering (sparse fieldsets)
   - ETag for caching

3. **AI Operations**:
   - Queue-based processing for STT
   - Vector search optimization (HNSW indexes)
   - Batch embedding generation

## Monitoring & Observability

- **Structured Logging**: Structlog with JSON output
- **Request Tracing**: Unique request IDs
- **Performance Metrics**: Response time tracking
- **Error Tracking**: Exception logging with context

---

This structure provides a scalable, maintainable foundation for the psychiatric EHR system while maintaining strict adherence to Clean Architecture principles.
