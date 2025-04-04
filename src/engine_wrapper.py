"""
Wrapper for the Stockfish chess engine.
"""

import os
import subprocess
import time
from typing import List, Optional

class StockfishError(Exception):
    """Exception raised for errors in the Stockfish engine."""
    pass

# Global variables
_engine_process: Optional[subprocess.Popen] = None
_initialized = False

def _get_stockfish_path() -> str:
    """Get the path to the Stockfish binary."""
    path = os.environ.get("STOCKFISH_PATH", "/Users/wilson/AI/new/dylangames/dylangames-engines/games/chess/stockfish/builds/17.1/macos/universal/stockfish")
    if not os.path.isfile(path):
        raise EnvironmentError(
            f"Stockfish binary not found at {path}. "
            "Please set STOCKFISH_PATH to point to your Stockfish binary."
        )
    return path

def _send_command(command: str, timeout: float = 2.0) -> None:
    """Send a command to the engine and wait for it to be processed."""
    global _engine_process
    if not _engine_process or _engine_process.poll() is not None:
        raise StockfishError("Engine process is not running")

    try:
        _engine_process.stdin.write(f"{command}\n".encode())
        _engine_process.stdin.flush()
    except BrokenPipeError:
        raise StockfishError("Failed to communicate with engine")

def _read_response(until: str = None, timeout: float = 2.0) -> List[str]:
    """Read the engine's response until a specific string is found or timeout."""
    global _engine_process
    if not _engine_process or _engine_process.poll() is not None:
        raise StockfishError("Engine process is not running")

    start_time = time.time()
    response = []
    found_until = False

    while True:
        if time.time() - start_time > timeout:
            raise StockfishError("Timeout waiting for engine response")

        try:
            # Check if there's data available to read
            import select
            ready = select.select([_engine_process.stdout], [], [], 0.1)[0]
            if not ready:
                # If we're not waiting for a specific response or we found it, we're done
                if not until or found_until:
                    break
                # If we're waiting for a response but there's no data, check if process is alive
                if _engine_process.poll() is not None:
                    raise StockfishError("Engine process terminated unexpectedly")
                continue

            line = _engine_process.stdout.readline()
            if not line:
                continue

            # Decode and strip the line
            try:
                line = line.decode().strip()
            except UnicodeDecodeError:
                continue

            if line:
                response.append(line)
                # Check if this line matches what we're waiting for
                if until and line.startswith(until):
                    found_until = True
                    # Don't break here - read any remaining output

        except Exception as e:
            raise StockfishError(f"Failed to read engine response: {str(e)}")

    if until and not found_until:
        raise StockfishError(f"Expected response '{until}' not found in engine output")

    return response

def initialize_engine(stockfish_path: str = None) -> None:
    """Initialize the Stockfish engine.

    Args:
        stockfish_path: Optional path to Stockfish binary. If not provided,
                       will try to use STOCKFISH_PATH env var.
    """
    global _engine_process, _initialized

    # Get Stockfish path
    path = stockfish_path or _get_stockfish_path()

    if not os.path.isfile(path):
        raise StockfishError(f"Stockfish binary not found at {path}")

    if not os.access(path, os.X_OK):
        raise StockfishError(f"Stockfish binary at {path} is not executable")

    # Stop any existing engine
    stop_engine()

    try:
        _engine_process = subprocess.Popen(
            [path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # Use bytes mode
            bufsize=0,   # No buffering
            cwd=os.path.dirname(path)  # Run in same directory as binary
        )

        # Send UCI command and wait for uciok
        _send_command("uci")
        response = _read_response(until="uciok", timeout=5.0)

        # Set some standard options
        _send_command("setoption name UCI_Chess960 value false")
        _send_command("setoption name Threads value 1")
        _send_command("setoption name Hash value 128")
        _send_command("isready")
        response = _read_response(until="readyok", timeout=5.0)

        _initialized = True
    except Exception as e:
        stop_engine()
        raise StockfishError(f"Failed to initialize engine: {str(e)}")

def get_best_move(fen: str, move_history: List[str]) -> str:
    """Get the best move for a given position."""
    global _engine_process, _initialized

    if not _initialized or not _engine_process or _engine_process.poll() is not None:
        raise StockfishError("Engine is not initialized")

    try:
        # First set starting position
        _send_command("position startpos")

        # Then set the actual position with FEN and moves
        position_cmd = f"position fen {fen}"
        if move_history:
            position_cmd += f" moves {' '.join(move_history)}"
        _send_command(position_cmd)

        # Make sure engine is ready
        _send_command("isready")
        response = _read_response(until="readyok", timeout=5.0)

        # Get best move with timeout
        _send_command("go movetime 1000")  # Reduced time to 1 second for tests
        try:
            response = _read_response(until="bestmove", timeout=3.0)  # Increased timeout slightly
        except StockfishError as e:
            if "timeout" in str(e).lower():
                # Try to stop the engine if it's taking too long
                _send_command("stop")
                # Try to read the response again after stopping
                try:
                    response = _read_response(until="bestmove", timeout=2.0)
                except:
                    raise StockfishError("Engine took too long to respond")
            else:
                raise

        # Parse the best move
        for line in reversed(response):
            if line.startswith("bestmove"):
                move = line.split()[1]
                if move == "(none)":
                    raise StockfishError("No legal moves in position")
                return move

        raise StockfishError("Failed to get best move from engine")
    except Exception as e:
        # If we encounter any error, try to reinitialize the engine
        stop_engine()
        raise StockfishError(f"Error getting best move: {str(e)}")

def stop_engine() -> None:
    """Stop the Stockfish engine."""
    global _engine_process, _initialized

    if _engine_process:
        try:
            if _engine_process.poll() is None:
                # Try graceful shutdown first
                try:
                    _send_command("quit")
                    _engine_process.communicate(timeout=1.0)
                except:
                    pass

                # If still running, terminate
                if _engine_process.poll() is None:
                    _engine_process.terminate()
                    try:
                        _engine_process.wait(timeout=1.0)
                    except:
                        pass

                # If still running, kill
                if _engine_process.poll() is None:
                    _engine_process.kill()
                    try:
                        _engine_process.wait(timeout=1.0)
                    except:
                        pass
        except:
            pass
        finally:
            try:
                _engine_process.kill()
            except:
                pass
            _engine_process = None
            _initialized = False