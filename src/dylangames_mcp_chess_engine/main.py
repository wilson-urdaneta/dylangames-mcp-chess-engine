"""Provide FastMCP server for the Chess Engine module."""

import argparse
import logging
import sys
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import AsyncIterator, List, Optional

import chess
from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from dylangames_mcp_chess_engine.config import settings
from dylangames_mcp_chess_engine.engine_wrapper import StockfishEngine, StockfishError


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
        logger.error(f"pyproject.toml not found at {pyproject_path}")
        raise RuntimeError(f"pyproject.toml not found at {pyproject_path}")

    # Test engine initialization
    try:
        engine = StockfishEngine()
        engine.stop()
        logger.info("Engine test initialization successful")
    except StockfishError as e:
        logger.error(f"Engine initialization error: {e}")
        # Let initialization handle the error if path is bad

    return logger


logger = setup_environment()

logger.info(f"Configuring FastMCP to use host='{settings.MCP_HOST}' port={settings.MCP_PORT}")

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

    status: str = Field(..., description="Game status (IN_PROGRESS, CHECKMATE, STALEMATE, DRAW...)")
    winner: Optional[str] = Field(None, description="Winner ('WHITE', 'BLACK') if applicable, else null.")


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage the lifespan of the MCP application."""
    global _engine
    try:
        logger.info("Starting chess engine server (via MCP lifespan)...")
        _engine = StockfishEngine()
        logger.info("Engine initialized successfully (via MCP lifespan)")
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
    port=settings.MCP_PORT
)


@app.tool()
async def get_best_move_tool(request: ChessMoveRequest) -> ChessMoveResponse:
    """Get the best chess move for a given position."""
    if not _engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    try:
        logger.info(f"Received request for position: {request.fen}")
        logger.debug(f"Move history: {request.move_history}")
        best_move = _engine.get_best_move(request.fen, request.move_history)
        logger.info(f"Best move found: {best_move}")
        return ChessMoveResponse(best_move_uci=best_move)
    except StockfishError as e:
        logger.error(f"Engine error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.tool()
async def validate_move_tool(request: ValidateMoveRequest) -> BoolResponse:
    """Validates if a chess move is legal for a given position."""
    logger.debug(f"Validating move '{request.move}' for position '{request.position}'")
    try:
        board = chess.Board(request.position)
        uci_move = chess.Move.from_uci(request.move)
        is_legal = uci_move in board.legal_moves
        logger.debug(f"Move '{request.move}' validation result: {is_legal}")
        return BoolResponse(result=is_legal)
    except ValueError:
        logger.warning(f"Invalid FEN '{request.position}' or move '{request.move}' format.")
        return BoolResponse(result=False)  # Treat format errors as invalid
    except Exception as e:
        logger.error(f"Error validating move: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error validating move.")


@app.tool()
async def get_legal_moves_tool(request: PositionRequest) -> ListResponse:
    """Get all legal moves for a given position."""
    try:
        board = chess.Board(request.position)
        legal_moves = [move.uci() for move in board.legal_moves]
        return ListResponse(result=legal_moves)
    except ValueError:
        logger.warning(f"Invalid FEN format: {request.position}")
        raise HTTPException(status_code=400, detail="Invalid FEN format")
    except Exception as e:
        logger.error(f"Error getting legal moves: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error getting legal moves.")


@app.tool()
async def get_game_status_tool(request: PositionRequest) -> GameStatusResponse:
    """Get the status of a chess game from a position."""
    try:
        board = chess.Board(request.position)
        
        # Check for game-ending conditions
        if board.is_checkmate():
            winner = "BLACK" if board.turn == chess.WHITE else "WHITE"
            return GameStatusResponse(status="CHECKMATE", winner=winner)
        elif board.is_stalemate():
            return GameStatusResponse(status="STALEMATE")
        elif board.is_insufficient_material():
            return GameStatusResponse(status="DRAW", winner=None)
        elif board.is_fifty_moves():
            return GameStatusResponse(status="DRAW", winner=None)
        elif board.is_repetition():
            return GameStatusResponse(status="DRAW", winner=None)
        else:
            return GameStatusResponse(status="IN_PROGRESS")
            
    except ValueError:
        logger.warning(f"Invalid FEN format: {request.position}")
        raise HTTPException(status_code=400, detail="Invalid FEN format")
    except Exception as e:
        logger.error(f"Error getting game status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error getting game status.")


def main_cli():
    """Parse arguments and runs the MCP server."""
    parser = argparse.ArgumentParser(description="Chess Engine MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",  # Default to SSE
        help="Transport mode for the MCP server (default: sse)",
    )
    args = parser.parse_args()

    # Logging setup should already be done by setup_environment() called globally
    logger.info(f"Starting MCP server in {args.transport} mode...")
    logger.info(f"Configuration - Host: {settings.MCP_HOST}, Port: {settings.MCP_PORT}")

    # Run the app instance using the selected transport
    app.run(
        transport=args.transport,
    )


if __name__ == "__main__":
    main_cli()
