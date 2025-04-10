"""Models for the chess engine."""

from typing import Optional

from pydantic import BaseModel


class PositionRequest(BaseModel):
    """Request model for position-based operations."""

    position: str
    move_history: Optional[list[str]] = None


class GameStatusResponse(BaseModel):
    """Response model for game status."""

    status: str  # "CHECKMATE", "DRAW", "IN_PROGRESS"
    winner: Optional[str] = None  # "WHITE", "BLACK", or None
    draw_reason: Optional[str] = (
        None  # "STALEMATE", "INSUFFICIENT_MATERIAL", etc.
    )


class BestMoveResponse(BaseModel):
    """Response model for best move."""

    best_move_uci: str
    evaluation: Optional[float] = None
    depth: Optional[int] = None
