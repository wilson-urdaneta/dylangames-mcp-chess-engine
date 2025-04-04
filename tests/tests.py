"""Test suite for the chess engine module."""

import pytest

from src.engine_wrapper import (
    StockfishError,
    get_best_move,
    initialize_engine,
    stop_engine,
)


@pytest.fixture(scope="session", autouse=True)
def ensure_engine_running():
    """Ensure the Stockfish engine is running for tests."""
    try:
        initialize_engine()
        yield
    except StockfishError as e:
        pytest.fail(f"Failed to initialize engine: {e}")
    finally:
        stop_engine()


def test_initialize_engine():
    """Test engine initialization."""
    try:
        initialize_engine()
        assert True  # If we get here, initialization succeeded
    except StockfishError as e:
        pytest.fail(f"Failed to initialize engine: {e}")


def test_get_best_move_basic():
    """Test getting best move from starting position."""
    try:
        move = get_best_move(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", []
        )
        assert move is not None and len(move) >= 4
    except StockfishError as e:
        pytest.fail(f"Failed to get best move: {e}")


def test_get_best_move_invalid_fen():
    """Test handling of invalid FEN string."""
    with pytest.raises(StockfishError):
        get_best_move("invalid fen", [])


def test_get_best_move_valid_position():
    """Test getting best move from a specific position."""
    fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
    try:
        move = get_best_move(fen, [])
        assert move is not None and len(move) >= 4
    except StockfishError as e:
        pytest.fail(f"Failed to get best move: {e}")


def test_get_best_move_with_history():
    """Test getting best move with move history."""
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    try:
        move = get_best_move(fen, ["e2e4", "e7e5"])
        assert move is not None and len(move) >= 4
    except StockfishError as e:
        pytest.fail(f"Failed to get best move: {e}")
