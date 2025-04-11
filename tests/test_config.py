"""Test configuration handling."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Import will fail until we create the module
from dylangames_mcp_chess_engine.config import Settings


def test_default_settings():
    """Test default settings creation with no environment variables."""
    # Clear any existing environment variables
    for key in ["MCP_HOST", "MCP_PORT", "ENGINE_PATH", "LOG_LEVEL"]:
        if key in os.environ:
            del os.environ[key]

    # Create settings object
    settings = Settings()

    # Check default values
    assert settings.MCP_HOST == "127.0.0.1"
    assert settings.MCP_PORT == 9000
    assert settings.ENGINE_PATH is None
    assert settings.LOG_LEVEL == "DEBUG"


def test_custom_settings_from_env():
    """Test settings with custom environment variables."""
    # Set environment variables
    os.environ["MCP_HOST"] = "0.0.0.0"
    os.environ["MCP_PORT"] = "8080"
    os.environ["ENGINE_PATH"] = "/path/to/engine"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Create settings object
    settings = Settings()

    # Check custom values
    assert settings.MCP_HOST == "0.0.0.0"
    assert settings.MCP_PORT == 8080
    assert settings.ENGINE_PATH == "/path/to/engine"
    assert settings.LOG_LEVEL == "DEBUG"


def test_invalid_port():
    """Test that an invalid port raises a ValidationError."""
    with (
        patch.dict(os.environ, {"MCP_PORT": "invalid"}, clear=True),
        pytest.raises(ValidationError),
    ):
        Settings(_env_file=None)  # Explicitly disable .env file loading


def test_invalid_log_level():
    """Test that an invalid log level raises a ValidationError."""
    with (
        patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True),
        pytest.raises(ValidationError),
    ):
        Settings(_env_file=None)  # Explicitly disable .env file loading


def test_partial_override():
    """Test settings with partial environment variables."""
    # Set only some environment variables
    os.environ["MCP_PORT"] = "8888"
    # Remove the others if they exist
    for key in ["MCP_HOST", "ENGINE_PATH", "LOG_LEVEL"]:
        if key in os.environ:
            del os.environ[key]

    # Create settings object
    settings = Settings()

    # Check mixed values (custom and default)
    assert settings.MCP_HOST == "127.0.0.1"  # Default
    assert settings.MCP_PORT == 8888  # Custom
    assert settings.ENGINE_PATH is None  # Default
    assert settings.LOG_LEVEL == "DEBUG"  # Changed from INFO to DEBUG
