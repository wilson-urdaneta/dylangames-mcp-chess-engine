"""Integration tests for the chess engine MCP server."""

import asyncio
import json
import logging
import signal
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from mcp import ClientSession, types
from mcp.client.sse import sse_client


def setup_test_logging():
    """Set up logging for tests."""
    project_root = Path(__file__).parent.parent.absolute()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(
        logs_dir / "chess_engine.log",
        mode="w",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    error_handler = logging.FileHandler(
        logs_dir / "chess_engine.error.log",
        mode="w",
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)

    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(stream_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    return logs_dir


def print_logs():
    """Print contents of the log files."""
    project_root = Path(__file__).parent.parent.absolute()
    logs_dir = project_root / "logs"

    print("\n=== chess_engine.log ===")
    try:
        with open(logs_dir / "chess_engine.log") as f:
            print(f.read())
    except FileNotFoundError:
        print("Log file not found")

    print("\n=== chess_engine.error.log ===")
    try:
        with open(logs_dir / "chess_engine.error.log") as f:
            print(f.read())
    except FileNotFoundError:
        print("Error log file not found")


@pytest_asyncio.fixture(scope="session")
def logs_dir():
    """Set up logging for the test session."""
    pass


@pytest_asyncio.fixture
async def run_server(logs_dir):
    """Start the MCP server as a subprocess using python -m."""
    logger = logging.getLogger("test_fixture")
    process = None
    module_path = "dylangames_mcp_chess_engine.main"
    cmd = [sys.executable, "-m", module_path]
    logger.info(f"Starting server with command: {' '.join(cmd)}")

    try:
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        logger.info("Waiting for server to initialize...")
        await asyncio.sleep(5)
        logger.info("Server potentially initialized.")

        if process.poll() is not None:
            msg = (
                "Server process terminated unexpectedly "
                f"with code {process.returncode}"
            )
            raise RuntimeError(msg)

        yield

    finally:
        logger.info("Shutting down server process...")
        if process and process.poll() is None:
            try:
                if sys.platform == "win32":
                    process.send_signal(signal.CTRL_C_EVENT)
                else:
                    process.send_signal(signal.SIGINT)
                process.wait(timeout=5)
                msg = (
                    "Server process exited gracefully "
                    f"with code {process.returncode}"
                )
                logger.info(msg)
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Server process did not exit gracefully, killing."
                )
                process.kill()
                process.wait()
                logger.info("Server process killed.")
            except Exception as e:
                logger.error(f"Error during server shutdown: {e}")
                if process.poll() is None:
                    process.kill()
                    process.wait()
        elif process:
            msg = (
                "Server process already terminated "
                f"with code {process.returncode}"
            )
            logger.info(msg)
        print_logs()


@pytest.mark.asyncio
async def test_http_get_best_move(run_server):
    """Test the get_best_move tool via SSE transport."""
    sse_endpoint_url = "http://127.0.0.1:8001/sse"
    tool_arguments = {
        "request": {
            "fen": (
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR " "w KQkq - 0 1"
            ),
            "move_history": [],
        }
    }

    try:
        msg = f"Attempting to connect to SSE endpoint: {sse_endpoint_url}"
        logging.info(msg)
        async with sse_client(sse_endpoint_url, timeout=15.0) as streams:
            logging.info("SSE client connected.")
            async with ClientSession(*streams) as session:
                logging.info("MCP Session created.")
                await session.initialize()
                logging.info("MCP Session initialized.")

                msg = (
                    "Calling tool 'get_best_move_tool' "
                    f"with args: {tool_arguments}"
                )
                logging.info(msg)
                result = await session.call_tool(
                    "get_best_move_tool", tool_arguments
                )
                logging.info("Tool call finished.")

                print(f"Tool Result: {result}")

                assert result is not None
                assert hasattr(result, "content")
                assert isinstance(result.content, list)
                assert len(result.content) > 0
                assert isinstance(result.content[0], types.TextContent)
                assert hasattr(result.content[0], "text")

                result_text = result.content[0].text
                print(f"Result content text: {result_text}")
                try:
                    result_data = json.loads(result_text)
                    assert "best_move_uci" in result_data
                    assert isinstance(result_data["best_move_uci"], str)
                    assert len(result_data["best_move_uci"]) > 0
                    msg = (
                        "Best move verified in JSON: "
                        f"{result_data['best_move_uci']}"
                    )
                    print(msg)
                except json.JSONDecodeError:
                    assert "best_move_uci" in result_text
                    print(f"Best move verified in text: {result_text}")

    except Exception as e:
        import traceback

        traceback.print_exc()  # Print full traceback for debugging
        pytest.fail(
            f"Failed to call tool via SSE: {type(e).__name__}: {str(e)}"
        )
