import asyncio
import json
import logging
import os
import signal
import subprocess  # Added
import sys
import time  # Added
from pathlib import Path
from typing import AsyncGenerator

import httpx  # Keep for health check (optional) or remove if not needed
import pytest
import pytest_asyncio

# Removed uvicorn import
from mcp import ClientSession  # Keep
from mcp import types
from mcp.client.sse import sse_client  # Keep
from mcp.server.fastmcp import FastMCP

# from dylangames_mcp_chess_engine.main import app, setup_environment


def setup_test_logging():
    """Set up logging for tests."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.absolute()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Configure logging
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Create handlers
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(
        logs_dir / "chess_engine.log",
        mode="w",  # Overwrite the file each time
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)

    error_handler = logging.FileHandler(
        logs_dir / "chess_engine.error.log",
        mode="w",  # Overwrite the file each time
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)

    # Set formatter for all handlers
    formatter = logging.Formatter(log_format)
    stream_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Configure root logger
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
    # return setup_test_logging() # Comment out if causing issues with app logging
    pass  # Placeholder if test logging is removed


# --- New fixture to run main.py as subprocess ---
@pytest_asyncio.fixture
async def run_server(logs_dir):  # Depends on logs_dir fixture if used
    """Starts the MCP server as a subprocess using python -m."""
    logger = logging.getLogger("test_fixture")
    process = None
    # Construct the command using sys.executable for robustness
    # Assumes tests run from the project root where poetry run works
    # Or that the correct virtualenv python is used
    module_path = "dylangames_mcp_chess_engine.main"
    cmd = [sys.executable, "-m", module_path]
    logger.info(f"Starting server with command: {' '.join(cmd)}")

    try:
        # Use Popen to start the server in the background
        process = subprocess.Popen(
            cmd,
            stdout=sys.stdout,  # Pipe output to test runner stdout/stderr
            stderr=sys.stderr,
            # cwd= # Optional: set working directory if needed
        )

        # Wait for the server to initialize (adjust sleep time as needed)
        # Check logs manually or implement a more robust readiness check if possible
        logger.info("Waiting for server to initialize...")
        await asyncio.sleep(5)  # Increased sleep time for safety
        logger.info("Server potentially initialized.")

        # Check if process died immediately
        if process.poll() is not None:
            raise RuntimeError(
                f"Server process terminated unexpectedly with code {process.returncode}"
            )

        yield  # Test runs here

    finally:
        logger.info("Shutting down server process...")
        if process and process.poll() is None:
            try:
                # Try graceful termination first (Ctrl+C equivalent)
                if sys.platform == "win32":
                    process.send_signal(signal.CTRL_C_EVENT)
                else:
                    process.send_signal(signal.SIGINT)
                process.wait(timeout=5)  # Wait for clean shutdown
                logger.info(
                    f"Server process exited gracefully (code {process.returncode})."
                )
            except subprocess.TimeoutExpired:
                logger.warning(
                    "Server process did not exit gracefully, killing."
                )
                process.kill()  # Force kill if timeout
                process.wait()  # Wait for kill to complete
                logger.info("Server process killed.")
            except Exception as e:
                logger.error(f"Error during server shutdown: {e}")
                if process.poll() is None:
                    process.kill()
                    process.wait()
        elif process:
            logger.info(
                f"Server process already terminated (code {process.returncode})."
            )
        print_logs()  # Print logs after shutdown attempt


@pytest.mark.asyncio
async def test_http_get_best_move(run_server):  # Use the new fixture
    """Test calling the tool via the SSE transport."""

    # Define the SSE endpoint URL (use default /sse)
    # Assumes main.py runs on localhost:8001 as configured in its run() call
    sse_endpoint_url = "http://127.0.0.1:8001/sse"

    # Define the arguments for the get_best_move_tool
    tool_arguments = {
        "request": {
            "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "move_history": [],
        }
    }
    # OR try direct args if the above fails:
    # tool_arguments = {
    #     "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    #     "move_history": []
    # }

    try:
        # Connect to the SSE endpoint
        # Note: Ensure the server has fully started before this runs (handled by fixture sleep)
        logging.info(
            f"Attempting to connect to SSE endpoint: {sse_endpoint_url}"
        )
        async with sse_client(
            sse_endpoint_url, timeout=15.0
        ) as streams:  # Increased timeout
            logging.info("SSE client connected.")
            # Create an MCP session
            async with ClientSession(*streams) as session:
                logging.info("MCP Session created.")
                # Initialize the session
                await session.initialize()
                logging.info("MCP Session initialized.")

                # Call the tool
                logging.info(
                    f"Calling tool 'get_best_move_tool' with args: {tool_arguments}"
                )
                result = await session.call_tool(
                    "get_best_move_tool", tool_arguments
                )
                logging.info("Tool call finished.")

                # Print the result for debugging
                print(f"Tool Result: {result}")

                # Verify the result (adjust assertions based on actual result structure)
                assert result is not None
                assert hasattr(
                    result, "content"
                ), "Result object lacks 'content' attribute"
                assert isinstance(
                    result.content, list
                ), "'result.content' is not a list"
                assert (
                    len(result.content) > 0
                ), "'result.content' list is empty"
                assert isinstance(
                    result.content[0], types.TextContent
                ), "First content item is not TextContent"
                assert hasattr(
                    result.content[0], "text"
                ), "Result content lacks 'text' attribute"

                # More specific check - assuming the response model is serialized to text/json within content
                result_text = result.content[0].text
                print(f"Result content text: {result_text}")
                # Try parsing if it looks like JSON, otherwise check for string content
                try:
                    result_data = json.loads(result_text)
                    assert "best_move_uci" in result_data
                    assert isinstance(result_data["best_move_uci"], str)
                    assert (
                        len(result_data["best_move_uci"]) > 0
                    )  # e.g., 4 chars like 'e2e4'
                    print(
                        f"Best move verified in JSON: {result_data['best_move_uci']}"
                    )
                except json.JSONDecodeError:
                    # If not JSON, check if the expected key is just in the string
                    assert "best_move_uci" in result_text
                    print(
                        f"Best move verified in text: {result_text}"
                    )  # Adjust assertion if needed

    except Exception as e:
        import traceback

        traceback.print_exc()  # Print full traceback for debugging
        pytest.fail(
            f"Failed to call tool via SSE: {type(e).__name__}: {str(e)}"
        )
