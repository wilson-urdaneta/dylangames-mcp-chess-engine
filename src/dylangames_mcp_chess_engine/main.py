"""Main module for the MCP chess engine service."""

import argparse
import logging
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import AsyncIterator, List, Optional

import chess
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from dylangames_mcp_chess_engine.config import settings
from dylangames_mcp_chess_engine.engine_wrapper import (
    StockfishEngine,
    StockfishError,
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Set up and validate the environment."""
    global _engine

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
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(main_file_handler)
    root_logger.addHandler(error_file_handler)

    logger = logging.getLogger("chess_engine")

    # Verify pyproject.toml exists
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        logger.error("pyproject.toml not found at %s", pyproject_path)
        msg = f"pyproject.toml not found at {pyproject_path}"
        raise RuntimeError(msg)

    # Test engine initialization
    try:
        _engine = StockfishEngine()
        logger.info("Engine test initialization successful")
    except StockfishError as e:
        logger.error("Engine initialization error: %s", e)
        # Let initialization handle the error if path is bad

    return logger


logger = setup_environment()

logger.info(
    "Configuring FastMCP to use "
    f"host='{settings.MCP_HOST}' port={settings.MCP_PORT}"
)

# Global engine instance
_engine: Optional[StockfishEngine] = None


class ChessMoveRequest(BaseModel):
    """Request model for chess move generation."""

    fen: str
    move_history: List[str] = []


class ChessMoveResponse(BaseModel):
    """Response model for chess move generation."""

    best_move_uci: str


class PositionRequest(BaseModel):
    """Request model for position-based queries."""

    position: str = Field(..., description="Board position in FEN format.")


class ValidateMoveRequest(BaseModel):
    """Request model for move validation."""

    position: str = Field(..., description="Board position in FEN format.")
    move: str = Field(..., description="Move in UCI format (e.g., 'e2e4').")


class BoolResponse(BaseModel):
    """Response model for boolean results."""

    result: bool


class ListResponse(BaseModel):
    """Response model for list results."""

    result: List[str]


class GameStatusResponse(BaseModel):
    """Response model for game status."""

    status: str = Field(
        ...,
        description="Game status (IN_PROGRESS, CHECKMATE, STALEMATE, DRAW...)",
    )
    winner: Optional[str] = Field(
        None, description="Winner ('WHITE', 'BLACK') if applicable, else null."
    )


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage the lifespan of the MCP application."""
    global _engine
    try:
        logger.info("Starting chess engine server (via MCP lifespan)...")
        if not _engine:
            _engine = StockfishEngine()
            logger.info("Engine initialized successfully (via MCP lifespan)")
        else:
            logger.info("Reusing existing engine instance")
        yield
    finally:
        logger.info("Stopping engine (via MCP lifespan)...")
        if _engine:
            _engine.stop()
            _engine = None
        logger.info("Engine stopped (via MCP lifespan).")


app = FastMCP(
    "chess_engine",
    lifespan=lifespan,
    host=settings.MCP_HOST,
    port=settings.MCP_PORT,
)


@app.tool()
async def get_best_move_tool(request: ChessMoveRequest) -> dict:
    """Get the best move in the given position using the chess engine.

    Args:
        request: The request containing the position and move history.

    Returns:
        A dictionary containing either {"result": {"best_move_uci": str}}
        for success or {"error": str} for failure.
    """
    if _engine is None:
        return {"error": "Engine not initialized"}

    try:
        best_move = _engine.get_best_move(request.fen, request.move_history)
        return {"result": {"best_move_uci": best_move}}
    except StockfishError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


@app.tool()
async def validate_move_tool(request: ValidateMoveRequest) -> dict:
    """Validate if a move is legal in the given position.

    Args:
        request: The request containing the position and move to validate.

    Returns:
        A dictionary containing either {"result": bool} for success
        or {"error": str} for failure.
    """
    try:
        board = chess.Board(request.position)
        move = chess.Move.from_uci(request.move)
        return {"result": move in board.legal_moves}
    except ValueError:
        return {"result": False}  # Invalid FEN or move format
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_legal_moves_tool(request: PositionRequest) -> dict:
    """Get all legal moves in the given position.

    Args:
        request: The request containing the position to analyze.

    Returns:
        A dictionary containing either {"result": List[str]} for success
        or {"error": str} for failure.
    """
    try:
        board = chess.Board(request.position)
        legal_moves = [move.uci() for move in board.legal_moves]
        return {"result": legal_moves}
    except ValueError as e:
        return {"error": f"Invalid FEN format: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


@app.tool()
async def get_game_status_tool(request: PositionRequest) -> dict:
    """Get the current game status from the given position.

    Args:
        request: The request containing the position to analyze.

    Returns:
        dict: A dictionary with either:
            - {"result": {"status": str, "winner": Optional[str]}}
            - {"error": str}
    """
    try:
        board = chess.Board(request.position)

        if board.is_checkmate():
            status = "CHECKMATE"
            winner = "BLACK" if board.turn == chess.WHITE else "WHITE"
        elif board.is_stalemate():
            status = "STALEMATE"
            winner = None
        elif board.is_insufficient_material():
            status = "DRAW"
            winner = None
        else:
            status = "IN_PROGRESS"
            winner = None

        return {"result": {"status": status, "winner": winner}}
    except ValueError as e:
        return {"error": f"Invalid FEN format: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


def main_cli():
    """Run the MCP server with command line arguments."""
    parser = argparse.ArgumentParser(description="Chess Engine MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",  # Default to SSE
        help=("Transport mode for the MCP server " "(default: sse)"),
    )
    args = parser.parse_args()

    # Logging setup should already be done by
    # setup_environment() called globally
    logger.info("Starting MCP server in {} mode...".format(args.transport))
    config_msg = "Configuration - Host: {}, Port: {}"
    logger.info(config_msg.format(settings.MCP_HOST, settings.MCP_PORT))

    # Run the app instance using the selected transport
    app.run(transport=args.transport)


def main() -> None:
    """Start the MCP server with the configured settings."""
    from dylangames_mcp_chess_engine.config import Settings

    settings = Settings()  # type: ignore
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.info(
        "Starting MCP server on port %s with log level %s",
        settings.port,
        settings.log_level,
    )


if __name__ == "__main__":
    main_cli()
