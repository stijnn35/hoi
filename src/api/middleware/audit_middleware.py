"""
Audit logging middleware.
Automatically logs all API requests for GDPR Article 30 compliance.
"""

import uuid
from typing import Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import insert

from src.core.config.logging import get_logger
from src.domain.models import User, AuditLog
from src.infrastructure.database.connection import get_async_session

logger = get_logger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Audit logging middleware for GDPR compliance.
    Logs all data access and modifications to audit_logs table.
    """

    # Paths to exclude from audit logging (to reduce noise)
    EXCLUDE_PATHS = {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/static",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log to audit trail.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip audit logging for excluded paths
        if self._should_exclude(request.url.path):
            return await call_next(request)

        # Generate request ID for tracing
        request_id = uuid.uuid4()
        request.state.request_id = request_id

        # Get user from request state (set by auth middleware)
        current_user: User = getattr(request.state, "user", None)

        # Extract client IP
        client_ip = self._get_client_ip(request)

        # Extract user agent
        user_agent = request.headers.get("user-agent", "")

        # Process request
        start_time = datetime.utcnow()
        response = None
        error = None

        try:
            response = await call_next(request)
            return response

        except Exception as e:
            error = e
            raise

        finally:
            # Log to audit trail (async, don't block response)
            try:
                await self._log_to_audit(
                    request=request,
                    response=response,
                    user=current_user,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    request_id=request_id,
                    error=error
                )
            except Exception as audit_error:
                # Never fail request due to audit logging errors
                logger.error(
                    "Failed to write audit log",
                    error=str(audit_error),
                    request_id=str(request_id),
                    exc_info=True
                )

    def _should_exclude(self, path: str) -> bool:
        """Check if path should be excluded from audit logging."""
        return any(path.startswith(exclude) for exclude in self.EXCLUDE_PATHS)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request.
        Handles X-Forwarded-For header for proxied requests.

        Args:
            request: HTTP request

        Returns:
            Client IP address
        """
        # Check X-Forwarded-For header (from proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take first IP in chain
            return forwarded_for.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        if request.client:
            return request.client.host

        return "unknown"

    async def _log_to_audit(
        self,
        request: Request,
        response: Response | None,
        user: User | None,
        client_ip: str,
        user_agent: str,
        request_id: uuid.UUID,
        error: Exception | None
    ) -> None:
        """
        Write audit log entry to database.

        Args:
            request: HTTP request
            response: HTTP response (if successful)
            user: Authenticated user
            client_ip: Client IP address
            user_agent: User agent string
            request_id: Request trace ID
            error: Exception if request failed
        """
        # Determine action type from method
        method_action_map = {
            "GET": "READ",
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }
        action_type = method_action_map.get(request.method, "OTHER")

        # Extract resource type from path
        resource_type = self._extract_resource_type(request.url.path)

        # Extract resource ID from path if present
        resource_id = self._extract_resource_id(request.url.path)

        # Determine if access was granted
        access_granted = error is None and (response is None or response.status_code < 400)

        # Get denial reason if access denied
        denial_reason = None
        if not access_granted:
            if error:
                denial_reason = str(error)
            elif response and response.status_code >= 400:
                denial_reason = f"HTTP {response.status_code}"

        # Build metadata
        metadata = {
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "status_code": response.status_code if response else None,
        }

        # Insert audit log
        async for session in get_async_session():
            try:
                stmt = insert(AuditLog).values(
                    timestamp=datetime.utcnow(),
                    actor_user_id=user.id if user else None,
                    actor_ip_address=client_ip,
                    actor_user_agent=user_agent,
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    patient_id=None,  # Will be set by application layer when known
                    access_granted=access_granted,
                    denial_reason=denial_reason,
                    request_id=request_id,
                    metadata=metadata
                )
                await session.execute(stmt)
                await session.commit()

                logger.debug(
                    "Audit log created",
                    request_id=str(request_id),
                    action=action_type,
                    resource=resource_type,
                    granted=access_granted
                )

            except Exception as e:
                logger.error(
                    "Failed to insert audit log",
                    error=str(e),
                    exc_info=True
                )
                await session.rollback()

    def _extract_resource_type(self, path: str) -> str:
        """
        Extract resource type from URL path.

        Args:
            path: URL path

        Returns:
            Resource type string
        """
        # Example: /api/v1/patients/123 -> "patient"
        parts = path.strip("/").split("/")
        if len(parts) >= 3:
            resource = parts[2].rstrip("s")  # Remove plural 's'
            return resource
        return "unknown"

    def _extract_resource_id(self, path: str) -> uuid.UUID | None:
        """
        Extract resource ID from URL path.

        Args:
            path: URL path

        Returns:
            Resource UUID or None
        """
        # Example: /api/v1/patients/123 -> UUID("123...")
        parts = path.strip("/").split("/")
        if len(parts) >= 4:
            try:
                return uuid.UUID(parts[3])
            except (ValueError, IndexError):
                pass
        return None

    def __repr__(self) -> str:
        return "<AuditMiddleware>"
