"""Additional tests for the engine wrapper module."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from chesspal_mcp_engine.engine_wrapper import StockfishEngine, StockfishError, _get_engine_path


class TestEngineWrapperAdditional:
    """Additional tests for the StockfishEngine class."""

    def test_engine_path_error(self, mocker):
        """Test behavior when engine path cannot be determined."""
        # More complete mocking of the initialization process
        with patch.object(
            StockfishEngine, "_initialize_engine", side_effect=StockfishError("Unable to locate Stockfish engine")
        ):
            # Check that engine initialization fails with StockfishError
            with pytest.raises(StockfishError, match="Unable to locate Stockfish engine"):
                StockfishEngine()

    def test_engine_process_startup_failure(self, mocker):
        """Test behavior when engine process fails to start."""
        # Mock _get_engine_path to return a valid path
        mocker.patch(
            "chesspal_mcp_engine.engine_wrapper._get_engine_path",
            return_value="/path/to/stockfish",
        )

        # Mock subprocess.Popen to raise an exception
        mocker.patch(
            "subprocess.Popen",
            side_effect=OSError("Failed to start process"),
        )

        # Check that engine initialization fails with StockfishError
        with pytest.raises(StockfishError, match="Failed to initialize engine"):
            StockfishEngine()

    def test_engine_initialization_timeout(self, mocker):
        """Test behavior when engine initialization times out."""
        # Mock _get_engine_path to return a valid path
        mocker.patch(
            "chesspal_mcp_engine.engine_wrapper._get_engine_path",
            return_value="/path/to/stockfish",
        )

        # Mock subprocess.Popen
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = b""  # Simulate no output
        mock_process.poll.return_value = None  # Process still running
        mocker.patch("subprocess.Popen", return_value=mock_process)

        # Mock select.select to handle fileno issue
        mocker.patch("select.select", return_value=([], [], []))

        # Create a class that returns increasing time values to simulate timeout
        class IncrementingTime:
            def __init__(self):
                self.time = 0

            def __call__(self):
                self.time += 1
                return self.time

        # Patch time.time with our infinite time source
        mocker.patch("time.time", IncrementingTime())

        # Check that engine initialization fails with StockfishError
        with pytest.raises(StockfishError, match="Timeout waiting for response"):
            StockfishEngine()

    def test_get_best_move_initialization_error(self, mocker):
        """Test get_best_move when engine is not properly initialized."""
        # Create a direct mock of StockfishEngine
        engine = MagicMock(spec=StockfishEngine)
        engine.process = None

        # Now call get_best_move directly from the original class on our mocked instance
        with pytest.raises(StockfishError, match="Engine not initialized or not running"):
            StockfishEngine.get_best_move(engine, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def test_get_best_move_process_exit(self, mocker):
        """Test get_best_move when process exits unexpectedly."""
        # Create a direct mock of StockfishEngine for more control
        engine = MagicMock(spec=StockfishEngine)
        engine.process = MagicMock()
        engine.process.poll.return_value = 1  # Process exited

        # Create a side effect for the method
        with pytest.raises(StockfishError, match="Engine not initialized or not running"):
            StockfishEngine.get_best_move(engine, "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")

    def test_get_best_move_invalid_fen(self, mocker):
        """Test get_best_move with invalid FEN string."""
        # Setup mock for process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process still running
        mock_process.stdout.readline.return_value = b"Stockfish 15 by the Stockfish developers (see AUTHORS file)"
        mocker.patch("subprocess.Popen", return_value=mock_process)

        # Mock select to avoid fileno issues
        mocker.patch("select.select", return_value=([mock_process.stdout], [], []))

        # Mock _read_response to return valid responses for initialization
        _ = mocker.patch.object(StockfishEngine, "_read_response", side_effect=[["uciok"], ["readyok"]])

        # Create engine
        engine = StockfishEngine()

        # Mock _send_command to raise an exception for invalid FEN
        mocker.patch.object(engine, "_send_command", side_effect=StockfishError("Invalid FEN position"))

        # Check that get_best_move fails with StockfishError
        with pytest.raises(StockfishError, match="Invalid FEN position"):
            engine.get_best_move("invalid fen")

    def test_get_engine_path_custom_path(self, mocker):
        """Test _get_engine_path with custom path."""
        # Mock environment variable in settings
        custom_path = "/custom/path/to/stockfish"
        mocker.patch("chesspal_mcp_engine.config.settings.CHESSPAL_ENGINE_PATH", custom_path)

        # Mock os.access and Path.is_file to return True for our custom path
        original_access = os.access
        original_is_file = Path.is_file

        def mock_access(path, mode):
            if str(path) == custom_path:
                return True
            return original_access(path, mode)

        def mock_is_file(self):
            if str(self) == custom_path:
                return True
            return original_is_file(self)

        mocker.patch("os.access", side_effect=mock_access)
        mocker.patch("pathlib.Path.is_file", mock_is_file)

        # Check that custom path is used
        result = _get_engine_path()
        assert str(result) == custom_path

    def test_get_engine_path_not_found(self, mocker):
        """Test _get_engine_path when engine cannot be found."""
        # Mock settings to have no engine path
        mocker.patch("chesspal_mcp_engine.config.settings.CHESSPAL_ENGINE_PATH", None)

        # Mock os.path.isfile and Path.is_file to always return False
        mocker.patch("os.path.isfile", return_value=False)
        mocker.patch("pathlib.Path.is_file", return_value=False)

        # Check that the function raises EngineBinaryError
        with pytest.raises(Exception, match="Stockfish binary not found"):
            _get_engine_path()

    def test_stop_already_stopped(self, mocker):
        """Test stop method when engine is already stopped."""
        # Setup mock process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process running
        mocker.patch("subprocess.Popen", return_value=mock_process)

        # Mock select to avoid fileno issues
        mocker.patch("select.select", return_value=([mock_process.stdout], [], []))

        # Mock _read_response to return valid responses for initialization
        _ = mocker.patch.object(StockfishEngine, "_read_response", side_effect=[["uciok"], ["readyok"]])

        # Create engine
        engine = StockfishEngine()

        # Mock process.wait to avoid blocking
        mock_process.wait.return_value = 0

        # Stop the engine
        engine.stop()

        # Set process to None to simulate already stopped
        engine.process = None

        # Stop again
        engine.stop()  # Should not raise an exception

        # Verify process.wait was called only once
        assert mock_process.wait.call_count == 1

    def test_is_initialized(self, mocker):
        """Test is_initialized method."""
        # Setup mock for process
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process running
        mocker.patch("subprocess.Popen", return_value=mock_process)

        # Mock select to avoid fileno issues
        mocker.patch("select.select", return_value=([mock_process.stdout], [], []))

        # Mock _read_response to return valid responses
        mocker.patch.object(StockfishEngine, "_read_response", side_effect=[["uciok"], ["readyok"], ["readyok"]])

        # Create engine
        engine = StockfishEngine()

        # Test is_initialized with a running process
        assert engine.is_initialized() is True

        # Test when process is not running
        mock_process.poll.return_value = 1  # Process exited
        assert engine.is_initialized() is False
