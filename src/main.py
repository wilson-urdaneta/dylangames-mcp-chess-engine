"""
FastMCP server for the Chess Engine module.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List
from logging.handlers import RotatingFileHandler
from pydantic import BaseModel
from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP

from src.engine_wrapper import initialize_engine, get_best_move, stop_engine, StockfishError

def setup_environment():
    """Setup and validate the environment."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.absolute()

    # Create logs directory if it doesn't exist
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Create handlers
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.INFO)

    main_file_handler = RotatingFileHandler(
        logs_dir / 'chess_engine.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    main_file_handler.setLevel(logging.INFO)

    error_file_handler = RotatingFileHandler(
        logs_dir / 'chess_engine.error.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)

    # Set formatter for all handlers
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    main_file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            stream_handler,
            main_file_handler,
            error_file_handler
        ]
    )
    logger = logging.getLogger('chess_engine')

    # Log environment information
    env_info = {
        "project_root": str(project_root),
        "current_working_directory": os.getcwd(),
        "python_path": os.environ.get('PYTHONPATH', 'Not set'),
        "poetry_env": os.environ.get('POETRY_ACTIVE', 'Not in Poetry env'),
        "python_version": sys.version,
        "log_directory": str(logs_dir)
    }

    logger.info("Environment Information:", extra={"env_info": env_info})

    # Verify pyproject.toml exists
    pyproject_path = project_root / 'pyproject.toml'
    if not pyproject_path.exists():
        logger.error(f"pyproject.toml not found at {pyproject_path}")
        raise RuntimeError(f"pyproject.toml not found at {pyproject_path}")

    # Verify Stockfish path
    stockfish_path = os.environ.get('STOCKFISH_PATH')
    if not stockfish_path:
        logger.warning("STOCKFISH_PATH not set")
    else:
        logger.info(f"STOCKFISH_PATH: {stockfish_path}")
        if not os.path.isfile(stockfish_path):
            logger.error(f"Stockfish binary not found at {stockfish_path}")

    return logger

# Initialize logging and environment
logger = setup_environment()

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

def main():
    """Main entry point for the chess engine server."""
    try:
        # Initialize engine at startup
        logger.info("Starting chess engine server...")
        initialize_engine()
        logger.info("Engine initialized successfully")

        # Keep the server running
        logger.info("Starting MCP server with stdio transport...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Stopping engine...")
        stop_engine()

if __name__ == "__main__":
    main()