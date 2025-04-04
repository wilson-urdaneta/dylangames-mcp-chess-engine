"""
FastMCP server for the Chess Engine module.
"""

import os
import sys
import logging
from typing import List
from pydantic import BaseModel
from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP

from src.engine_wrapper import initialize_engine, get_best_move, stop_engine, StockfishError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),  # Log to stderr for Claude Desktop
        logging.FileHandler('chess_engine.log')  # Also log to file
    ]
)
logger = logging.getLogger('chess_engine')

# Initialize FastMCP
mcp = FastMCP("chess_engine")

class ChessMoveRequest(BaseModel):
    """Request model for chess move generation."""
    fen: str
    move_history: List[str] = []

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
        logger.info(f"Received request for position: {request.fen}")
        logger.debug(f"Move history: {request.move_history}")

        # Initialize engine if not already initialized
        if not hasattr(get_best_move_tool, 'engine_initialized'):
            logger.info("Initializing Stockfish engine...")
            try:
                initialize_engine()
                get_best_move_tool.engine_initialized = True
                logger.info("Engine initialized successfully")
            except StockfishError as e:
                logger.error(f"Failed to initialize engine: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        # Get best move
        best_move = get_best_move(request.fen, request.move_history)
        logger.info(f"Best move found: {best_move}")
        return ChessMoveResponse(best_move_uci=best_move)

    except StockfishError as e:
        logger.error(f"Engine error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    try:
        # Log the current working directory and PYTHONPATH
        logger.info(f"Current working directory: {os.getcwd()}")
        logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
        logger.info(f"Poetry environment: {os.environ.get('POETRY_ACTIVE', 'Not in Poetry env')}")

        # Initialize engine at startup
        logger.info("Starting chess engine server...")
        initialize_engine()
        logger.info("Engine initialized successfully")

        # Keep the server running
        mcp.run(transport="stdio")  # Explicitly set transport for Claude Desktop
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Stopping engine...")
        stop_engine()