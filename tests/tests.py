"""Test suite for the chess engine service."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from dylangames_mcp_chess_engine.engine_wrapper import StockfishEngine, StockfishError


def test_engine_initialization():
    """Test that the engine can be initialized."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path, \
         patch('subprocess.Popen') as mock_popen, \
         patch('select.select') as mock_select:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_process = mock_popen.return_value
        mock_process.poll.return_value = None
        mock_process.stdout.fileno.return_value = 1
        mock_process.stdout.readline.side_effect = [
            b"Stockfish 17.1\n",
            b"uciok\n",
            b"readyok\n"
        ]
        mock_select.return_value = ([mock_process.stdout], [], [])

        engine = StockfishEngine()
        assert isinstance(engine, StockfishEngine)


def test_engine_get_best_move():
    """Test getting the best move from the engine."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path, \
         patch('subprocess.Popen') as mock_popen, \
         patch('select.select') as mock_select:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_process = mock_popen.return_value
        mock_process.poll.return_value = None
        mock_process.stdout.fileno.return_value = 1
        mock_process.stdout.readline.side_effect = [
            b"Stockfish 17.1\n",
            b"uciok\n",
            b"readyok\n",
            b"info depth 1 seldepth 1 multipv 1 score cp 38 nodes 20 nps 20000 tbhits 0 time 1 pv e2e4\n",
            b"bestmove e2e4 ponder e7e6\n"
        ]
        mock_select.return_value = ([mock_process.stdout], [], [])

        engine = StockfishEngine()
        best_move = engine.get_best_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert best_move == "e2e4"


def test_engine_error_handling():
    """Test that the engine handles errors correctly."""
    with patch('dylangames_mcp_chess_engine.engine_wrapper._get_engine_path') as mock_get_path, \
         patch('subprocess.Popen') as mock_popen:
        mock_get_path.return_value = Path("/mock/stockfish")
        mock_popen.side_effect = Exception("Mock error")
        
        with pytest.raises(StockfishError, match='Failed to initialize engine: Mock error'):
            engine = StockfishEngine()
