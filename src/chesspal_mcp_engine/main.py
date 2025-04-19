"""Main module for the MCP chess engine service."""

import argparse
from contextlib import asynccontextmanager

# from pathlib import Path # Removed unused import
from typing import AsyncIterator, List, Optional

import chess
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

from chesspal_mcp_engine.config import settings
from chesspal_mcp_engine.engine_wrapper import StockfishEngine, StockfishError, _get_engine_path
from chesspal_mcp_engine.logging_config import get_logger, setup_logging
from chesspal_mcp_engine.shutdown import setup_signal_handlers

# Global engine instance - Initialize as None
_engine: Optional[StockfishEngine] = None
logger = get_logger(__name__)  # Get logger instance


def setup_environment():
    """Set up and validate the environment. Moved inside main_cli."""
    global _engine

    # Set up signal handlers for graceful shutdown
    setup_signal_handlers()
    logger.info("Signal handlers for graceful shutdown are set up")

    # Initialize engine
    try:
        _engine = StockfishEngine()
        logger.info("Engine initialization successful")
        try:
            stockfish_path = _get_engine_path()
            logger.info("Stockfish engine binary location: %s", stockfish_path)
        except Exception as e:
            logger.warning("Unable to retrieve Stockfish engine path: %s", e)
    except StockfishError as e:
        logger.error("Engine initialization failed: %s", e)
        # Depending on desired behavior, might want to exit or raise here
        # For now, allow server to start but tools might fail
    except Exception as e:
        logger.error("Unexpected error during engine initialization: %s", e, exc_info=True)
        # Allow server to start but tools might fail


# Initialize logging first - This needs to happen early
# But the setup_environment call needs to be deferred
setup_logging(settings.LOG_LEVEL)  # Pass log level directly

# logger = setup_environment() # Defer this call

# logger.info( # Defer this call
#     "Configuring FastMCP to use host='%s' port=%d",
#     settings.MCP_HOST,
#     settings.MCP_PORT,
# )


class ChessMoveRequest(BaseModel):
    """Request model for chess move generation."""

    fen: str
    move_history: List[str] = []


class ChessMoveResponse(BaseModel):
    """Response model for chess move generation."""

    best_move_uci: str


class PositionRequest(BaseModel):
    """Request model for position-based queries."""

    fen: str = Field(..., description="Board position in FEN format.")


class ValidateMoveRequest(BaseModel):
    """Request model for move validation."""

    fen: str = Field(..., description="Board position in FEN format.")
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
    winner: Optional[str] = Field(None, description="Winner ('WHITE', 'BLACK') if applicable, else null.")


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[None]:
    """Manage the lifespan of the MCP application."""
    global _engine
    try:
        logger.info("Starting chess engine server (via MCP lifespan)...")
        if not _engine:
            _engine = StockfishEngine()
            logger.info("Engine initialized successfully (via MCP lifespan)")
            # Log the exact path of the Stockfish binary being used
            try:
                stockfish_path = _get_engine_path()
                logger.info(
                    "Stockfish engine binary location: %s",
                    stockfish_path,
                )
            except Exception as e:
                logger.warning(
                    "Unable to retrieve Stockfish engine path: %s",
                    e,
                )
        else:
            logger.info("Reusing existing engine instance")
            # Still try to log the path for the existing instance
            try:
                stockfish_path = _get_engine_path()
                logger.info(
                    "Stockfish engine binary location: %s",
                    stockfish_path,
                )
            except Exception as e:
                logger.warning(
                    "Unable to retrieve Stockfish engine path: %s",
                    e,
                )
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
        logger.warning("Stockfish engine error: %s", e)
        return {"error": str(e)}
    except Exception as e:
        logger.error(
            "Unexpected internal error in get_best_move_tool: %s",
            e,
            exc_info=True,
        )
        return {"error": "Internal server error"}


@app.tool()
async def validate_move_tool(request: ValidateMoveRequest) -> dict:
    """Validate if a move is legal in the given position.

    Args:
        request: The request containing the FEN position and move to validate.

    Returns:
        A dictionary containing either {"result": bool} for success
        or {"error": str} for failure.
    """
    try:
        board = chess.Board(request.fen)
    except ValueError as e:
        logger.warning("Invalid FEN format in validate_move_tool: %s", e)
        return {"error": "Invalid FEN format: %s" % e}

    try:
        move = chess.Move.from_uci(request.move)
    except ValueError as e:
        logger.warning("Invalid move format in validate_move_tool: %s", e)
        return {"error": "Invalid move format: %s" % e}

    try:
        result = move in board.legal_moves
        return {"result": result}
    except Exception as e:
        logger.error(
            "Unexpected internal error in validate_move_tool: %s",
            e,
            exc_info=True,
        )
        return {"error": "Internal server error"}


@app.tool()
async def get_legal_moves_tool(request: PositionRequest) -> dict:
    """Get all legal moves in the given position.

    Args:
        request: The request containing the FEN position.

    Returns:
        A dictionary containing either {"result": List[str]} for success
        or {"error": str} for failure.
    """
    try:
        board = chess.Board(request.fen)
    except ValueError as e:
        logger.warning("Invalid FEN format in get_legal_moves_tool: %s", e)
        return {"error": "Invalid FEN format: %s" % e}

    try:
        legal_moves = [move.uci() for move in board.legal_moves]
        return {"result": legal_moves}
    except Exception as e:
        logger.error(
            "Unexpected internal error in get_legal_moves_tool: %s",
            e,
            exc_info=True,
        )
        return {"error": "Internal server error"}


@app.tool()
async def get_game_status_tool(request: PositionRequest) -> dict:
    """Get the game status for the given position.

    Args:
        request: The request containing the FEN position.

    Returns:
        A dictionary containing either {"result": GameStatusResponse}
        for success or {"error": str} for failure.
    """
    try:
        board = chess.Board(request.fen)
    except ValueError as e:
        logger.warning("Invalid FEN format in get_game_status_tool: %s", e)
        return {"error": "Invalid FEN format: %s" % e}

    try:
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
    except Exception as e:
        logger.error(
            "Unexpected internal error in get_game_status_tool: %s",
            e,
            exc_info=True,
        )
        return {"error": "Internal server error"}


def main_cli():
    """Parse arguments, set up environment, and run the MCP server."""
    parser = argparse.ArgumentParser(description="Chess Engine MCP Server")
    parser.add_argument(
        "--transport",
        choices=["sse", "stdio"],
        default="sse",  # Default to SSE
        help=("Transport mode for the MCP server " "(default: sse)"),
    )
    args = parser.parse_args()  # Parse args early to handle --help

    # Now setup environment (logging is already set up globally)
    setup_environment()

    logger.info("Starting MCP server in %s mode...", args.transport)
    logger.info(
        "Configuration - Host: %s, Port: %d",
        settings.MCP_HOST,
        settings.MCP_PORT,
    )

    # Get stockfish path for display
    try:
        stockfish_path = _get_engine_path()

        # Make sure these messages appear in the console no matter what
        print("\033[32mINFO\033[0m:     Stockfish engine:")
        print("\033[32mINFO\033[0m:     → %s" % stockfish_path)
        print("\033[32mINFO\033[0m:     Transport mode: %s" % args.transport)

        # Still log to uvicorn logger for completeness
        uvicorn_logger = get_logger("uvicorn")
        uvicorn_logger.info("Stockfish engine:")
        uvicorn_logger.info("→ %s", stockfish_path)
        uvicorn_logger.info("Transport mode: %s", args.transport)
    except Exception as e:
        logger.warning("Unable to retrieve Stockfish engine path: %s", e)
        print("\033[33mWARNING\033[0m: " "Unable to retrieve Stockfish engine path: %s" % e)

    # Run the app instance using the selected transport
    app.run(transport=args.transport)


# Removed redundant main() function

if __name__ == "__main__":
    main_cli()
