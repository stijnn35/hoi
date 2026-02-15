"""
Domain models package.
Exports all SQLAlchemy models for easy import.
"""

from src.domain.models.user import User
from src.domain.models.role import Role, UserRole, ROLE_PERMISSIONS
from src.domain.models.practitioner import Practitioner
from src.domain.models.organization import Organization
from src.domain.models.patient import Patient
from src.domain.models.location import Location
from src.domain.models.consent import Consent
from src.domain.models.encounter import Encounter
from src.domain.models.observation import Observation
from src.domain.models.clinical_note import ClinicalNote, ClinicalNoteVersion
from src.domain.models.session_transcript import SessionTranscript
from src.domain.models.ai_summary import AISummary, RAGQueryLog
from src.domain.models.audit_log import AuditLog, AnonymizationLog
from src.domain.models.rom_questionnaire import ROMQuestionnaire, ROMResponse

__all__ = [
    # Authentication & Authorization
    "User",
    "Role",
    "UserRole",
    "ROLE_PERMISSIONS",
    # FHIR Resources
    "Practitioner",
    "Organization",
    "Patient",
    "Location",
    "Consent",
    "Encounter",
    "Observation",
    # Clinical Documentation
    "ClinicalNote",
    "ClinicalNoteVersion",
    # AI Integration
    "SessionTranscript",
    "AISummary",
    "RAGQueryLog",
    # Audit & Compliance
    "AuditLog",
    "AnonymizationLog",
    # ROM
    "ROMQuestionnaire",
    "ROMResponse",
]
