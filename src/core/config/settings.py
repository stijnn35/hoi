"""
Application configuration using Pydantic Settings.
Loads environment variables from .env file.
"""

from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Application
    APP_NAME: str = "Psychiatric EHR System"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", pattern="^(development|staging|production)$")
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string with asyncpg driver")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 0
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL uses asyncpg driver."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use asyncpg driver (postgresql+asyncpg://)")
        return v

    # Security & Authentication
    JWT_SECRET_KEY: str = Field(..., min_length=32, description="Secret key for JWT tokens")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MFA_ISSUER: str = "PsychiatricEHR"

    # Password Policy
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGITS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # Encryption
    ENCRYPTION_KEY: str = Field(..., min_length=32, description="AES encryption key")
    BSN_ENCRYPTION_KEY: str = Field(..., min_length=32, description="BSN-specific encryption key")

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # AI Services - OpenAI
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSION: int = 1536
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.7

    # AI Services - Presidio (PII Anonymization)
    PRESIDIO_ANALYZER_URL: Optional[str] = "http://localhost:5001"
    PRESIDIO_ANONYMIZER_URL: Optional[str] = "http://localhost:5002"

    # FHIR
    FHIR_VERSION: str = "R4"
    FHIR_BASE_URL: str = "https://vonk.fire.ly"
    FHIR_VALIDATION_STRICT: bool = True

    # File Storage
    AUDIO_STORAGE_PATH: str = "/var/psychiatric_ehr/audio"
    MAX_AUDIO_FILE_SIZE_MB: int = 500
    ALLOWED_AUDIO_FORMATS: List[str] = ["mp3", "wav", "m4a", "ogg"]

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FORMAT: str = Field(default="json", pattern="^(json|text)$")
    LOG_FILE_PATH: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10

    # Session Management
    SESSION_TIMEOUT_MINUTES: int = 30
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION_MINUTES: int = 15

    # GDPR Compliance
    DATA_RETENTION_YEARS: int = 7
    AUTO_ANONYMIZE_AFTER_YEARS: int = 10
    CONSENT_RENEWAL_MONTHS: int = 12

    # Background Tasks (Celery/Redis)
    CELERY_BROKER_URL: Optional[str] = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: Optional[str] = "redis://localhost:6379/0"

    # Vector Store (pgvector)
    VECTOR_DIMENSION: int = 1536
    VECTOR_INDEX_TYPE: str = "hnsw"
    VECTOR_M: int = 16  # HNSW M parameter
    VECTOR_EF_CONSTRUCTION: int = 64  # HNSW ef_construction parameter

    # Audit Trail
    AUDIT_LOG_RETENTION_DAYS: int = 2555  # ~7 years
    AUDIT_LOG_COMPRESSION_ENABLED: bool = True

    @property
    def database_url_sync(self) -> str:
        """Return synchronous database URL for Alembic."""
        return self.DATABASE_URL.replace("+asyncpg", "")

    @property
    def max_audio_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.MAX_AUDIO_FILE_SIZE_MB * 1024 * 1024

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()
