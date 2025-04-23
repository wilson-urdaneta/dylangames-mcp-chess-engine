"""Tests for error handling in the engine_wrapper module."""

import os
import platform

import pytest

from chesspal_mcp_engine.engine_wrapper import EngineBinaryError, _get_engine_path


class TestEngineWrapperErrorHandling:
    """Test error handling in the engine_wrapper module."""

    def test_engine_binary_error_invalid_path(self, monkeypatch):
        """Test EngineBinaryError when fallback path is invalid."""
        # Mock system check to find no system stockfish
        monkeypatch.setattr("chesspal_mcp_engine.config.settings.CHESSPAL_ENGINE_PATH", None)
        monkeypatch.setattr("os.access", lambda *args, **kwargs: False)
        monkeypatch.setattr("pathlib.Path.is_file", lambda *args, **kwargs: False)

        # Mock platform detection
        monkeypatch.setattr(platform, "system", lambda: "Linux")

        with pytest.raises(EngineBinaryError) as exc_info:
            _get_engine_path()

        assert "Stockfish binary not found at fallback path" in str(exc_info.value)

    def test_engine_binary_error_not_executable(self, monkeypatch):
        """Test EngineBinaryError when fallback path exists but is not executable."""
        # Mock system check to find no system stockfish
        monkeypatch.setattr("chesspal_mcp_engine.config.settings.CHESSPAL_ENGINE_PATH", None)
        monkeypatch.setattr("os.access", lambda path, mode: False if mode == os.X_OK else True)
        monkeypatch.setattr("pathlib.Path.is_file", lambda *args: True)

        # Mock platform detection
        monkeypatch.setattr(platform, "system", lambda: "Linux")

        with pytest.raises(EngineBinaryError) as exc_info:
            _get_engine_path()

        assert "exists but is not executable" in str(exc_info.value)

    def test_engine_binary_error_unsupported_platform(self, monkeypatch):
        """Test EngineBinaryError for unsupported platform."""
        # Mock system check to find no system stockfish
        monkeypatch.setattr("chesspal_mcp_engine.config.settings.CHESSPAL_ENGINE_PATH", None)
        monkeypatch.setattr("os.access", lambda *args, **kwargs: False)
        monkeypatch.setattr("pathlib.Path.is_file", lambda *args, **kwargs: False)

        # Mock platform detection for unsupported OS
        monkeypatch.setattr(platform, "system", lambda: "SolarisOS")
        monkeypatch.setattr("chesspal_mcp_engine.config.settings.CHESSPAL_ENGINE_OS", None)

        with pytest.raises(EngineBinaryError) as exc_info:
            _get_engine_path()

        # Fix: Make the comparison case-insensitive
        assert "unsupported platform: solarisos" in str(exc_info.value).lower()

    def test_engine_binary_error_with_env_path(self, monkeypatch):
        """Test EngineBinaryError with invalid CHESSPAL_ENGINE_PATH."""
        # Mock environment path
        invalid_path = "/invalid/path/to/stockfish"
        monkeypatch.setattr("chesspal_mcp_engine.config.settings.CHESSPAL_ENGINE_PATH", invalid_path)
        monkeypatch.setattr("os.access", lambda *args, **kwargs: False)
        monkeypatch.setattr("pathlib.Path.is_file", lambda *args, **kwargs: False)

        # Mock platform detection
        monkeypatch.setattr(platform, "system", lambda: "Linux")

        with pytest.raises(EngineBinaryError) as exc_info:
            _get_engine_path()

        # Check that error message mentions the invalid env path
        assert invalid_path in str(exc_info.value)
