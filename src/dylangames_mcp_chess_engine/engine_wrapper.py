"""Provide a wrapper for the Stockfish chess engine."""

import logging
import os
import select
import subprocess
import time
from pathlib import Path
from typing import List, Optional

# Initialize logger
logger = logging.getLogger(__name__)


class StockfishError(Exception):
    """Error communicating with the Stockfish engine."""

    pass


# Global variables to track engine state
_engine_process: Optional[subprocess.Popen] = None
_initialized: bool = False


def _get_stockfish_path() -> str:
    """Get the path to the Stockfish binary."""
    path = os.environ.get("STOCKFISH_PATH")
    if not path:
        logger.warning("STOCKFISH_PATH not set, using default path")
        path = str(Path(__file__).parent.parent / "stockfish" / "stockfish")

    if not os.path.isfile(path):
        error_msg = f"Stockfish binary not found at {path}"
        logger.error(error_msg)
        raise StockfishError(error_msg)

    logger.info(f"Using Stockfish binary at: {path}")
    return path


def _send_command(command: str) -> None:
    """Send a command to the Stockfish engine."""
    if not _engine_process or _engine_process.poll() is not None:
        error_msg = "Engine process is not running"
        logger.error(error_msg)
        raise StockfishError(error_msg)

    try:
        logger.debug(f"Sending command: {command}")
        _engine_process.stdin.write(f"{command}\n".encode())
        _engine_process.stdin.flush()
    except BrokenPipeError as e:
        error_msg = f"Failed to send command: {e}"
        logger.error(error_msg)
        raise StockfishError(error_msg)


def _read_response(until: str = None, timeout: float = 2.0) -> List[str]:
    """Read response from the Stockfish engine."""
    if not _engine_process or _engine_process.poll() is not None:
        error_msg = "Engine process is not running"
        logger.error(error_msg)
        raise StockfishError(error_msg)

    responses = []
    start_time = time.time()

    try:
        while True:
            if time.time() - start_time > timeout:
                error_msg = f"Timeout waiting for response (waited {timeout}s)"
                logger.error(error_msg)
                raise StockfishError(error_msg)

            # Check if there's data available to read
            if select.select([_engine_process.stdout], [], [], 0.1)[0]:
                line = _engine_process.stdout.readline().decode().strip()
                if line:
                    logger.debug(f"Received: {line}")
                    responses.append(line)
                    if until and line.startswith(until):
                        break
            elif _engine_process.poll() is not None:
                error_msg = "Engine process terminated unexpectedly"
                logger.error(error_msg)
                raise StockfishError(error_msg)

    except Exception as e:
        error_msg = f"Error reading engine response: {e}"
        logger.error(error_msg)
        raise StockfishError(error_msg)

    return responses


def initialize_engine() -> None:
    """Initialize the Stockfish engine process."""
    global _engine_process, _initialized

    if _initialized and _engine_process and _engine_process.poll() is None:
        logger.info("Engine already initialized")
        return

    try:
        # Stop any existing process
        stop_engine()

        # Start new process
        stockfish_path = _get_stockfish_path()
        logger.info("Starting Stockfish process...")
        _engine_process = subprocess.Popen(
            [stockfish_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            text=False,
        )

        # Initialize UCI mode
        logger.info("Initializing UCI mode...")
        _send_command("uci")
        responses = _read_response(until="uciok", timeout=5.0)
        if not any(r.startswith("uciok") for r in responses):
            raise StockfishError("Failed to initialize UCI mode")

        # Set options
        logger.info("Setting engine options...")
        _send_command("setoption name Hash value 128")
        _send_command("setoption name Threads value 4")

        # Verify engine is ready
        _send_command("isready")
        responses = _read_response(until="readyok", timeout=5.0)
        if not any(r.startswith("readyok") for r in responses):
            raise StockfishError("Engine not responding to isready command")

        _initialized = True
        logger.info("Engine initialized successfully")

    except Exception as e:
        error_msg = f"Failed to initialize engine: {e}"
        logger.error(error_msg)
        stop_engine()
        raise StockfishError(error_msg)


def get_best_move(fen: str, move_history: List[str] = None) -> str:
    """Get the best move for a given position."""
    if (
        not _initialized
        or not _engine_process
        or _engine_process.poll() is not None
    ):
        error_msg = "Engine not initialized or not running"
        logger.error(error_msg)
        raise StockfishError(error_msg)

    try:
        logger.info(f"Getting best move for position: {fen}")
        if move_history:
            logger.debug(f"Move history: {move_history}")

        # Set position
        position_cmd = f"position fen {fen}"
        if move_history:
            position_cmd += f" moves {' '.join(move_history)}"
        _send_command(position_cmd)

        # Get best move
        logger.debug("Calculating best move...")
        _send_command("go movetime 3000")
        responses = _read_response(until="bestmove", timeout=5.0)

        # Parse response
        for response in responses:
            if response.startswith("bestmove"):
                best_move = response.split()[1]
                logger.info(f"Best move found: {best_move}")
                return best_move

        error_msg = "No best move found in engine response"
        logger.error(error_msg)
        raise StockfishError(error_msg)

    except Exception as e:
        error_msg = f"Error getting best move: {e}"
        logger.error(error_msg)
        raise StockfishError(error_msg)


def stop_engine() -> None:
    """Stop the Stockfish engine."""
    global _engine_process, _initialized

    if _engine_process:
        try:
            logger.info("Stopping engine process...")
            if _engine_process.poll() is None:
                _send_command("quit")
                _engine_process.wait(timeout=2.0)
        except Exception as e:
            logger.warning(f"Error during graceful shutdown: {e}")
            try:
                _engine_process.kill()
            except Exception as e:
                logger.error(f"Failed to kill engine process: {e}")
        finally:
            _engine_process = None
            _initialized = False
            logger.info("Engine stopped")
