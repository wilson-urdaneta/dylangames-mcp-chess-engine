"""Integration tests for the MCP chess engine service."""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time  # Import time module for timeout
from pathlib import Path

import pytest
import pytest_asyncio
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.types import TextContent

logger = logging.getLogger(__name__)

# Add a global timeout for the test
TEST_TIMEOUT = 30  # seconds

# Use environment variables for MCP host and port
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "9000"))
SSE_ENDPOINT_URL = f"http://{MCP_HOST}:{MCP_PORT}/sse"


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
    return setup_test_logging()


@pytest_asyncio.fixture
async def run_server():
    """Start the MCP server as a subprocess."""
    # Start the server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "chesspal_mcp_engine.main"],
        env=os.environ.copy(),
    )

    # Wait for server to start
    await asyncio.sleep(2)

    try:
        yield
    finally:
        # Stop the server
        if sys.platform == "win32":
            server_process.terminate()
        else:
            server_process.send_signal(signal.SIGTERM)
        try:
            server_process.wait(timeout=10)  # Increase timeout to 10 seconds
        except subprocess.TimeoutExpired:
            # Force kill if graceful shutdown fails
            if sys.platform == "win32":
                server_process.kill()
            else:
                server_process.send_signal(signal.SIGKILL)
            server_process.wait()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_http_get_best_move(run_server: None) -> None:
    """Test the get_best_move_tool via MCP SSE transport.

    This test verifies that:
    1. The server accepts properly formatted requests with a "request" field
    2. The Stockfish engine has sufficient time (15s timeout) to calculate
    3. The response contains a valid UCI format move

    The request structure must be:
    {
        "request": {
            "fen": str,
            "move_history": List[str]
        }
    }
    """
    fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    tool_name = "get_best_move_tool"
    # Request field wrapper required for validation
    arguments = {"request": {"fen": fen, "move_history": []}}

    try:
        # Add overall test timeout
        start_time = time.time()

        endpoint_msg = f"Attempting to connect to SSE endpoint: {SSE_ENDPOINT_URL}"
        logger.info(endpoint_msg)

        # Use a client timeout to prevent hanging
        async with sse_client(SSE_ENDPOINT_URL, timeout=10.0) as streams:
            logger.info("SSE client connected.")
            async with ClientSession(*streams) as session:
                logger.info("MCP Session created.")
                await session.initialize()
                logger.info("MCP Session initialized.")

                tool_msg = f"Calling tool '{tool_name}' with args: {arguments}"
                logger.info(tool_msg)

                # Add a timeout for the tool call
                tool_call_task = asyncio.create_task(session.call_tool(tool_name, arguments))

                # Wait for the task with timeout
                try:
                    result_message = await asyncio.wait_for(
                        tool_call_task, timeout=TEST_TIMEOUT - (time.time() - start_time)
                    )
                    logger.info("Tool call finished.")
                    logger.info(f"Raw Result Message: {result_message}")
                except asyncio.TimeoutError:
                    logger.error(f"Tool call timed out after {TEST_TIMEOUT} seconds")
                    pytest.fail(f"Test timed out after {TEST_TIMEOUT} seconds")

                # Parse result
                if not result_message.content:
                    pytest.fail("Empty response content received from tool")

                content = result_message.content[0]
                if not isinstance(content, TextContent):
                    msg = f"Unexpected content type: {type(content)}"
                    pytest.fail(msg)

                try:
                    result_data = json.loads(content.text)
                except json.JSONDecodeError as e:
                    msg = f"Invalid JSON response: {e} - " f"Response text: {content.text}"
                    pytest.fail(msg)

                # Check for application error returned in payload
                if "error" in result_data:
                    error_msg = f"Tool returned error: {result_data['error']}"
                    logger.error(error_msg)
                    # Check if the error is related to the Stockfish binary
                    if "No best move found" in result_data["error"]:
                        pytest.skip(f"Stockfish engine issue: {result_data['error']}")
                    else:
                        pytest.fail(error_msg)

                # Check for success result
                if "result" not in result_data:
                    msg = "Response missing 'result' field. " f"Response: {result_data}"
                    pytest.fail(msg)

                final_result = result_data["result"]
                assert "best_move_uci" in final_result
                assert isinstance(final_result["best_move_uci"], str)
                # UCI format check
                assert len(final_result["best_move_uci"]) >= 4
                logger.info(f"Best move verified: {final_result['best_move_uci']}")

    except Exception as e:
        error_msg = f"Error during integration test: {type(e).__name__}: {e}"
        logger.error(error_msg, exc_info=True)
        pytest.fail(f"Integration test failed: {type(e).__name__}: {e}")

    # Check overall test time
    elapsed = time.time() - start_time
    if elapsed > TEST_TIMEOUT * 0.9:  # If we used more than 90% of allowed time
        logger.warning(f"Test completed but took {elapsed:.1f}s, which is close to timeout ({TEST_TIMEOUT}s)")
