"""
Database initialization script.
Sets up the database, runs migrations, and seeds initial data.
"""

import asyncio
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")

from src.core.config.logging import get_logger
from src.core.config.settings import settings

logger = get_logger(__name__)


def run_command(command: list[str], description: str) -> bool:
    """
    Run a shell command and handle errors.

    Args:
        command: Command to run
        description: Description of the command

    Returns:
        True if successful
    """
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print(result.stdout)
        logger.info(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(
            f"❌ {description} failed",
            error=str(e),
            stdout=e.stdout,
            stderr=e.stderr
        )
        print(f"\nError output:\n{e.stderr}")
        return False


async def check_database_connection() -> bool:
    """
    Check if database is accessible.

    Returns:
        True if database is accessible
    """
    logger.info("Checking database connection...")
    try:
        from src.infrastructure.database.connection import get_async_engine

        engine = get_async_engine()
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")

        logger.info("✅ Database connection successful")
        return True

    except Exception as e:
        logger.error("❌ Database connection failed", error=str(e))
        return False


async def create_extensions() -> bool:
    """
    Create required PostgreSQL extensions.

    Returns:
        True if successful
    """
    logger.info("Creating PostgreSQL extensions...")

    try:
        from src.infrastructure.database.connection import get_async_engine

        engine = get_async_engine()
        async with engine.connect() as conn:
            # Create extensions
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
            await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
            await conn.commit()

        logger.info("✅ PostgreSQL extensions created")
        return True

    except Exception as e:
        logger.error("❌ Failed to create extensions", error=str(e))
        return False


async def main() -> None:
    """Main initialization function."""
    print("\n" + "=" * 70)
    print("     Psychiatric EHR - Database Initialization")
    print("=" * 70 + "\n")

    logger.info("Starting database initialization...")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[-1]}")  # Hide credentials

    # Step 1: Check database connection
    print("\n[1/5] Checking database connection...")
    if not await check_database_connection():
        print("\n❌ Cannot connect to database. Please ensure PostgreSQL is running.")
        print(f"   Database URL: {settings.DATABASE_URL.split('@')[-1]}")
        print("\nTo create the database manually:")
        print("   createdb psychiatric_ehr")
        sys.exit(1)

    # Step 2: Create extensions
    print("\n[2/5] Creating PostgreSQL extensions...")
    if not await create_extensions():
        print("\n⚠️  Warning: Failed to create extensions. Migration may fail.")
        print("   Run manually:")
        print("   psql psychiatric_ehr -c \"CREATE EXTENSION vector;\"")

    # Step 3: Run migrations
    print("\n[3/5] Running database migrations...")
    if not run_command(
        ["alembic", "upgrade", "head"],
        "Database migrations"
    ):
        print("\n❌ Migration failed. Please check the error above.")
        sys.exit(1)

    # Step 4: Seed roles
    print("\n[4/5] Seeding default roles...")
    if not run_command(
        ["python", "scripts/seed_roles.py"],
        "Role seeding"
    ):
        print("\n❌ Role seeding failed.")
        sys.exit(1)

    # Step 5: Create admin user (optional)
    print("\n[5/5] Create admin user (optional)")
    print("\nWould you like to create an admin user now? (y/n): ", end="")
    response = input().strip().lower()

    if response == 'y':
        if not run_command(
            ["python", "scripts/create_admin.py"],
            "Admin user creation"
        ):
            print("\n⚠️  Admin user creation failed or was skipped.")
    else:
        print("\nℹ️  You can create an admin user later by running:")
        print("   python scripts/create_admin.py")

    # Done!
    print("\n" + "=" * 70)
    print("✅ Database initialization completed successfully!")
    print("=" * 70 + "\n")

    print("Next steps:")
    print("  1. Start the application: python src/main.py")
    print("  2. Access API docs: http://localhost:8000/docs")
    print("  3. Enable MFA for admin user after first login")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Initialization cancelled by user.\n")
        sys.exit(1)
    except Exception as e:
        logger.error("Initialization failed", error=str(e), exc_info=True)
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
