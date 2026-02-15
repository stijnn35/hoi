"""
Create initial admin user.
Interactive script to create a super admin user for system administration.
"""

import asyncio
import getpass
import sys
from uuid import uuid4

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, ".")

from src.core.config.logging import get_logger
from src.domain.models import User, Role, UserRole
from src.infrastructure.database.connection import get_async_session

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address

    Returns:
        True if valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password strength.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"

    return True, ""


async def create_admin_user(
    session: AsyncSession,
    email: str,
    username: str,
    password: str
) -> User:
    """
    Create admin user with SUPER_ADMIN role.

    Args:
        session: Database session
        email: User email
        username: Username
        password: Password (will be hashed)

    Returns:
        Created user
    """
    # Check if user already exists
    result = await session.execute(
        select(User).where(
            (User.email == email) | (User.username == username)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise ValueError(f"User with email '{email}' or username '{username}' already exists")

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Create user
    user = User(
        id=uuid4(),
        email=email,
        username=username,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=True,  # Auto-verify admin
        mfa_enabled=False,  # MFA can be enabled later
    )

    session.add(user)
    await session.flush()  # Flush to get user ID

    # Get SUPER_ADMIN role
    result = await session.execute(
        select(Role).where(Role.name == "SUPER_ADMIN")
    )
    admin_role = result.scalar_one_or_none()

    if not admin_role:
        raise ValueError(
            "SUPER_ADMIN role not found. Please run 'python scripts/seed_roles.py' first."
        )

    # Assign role
    user_role = UserRole(
        id=uuid4(),
        user_id=user.id,
        role_id=admin_role.id,
        assigned_by=user.id,  # Self-assigned for first admin
    )

    session.add(user_role)
    await session.commit()

    logger.info(
        "Admin user created successfully",
        user_id=str(user.id),
        email=email,
        username=username
    )

    return user


async def interactive_create_admin() -> None:
    """Interactive admin user creation."""
    print("\n" + "=" * 60)
    print("     Psychiatric EHR - Admin User Creation")
    print("=" * 60 + "\n")

    # Get email
    while True:
        email = input("Admin email address: ").strip()
        if validate_email(email):
            break
        print("❌ Invalid email format. Please try again.\n")

    # Get username
    while True:
        username = input("Admin username: ").strip()
        if len(username) >= 3:
            break
        print("❌ Username must be at least 3 characters long.\n")

    # Get password
    while True:
        password = getpass.getpass("Admin password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if password != password_confirm:
            print("❌ Passwords do not match. Please try again.\n")
            continue

        is_valid, error_msg = validate_password(password)
        if not is_valid:
            print(f"❌ {error_msg}\n")
            continue

        break

    print("\n" + "-" * 60)
    print("Creating admin user...")
    print("-" * 60 + "\n")

    try:
        async for session in get_async_session():
            user = await create_admin_user(session, email, username, password)

        print("✅ Admin user created successfully!\n")
        print(f"   Email:    {email}")
        print(f"   Username: {username}")
        print(f"   Role:     SUPER_ADMIN")
        print(f"\n   User ID:  {user.id}\n")
        print("=" * 60)
        print("\n⚠️  IMPORTANT: Please enable MFA after first login!\n")

    except ValueError as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        logger.error("Failed to create admin user", error=str(e), exc_info=True)
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)


async def non_interactive_create_admin(
    email: str,
    username: str,
    password: str
) -> None:
    """
    Non-interactive admin creation (for automation).

    Args:
        email: Admin email
        username: Admin username
        password: Admin password
    """
    try:
        async for session in get_async_session():
            user = await create_admin_user(session, email, username, password)

        logger.info("Admin user created", user_id=str(user.id))

    except Exception as e:
        logger.error("Failed to create admin user", error=str(e), exc_info=True)
        raise


async def main() -> None:
    """Main execution function."""
    # Check for command line arguments
    if len(sys.argv) == 4:
        # Non-interactive mode
        email = sys.argv[1]
        username = sys.argv[2]
        password = sys.argv[3]

        logger.info("Creating admin user (non-interactive mode)")
        await non_interactive_create_admin(email, username, password)
    else:
        # Interactive mode
        await interactive_create_admin()


if __name__ == "__main__":
    asyncio.run(main())
