"""
User model for authentication and authorization.
"""

from datetime import datetime
from typing import List

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from src.infrastructure.database.base import Base, TimestampMixin, UUIDMixin


class User(Base, UUIDMixin, TimestampMixin):
    """
    User account for system access.
    Represents any user who can log into the system (practitioners, admins, patients with portal access).
    """

    __tablename__ = "users"

    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (login identifier)"
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Username (alternative login identifier)"
    )

    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )

    # Account status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Account active status"
    )

    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email verification status"
    )

    # Multi-Factor Authentication
    mfa_enabled = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="MFA activation flag"
    )

    mfa_secret = Column(
        String(255),
        nullable=True,
        comment="TOTP secret for MFA (encrypted)"
    )

    # Login tracking
    last_login = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last successful login timestamp"
    )

    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Consecutive failed login attempts"
    )

    locked_until = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account lock expiration timestamp"
    )

    # Password reset
    password_reset_token = Column(
        String(255),
        nullable=True,
        comment="Password reset token (hashed)"
    )

    password_reset_expires = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Password reset token expiration"
    )

    # Email verification
    verification_token = Column(
        String(255),
        nullable=True,
        comment="Email verification token"
    )

    verification_expires = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Email verification token expiration"
    )

    # Relationships
    roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    practitioner = relationship(
        "Practitioner",
        back_populates="user",
        uselist=False
    )

    patient = relationship(
        "Patient",
        back_populates="user",
        uselist=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, active={self.is_active})>"

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until

    @property
    def role_names(self) -> List[str]:
        """Get list of role names for this user."""
        return [user_role.role.name for user_role in self.roles]
