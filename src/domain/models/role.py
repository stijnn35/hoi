"""
Role and UserRole models for RBAC (Role-Based Access Control).
"""

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class Role(Base, UUIDMixin, TimestampMixin):
    """
    Role definition for RBAC.
    Defines a set of permissions that can be assigned to users.
    """

    __tablename__ = "roles"

    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Role name (e.g., PSYCHOLOGIST, ADMIN, PATIENT)"
    )

    description = Column(
        Text,
        nullable=True,
        comment="Role description"
    )

    permissions = Column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Permission matrix (JSON object)"
    )

    # Relationships
    user_roles = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"

    def has_permission(self, resource: str, action: str) -> bool:
        """
        Check if this role has a specific permission.

        Args:
            resource: Resource name (e.g., 'patient', 'encounter')
            action: Action name (e.g., 'read', 'write', 'delete')

        Returns:
            True if permission exists, False otherwise
        """
        if not self.permissions:
            return False

        resource_perms = self.permissions.get(resource, {})
        if isinstance(resource_perms, dict):
            return resource_perms.get(action, False)

        # Handle wildcard permissions
        if resource_perms == "*" or resource_perms is True:
            return True

        return False


class UserRole(Base, UUIDMixin):
    """
    Many-to-many relationship between users and roles.
    Tracks role assignments with metadata.
    """

    __tablename__ = "user_roles"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to user"
    )

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to role"
    )

    assigned_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default="now()",
        comment="Role assignment timestamp"
    )

    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who assigned this role"
    )

    # Relationships
    user = relationship("User", back_populates="roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigner = relationship("User", foreign_keys=[assigned_by])

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_id={self.role_id})>"


# Standard role permission templates
ROLE_PERMISSIONS = {
    "SUPER_ADMIN": {
        "*": "*"  # Full access to everything
    },
    "PSYCHOLOGIST": {
        "patient": {"read": True, "write": True, "delete": False},
        "encounter": {"read": True, "write": True, "delete": False},
        "observation": {"read": True, "write": True, "delete": False},
        "clinical_note": {"read": True, "write": True, "delete": False},
        "consent": {"read": True, "write": True, "delete": False},
        "ai_services": {"read": True, "write": True, "delete": False},
        "rom": {"read": True, "write": True, "delete": False},
        "audit_log": {"read": True, "write": False, "delete": False},
    },
    "PSYCHIATRIST": {
        "patient": {"read": True, "write": True, "delete": False},
        "encounter": {"read": True, "write": True, "delete": False},
        "observation": {"read": True, "write": True, "delete": False},
        "clinical_note": {"read": True, "write": True, "delete": False},
        "consent": {"read": True, "write": True, "delete": False},
        "ai_services": {"read": True, "write": True, "delete": False},
        "rom": {"read": True, "write": True, "delete": False},
        "medication": {"read": True, "write": True, "delete": False},
    },
    "THERAPIST": {
        "patient": {"read": True, "write": False, "delete": False},
        "encounter": {"read": True, "write": True, "delete": False},
        "observation": {"read": True, "write": True, "delete": False},
        "clinical_note": {"read": True, "write": True, "delete": False},
        "consent": {"read": True, "write": False, "delete": False},
        "ai_services": {"read": True, "write": True, "delete": False},
    },
    "ADMIN_STAFF": {
        "patient": {"read": True, "write": True, "delete": False},
        "encounter": {"read": True, "write": True, "delete": False},
        "organization": {"read": True, "write": True, "delete": False},
        "location": {"read": True, "write": True, "delete": False},
    },
    "PATIENT": {
        "patient": {"read": "own", "write": "own", "delete": False},
        "encounter": {"read": "own", "write": False, "delete": False},
        "observation": {"read": "own", "write": False, "delete": False},
        "clinical_note": {"read": "own", "write": False, "delete": False},
        "consent": {"read": "own", "write": "own", "delete": False},
    },
    "RESEARCHER": {
        "patient": {"read": "anonymized", "write": False, "delete": False},
        "observation": {"read": "anonymized", "write": False, "delete": False},
        "clinical_note": {"read": "anonymized", "write": False, "delete": False},
    },
}
