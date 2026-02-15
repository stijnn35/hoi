"""
Database connection management using async SQLAlchemy.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from src.core.config.logging import get_logger
from src.core.config.settings import settings

logger = get_logger(__name__)


# Global engine instance
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_async_engine() -> AsyncEngine:
    """
    Get or create the async SQLAlchemy engine.

    Returns:
        AsyncEngine instance
    """
    global _engine

    if _engine is None:
        logger.info(
            "Creating async database engine",
            database_url=settings.DATABASE_URL.split("@")[-1],  # Hide credentials
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
        )

        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_size=settings.DATABASE_POOL_SIZE,
            max_overflow=settings.DATABASE_MAX_OVERFLOW,
            pool_recycle=settings.DATABASE_POOL_RECYCLE,
            pool_pre_ping=True,  # Verify connections before using
            poolclass=NullPool if settings.is_development() else None,
        )

    return _engine


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session maker.

    Returns:
        async_sessionmaker instance
    """
    global _async_session_maker

    if _async_session_maker is None:
        engine = get_async_engine()
        _async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

    return _async_session_maker


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for FastAPI routes.

    Yields:
        AsyncSession instance
    """
    async_session_maker = get_async_session_maker()
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_database_connection() -> None:
    """
    Close database connections.
    Should be called on application shutdown.
    """
    global _engine, _async_session_maker

    if _engine is not None:
        logger.info("Closing database connections")
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
