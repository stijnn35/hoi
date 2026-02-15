"""
Main FastAPI application entry point.
Psychiatric EHR System - AI-Driven EPD for Psychologists.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.middleware.auth_middleware import AuthenticationMiddleware
from src.api.middleware.audit_middleware import AuditMiddleware
from src.api.middleware.rbac_middleware import RBACMiddleware
from src.core.config.logging import get_logger
from src.core.config.settings import settings
from src.infrastructure.database.connection import (
    close_database_connection,
    get_async_engine,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(
        "Starting Psychiatric EHR System",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT
    )

    # Initialize database connection
    engine = get_async_engine()
    logger.info("Database connection initialized")

    # TODO: Load ROM questionnaires from fixtures
    # TODO: Initialize default roles and permissions
    # TODO: Start background task workers (Celery)

    yield

    # Shutdown
    logger.info("Shutting down Psychiatric EHR System")

    # Close database connections
    await close_database_connection()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Driven Electronic Patient Dossier for Psychiatric Care",
    docs_url="/docs" if settings.is_development() else None,
    redoc_url="/redoc" if settings.is_development() else None,
    lifespan=lifespan,
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Audit middleware (log all requests)
app.add_middleware(AuditMiddleware)

# RBAC middleware (enforce permissions)
app.add_middleware(RBACMiddleware)

# Authentication middleware (validate JWT)
app.add_middleware(AuthenticationMiddleware)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> JSONResponse:
    """
    Health check endpoint.
    Returns application status and version.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> JSONResponse:
    """
    Root endpoint.
    Provides API information.
    """
    return JSONResponse(
        content={
            "message": "Psychiatric EHR API",
            "version": settings.APP_VERSION,
            "docs": "/docs" if settings.is_development() else None,
        }
    )


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler.
    Catches all unhandled exceptions.
    """
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error" if settings.is_production() else str(exc)
        }
    )


# TODO: Include API routers
# from src.api.routes import auth, patients, practitioners, encounters, etc.
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
# ...


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development(),
        log_level=settings.LOG_LEVEL.lower(),
    )
