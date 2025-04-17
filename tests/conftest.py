"""Configure pytest for the test suite."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables for all tests."""
    old_env = dict(os.environ)
    os.environ.update(
        {
            "PYTHON_ENV": "test",
            "MCP_HOST": "127.0.0.1",
            "MCP_PORT": "9000",
            "LOG_LEVEL": "DEBUG",
        }
    )
    yield
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def test_positions():
    """Common test positions used across test files."""
    return {
        "STARTING_FEN": (
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        ),
        "CHECKMATE_FEN": (  # Fool's mate
            "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1"
        ),
        "STALEMATE_FEN": ("k7/8/1Q6/8/8/8/8/K7 b - - 0 1"),
        "INSUFFICIENT_MATERIAL_FEN": (
            "8/8/8/8/8/8/8/k1K5 w - - 0 1"
        ),  # King vs King
    }


@pytest.fixture
def mock_engine_process():
    """Mock subprocess.Popen for engine tests."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = mock_popen.return_value
        mock_process.poll.return_value = None
        mock_process.stdout.fileno.return_value = 1
        mock_process.stdout.readline.side_effect = [
            b"Stockfish 17.1\n",
            b"uciok\n",
            b"readyok\n",
        ]
        yield mock_process


@pytest.fixture
def mock_engine_path():
    """Mock engine path for tests."""
    with patch(
        "dylangames_mcp_chess_engine.engine_wrapper._get_engine_path"
    ) as mock_get_path:
        mock_get_path.return_value = Path("/mock/stockfish")
        yield mock_get_path


@pytest.fixture
def mock_select():
    """Mock select.select for engine tests."""
    with patch("select.select") as mock_select:
        mock_select.return_value = ([MagicMock()], [], [])
        yield mock_select
