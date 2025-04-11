# ChessPal Chess Engine - A Stockfish-powered chess engine exposed as an MCP server using FastMCP

[![PyPI version](https://img.shields.io/pypi/v/chesspal-mcp-engine.svg)](https://pypi.org/project/chesspal-mcp-engine/)
[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD](https://github.com/wilson-urdaneta/dylangames-mcp-chess-engine/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/wilson-urdaneta/dylangames-mcp-chess-engine/actions)

A Stockfish-powered chess engine exposed as an MCP server using FastMCP. Calculates best moves via MCP tools accessible over SSE (default) or stdio transports using an MCP client library. Part of the ChessPal project.

## Features

- Robust Stockfish engine integration with proper process management
- Exposes engine functionality via the Model Context Protocol (MCP) using FastMCP.
- Supports both SSE and stdio MCP transports for client interaction.
- UCI protocol implementation for chess move generation
- Comprehensive test suite with TDD approach
- Error handling and recovery mechanisms
- Support for FEN positions and move history
- Flexible engine binary configuration

## Prerequisites

- Python 3.10 or higher
- Poetry for dependency management (install from [Poetry's documentation](https://python-poetry.org/docs/#installation))
- Stockfish chess engine binary (version 17.1 recommended)

## Installation

Install the published package from PyPI using pip:

```bash
pip install chesspal-mcp-engine
```

Installation for development

1. Clone the repository:
```bash
git clone https://github.com/wilson-urdaneta/dylangames-mcp-chess-engine.git
cd dylangames-mcp-chess-engine
```

2. Install dependencies and create virtual environment using Poetry:
```bash
poetry install
```

3. Configure the engine binary:
   - Option 1: Set `ENGINE_PATH` environment variable to point to your Stockfish binary
   - Option 2: Use the fallback configuration with these environment variables:
     ```bash
     # All variables have defaults, override as needed
     export ENGINE_NAME=stockfish     # Default: stockfish
     export ENGINE_VERSION=17.1       # Default: 17.1
     export ENGINE_OS=linux           # Default: linux
     export ENGINE_BINARY=stockfish   # Default: stockfish (include .exe for Windows)
     ```

## Stockfish Binary Setup

The ChessPal Chess Engine requires a Stockfish binary to run the server and integration tests. You have three options for setting up the binary:

### Option 1: Set ENGINE_PATH (Recommended)

Point to any Stockfish executable on your system:

```bash
# Unix-like systems (binary from apt/brew or downloaded)
export ENGINE_PATH=/usr/local/bin/stockfish

# Windows (PowerShell)
$env:ENGINE_PATH="C:\path\to\stockfish.exe"
```

The binary can be:
- System-installed via package managers (`apt install stockfish`, `brew install stockfish`)
- Downloaded from [Stockfish releases](https://github.com/official-stockfish/Stockfish/releases)
- Manually compiled from source

### Option 2: Use engines/ Directory

If `ENGINE_PATH` is not set, the server will look for the binary in a predefined directory structure:

1. Download the official binary for your OS from [Stockfish releases](https://github.com/official-stockfish/Stockfish/releases)
2. Place it in: `engines/stockfish/<version>/<os>/<binary_name>`
   - See `engines/README.md` for the exact directory structure
3. Set `ENGINE_OS` environment variable to match your system:
   ```bash
   export ENGINE_OS=macos    # For macOS
   export ENGINE_OS=linux    # For Linux
   export ENGINE_OS=windows  # For Windows
   ```

### Option 3: Build from Source (Advanced)

Advanced users can compile Stockfish from source using our separate `dylangames-engine` repository. This option provides maximum control over the build configuration but requires C++ development experience.

## Usage

### Starting the Server

The server uses FastMCP with support for both Server-Sent Events (SSE) and stdio transports. You can start it using:

#### SSE Mode (Default)

```bash
poetry run python -m dylangames_mcp_chess_engine.main
```

This command starts the MCP server in SSE mode, which listens for SSE connections on the configured host and port (default: 127.0.0.1:9000). This mode is ideal for programmatic clients and agents that need to interact with the chess engine over HTTP.

#### Stdio Mode

```bash
poetry run python -m dylangames_mcp_chess_engine.main --transport stdio
```

This command starts the MCP server in stdio mode, which communicates through standard input/output. This mode is useful for direct integration with tools like Claude Desktop or for testing purposes.

### API Endpoints

The module exposes the following endpoint through FastMCP:

- `get_best_move_tool`: Get the best move for a given chess position

Example request using the MCP SSE client:
```python
from mcp.client.sse import sse_client
from mcp import ClientSession

async def get_best_move():
    # Connect to the SSE endpoint
    async with sse_client("http://127.0.0.1:9000/sse", timeout=10.0) as streams:
        # Create an MCP session
        async with ClientSession(*streams) as session:
            # Initialize the session
            await session.initialize()

            # Call the tool - Note: Arguments MUST be wrapped in a "request" field
            result = await session.call_tool('get_best_move_tool', {
                "request": {  # Required wrapper field
                    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                    "move_history": []
                }
            })

            print(f"Best move: {result.best_move_uci}")  # e.g., "e2e4"
```

#### Request Format

The `get_best_move_tool` expects requests in the following format:
```json
{
    "request": {
        "fen": "string",       // Required: FEN string representing the position
        "move_history": []     // Optional: List of previous moves in UCI format
    }
}
```

Note: The outer "request" wrapper field is required for proper request validation.

#### Timeouts

The engine is configured with the following timeouts:
- Engine calculation time: 3000ms (set via `go movetime 3000`)
- Response wait timeout: 30s (allows time for engine initialization and calculation)
- SSE client connection timeout: 15s (configurable in client code)

These timeouts ensure reliable operation while allowing sufficient time for move calculation, even on slower systems or when the engine needs more time to process complex positions.

### Environment Variables

The module uses the following environment variables for configuration:

```bash
# Primary configuration
ENGINE_PATH=/path/to/your/engine/binary

# Fallback configuration (used if ENGINE_PATH is not set/invalid)
ENGINE_NAME=stockfish       # Default: stockfish
ENGINE_VERSION=17.1         # Default: 17.1
ENGINE_OS=linux            # Default: linux
ENGINE_BINARY=stockfish    # Default: stockfish (include .exe for Windows)

# MCP Server Configuration
MCP_HOST=127.0.0.1        # Default: 127.0.0.1
MCP_PORT=9000             # Default: 9000
```

See `.env.example` for a complete example configuration.

## Development

### Project Structure

```
dylangames-mcp-chess-engine/
├── src/                    # Source code
│   └── dylangames_mcp_chess_engine/
│       ├── __init__.py
│       ├── main.py        # FastMCP server
│       └── engine_wrapper.py  # Stockfish wrapper
├── tests/                 # Test suite
│   └── test_engine_wrapper.py
├── engines/              # Engine binaries directory
├── pyproject.toml       # Poetry dependencies and configuration
├── poetry.lock         # Locked dependencies
├── .env.example        # Environment variables example
└── README.md          # This file
```

### Development Workflow

1. Install dependencies:
```bash
poetry install
```

2. Activate the virtual environment:
```bash
poetry shell
```

3. Run tests:
```bash
poetry run pytest
poetry run pytest tests/ -v
```

4. Run code quality tools:
```bash
poetry run black .
poetry run isort .
poetry run flake8
poetry run pre-commit run --all-files
```

5. Using the mcp inspector:
```bash
poetry run mcp dev src/dylangames_mcp_chess_engine/main.py

# In the inspector UI
# STDIO configuration
Command: poetry
Arguments: run python -m dylangames_mcp_chess_engine.main --transport stdio

# SSE
# In a separate terminal run the app in SSE mode
poetry run python -m dylangames_mcp_chess_engine.main
# In the mcp inspector UI
Transport Type > SSE
```

```json
{
  "fen": "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
  "move_history": []
}
```

### Adding Dependencies

To add new dependencies:
```bash
# Add a production dependency
poetry add package-name

# Add a development dependency
poetry add --group dev package-name
```

### Code Quality

The codebase follows these standards:
- Type hints for all functions
- Comprehensive error handling
- Detailed docstrings (Google style)
- PEP 8 compliance via Black, isort, and flake8
- Proper resource management

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters:
   ```bash
   poetry run black .
   poetry run isort .
   poetry run flake8
   poetry run pytest
   ```
5. Submit a pull request

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment. The pipeline is triggered on:
- Push to `main` branch
- Pull requests to `main` branch
- Tag pushes starting with `v` (e.g., v1.0.0)

### Pipeline Stages

1. **Lint** (`lint` job)
   - Runs on Ubuntu latest
   - Checks code formatting with Black
   - Verifies import sorting with isort
   - Performs code quality checks with flake8

2. **Test** (`test` job)
   - Runs on Ubuntu latest
   - Installs Stockfish engine
   - Executes the test suite with pytest

3. **Package** (`package` job)
   - Runs after successful lint and test
   - Builds the Python package using Poetry
   - Uploads build artifacts for release

4. **Release** (`release` job)
   - Runs only on version tags (e.g., v1.0.0)
   - Creates GitHub releases
   - Optionally publishes to PyPI (disabled by default)

### Versioning and Tags

The project uses semantic versioning with two types of tags:

1. **External Releases** (e.g., `v1.0.0`)
   - Public releases available to users
   - Triggers full release process
   - Creates GitHub release with release notes
   - Can optionally publish to PyPI

2. **Internal Releases** (e.g., `v1.0.0-internal`)
   - Used for internal testing and development
   - Skips the release job
   - Useful for testing release process without affecting public releases

### PyPI Publishing

PyPI publishing is disabled by default. To enable:
1. Set `ENABLE_PYPI` to `true` in the workflow file
2. Configure `PYPI_TOKEN` secret in GitHub repository settings

## License

GNU General Public License v3.0 - see [LICENSE](LICENSE) file for details.

## Support

For issues and feature requests, please use the GitHub issue tracker.

## Running Tests

The project includes both unit tests and integration tests:

### Running All Tests

```bash
poetry run pytest
```

This runs the complete test suite. Note that integration tests require a Stockfish binary to be available through either Option 1 or 2 above.

### Running Unit Tests Only

```bash
poetry run pytest -m "not integration"
```

This runs only the unit tests, where Stockfish interaction is mocked and no binary is required.

### Test Categories

- **Unit Tests**: Test individual components with mocked dependencies
- **Integration Tests**: Test actual Stockfish binary interaction
  - Require Stockfish binary (see setup options above)
  - Test real engine initialization and move calculation
  - Skip automatically if no binary is available
