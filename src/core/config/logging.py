"""
Structured logging configuration using structlog.
Provides JSON logging for production and human-readable logs for development.
"""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from src.core.config.settings import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to log entries."""
    event_dict["app_name"] = settings.APP_NAME
    event_dict["app_version"] = settings.APP_VERSION
    event_dict["environment"] = settings.ENVIRONMENT
    return event_dict


def drop_color_message_key(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Remove color_message from event_dict if it exists.
    Used for JSON formatting where ANSI codes are not needed.
    """
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging() -> None:
    """Configure structlog for structured logging."""

    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Shared processors for all configurations
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_app_context,
    ]

    # Development vs Production configuration
    if settings.is_development() and settings.LOG_FORMAT == "text":
        # Human-readable console output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.rich_traceback
            )
        ]
    else:
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            drop_color_message_key,
            structlog.processors.JSONRenderer()
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Silence noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# Initialize logging on module import
configure_logging()
