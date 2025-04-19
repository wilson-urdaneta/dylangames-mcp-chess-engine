"""Tests for Docker image build and basic execution."""

import subprocess
import uuid

import pytest

# Define a unique image tag for testing to avoid conflicts
TEST_IMAGE_TAG = f"chesspal-mcp-engine-test:{uuid.uuid4()}"


@pytest.mark.docker
def test_docker_build_and_run_help():
    """
    Tests if the Docker image builds successfully and the entry point
    responds to --help. Assumes Docker is available in the environment.
    """
    # Build the Docker image
    build_command = ["docker", "build", "-t", TEST_IMAGE_TAG, "."]
    build_result = subprocess.run(build_command, capture_output=True, text=True)

    print("--- Docker Build Output ---")
    print(build_result.stdout)
    print(build_result.stderr)
    print("--- End Docker Build Output ---")

    assert build_result.returncode == 0, f"Docker build failed: {build_result.stderr}"

    # Run the container with --help
    run_command = ["docker", "run", "--rm", TEST_IMAGE_TAG, "--help"]
    run_result = subprocess.run(run_command, capture_output=True, text=True)

    print("--- Docker Run Output ---")
    print(run_result.stdout)
    print(run_result.stderr)
    print("--- End Docker Run Output ---")

    # Clean up the test image
    cleanup_command = ["docker", "rmi", TEST_IMAGE_TAG]
    subprocess.run(cleanup_command, capture_output=True, text=True)

    assert run_result.returncode == 0, f"Docker run --help failed: {run_result.stderr}"
    assert (
        "usage: chesspal-mcp-engine" in run_result.stdout.lower() or "usage: main.py" in run_result.stdout.lower()
    ), "Entry point help message not found in output."
