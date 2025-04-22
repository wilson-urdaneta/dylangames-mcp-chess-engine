"""Additional tests for main engine functionality."""

import pytest
from pytest_mock import MockerFixture

import chesspal_mcp_engine.main as main_module
from chesspal_mcp_engine.main import (
    ChessMoveRequest,
    PositionRequest,
    ValidateMoveRequest,
    get_best_move_tool,
    get_game_status_tool,
    get_legal_moves_tool,
    validate_move_tool,
)


@pytest.fixture
def mock_engine(mocker: MockerFixture):
    """Fixture for mocking StockfishEngine."""
    mock_engine = mocker.MagicMock()
    mock_engine.get_best_move.return_value = "e2e4"
    mocker.patch.object(main_module, "_engine", mock_engine)
    return mock_engine


class TestMainEngineAdditional:
    """Additional tests for main engine functionality."""

    @pytest.mark.asyncio
    async def test_get_best_move_tool_engine_not_initialized(self, mocker: MockerFixture):
        """Test get_best_move_tool when engine is not initialized."""
        # Ensure _engine is None
        mocker.patch.object(main_module, "_engine", None)

        # Call the function
        request = ChessMoveRequest(fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", move_history=[])
        result = await get_best_move_tool(request)

        # Check result contains error
        assert "error" in result
        assert "Engine not initialized" in result["error"]

    @pytest.mark.asyncio
    async def test_validate_move_tool_invalid_fen(self, mocker: MockerFixture):
        """Test validate_move_tool with invalid FEN."""
        # Call with invalid FEN
        request = ValidateMoveRequest(fen="invalid fen", move="e2e4")
        result = await validate_move_tool(request)

        # Check result contains error
        assert "error" in result
        assert "Invalid FEN format" in result["error"]

    @pytest.mark.asyncio
    async def test_get_legal_moves_tool_invalid_fen(self, mocker: MockerFixture):
        """Test get_legal_moves_tool with invalid FEN."""
        # Call with invalid FEN
        request = PositionRequest(fen="invalid fen")
        result = await get_legal_moves_tool(request)

        # Check result contains error
        assert "error" in result
        assert "Invalid FEN format" in result["error"]

    @pytest.mark.asyncio
    async def test_get_game_status_tool_invalid_fen(self, mocker: MockerFixture):
        """Test get_game_status_tool with invalid FEN."""
        # Call with invalid FEN
        request = PositionRequest(fen="invalid fen")
        result = await get_game_status_tool(request)

        # Check result contains error
        assert "error" in result
        assert "Invalid FEN format" in result["error"]

    @pytest.mark.asyncio
    async def test_get_best_move_tool_exception_handling(self, mock_engine, mocker: MockerFixture):
        """Test get_best_move_tool error handling."""
        # Configure mock engine to raise exceptions
        mock_engine.get_best_move.side_effect = Exception("Unexpected error")

        # Call the function
        request = ChessMoveRequest(fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", move_history=[])
        result = await get_best_move_tool(request)

        # Check result contains error
        assert "error" in result
        assert "Internal server error" in result["error"]
