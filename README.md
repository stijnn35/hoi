# Psychiatric EHR System

AI-Driven Electronic Patient Dossier (EPD) for Psychiatric Care

## Overview

A secure, FHIR-compliant Electronic Health Record system specifically designed for psychologists and psychiatric care providers. Built with FastAPI, PostgreSQL, and AI integration for enhanced clinical workflows.

## Key Features

### 🔒 Security & Compliance
- **GDPR/AVG Compliant**: Full GDPR Article 30 audit trail
- **Multi-Factor Authentication (MFA)**: TOTP-based 2FA
- **Role-Based Access Control (RBAC)**: Granular permission system
- **Row-Level Security (RLS)**: Database-level access control
- **Encryption**: AES-256 encryption for sensitive data (BSN, clinical notes)
- **Immutable Audit Logs**: Complete tracking of all data access

### 🏥 FHIR Compliance
- **HL7 FHIR R4 Standard**: All resources FHIR-compliant
- **fhir.resources Library**: Strict validation
- **Standard Terminologies**: SNOMED CT, LOINC, ICD-10 support

### 🧠 Psychology-Specific Features
- **Layered Consent Management**: Per-session AI processing consent
- **ROM Integration**: BSI, GAF, PHQ-9, GAD-7 questionnaires
- **Automated Scoring**: Pandas-based ROM calculation
- **Auto-save Clinical Notes**: Prevent data loss

### 🤖 AI Integration
- **Speech-to-Text (STT)**: Session transcription with timestamps
- **AI Summarization**: Evidence-linked summaries with citations
- **RAG Chatbot**: Secure, RBAC-scoped clinical assistant
- **PII Anonymization**: Microsoft Presidio integration
- **Vector Search**: pgvector for semantic search

## Tech Stack

### Backend
- **FastAPI**: Async Python web framework
- **PostgreSQL**: Primary database
- **pgvector**: Vector similarity search
- **SQLAlchemy**: Async ORM
- **Alembic**: Database migrations

### Security
- **python-jose**: JWT token management
- **passlib**: Password hashing (bcrypt)
- **MFA**: TOTP implementation

### AI/ML
- **OpenAI API**: GPT-4 for summarization, embeddings
- **Presidio**: PII detection and anonymization
- **Pydantic-AI**: AI workflow orchestration
- **LangChain**: RAG implementation

### Data Processing
- **Pandas**: ROM scoring calculations
- **NumPy**: Numerical operations

## Architecture

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
│  Routes, Middleware, Dependencies       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│       Application Layer                 │
│  Services, Use Cases, Business Logic    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Domain Layer                    │
│  Models, Schemas, Business Rules        │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│     Infrastructure Layer                │
│  Database, Security, AI, External APIs  │
└─────────────────────────────────────────┘
```

See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for detailed architecture documentation.

## Database Schema

Comprehensive FHIR-compliant schema with:
- **Authentication**: Users, Roles, MFA
- **FHIR Resources**: Patients, Practitioners, Organizations
- **Clinical Data**: Encounters, Observations, Clinical Notes
- **Consent Management**: Granular consent tracking
- **AI Integration**: Transcripts, Summaries, Vector embeddings
- **Audit Trail**: Immutable logs, Anonymization tracking
- **ROM**: Questionnaire definitions and responses

See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) for complete schema documentation.

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ with pgvector extension
- Redis (for background tasks)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd psychiatric-ehr
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb psychiatric_ehr

   # Enable pgvector extension
   psql psychiatric_ehr -c "CREATE EXTENSION IF NOT EXISTS vector;"

   # Run migrations
   alembic upgrade head
   ```

6. **Run the application**
   ```bash
   # Development mode
   python src/main.py

   # Or using uvicorn directly
   uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Development

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## API Documentation

Once running, access interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security Considerations

### Environment Variables
Never commit `.env` files. Always use `.env.example` as a template.

### Secret Keys
Generate secure secret keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Database Encryption
BSN (Dutch national ID) is encrypted at rest using AES-256:
```sql
-- Encrypted using pgcrypto
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

## GDPR Compliance

- ✅ Right to access (audit logs)
- ✅ Right to rectification (versioned clinical notes)
- ✅ Right to erasure (soft delete with retention policies)
- ✅ Right to data portability (FHIR export)
- ✅ Consent management (layered consent model)
- ✅ Processing records (audit + anonymization logs)
- ✅ Data minimization (RLS policies)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_services/test_patient_service.py

# Run integration tests
pytest tests/integration/
```

## Deployment

### Docker

```bash
# Build image
docker build -t psychiatric-ehr:latest .

# Run container
docker run -p 8000:8000 --env-file .env psychiatric-ehr:latest
```

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in .env
- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Configure SSL/TLS certificates
- [ ] Set up database backups (daily + transaction logs)
- [ ] Configure monitoring (Sentry, DataDog, etc.)
- [ ] Enable rate limiting
- [ ] Review CORS settings
- [ ] Set up log aggregation
- [ ] Configure firewall rules
- [ ] Enable database connection pooling
- [ ] Set up CDN for static files

## Contributing

1. Create feature branch from `main`
2. Follow Clean Architecture principles
3. Write tests (aim for >80% coverage)
4. Update documentation
5. Submit pull request

## License

[Add license information]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]

## Acknowledgments

- HL7 FHIR for healthcare interoperability standards
- Microsoft Presidio for PII anonymization
- OpenAI for AI capabilities
- FastAPI community

---

**Version**: 0.1.0
**Last Updated**: 2026-02-15
