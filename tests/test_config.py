"""Test configuration handling."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Import will fail until we create the module
from chesspal_mcp_engine.config import Settings


def test_default_settings():
    """Test default settings creation with no environment variables."""
    # Clear any existing environment variables
    for key in ["MCP_HOST", "MCP_PORT", "ENGINE_PATH", "LOG_LEVEL"]:
        if key in os.environ:
            del os.environ[key]

    # Create settings object
    settings = Settings()  # No longer needs type ignore

    # Check default values
    assert settings.MCP_HOST == "127.0.0.1"
    assert settings.MCP_PORT == 9000
    assert settings.CHESSPAL_ENGINE_PATH is None  # Updated var name
    assert settings.LOG_LEVEL in ["DEBUG", "INFO"]  # Default depends on ENVIRONMENT


def test_custom_settings_from_env():
    """Test settings with custom environment variables."""
    # Set environment variables
    os.environ["MCP_HOST"] = "0.0.0.0"
    os.environ["MCP_PORT"] = "8080"
    os.environ["CHESSPAL_ENGINE_PATH"] = "/path/to/engine"  # Updated env var name
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Create settings object
    settings = Settings()  # No longer needs type ignore

    # Check custom values
    assert settings.MCP_HOST == "0.0.0.0"
    assert settings.MCP_PORT == 8080
    assert settings.CHESSPAL_ENGINE_PATH == "/path/to/engine"  # Updated var name
    assert settings.LOG_LEVEL == "DEBUG"


def test_invalid_port():
    """Test that an invalid port raises a ValidationError."""
    with (
        patch.dict(os.environ, {"MCP_PORT": "invalid"}, clear=True),
        pytest.raises(ValidationError),
    ):
        Settings()  # No longer needs type ignore


def test_invalid_log_level():
    """Test that an invalid log level defaults to INFO after logging a warning."""
    # The validator now defaults to INFO instead of raising ValidationError
    with patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True):
        settings = Settings()  # No longer needs type ignore
        assert settings.LOG_LEVEL == "INFO"


def test_partial_override():
    """Test settings with partial environment variables."""
    # Set only some environment variables
    os.environ["MCP_PORT"] = "8888"
    # Remove the others if they exist
    for key in ["MCP_HOST", "ENGINE_PATH", "LOG_LEVEL"]:
        if key in os.environ:
            del os.environ[key]

    # Create settings object
    settings = Settings()  # No longer needs type ignore

    # Check mixed values (custom and default)
    assert settings.MCP_HOST == "127.0.0.1"  # Default
    assert settings.MCP_PORT == 8888  # Custom
    assert settings.CHESSPAL_ENGINE_PATH is None  # Updated var name
    assert settings.LOG_LEVEL in ["DEBUG", "INFO"]  # Default depends on ENVIRONMENT
