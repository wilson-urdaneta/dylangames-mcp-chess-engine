"""Test suite for main engine functionality."""

from unittest.mock import patch, MagicMock
import pytest
from dylangames_mcp_chess_engine.main import (
    validate_move_tool,
    get_legal_moves_tool,
    get_game_status_tool,
    ValidateMoveRequest,
    PositionRequest,
    get_best_move_tool,
    ChessMoveRequest,
    _engine,
)
from dylangames_mcp_chess_engine.engine_wrapper import StockfishEngine, StockfishError
from dylangames_mcp_chess_engine.models import GameStatusResponse

# Test positions
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CHECKMATE_FEN = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 1"  # Fool's mate position (Black has checkmated White)
STALEMATE_FEN = "k7/8/1Q6/8/8/8/8/K7 b - - 0 1"
INSUFFICIENT_MATERIAL_FEN = "8/8/8/8/8/8/8/k1K5 w - - 0 1"  # King vs King

class MockEngine:
    """Mock engine that returns a fixed string value."""
    def get_best_move(self, fen, move_history=None):
        return "e2e4"

@pytest.mark.asyncio
async def test_validate_move_tool_valid_move():
    request = ValidateMoveRequest(position=STARTING_FEN, move="e2e4")
    response = await validate_move_tool(request)
    assert response.result is True

@pytest.mark.asyncio
async def test_validate_move_tool_invalid_syntax():
    request = ValidateMoveRequest(position=STARTING_FEN, move="e2e9")
    response = await validate_move_tool(request)
    assert response.result is False

@pytest.mark.asyncio
async def test_validate_move_tool_illegal_move():
    request = ValidateMoveRequest(position=STARTING_FEN, move="e1e2")
    response = await validate_move_tool(request)
    assert response.result is False

@pytest.mark.asyncio
async def test_validate_move_tool_invalid_fen():
    request = ValidateMoveRequest(position="invalid fen", move="e2e4")
    response = await validate_move_tool(request)
    assert response.result is False

@pytest.mark.asyncio
async def test_get_legal_moves_tool_starting_position():
    request = PositionRequest(position=STARTING_FEN)
    response = await get_legal_moves_tool(request)
    # Starting position should have 20 legal moves
    assert len(response.result) == 20
    # Check for some common opening moves
    assert "e2e4" in response.result
    assert "d2d4" in response.result

@pytest.mark.asyncio
async def test_get_legal_moves_tool_checkmate():
    request = PositionRequest(position=CHECKMATE_FEN)
    response = await get_legal_moves_tool(request)
    # In checkmate position, there should be no legal moves
    assert len(response.result) == 0

@pytest.mark.asyncio
async def test_get_legal_moves_tool_invalid_fen():
    request = PositionRequest(position="invalid fen")
    with pytest.raises(Exception):  # Should raise an error for invalid FEN
        await get_legal_moves_tool(request)

@pytest.mark.asyncio
async def test_game_status_tool_in_progress():
    request = PositionRequest(position=STARTING_FEN)
    response = await get_game_status_tool(request)
    assert response.status == "IN_PROGRESS"
    assert response.winner is None

@pytest.mark.asyncio
async def test_game_status_tool_checkmate():
    request = PositionRequest(position=CHECKMATE_FEN)
    response = await get_game_status_tool(request)
    assert response.status == "CHECKMATE"
    assert response.winner == "BLACK"  # Black has checkmated White in Fool's mate

@pytest.mark.asyncio
async def test_game_status_tool_stalemate():
    request = PositionRequest(position=STALEMATE_FEN)
    response = await get_game_status_tool(request)
    assert response.status == "STALEMATE"

@pytest.mark.asyncio
async def test_game_status_tool_insufficient_material():
    request = PositionRequest(position=INSUFFICIENT_MATERIAL_FEN)
    response = await get_game_status_tool(request)
    assert response.status == "DRAW"

@pytest.mark.asyncio
async def test_game_status_tool_invalid_fen():
    request = PositionRequest(position="invalid fen")
    with pytest.raises(Exception):  # Should raise an error for invalid FEN
        await get_game_status_tool(request)

@pytest.mark.asyncio
async def test_get_best_move_tool():
    """Test the get_best_move_tool function."""
    # Create a mock engine instance
    mock_engine = MagicMock(spec=StockfishEngine)
    mock_engine.get_best_move.return_value = "e2e4"

    # Patch the global _engine variable with our mock
    with patch("dylangames_mcp_chess_engine.main._engine", mock_engine):
        # Prepare the request object
        request = ChessMoveRequest(
            fen=STARTING_FEN,
            move_history=[]
        )

        # Call the tool function
        response = await get_best_move_tool(request)

        # Assert the response matches expected format
        assert hasattr(response, "best_move_uci")
        assert response.best_move_uci == "e2e4"

        # Verify the mock was called correctly
        mock_engine.get_best_move.assert_called_once_with(STARTING_FEN, []) 