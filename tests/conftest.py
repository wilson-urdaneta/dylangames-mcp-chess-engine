"""Configure pytest for the test suite."""

import os
import pytest


@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables for all tests."""
    old_env = dict(os.environ)
    os.environ.update({
        "PYTHON_ENV": "test",
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": "8001",
        "LOG_LEVEL": "DEBUG"
    })
    yield
    os.environ.clear()
    os.environ.update(old_env) 