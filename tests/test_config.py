"""Test configuration handling."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

# Import will fail until we create the module
from dylangames_mcp_chess_engine.config import Settings


def test_default_settings():
    """Test that default settings are applied correctly."""
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings(_env_file=None)  # Explicitly disable .env file loading
        assert settings.ENGINE_PATH is None
        assert settings.ENGINE_NAME == "stockfish"
        assert settings.ENGINE_VERSION == "17.1"
        assert settings.ENGINE_OS == "macos"
        assert settings.ENGINE_BINARY == "stockfish"
        assert settings.MCP_HOST == "127.0.0.1"
        assert settings.MCP_PORT == 9000
        assert settings.LOG_LEVEL == "INFO"


def test_custom_settings_from_env():
    """Test that environment variables override defaults."""
    test_env = {
        "ENGINE_PATH": "/custom/path/to/engine",
        "ENGINE_NAME": "custom_engine",
        "ENGINE_VERSION": "16.0",
        "ENGINE_OS": "darwin",
        "ENGINE_BINARY": "custom_binary",
        "MCP_HOST": "0.0.0.0",
        "MCP_PORT": "8080",
        "LOG_LEVEL": "DEBUG",
    }
    with patch.dict(os.environ, test_env, clear=True):
        settings = Settings(_env_file=None)  # Explicitly disable .env file loading
        assert settings.ENGINE_PATH == "/custom/path/to/engine"
        assert settings.ENGINE_NAME == "custom_engine"
        assert settings.ENGINE_VERSION == "16.0"
        assert settings.ENGINE_OS == "darwin"
        assert settings.ENGINE_BINARY == "custom_binary"
        assert settings.MCP_HOST == "0.0.0.0"
        assert settings.MCP_PORT == 8080  # Should be converted to int
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
    """Test that partial environment overrides work correctly."""
    test_env = {
        "ENGINE_PATH": "/custom/path",
        "MCP_PORT": "8888",
    }
    with patch.dict(os.environ, test_env, clear=True):
        settings = Settings(_env_file=None)  # Explicitly disable .env file loading
        # Overridden values
        assert settings.ENGINE_PATH == "/custom/path"
        assert settings.MCP_PORT == 8888
        # Default values
        assert settings.ENGINE_NAME == "stockfish"
        assert settings.MCP_HOST == "127.0.0.1"
        assert settings.LOG_LEVEL == "INFO"
