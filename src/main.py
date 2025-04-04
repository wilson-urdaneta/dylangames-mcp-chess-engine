"""
FastMCP server for the Chess Engine module.
"""

from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

from src.engine_wrapper import initialize_engine, get_best_move, stop_engine, StockfishError

try:
    # Initialize engine with default path (will try packaged binary first)
    initialize_engine()
except StockfishError as e:
    print(f"Error initializing Stockfish: {e}")
    raise  # Re-raise to prevent server from starting with uninitialized engine

# Create FastMCP instance
mcp = FastMCP("chess_engine")

class ChessMoveRequest(BaseModel):
    """Request model for chess move generation."""
    fen: str
    move_history: List[str]

class ChessMoveResponse(BaseModel):
    """Response model for chess move generation."""
    best_move_uci: str

@mcp.tool()
async def get_best_move_tool(request: ChessMoveRequest) -> ChessMoveResponse:
    """
    Get the best chess move for a given position.

    Args:
        request: ChessMoveRequest containing FEN and move history.

    Returns:
        ChessMoveResponse containing the best move in UCI format.

    Raises:
        HTTPException: If there's an error getting the best move.
    """
    try:
        best_move = get_best_move(request.fen, request.move_history)
        return ChessMoveResponse(best_move_uci=best_move)
    except StockfishError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    try:
        mcp.run(transport="stdio")
    finally:
        stop_engine()