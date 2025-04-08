"""Provide FastMCP server for the Chess Engine module."""

import logging
import sys
import argparse
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, AsyncIterator  # Added AsyncIterator

# Removed FastAPI import, kept HTTPException for tool error handling
from fastapi import HTTPException  # Keep for now, see tool error handling
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from .engine_wrapper import (
    EngineBinaryError,
    StockfishError,
    _get_engine_path,
    get_best_move,
    initialize_engine,
    stop_engine,
)


# setup_environment function remains the same
def setup_environment():
    """Set up and validate the environment."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent.absolute()

    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create handlers
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.INFO)

    main_file_handler = RotatingFileHandler(
        logs_dir / "chess_engine.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    main_file_handler.setLevel(logging.INFO)

    error_file_handler = RotatingFileHandler(
        logs_dir / "chess_engine.error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_file_handler.setLevel(logging.ERROR)

    # Set formatter for all handlers
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    main_file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Clear existing handlers if necessary (e.g., if run multiple times)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(main_file_handler)
    root_logger.addHandler(error_file_handler)

    logger = logging.getLogger("chess_engine")

    # Log environment information
    # (Removed env_info logging for brevity, can be added back if needed)
    # logger.info("Environment Information:", extra={"env_info": env_info})

    # Verify pyproject.toml exists
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        logger.error(f"pyproject.toml not found at {pyproject_path}")
        raise RuntimeError(f"pyproject.toml not found at {pyproject_path}")

    # Verify engine path using the new logic
    try:
        engine_path = _get_engine_path()
        logger.info(f"Engine path resolved: {engine_path}")
    except EngineBinaryError as e:
        logger.error(f"Engine binary error: {e}")
        # Let initialization handle the error if path is bad

    return logger


# Initialize logging and environment
logger = setup_environment()


# Pydantic models remain the same
class ChessMoveRequest(BaseModel):
    """Request model for chess move generation."""

    fen: str
    move_history: List[str] = []


class ChessMoveResponse(BaseModel):
    """Response model for chess move generation."""

    best_move_uci: str


# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(
    server: FastMCP,
) -> AsyncIterator[None]:  # Type hint uses FastMCP
    """Manage the lifespan of the MCP application."""
    # This will be used by FastMCP's own run method
    try:
        logger.info("Starting chess engine server (via MCP lifespan)...")
        initialize_engine()
        logger.info("Engine initialized successfully (via MCP lifespan)")
        yield  # MCP server runs here
    finally:
        logger.info("Stopping engine (via MCP lifespan)...")
        stop_engine()
        logger.info("Engine stopped (via MCP lifespan).")


# --- Create FastMCP App with Lifespan ---
# Define the MCP application instance
mcp_app = FastMCP(
    "chess_engine", lifespan=lifespan, port=8001  # Configure port here
)


# --- Define MCP Tool ---
# Decorator now uses the 'mcp_app' variable
@mcp_app.tool()
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
        best_move = get_best_move(request.fen, request.move_history)
        logger.info(f"Best move found: {best_move}")
        return ChessMoveResponse(best_move_uci=best_move)
    except StockfishError as e:
        logger.error(f"Engine error: {e}")
        # You might need to return an MCP error format instead of raising HTTPException
        # Check FastMCP docs for error handling in tools. For now, keep HTTPException.
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# --- Main execution block using mcp.run() ---
if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Chess Engine MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",
        help="Transport mode for the MCP server (default: sse)",
    )
    args = parser.parse_args()

    # Start the server with the specified transport
    if args.transport == "stdio":
        logger.info("Starting MCP server in stdio mode...")
        mcp_app.run(transport="stdio")
    else:
        logger.info("Starting MCP server in SSE mode on 127.0.0.1:8001...")
        mcp_app.run(transport="sse")
