# ChessPal - Chess Engine Module

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json)](https://python-poetry.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI/CD](https://github.com/wilson-urdaneta/dylangames-mcp-chess-engine/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/wilson-urdaneta/dylangames-mcp-chess-engine/actions)

A robust chess engine module for the ChessPal gaming platform, powered by Stockfish and FastMCP. This module provides a reliable interface to the Stockfish chess engine through a FastAPI server, making it easy to integrate chess functionality into your applications.

## Features

- Robust Stockfish engine integration with proper process management
- FastMCP server for easy integration with ChessPal platform
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

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dylangames-mcp-chess-engine.git
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

## Usage

### Starting the Server

You can run the server in two ways:

1. Using Poetry run (recommended):
```bash
poetry run chess-engine
```

2. Or activate the Poetry shell first:
```bash
poetry shell
python -m dylangames_mcp_chess_engine.main
```

The server will start and listen for incoming requests.

### API Endpoints

The module exposes the following endpoint through FastMCP:

- `get_best_move_tool`: Get the best move for a given chess position

Example request:
```python
from mcp import FastMCP

mcp = FastMCP("chess_engine")

response = await mcp.get_best_move_tool({
    "fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "move_history": []
})

print(response.best_move_uci)  # e.g., "e2e4"
```

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
```

4. Run code quality tools:
```bash
poetry run black .
poetry run isort .
poetry run flake8
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
