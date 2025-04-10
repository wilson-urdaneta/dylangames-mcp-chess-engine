"""Integration tests for the MCP chess engine service."""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient


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
        [sys.executable, "-m", "dylangames_mcp_chess_engine.main"],
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
        server_process.wait(timeout=5)


@pytest.mark.asyncio
async def test_http_get_best_move(run_server: None) -> None:
    """Test the get_best_move_tool via SSE transport."""
    async with AsyncClient() as client:
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        response = await client.post(
            "http://localhost:8080/tools/get_best_move_tool",
            json={"fen": fen},
            headers={"Accept": "text/event-stream"},
        )
        assert response.status_code == 200

        # Parse SSE response
        events = []
        for line in response.text.split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))

        assert len(events) > 0
        result = events[-1]  # Get the last event
        assert "best_move_uci" in result["result"]
        assert len(result["result"]["best_move_uci"]) >= 4  # Valid UCI move
