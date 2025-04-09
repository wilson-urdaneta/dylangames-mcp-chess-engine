# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-04-09

### Added

* Initial public release of `chesspal-mcp-engine`.
* Implemented MCP server using `FastMCP` exposing a Stockfish chess engine.
* Added `get_best_move_tool` for calculating the best move given a FEN position and optional move history.
* Implemented chess engine process lifecycle management using `FastMCP`'s `lifespan` context manager.
* Added support for SSE transport using `mcp.run(transport='sse')` (default when run via `python -m`).
* Added support for stdio transport using `mcp.run(transport='stdio')` selectable via the `--transport stdio` command-line flag.
* Configured server host and port via `MCP_HOST` and `MCP_PORT` environment variables (defaults to 127.0.0.1:8001).
* Added integration test (`test_integration.py`) using `subprocess` to run the server and `mcp.client.sse.sse_client` / `mcp.ClientSession` for SSE transport verification.
* Added unit tests (`test_engine_wrapper.py`) for the Stockfish wrapper logic.
* Configured detailed logging to console (stderr) and rotating files (`logs/`).
* Set up project structure using `src/` layout and Poetry.
* Added basic CI/CD workflow using GitHub Actions (lint, test, build, release, optional PyPI publish).
* Included documentation (`README.md`, `.env.example`, `CHANGELOG.md`).
* Configured code quality tools (Black, isort, flake8).
