"""Test suite for engine binary handling."""

import os
import platform
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Optional

import pytest
import subprocess
import select
import sys

from dylangames_mcp_chess_engine.engine_wrapper import StockfishEngine, StockfishError, EngineBinaryError, _get_engine_path


def get_os_name():
    """Get the OS name in the format expected by the engine wrapper."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    return system


class MockPipe:
    """Mock pipe for testing."""
    def __init__(self, responses=None):
        self.responses = responses or []
        self.current = 0
        self._fileno = 1
        self.commands = []  # Track commands sent to stdin
        self.done = False  # Flag to indicate when we're done sending responses

    def fileno(self):
        """Return a valid file descriptor number."""
        return self._fileno

    def write(self, data):
        """Track commands written to stdin."""
        self.commands.append(data)

    def flush(self):
        pass

    def readline(self):
        """Return the next response or empty string if done."""
        if self.current < len(self.responses):
            response = self.responses[self.current]
            self.current += 1
            if self.current == len(self.responses):
                self.done = True
            return response
        return b""  # No more responses


class MockProcess:
    """Mock subprocess.Popen for testing."""
    def __init__(self, responses=None):
        self.stdin = MockPipe()
        self.stdout = MockPipe(responses)
        self.stderr = MockPipe()
        self._returncode = None

    def poll(self):
        return self._returncode

    def wait(self, timeout=None):
        self._returncode = 0
        return 0

    def terminate(self):
        self._returncode = 0


@pytest.fixture
def mock_engine(monkeypatch):
    """Fixture to provide a mock engine process."""
    responses = [
        b"Stockfish 17.1\n",
        b"uciok\n",
        b"readyok\n",
    ]
    mock_process = MockProcess(responses)

    def mock_popen(*args, **kwargs):
        return mock_process

    def mock_select(rlist, wlist, xlist, timeout=None):
        stdout = rlist[0]
        if isinstance(stdout, MockPipe) and stdout.current < len(stdout.responses):
            return [stdout], [], []
        return [], [], []

    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    monkeypatch.setattr(select, "select", mock_select)
    return mock_process


def test_initialize_engine(mock_engine):
    """Test engine initialization with mocked subprocess."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path:
        mock_get_path.return_value = Path("/mock/stockfish")
        engine = StockfishEngine()
        assert engine.process is not None


def test_get_best_move_success(mock_engine):
    """Test getting best move with mocked engine responses."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_engine.stdout.responses.extend([
            b"info depth 10 seldepth 15 multipv 1 score cp 38 nodes 20 nps 20000 tbhits 0 time 1 pv e2e4 e7e5\n",
            b"bestmove e2e4 ponder e7e5\n"
        ])
        engine = StockfishEngine()
        best_move = engine.get_best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert best_move == "e2e4"
        # Verify the position command was sent correctly
        assert any(cmd == b"position fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\n" 
                  for cmd in mock_engine.stdin.commands)
        # Verify go command was sent
        assert any(cmd.startswith(b"go movetime") for cmd in mock_engine.stdin.commands)


def test_get_best_move_with_history(mock_engine):
    """Test getting best move with move history."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_engine.stdout.responses.extend([
            b"info depth 10 seldepth 15 multipv 1 score cp -52 nodes 25 nps 25000 tbhits 0 time 1 pv e7e5\n",
            b"bestmove e7e5 ponder g1f3\n"
        ])
        engine = StockfishEngine()
        move_history = ["e2e4"]
        best_move = engine.get_best_move(
            "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            move_history
        )
        assert best_move == "e7e5"
        # Verify the position command includes move history
        expected_pos_cmd = (
            b"position fen rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1 "
            b"moves e2e4\n"
        )
        assert any(cmd == expected_pos_cmd for cmd in mock_engine.stdin.commands)


def test_get_best_move_engine_error(mock_engine):
    """Test error handling when engine fails to respond properly."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path:
        mock_get_path.return_value = Path("/mock/stockfish")
        # Initialize with UCI responses
        mock_engine.stdout.responses = [
            b"Stockfish 17.1\n",
            b"uciok\n",
            b"readyok\n",
            # Then simulate engine responding with info but no bestmove
            b"info depth 10 seldepth 15 multipv 1 score cp 38 nodes 20 nps 20000 tbhits 0 time 1 pv e2e4\n",
            b"info depth 15 seldepth 20 multipv 1 score cp 45 nodes 50 nps 25000 tbhits 0 time 2 pv e2e4\n",
            b"info depth 20 seldepth 25 multipv 1 score cp 52 nodes 100 nps 30000 tbhits 0 time 3 pv e2e4\n",
        ]
        engine = StockfishEngine()
        with pytest.raises(StockfishError) as exc_info:
            engine.get_best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert "Error getting best move: No best move found in engine response" in str(exc_info.value)


def test_stop_engine(mock_engine):
    """Test engine shutdown."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path:
        mock_get_path.return_value = Path("/mock/stockfish")
        engine = StockfishEngine()
        engine.stop()
        assert engine.process is None


@pytest.mark.integration
def test_initialize_engine_with_real_binary():
    """Test initializing the engine with the actual Stockfish binary."""
    try:
        engine = StockfishEngine()
        assert engine.process is not None
        assert engine.process.poll() is None  # Process should be running
    except StockfishError as e:
        pytest.skip(f"Stockfish binary not available: {e}")
    finally:
        if 'engine' in locals():
            engine.stop()


@pytest.mark.integration
def test_get_best_move_with_real_engine():
    """Test getting a move from the real Stockfish engine."""
    try:
        engine = StockfishEngine()
        # Test with a simple starting position
        best_move = engine.get_best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert isinstance(best_move, str)
        assert len(best_move) == 4  # UCI moves are 4 characters long
    except StockfishError as e:
        pytest.skip(f"Stockfish binary not available: {e}")
    finally:
        if 'engine' in locals():
            engine.stop()


@pytest.mark.integration
def test_get_engine_path_error():
    """Test that _get_engine_path raises appropriate error when binary is missing."""
    with patch('platform.system', return_value='unsupported'), \
         patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EngineBinaryError, match="Unsupported platform: unsupported"):
            _get_engine_path()


class TestEnginePath:
    """Tests for engine path resolution."""

    def test_engine_path_env_valid(self, tmp_path):
        """Test that ENGINE_PATH is used when set and valid."""
        mock_binary = tmp_path / "stockfish"
        mock_binary.touch()
        mock_binary.chmod(0o755)  # Make executable
        
        with patch.dict(os.environ, {"ENGINE_PATH": str(mock_binary)}):
            path = _get_engine_path()
            assert path == mock_binary

    def test_engine_path_env_invalid(self, tmp_path):
        """Test that invalid ENGINE_PATH raises error."""
        invalid_path = tmp_path / "nonexistent"
        with patch.dict(os.environ, {"ENGINE_PATH": str(invalid_path)}):
            with pytest.raises(EngineBinaryError, match="ENGINE_PATH is set but points to invalid binary"):
                _get_engine_path()

    def test_engine_path_env_not_executable(self, tmp_path):
        """Test that non-executable ENGINE_PATH raises error."""
        mock_binary = tmp_path / "stockfish"
        mock_binary.touch()
        mock_binary.chmod(0o644)  # Not executable
        
        with patch.dict(os.environ, {"ENGINE_PATH": str(mock_binary)}):
            with pytest.raises(EngineBinaryError, match="ENGINE_PATH is set but points to invalid binary"):
                _get_engine_path()

    def test_fallback_path_with_engine_os(self, tmp_path):
        """Test fallback path construction with ENGINE_OS set."""
        mock_binary = tmp_path / "stockfish"
        mock_binary.touch()
        mock_binary.chmod(0o755)

        with patch.dict(os.environ, {"ENGINE_OS": "linux"}), \
             patch('pathlib.Path.resolve', return_value=mock_binary), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('os.access', return_value=True):
            path = _get_engine_path()
            assert path == mock_binary

    def test_fallback_path_os_detection(self, tmp_path):
        """Test OS detection when ENGINE_OS is not set."""
        mock_binary = tmp_path / "stockfish"
        mock_binary.touch()
        mock_binary.chmod(0o755)

        with patch.dict(os.environ, {}, clear=True), \
             patch('pathlib.Path.resolve', return_value=mock_binary), \
             patch('pathlib.Path.is_file', return_value=True), \
             patch('os.access', return_value=True), \
             patch('platform.system', return_value='Darwin'):
            path = _get_engine_path()
            assert path == mock_binary

    def test_fallback_path_missing_binary(self):
        """Test error when binary is missing from fallback path."""
        with patch.dict(os.environ, {"ENGINE_OS": "linux"}), \
             patch('pathlib.Path.is_file', return_value=False):
            with pytest.raises(EngineBinaryError, match="Stockfish binary not found at fallback path"):
                _get_engine_path()

    def test_unsupported_platform(self):
        """Test error on unsupported platform."""
        with patch('platform.system', return_value='unsupported'), \
             patch.dict(os.environ, {}, clear=True):
            with pytest.raises(EngineBinaryError, match="Unsupported platform: unsupported"):
                _get_engine_path()

def test_engine_error_handling():
    """Test error handling when the engine fails."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path, \
         patch('subprocess.Popen') as mock_popen, \
         patch('select.select') as mock_select:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_popen.side_effect = Exception("Mock error")
        mock_select.return_value = ([], [], [])
        
        with pytest.raises(StockfishError, match="Failed to initialize engine: Mock error"):
            engine = StockfishEngine()

def test_engine_initialization():
    """Test that the engine can be initialized."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path, \
         patch('subprocess.Popen') as mock_popen:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_process = MockProcess([
            b"Stockfish 17.1\n",
            b"uciok\n",
            b"readyok\n"
        ])
        mock_popen.return_value = mock_process
        
        engine = StockfishEngine()
        assert engine.process is not None
        assert mock_popen.call_count == 1
        assert mock_popen.call_args[0][0] == ["/mock/stockfish"]

def test_engine_get_best_move():
    """Test getting the best move from the engine."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path, \
         patch('subprocess.Popen') as mock_popen, \
         patch('select.select') as mock_select:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_process = mock_popen.return_value
        mock_process.poll.return_value = None
        mock_process.stdout = MockPipe([
            b"Stockfish 17.1\n",
            b"uciok\n",
            b"readyok\n",
            b"info depth 1 seldepth 1 multipv 1 score cp 38 nodes 20 nps 20000 tbhits 0 time 1 pv e2e4\n",
            b"bestmove e2e4 ponder e7e6\n"
        ])
        mock_stdout = mock_process.stdout
        mock_select.return_value = ([mock_stdout], [], [])
        
        engine = StockfishEngine()
        best_move = engine.get_best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert best_move == "e2e4"
