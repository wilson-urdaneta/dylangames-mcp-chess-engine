"""Configuration management for the chess engine service."""

import os
import platform
from enum import Enum
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_default_os() -> str:
    """Get the default OS name for the engine binary."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


class LogLevel(str, Enum):
    """Valid log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Configuration settings for the chess engine service."""

    # Engine settings
    ENGINE_PATH: Optional[str] = Field(
        None,
        description=(
            "Optional path to the engine binary. "
            "If not set, will use built-in path."
        ),
    )
    ENGINE_NAME: str = Field(
        "stockfish", description="Name of the chess engine."
    )
    ENGINE_VERSION: str = Field(
        "17.1", description="Version of the chess engine."
    )
    ENGINE_OS: str = Field(
        default_factory=_get_default_os,
        description=(
            "Operating system for the engine binary. Defaults to current OS."
        ),
    )
    ENGINE_BINARY: str = Field(
        "stockfish", description="Name of the engine binary file."
    )

    # MCP server settings
    MCP_HOST: str = Field(
        "127.0.0.1", description="Host address for the MCP server."
    )
    MCP_PORT: int = Field(9000, description="Port for the MCP server.")

    # Logging settings
    LOG_LEVEL: str = Field(
        "INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    # Configure env file settings
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate that the log level is one of the allowed values."""
        try:
            return LogLevel[v.upper()].value
        except KeyError:
            raise ValueError(
                "Invalid log level: {}. Must be one of: {}".format(
                    v, ", ".join(LogLevel.__members__)
                )
            )

    @field_validator("MCP_PORT")
    def validate_port(cls, v: int) -> int:
        """Validate that the port is in a valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v


def get_settings():
    """Get settings instance, respecting test environment."""
    env = os.environ.get("PYTHON_ENV")
    if env == "test":
        # In test mode, only use environment variables, ignore .env file
        return Settings(_env_file=None)
    return Settings()


# Create a global settings instance
settings = get_settings()
