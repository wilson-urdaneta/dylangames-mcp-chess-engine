"""Centralized logging configuration for the chess engine service."""

import logging
import logging.handlers
import os
import sys
from typing import Optional

from dylangames_mcp_chess_engine.config import Settings


def setup_logging(settings: Settings) -> None:
    """Set up logging configuration for the application.

    This function configures the root logger with three handlers:
    1. Console handler (stderr) for WARNING and above
    2. Main rotating file handler for DEBUG and above
    3. Error rotating file handler for ERROR and above

    Args:
        settings: Application settings containing LOG_LEVEL
    """
    # Define log directory and create if it doesn't exist
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Define log file paths
    main_log_file = os.path.join(log_dir, "engine.log")
    error_log_file = os.path.join(log_dir, "engine.error.log")

    # Define log format
    log_format = "%(asctime)s - %(levelname)-8s - %(name)-25s - %(message)s"
    formatter = logging.Formatter(log_format)

    # Get root logger and clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Configure console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure main rotating file handler
    main_file_handler = logging.handlers.RotatingFileHandler(
        main_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
        mode="a",
    )
    main_file_handler.setLevel(logging.DEBUG)
    main_file_handler.setFormatter(formatter)
    root_logger.addHandler(main_file_handler)

    # Configure error rotating file handler
    error_file_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
        mode="a",
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(formatter)
    root_logger.addHandler(error_file_handler)

    # Log initial configuration
    root_logger.info(
        "Logging configured: Level %s, Console (WARNING+), "
        "File (DEBUG+ to %s), Error File (ERROR+ to %s)",
        settings.LOG_LEVEL,
        main_log_file,
        error_log_file,
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name, defaults to 'engine' if not provided

    Returns:
        A logger instance configured according to the root logger settings
    """
    default_name = "engine"
    return logging.getLogger(name or default_name)
