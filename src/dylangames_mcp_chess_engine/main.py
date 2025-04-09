"""Provide FastMCP server for the Chess Engine module."""

import argparse
import logging
import os
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import AsyncIterator, List

from fastapi import (  # Keep for now while determining error handling
    HTTPException,
)
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from dylangames_mcp_chess_engine.engine_wrapper import (
    EngineBinaryError,
    StockfishError,
    _get_engine_path,
    get_best_move,
    initialize_engine,
    stop_engine,
)


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
    stream_handler.setLevel(logging.WARNING)

    main_file_handler = RotatingFileHandler(
        logs_dir / "chess_engine.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
        mode="w",  # Overwrite logs on each start
    )
    main_file_handler.setLevel(logging.DEBUG)

    error_file_handler = RotatingFileHandler(
        logs_dir / "chess_engine.error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
        mode="w",  # Overwrite logs on each start
    )
    error_file_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    main_file_handler.setFormatter(formatter)
    error_file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(main_file_handler)
    root_logger.addHandler(error_file_handler)

    logger = logging.getLogger("chess_engine")

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


logger = setup_environment()

# Configure MCP server settings from environment variables
bind_host = os.environ.get("MCP_HOST", "127.0.0.1")
bind_port = int(os.environ.get("MCP_PORT", "8001"))
logger.info(f"Configuring FastMCP to use host='{bind_host}' port={bind_port}")


class ChessMoveRequest(BaseModel):
    """Request model for chess move generation."""

    fen: str
    move_history: List[str] = []


class ChessMoveResponse(BaseModel):
    """Response model for chess move generation."""

    best_move_uci: str


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage the lifespan of the MCP application."""
    try:
        logger.info("Starting chess engine server (via MCP lifespan)...")
        initialize_engine()
        logger.info("Engine initialized successfully (via MCP lifespan)")
        yield
    finally:
        logger.info("Stopping engine (via MCP lifespan)...")
        stop_engine()
        logger.info("Engine stopped (via MCP lifespan).")


app = FastMCP(
    "chess_engine",
    lifespan=lifespan,
    host=bind_host,
    port=bind_port,
)


@app.tool()
async def get_best_move_tool(request: ChessMoveRequest) -> ChessMoveResponse:
    """Get the best chess move for a given position."""
    try:
        logger.info(f"Received request for position: {request.fen}")
        logger.debug(f"Move history: {request.move_history}")
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
    """Parse arguments and runs the MCP server."""
    parser = argparse.ArgumentParser(description="Chess Engine MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",  # Default to SSE if flag is omitted
        help="Transport mode for the MCP server (default: sse)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        logger.info("Starting MCP server in stdio mode...")
        app.run(transport="stdio")
    else:
        # SSE Mode (Default)
        # Host/Port are already configured in the app instance via constructor
        logger.info(
            f"Starting MCP server in SSE mode "
            f"(binding to {bind_host}:{bind_port})..."
        )
        app.run(transport="sse")


if __name__ == "__main__":
    main()
