"""
Seed default roles and permissions.
Creates the standard RBAC roles for the psychiatric EHR system.
"""

import asyncio
import sys
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.insert(0, ".")

from src.core.config.logging import get_logger
from src.domain.models import Role, ROLE_PERMISSIONS
from src.infrastructure.database.connection import get_async_session

logger = get_logger(__name__)


async def seed_roles(session: AsyncSession) -> None:
    """
    Seed default roles into the database.

    Args:
        session: Database session
    """
    logger.info("Starting role seeding...")

    roles_created = 0
    roles_skipped = 0

    for role_name, permissions in ROLE_PERMISSIONS.items():
        # Check if role already exists
        result = await session.execute(
            select(Role).where(Role.name == role_name)
        )
        existing_role = result.scalar_one_or_none()

        if existing_role:
            logger.info(f"Role '{role_name}' already exists, skipping")
            roles_skipped += 1
            continue

        # Create role
        role = Role(
            id=uuid4(),
            name=role_name,
            description=get_role_description(role_name),
            permissions=permissions
        )

        session.add(role)
        roles_created += 1
        logger.info(f"Created role: {role_name}")

    await session.commit()

    logger.info(
        "Role seeding complete",
        created=roles_created,
        skipped=roles_skipped,
        total=len(ROLE_PERMISSIONS)
    )


def get_role_description(role_name: str) -> str:
    """
    Get description for a role.

    Args:
        role_name: Name of the role

    Returns:
        Role description
    """
    descriptions = {
        "SUPER_ADMIN": "System administrator with full access to all features and data",
        "PSYCHOLOGIST": "Licensed psychologist with clinical access to patient data",
        "PSYCHIATRIST": "Medical doctor psychiatrist with prescribing capabilities",
        "THERAPIST": "Therapist with limited clinical access",
        "ADMIN_STAFF": "Administrative staff with scheduling and organizational access",
        "PATIENT": "Patient portal access to own data only",
        "RESEARCHER": "Research access to anonymized data only",
    }
    return descriptions.get(role_name, f"Role: {role_name}")


async def main() -> None:
    """Main execution function."""
    logger.info("=== Role Seeding Script ===")

    try:
        async for session in get_async_session():
            await seed_roles(session)

        logger.info("✅ Role seeding completed successfully")

    except Exception as e:
        logger.error(
            "❌ Role seeding failed",
            error=str(e),
            exc_info=True
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
