"""Centralized structured logging configuration using structlog."""

import logging
import sys
from typing import Optional

import structlog


def setup_logging(log_level: str) -> None:
    """Set up structlog configuration for JSON logging to stderr.

    Args:
        log_level: The minimum log level string (e.g., "INFO", "DEBUG").
    """
    log_level_int = getattr(logging, log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            # Add log level and logger name info from the standard logger record.
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            # Add timestamps.
            structlog.processors.TimeStamper(fmt="iso"),
            # Perform %-style formatting.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        # Use stdlib's logging infrastructure for output.
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure the underlying stdlib formatter and handler.
    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on the final output dict.
        processor=structlog.processors.JSONRenderer(),
        # Keep foreign log messages (from non-structlog loggers) as-is.
        foreign_pre_chain=[structlog.stdlib.add_log_level, structlog.stdlib.add_logger_name],
    )

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)

    # Get the root logger, clear handlers, set level, and add the new handler.
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(log_level_int)
    root_logger.addHandler(handler)

    # Log initial configuration message using structlog
    logger = get_logger(__name__)
    logger.info(
        "Structlog configured",
        level=log_level,
        format="JSON",
        output="stderr",
    )


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """Get a structlog logger instance, compatible with standard logging.

    Args:
        name: Logger name.

    Returns:
        A structlog BoundLogger instance.
    """
    return structlog.stdlib.get_logger(name or "chesspal_engine")
