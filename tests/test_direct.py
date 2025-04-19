"""Direct test for the MCP chess engine service using an already running server."""

import asyncio
import json
import logging
import os
import sys
import time

import pytest
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.types import TextContent

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# Add a global timeout for the test
TEST_TIMEOUT = 30  # seconds

# Use environment variables for MCP host and port
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "9000"))
SSE_ENDPOINT_URL = f"http://{MCP_HOST}:{MCP_PORT}/sse"


@pytest.mark.asyncio
async def test_direct_get_best_move() -> None:
    """Test the get_best_move_tool via MCP SSE transport.

    This test connects to an already running MCP server.
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
        error_msg = f"Error during direct test: {type(e).__name__}: {e}"
        logger.error(error_msg, exc_info=True)
        pytest.fail(f"Direct test failed: {type(e).__name__}: {e}")

    # Check overall test time
    elapsed = time.time() - start_time
    if elapsed > TEST_TIMEOUT * 0.9:  # If we used more than 90% of allowed time
        logger.warning(f"Test completed but took {elapsed:.1f}s, which is close to timeout ({TEST_TIMEOUT}s)")
