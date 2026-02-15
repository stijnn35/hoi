"""
RBAC (Role-Based Access Control) middleware.
Enforces role-based permissions on all API endpoints.
"""

from typing import Callable, Optional
from uuid import UUID

from fastapi import Request, Response, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config.logging import get_logger
from src.domain.models import User, Role, UserRole, Patient
from src.infrastructure.database.connection import get_async_session

logger = get_logger(__name__)


class RBACMiddleware(BaseHTTPMiddleware):
    """
    Role-Based Access Control middleware.
    Enforces permissions based on user roles and resource ownership.
    """

    # Public endpoints that don't require authentication
    PUBLIC_PATHS = {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/forgot-password",
        "/api/v1/auth/reset-password",
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    # Admin-only endpoints
    ADMIN_ONLY_PATHS = {
        "/api/v1/admin",
        "/api/v1/audit-logs",
        "/api/v1/roles",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request through RBAC checks.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip RBAC for public endpoints
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Skip RBAC for static files
        if request.url.path.startswith("/static"):
            return await call_next(request)

        # Get current user from request state (set by auth middleware)
        current_user: Optional[User] = request.state.user if hasattr(request.state, "user") else None

        if not current_user:
            logger.warning(
                "RBAC check failed: No authenticated user",
                path=request.url.path,
                method=request.method
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )

        # Check admin-only endpoints
        if self._is_admin_only_path(request.url.path):
            if not await self._is_admin(current_user):
                logger.warning(
                    "RBAC check failed: Admin access required",
                    user_id=str(current_user.id),
                    path=request.url.path
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )

        # Extract resource and action from request
        resource_type, action = self._extract_resource_and_action(request)

        # Check permission
        has_permission = await self._check_permission(
            current_user,
            resource_type,
            action,
            request
        )

        if not has_permission:
            logger.warning(
                "RBAC check failed: Permission denied",
                user_id=str(current_user.id),
                resource_type=resource_type,
                action=action,
                path=request.url.path
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions for {action} on {resource_type}"
            )

        # Log successful authorization
        logger.debug(
            "RBAC check passed",
            user_id=str(current_user.id),
            resource_type=resource_type,
            action=action
        )

        # Proceed to next middleware/handler
        response = await call_next(request)
        return response

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public."""
        return any(path.startswith(public_path) for public_path in self.PUBLIC_PATHS)

    def _is_admin_only_path(self, path: str) -> bool:
        """Check if path requires admin access."""
        return any(path.startswith(admin_path) for admin_path in self.ADMIN_ONLY_PATHS)

    def _extract_resource_and_action(self, request: Request) -> tuple[str, str]:
        """
        Extract resource type and action from request.

        Args:
            request: HTTP request

        Returns:
            Tuple of (resource_type, action)
        """
        path = request.url.path
        method = request.method

        # Map HTTP methods to actions
        method_action_map = {
            "GET": "read",
            "POST": "write",
            "PUT": "write",
            "PATCH": "write",
            "DELETE": "delete",
        }
        action = method_action_map.get(method, "read")

        # Extract resource from path
        # Example: /api/v1/patients/123 -> resource_type = "patient"
        path_parts = path.strip("/").split("/")
        if len(path_parts) >= 3:
            resource_type = path_parts[2].rstrip("s")  # Remove plural 's'
        else:
            resource_type = "unknown"

        return resource_type, action

    async def _is_admin(self, user: User) -> bool:
        """
        Check if user has admin role.

        Args:
            user: User instance

        Returns:
            True if user is admin
        """
        return "SUPER_ADMIN" in user.role_names

    async def _check_permission(
        self,
        user: User,
        resource_type: str,
        action: str,
        request: Request
    ) -> bool:
        """
        Check if user has permission for action on resource.

        Args:
            user: User instance
            resource_type: Type of resource (patient, encounter, etc.)
            action: Action to perform (read, write, delete)
            request: HTTP request

        Returns:
            True if permission granted
        """
        # Super admin has all permissions
        if "SUPER_ADMIN" in user.role_names:
            return True

        # Load user roles with permissions
        async for session in get_async_session():
            result = await session.execute(
                select(Role)
                .join(UserRole)
                .where(UserRole.user_id == user.id)
            )
            roles = result.scalars().all()

            # Check each role for permission
            for role in roles:
                # Check wildcard permission
                if role.permissions.get("*") == "*":
                    return True

                # Check resource permission
                resource_perms = role.permissions.get(resource_type, {})

                # Handle direct boolean permissions
                if isinstance(resource_perms, bool):
                    return resource_perms

                # Handle wildcard resource permissions
                if resource_perms == "*" or resource_perms is True:
                    return True

                # Handle specific action permissions
                if isinstance(resource_perms, dict):
                    perm_value = resource_perms.get(action, False)

                    # Handle "own" permission (patient access to own data)
                    if perm_value == "own":
                        return await self._check_own_resource(user, request, session)

                    # Handle boolean permission
                    if perm_value is True:
                        return True

            return False

    async def _check_own_resource(
        self,
        user: User,
        request: Request,
        session: AsyncSession
    ) -> bool:
        """
        Check if user is accessing their own resource.
        Used for patient portal access.

        Args:
            user: User instance
            request: HTTP request
            session: Database session

        Returns:
            True if accessing own resource
        """
        # Extract resource ID from path
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) < 4:
            return False

        try:
            resource_id = UUID(path_parts[3])
        except (ValueError, IndexError):
            return False

        # Check if user has linked patient record
        result = await session.execute(
            select(Patient).where(Patient.user_id == user.id)
        )
        patient = result.scalar_one_or_none()

        if not patient:
            return False

        # Check if accessing own patient record
        return patient.id == resource_id

    def __repr__(self) -> str:
        return "<RBACMiddleware>"
