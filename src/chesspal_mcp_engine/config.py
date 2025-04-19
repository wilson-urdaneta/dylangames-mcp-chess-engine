"""Configuration management for the chess engine service."""

import platform  # Removed unused os import
from enum import Enum
from typing import Any, Optional  # Added Any

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .logging_config import get_logger  # Assuming logger is needed for validation warnings

logger = get_logger(__name__)


class Environment(str, Enum):
    """Application environment enum."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"


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

    # --- General Settings ---
    ENVIRONMENT: str = Field(
        default=Environment.DEVELOPMENT.value,
        description="Application environment (development, production).",
    )
    LOG_LEVEL: str = Field(
        default="INFO",  # Default for production
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )

    # --- MCP Server Settings ---
    MCP_HOST: str = Field(default="127.0.0.1", description="Host address for the MCP server.")
    MCP_PORT: int = Field(default=9000, description="Port for the MCP server.")

    # --- Chess Engine Specific Settings ---
    CHESSPAL_ENGINE_PATH: Optional[str] = Field(
        default=None,
        description="Optional path to the engine binary. If not set, will use built-in path.",
    )
    CHESSPAL_ENGINE_NAME: str = Field(default="stockfish", description="Name of the chess engine.")
    CHESSPAL_ENGINE_VERSION: str = Field(default="17.1", description="Version of the chess engine.")
    CHESSPAL_ENGINE_OS: str = Field(
        default_factory=_get_default_os,
        description="Operating system for the engine binary. Defaults to current OS.",
    )
    CHESSPAL_ENGINE_BINARY: str = Field(default="stockfish", description="Name of the engine binary file.")
    CHESSPAL_ENGINE_DEPTH: int = Field(default=10, description="Search depth for the chess engine.")
    CHESSPAL_ENGINE_TIMEOUT_MS: int = Field(
        default=1000, description="Timeout in milliseconds for engine move calculation."
    )

    # Configure Pydantic Settings
    # Load from environment variables ONLY. .env file loading is handled externally (e.g., Docker Compose).
    model_config = SettingsConfigDict(
        env_file=None,  # Explicitly disable .env file loading by pydantic-settings
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields from environment
    )

    @field_validator("ENVIRONMENT")
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        try:
            return Environment(v.lower()).value
        except ValueError:
            logger.warning(
                f"Invalid ENVIRONMENT value '{v}'. Defaulting to 'development'. Valid values: {', '.join([e.value for e in Environment])}"
            )
            return Environment.DEVELOPMENT.value

    @field_validator("LOG_LEVEL", mode="before")  # Use before to modify based on ENVIRONMENT
    def set_log_level_based_on_env(cls, v: Optional[str], values: Any) -> str:
        """Set default LOG_LEVEL based on ENVIRONMENT if not explicitly set."""
        # Note: Pydantic v2 validation logic differs slightly.
        # We access already validated 'ENVIRONMENT' if available.
        # This validator runs *before* the main LOG_LEVEL validator.
        env = values.data.get("ENVIRONMENT", Environment.DEVELOPMENT.value)  # Get potential env value
        if v is None:  # If LOG_LEVEL is not set via env var
            if env == Environment.DEVELOPMENT.value:
                return LogLevel.DEBUG.value
            else:
                return LogLevel.INFO.value
        return v  # Return the explicitly set value for further validation

    @field_validator("LOG_LEVEL")  # This runs after the 'before' validator
    def validate_log_level(cls, v: str) -> str:
        """Validate that the log level is one of the allowed values."""
        try:
            return LogLevel[v.upper()].value
        except KeyError:
            # Log a warning and default to INFO
            logger.warning(
                f"Invalid LOG_LEVEL '{v}'. Defaulting to INFO. Valid values: {', '.join(LogLevel.__members__)}"
            )
            return LogLevel.INFO.value

    @field_validator("MCP_PORT")
    def validate_port(cls, v: int) -> int:
        """Validate that the port is in a valid range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("CHESSPAL_ENGINE_DEPTH")
    def validate_depth(cls, v: int) -> int:
        """Validate engine depth."""
        if not 1 <= v <= 30:  # Example range, adjust as needed
            raise ValueError("Engine depth must be between 1 and 30")
        return v

    @field_validator("CHESSPAL_ENGINE_TIMEOUT_MS")
    def validate_timeout(cls, v: int) -> int:
        """Validate engine timeout."""
        if not 100 <= v <= 60000:  # Example range (0.1s to 60s)
            raise ValueError("Engine timeout must be between 100 and 60000 ms")
        return v


# Create global instance directly - reads from environment variables
try:
    settings = Settings()
except ValidationError as e:
    # Log validation errors and exit if config is invalid
    logger.critical(f"Configuration validation failed:\n{e}")
    # In a real app, might exit or raise a critical error
    # For now, just log and potentially proceed with defaults where possible
    # Re-instantiate with defaults might be complex, logging is crucial
    raise RuntimeError(f"Configuration validation failed: {e}") from e
