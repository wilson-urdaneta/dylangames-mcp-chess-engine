"""Tests for model classes."""

import pytest
from pydantic import ValidationError

from chesspal_mcp_engine.models import BestMoveResponse, GameStatusResponse, PositionRequest


class TestPositionRequest:
    """Tests for the PositionRequest model."""

    def test_valid_position_request(self):
        """Test creating a valid position request."""
        # Test with minimum required fields
        request = PositionRequest(position="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        assert request.position == "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert request.move_history is None

        # Test with all fields
        request = PositionRequest(
            position="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
            move_history=["e2e4"],
        )
        assert request.position == "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        assert request.move_history == ["e2e4"]

    def test_missing_position(self):
        """Test that position is required."""
        with pytest.raises(ValidationError):
            PositionRequest(position=None)  # type: ignore


class TestGameStatusResponse:
    """Tests for the GameStatusResponse model."""

    def test_valid_game_status_response(self):
        """Test creating valid game status responses."""
        # Test in-progress game
        response = GameStatusResponse(status="IN_PROGRESS")
        assert response.status == "IN_PROGRESS"
        assert response.winner is None
        assert response.draw_reason is None

        # Test checkmate
        response = GameStatusResponse(status="CHECKMATE", winner="WHITE")
        assert response.status == "CHECKMATE"
        assert response.winner == "WHITE"
        assert response.draw_reason is None

        # Test draw
        response = GameStatusResponse(status="DRAW", draw_reason="STALEMATE")
        assert response.status == "DRAW"
        assert response.winner is None
        assert response.draw_reason == "STALEMATE"

    def test_missing_status(self):
        """Test that status is required."""
        with pytest.raises(ValidationError):
            GameStatusResponse(status=None)  # type: ignore


class TestBestMoveResponse:
    """Tests for the BestMoveResponse model."""

    def test_valid_best_move_response(self):
        """Test creating valid best move responses."""
        # Test with minimum required fields
        response = BestMoveResponse(best_move_uci="e2e4")
        assert response.best_move_uci == "e2e4"
        assert response.evaluation is None
        assert response.depth is None

        # Test with all fields
        response = BestMoveResponse(best_move_uci="e2e4", evaluation=0.5, depth=20)
        assert response.best_move_uci == "e2e4"
        assert response.evaluation == 0.5
        assert response.depth == 20

    def test_missing_best_move(self):
        """Test that best_move_uci is required."""
        with pytest.raises(ValidationError):
            BestMoveResponse(best_move_uci=None)  # type: ignore
