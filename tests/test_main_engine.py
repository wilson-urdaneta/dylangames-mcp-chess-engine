"""Test suite for main engine functionality."""

from unittest.mock import MagicMock, patch

import pytest

from dylangames_mcp_chess_engine.engine_wrapper import StockfishEngine, StockfishError
from dylangames_mcp_chess_engine.main import (
    ChessMoveRequest,
    PositionRequest,
    ValidateMoveRequest,
    get_best_move_tool,
    get_game_status_tool,
    get_legal_moves_tool,
    validate_move_tool,
)


class MockEngine:
    """Mock engine that returns a fixed string value."""

    def get_best_move(self, fen, move_history=None):
        """Return a fixed move for testing."""
        return "e2e4"


@pytest.mark.asyncio
async def test_validate_move_tool_valid_move(test_positions):
    """Test validation of a valid chess move."""
    request = ValidateMoveRequest(
        position=test_positions["STARTING_FEN"], move="e2e4"
    )
    response = await validate_move_tool(request)
    assert response == {"result": True}


@pytest.mark.asyncio
async def test_validate_move_tool_invalid_syntax(test_positions):
    """Test validation of a move with invalid syntax."""
    request = ValidateMoveRequest(
        position=test_positions["STARTING_FEN"], move="e2e9"
    )
    response = await validate_move_tool(request)
    assert response == {"result": False}


@pytest.mark.asyncio
async def test_validate_move_tool_illegal_move(test_positions):
    """Test validation of an illegal chess move."""
    request = ValidateMoveRequest(
        position=test_positions["STARTING_FEN"], move="e1e2"
    )
    response = await validate_move_tool(request)
    assert response == {"result": False}


@pytest.mark.asyncio
async def test_validate_move_tool_invalid_fen():
    """Test validation with an invalid FEN string."""
    request = ValidateMoveRequest(position="invalid fen", move="e2e4")
    response = await validate_move_tool(request)
    assert response == {"result": False}


@pytest.mark.asyncio
async def test_get_legal_moves_tool_starting_position(test_positions):
    """Test getting legal moves from the starting position."""
    request = PositionRequest(position=test_positions["STARTING_FEN"])
    response = await get_legal_moves_tool(request)
    assert "result" in response
    assert len(response["result"]) == 20
    assert "e2e4" in response["result"]
    assert "d2d4" in response["result"]


@pytest.mark.asyncio
async def test_get_legal_moves_tool_checkmate(test_positions):
    """Test getting legal moves in a checkmate position."""
    request = PositionRequest(position=test_positions["CHECKMATE_FEN"])
    response = await get_legal_moves_tool(request)
    assert response == {"result": []}


@pytest.mark.asyncio
async def test_get_legal_moves_tool_invalid_fen():
    """Test getting legal moves with an invalid FEN string."""
    request = PositionRequest(position="invalid fen")
    response = await get_legal_moves_tool(request)
    assert "error" in response
    assert "Invalid FEN format" in response["error"]


@pytest.mark.asyncio
async def test_game_status_tool_in_progress(test_positions):
    """Test game status detection for an ongoing game."""
    request = PositionRequest(position=test_positions["STARTING_FEN"])
    response = await get_game_status_tool(request)
    assert response == {
        "result": {
            "status": "IN_PROGRESS",
            "winner": None
        }
    }


@pytest.mark.asyncio
async def test_game_status_tool_checkmate(test_positions):
    """Test game status detection for a checkmate position."""
    request = PositionRequest(position=test_positions["CHECKMATE_FEN"])
    response = await get_game_status_tool(request)
    assert response == {
        "result": {
            "status": "CHECKMATE",
            "winner": "BLACK"
        }
    }


@pytest.mark.asyncio
async def test_game_status_tool_stalemate(test_positions):
    """Test game status detection for a stalemate position."""
    request = PositionRequest(position=test_positions["STALEMATE_FEN"])
    response = await get_game_status_tool(request)
    assert response == {
        "result": {
            "status": "STALEMATE",
            "winner": None
        }
    }


@pytest.mark.asyncio
async def test_game_status_tool_insufficient_material(test_positions):
    """Test game status detection for insufficient material."""
    request = PositionRequest(
        position=test_positions["INSUFFICIENT_MATERIAL_FEN"]
    )
    response = await get_game_status_tool(request)
    assert response == {
        "result": {
            "status": "DRAW",
            "winner": None
        }
    }


@pytest.mark.asyncio
async def test_game_status_tool_invalid_fen():
    """Test game status detection with an invalid FEN string."""
    request = PositionRequest(position="invalid fen")
    response = await get_game_status_tool(request)
    assert "error" in response
    assert "Invalid FEN format" in response["error"]


@pytest.mark.asyncio
async def test_get_best_move_tool_success(test_positions):
    """Test the get_best_move_tool function success case."""
    mock_engine = MagicMock(spec=StockfishEngine)
    mock_engine.get_best_move.return_value = "e2e4"

    with patch("dylangames_mcp_chess_engine.main._engine", mock_engine):
        request = ChessMoveRequest(
            fen=test_positions["STARTING_FEN"],
            move_history=[]
        )
        response = await get_best_move_tool(request)
        assert response == {"result": {"best_move_uci": "e2e4"}}
        mock_engine.get_best_move.assert_called_once_with(
            test_positions["STARTING_FEN"], []
        )


@pytest.mark.asyncio
async def test_get_best_move_tool_engine_error(test_positions):
    """Test the get_best_move_tool function when engine fails."""
    mock_engine = MagicMock(spec=StockfishEngine)
    mock_engine.get_best_move.side_effect = StockfishError("Engine failed")

    with patch("dylangames_mcp_chess_engine.main._engine", mock_engine):
        request = ChessMoveRequest(
            fen=test_positions["STARTING_FEN"],
            move_history=[]
        )
        response = await get_best_move_tool(request)
        assert "error" in response
        assert "Engine failed" in response["error"]


@pytest.mark.asyncio
async def test_get_best_move_tool_not_initialized():
    """Test the get_best_move_tool function when engine is not initialized."""
    with patch("dylangames_mcp_chess_engine.main._engine", None):
        request = ChessMoveRequest(
            fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            move_history=[]
        )
        response = await get_best_move_tool(request)
        assert "error" in response
        assert "Engine not initialized" in response["error"]
