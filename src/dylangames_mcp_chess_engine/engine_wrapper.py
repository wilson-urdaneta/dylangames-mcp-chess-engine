"""Provide a wrapper for the Stockfish chess engine."""

import logging
import os
import platform
import select
import subprocess
import time
from pathlib import Path
from typing import List

# Add import for EngineRegistry
from dylangames_mcp_chess_engine.shutdown import EngineRegistry

# Initialize logger
logger = logging.getLogger(__name__)


def _get_engine_path() -> Path:
    """Get the path to the Stockfish engine binary.

    Returns:
        Path: Path to the Stockfish binary

    Raises:
        EngineBinaryError: If the binary cannot be found or accessed
    """
    # First try ENGINE_PATH environment variable
    engine_path = os.environ.get("ENGINE_PATH")
    if engine_path:
        path = Path(engine_path)
        if path.is_file() and os.access(path, os.X_OK):
            logger.info(f"Using engine binary from ENGINE_PATH: {path}")
            return path
        logger.warning(
            f"ENGINE_PATH set but invalid: {path} "
            "(file must exist and be executable)"
        )
        # Don't raise error yet, try system paths and fallback path

    # Next, try common system paths for stockfish
    logger.info("Checking common system paths for Stockfish binary")
    system_paths = [
        Path("/usr/games/stockfish"),
        Path("/usr/bin/stockfish"),
        Path("/usr/local/bin/stockfish"),
    ]

    for path in system_paths:
        if path.is_file() and os.access(path, os.X_OK):
            logger.info(f"Using engine binary from system path: {path}")
            return path

    # Fallback to constructed path
    logger.info("System paths not valid, attempting fallback path")

    # Get OS - either from ENV or detect
    engine_os = os.environ.get("ENGINE_OS")
    if not engine_os:
        system = platform.system().lower()
        if system == "darwin":
            engine_os = "macos"
        elif system == "linux":
            engine_os = "linux"
        elif system == "windows":
            engine_os = "windows"
        else:
            raise EngineBinaryError(f"Unsupported platform: {system}")
        logger.info(f"No ENGINE_OS set, detected OS as: {engine_os}")

    # Construct fallback path
    engine_name = os.environ.get("ENGINE_NAME", "stockfish")
    engine_version = os.environ.get("ENGINE_VERSION", "17.1")
    binary_name = "stockfish.exe" if engine_os == "windows" else "stockfish"

    fallback_path = (
        Path(__file__).parent.parent.parent
        / "engines"
        / engine_name
        / engine_version
        / engine_os
        / binary_name
    ).resolve()

    if not fallback_path.is_file():
        # If ENGINE_PATH was set but invalid, mention it in the error
        error_msg = (
            "Stockfish binary not found at fallback path: "
            f"{fallback_path}\n"
        )
        if engine_path:
            error_msg += (
                f"Note: ENGINE_PATH was set ({engine_path}) but is invalid.\n"
            )

        error_msg += (
            "Please either:\n"
            "1. Set ENGINE_PATH to point to your Stockfish binary, or\n"
            "2. Download the appropriate binary from "
            "https://github.com/official-stockfish/Stockfish/releases\n"
            f"   and place it at {fallback_path}"
        )
        raise EngineBinaryError(error_msg)

    if not os.access(fallback_path, os.X_OK):
        raise EngineBinaryError(
            "Stockfish binary at {path} exists but is not executable.\n"
            "Please ensure the file has proper execute permissions.".format(
                path=fallback_path
            )
        )

    logger.info(f"Using engine binary from fallback path: {fallback_path}")
    return fallback_path


class EngineBinaryError(Exception):
    """Error related to engine binary configuration or access."""

    pass


class StockfishError(Exception):
    """Error communicating with the Stockfish engine."""

    pass


class StockfishEngine:
    """A class to manage interactions with the Stockfish chess engine."""

    def __init__(self):
        """Initialize the Stockfish engine."""
        self.process = None
        self._initialize_engine()
        # Register with engine registry
        EngineRegistry.register(self)

    def _send_command(self, command: str) -> None:
        """Send a command to the Stockfish engine."""
        if not self.process or self.process.poll() is not None:
            raise StockfishError("Engine process is not running")

        try:
            logger.debug(f"Sending command: {command}")
            self.process.stdin.write(f"{command}\n".encode())
            self.process.stdin.flush()
        except BrokenPipeError as e:
            raise StockfishError(f"Failed to send command: {e}")

    def _read_response(
        self, until: str | None = None, timeout: float = 2.0
    ) -> List[str]:
        """Read response from the Stockfish engine.

        Args:
            until: String to look for in response
            timeout: Maximum time to wait for response

        Returns:
            List of response lines from the engine
        """
        if not self.process or self.process.poll() is not None:
            raise StockfishError("Engine process is not running")

        responses: List[str] = []
        start_time = time.time()

        try:
            while True:
                if time.time() - start_time > timeout:
                    # If we're looking for a specific response and
                    # haven't found it, return what we have so far
                    if until and responses:
                        return responses
                    raise StockfishError(
                        "Timeout waiting for response " f"(waited {timeout}s)"
                    )

                if select.select([self.process.stdout], [], [], 0.1)[0]:
                    line = self.process.stdout.readline()
                    line = line.decode().strip()
                    if line:
                        logger.debug(f"Received: {line}")
                        responses.append(line)
                        if until and line.startswith(until):
                            break
                elif self.process.poll() is not None:
                    raise StockfishError(
                        "Engine process terminated unexpectedly"
                    )

        except Exception as e:
            raise StockfishError(f"Error reading engine response: {e}")

        return responses

    def _initialize_engine(self) -> None:
        """Initialize the Stockfish engine process."""
        try:
            # Start new process
            stockfish_path = _get_engine_path()
            logger.info("Starting Stockfish process...")
            self.process = subprocess.Popen(
                [str(stockfish_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                text=False,
            )

            # Initialize UCI mode
            logger.info("Initializing UCI mode...")
            self._send_command("uci")
            responses = self._read_response(until="uciok", timeout=5.0)
            if not any(r.startswith("uciok") for r in responses):
                raise StockfishError("Failed to initialize UCI mode")

            # Set options
            logger.info("Setting engine options...")
            self._send_command("setoption name Hash value 128")
            self._send_command("setoption name Threads value 4")

            # Verify engine is ready
            self._send_command("isready")
            responses = self._read_response(until="readyok", timeout=5.0)
            if not any(r.startswith("readyok") for r in responses):
                raise StockfishError(
                    "Engine not responding to isready command"
                )

            logger.info("Engine initialized successfully")

        except Exception as e:
            self.stop()
            raise StockfishError(f"Failed to initialize engine: {e}")

    def get_best_move(
        self, fen: str, move_history: List[str] | None = None
    ) -> str:
        """Get the best move for a given position."""
        if not self.process or self.process.poll() is not None:
            raise StockfishError("Engine not initialized or not running")

        try:
            logger.info(f"Getting best move for position: {fen}")
            if move_history:
                logger.debug(f"Move history: {move_history}")

            # Set position
            position_cmd = f"position fen {fen}"
            if move_history:
                position_cmd += f" moves {' '.join(move_history)}"
            self._send_command(position_cmd)

            # Get best move
            logger.debug("Calculating best move...")
            self._send_command("go movetime 3000")
            logger.debug("Waiting for bestmove response with 30s timeout...")
            responses = self._read_response(until="bestmove", timeout=30.0)
            logger.debug(
                f"Received {len(responses)} response lines from engine"
            )

            # Parse response
            for response in responses:
                if response.startswith("bestmove"):
                    best_move = response.split()[1]
                    logger.info(f"Best move found: {best_move}")
                    return best_move

            logger.error(
                f"No 'bestmove' line found in engine responses: {responses}"
            )
            raise StockfishError("No best move found in engine response")

        except Exception as e:
            raise StockfishError(f"Error getting best move: {e}")

    def stop(self) -> None:
        """Stop the Stockfish engine."""
        if self.process:
            try:
                logger.info("Stopping engine process...")
                if self.process.poll() is None:
                    self._send_command("quit")
                    self.process.wait(timeout=5.0)
            except Exception as e:
                logger.warning(f"Error during graceful shutdown: {e}")
                try:
                    self.process.kill()
                except Exception as e:
                    logger.error(f"Failed to kill engine process: {e}")
            finally:
                self.process = None
                logger.info("Engine stopped")
                # Unregister from registry
                EngineRegistry.unregister(self)
