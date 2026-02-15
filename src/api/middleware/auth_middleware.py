"""
Authentication middleware.
Validates JWT tokens and loads user context.
"""

from typing import Callable, Optional

from fastapi import Request, Response, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config.logging import get_logger
from src.core.config.settings import settings
from src.domain.models import User
from src.infrastructure.database.connection import get_async_session

logger = get_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    JWT authentication middleware.
    Validates JWT tokens and attaches user to request state.
    """

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/auth/verify-email",
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through authentication.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Skip authentication for static files
        if request.url.path.startswith("/static"):
            return await call_next(request)

        # Extract token from Authorization header
        token = self._extract_token(request)

        if not token:
            logger.warning(
                "Authentication failed: No token provided",
                path=request.url.path,
                method=request.method
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token and load user
        user = await self._validate_token_and_load_user(token)

        if not user:
            logger.warning(
                "Authentication failed: Invalid token",
                path=request.url.path
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(
                "Authentication failed: User inactive",
                user_id=str(user.id)
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Check if account is locked
        if user.is_locked:
            logger.warning(
                "Authentication failed: Account locked",
                user_id=str(user.id),
                locked_until=user.locked_until
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is locked due to too many failed login attempts"
            )

        # Attach user to request state
        request.state.user = user

        # Set user context for database RLS policies
        # This will be used by database session to enforce row-level security
        request.state.user_id = str(user.id)

        logger.debug(
            "User authenticated successfully",
            user_id=str(user.id),
            email=user.email
        )

        # Proceed to next middleware/handler
        response = await call_next(request)
        return response

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (doesn't require auth)."""
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)

    def _extract_token(self, request: Request) -> Optional[str]:
        """
        Extract JWT token from Authorization header.

        Args:
            request: HTTP request

        Returns:
            JWT token or None
        """
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return None

        # Expected format: "Bearer <token>"
        parts = auth_header.split()

        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]

    async def _validate_token_and_load_user(self, token: str) -> Optional[User]:
        """
        Validate JWT token and load user from database.

        Args:
            token: JWT token string

        Returns:
            User instance or None
        """
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Extract user_id from token
            user_id: str = payload.get("sub")

            if not user_id:
                logger.warning("Token validation failed: No user_id in payload")
                return None

            # Load user from database
            async for session in get_async_session():
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    logger.warning(
                        "Token validation failed: User not found",
                        user_id=user_id
                    )
                    return None

                # Load user roles eagerly
                await session.refresh(user, ["roles"])

                return user

        except JWTError as e:
            logger.warning(
                "Token validation failed: JWT error",
                error=str(e)
            )
            return None
        except Exception as e:
            logger.error(
                "Token validation failed: Unexpected error",
                error=str(e),
                exc_info=True
            )
            return None

    def __repr__(self) -> str:
        return "<AuthenticationMiddleware>"
