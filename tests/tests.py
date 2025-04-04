"""
Unit tests for the Chess Engine module.
"""

import os
import pytest
from src.engine_wrapper import initialize_engine, get_best_move, stop_engine, StockfishError

@pytest.fixture(scope="session", autouse=True)
def engine():
    """Fixture to initialize and cleanup the engine for tests."""
    try:
        # First ensure any existing engine is stopped
        try:
            stop_engine()
        except:
            pass

        # Initialize the engine with default path
        initialize_engine()

        # Run a simple test to ensure it's working
        test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        test_move = get_best_move(test_fen, [])
        if not test_move or not isinstance(test_move, str) or len(test_move) < 4:
            raise StockfishError("Engine initialization test failed")

        yield
    finally:
        try:
            stop_engine()
        except:
            pass

@pytest.fixture(autouse=True)
def ensure_engine_running():
    """Fixture to ensure engine is running before each test."""
    global _engine_process, _initialized
    from src.engine_wrapper import _engine_process, _initialized

    if not _initialized or not _engine_process or _engine_process.poll() is not None:
        initialize_engine()

def test_initialize_engine():
    """Test that engine initialization works."""
    # The fixture ensures this is called, so if we get here, it passed
    pass

def test_get_best_move_basic():
    """Test getting a move from the starting position."""
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    move_history = []
    best_move = get_best_move(fen, move_history)
    assert isinstance(best_move, str)
    assert len(best_move) >= 4 and len(best_move) <= 5
    assert best_move.isalnum()  # Should only contain letters and numbers

def test_get_best_move_invalid_fen():
    """Test that invalid FEN raises an exception."""
    fen = "invalid fen"
    move_history = []
    with pytest.raises(StockfishError):
        get_best_move(fen, move_history)

def test_get_best_move_valid_position():
    """Test getting a move from a specific position."""
    fen = "r1bqkbnr/ppp2ppp/2n5/3pp3/3P4/2N5/PPP1PPPP/R1BQKBNR w KQkq - 0 5"
    move_history = ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"]
    best_move = get_best_move(fen, move_history)
    assert isinstance(best_move, str)
    assert len(best_move) >= 4 and len(best_move) <= 5
    assert best_move.isalnum()  # Should only contain letters and numbers

def test_get_best_move_with_history():
    """Test that move history is correctly handled."""
    fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    move_history = ["e2e4"]
    best_move = get_best_move(fen, move_history)
    assert isinstance(best_move, str)
    assert len(best_move) >= 4 and len(best_move) <= 5
    assert best_move.isalnum()  # Should only contain letters and numbers