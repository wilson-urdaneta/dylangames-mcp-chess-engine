"""Test suite for engine binary handling."""

import os
from unittest.mock import patch

import pytest

from dylangames_mcp_chess_engine.engine_wrapper import EngineBinaryError, _get_engine_path


def test_engine_path_set_and_valid():
    """Test when ENGINE_PATH is set and valid."""
    with patch.dict(os.environ, {"ENGINE_PATH": "/valid/path/to/engine"}, clear=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.access", return_value=True):
        path = _get_engine_path()
        assert path == "/valid/path/to/engine"


def test_engine_path_set_but_invalid():
    """Test when ENGINE_PATH is set but invalid (file doesn't exist)."""
    with patch.dict(os.environ, {"ENGINE_PATH": "/invalid/path/to/engine"}, clear=True), \
         patch("os.path.isfile", return_value=False):
        # Should fall back to default path construction
        with patch("os.path.isfile", side_effect=[False, True]), \
             patch("os.access", return_value=True):
            path = _get_engine_path()
            assert path.endswith("engines/stockfish/17.1/linux/stockfish")


def test_engine_path_unset_all_defaults():
    """Test when ENGINE_PATH is unset and all fallback vars use defaults."""
    with patch.dict(os.environ, {}, clear=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.access", return_value=True):
        path = _get_engine_path()
        assert path.endswith("engines/stockfish/17.1/linux/stockfish")


def test_engine_path_unset_some_fallback_vars():
    """Test when ENGINE_PATH is unset and some fallback vars are set."""
    with patch.dict(os.environ, {
        "ENGINE_OS": "windows",
        "ENGINE_BINARY": "stockfish.exe"
    }, clear=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.access", return_value=True):
        path = _get_engine_path()
        assert path.endswith("engines/stockfish/17.1/windows/stockfish.exe")


def test_engine_path_unset_empty_binary():
    """Test when ENGINE_PATH is unset and ENGINE_BINARY is empty."""
    with patch.dict(os.environ, {"ENGINE_BINARY": ""}, clear=True):
        with pytest.raises(EngineBinaryError, match="Engine binary name cannot be empty"):
            _get_engine_path()


def test_engine_path_unset_fallback_not_found():
    """Test when ENGINE_PATH is unset and fallback path doesn't exist."""
    with patch.dict(os.environ, {}, clear=True), \
         patch("os.path.isfile", return_value=False):
        with pytest.raises(EngineBinaryError, match="Engine binary not found"):
            _get_engine_path()


def test_engine_path_unset_fallback_not_executable():
    """Test when ENGINE_PATH is unset and fallback path exists but isn't executable."""
    with patch.dict(os.environ, {}, clear=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.access", return_value=False):
        with pytest.raises(EngineBinaryError, match="Engine binary is not executable"):
            _get_engine_path() 