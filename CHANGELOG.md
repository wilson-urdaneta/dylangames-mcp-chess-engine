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

## [0.2.0] - 2025-04-10

### Added

* **New Tools:** Added MCP tools using `python-chess` for core chess rule logic:
    * `validate_move_tool`: Validates if a move is legal for a given FEN position.
    * `get_legal_moves_tool`: Returns all legal moves for a given FEN position.
    * `get_game_status_tool`: Determines game status (in progress, checkmate, stalemate, draw) for a FEN position.
* **Configuration Management:** Added `pydantic-settings` and `python-dotenv` dependencies. Introduced `src/dylangames_mcp_chess_engine/config.py` with a `Settings` class to manage all environment variables centrally. Added `.env.example`.
* **Testing:**
    * Added `tests/test_config.py` for the new `Settings` class.
    * Added unit tests for the new chess logic tools (`validate_move_tool`, `get_legal_moves_tool`, `get_game_status_tool`) in `tests/test_main_engine.py`.
    * Added `@pytest.mark.integration` marker for tests requiring the actual Stockfish binary (`tests/test_integration.py`).
    * Registered `integration` marker in `pyproject.toml`.

### Changed

* **Configuration Usage:** Refactored `main.py` and `engine_wrapper.py` (`_get_engine_path`) to import and use the central `settings` object instead of direct `os.environ.get` calls.
* **Error Handling:** Refactored all MCP tools (`get_best_move_tool`, `validate_move_tool`, etc.) in `main.py` to return structured JSON dictionaries (`{"result": ...}` on success, `{"error": "..."}` on operational errors) instead of raising `HTTPException`. Unexpected internal errors now return `{"error": "Internal server error"}` after logging.
* **Unit Testing:** Refactored unit tests (`test_engine_wrapper.py` and tests for `get_best_move_tool` in `test_main_engine.py`) to mock `subprocess.Popen` and Stockfish process interactions, removing the dependency on the actual binary for these tests. Updated assertions to match the new dictionary-based error returns.
* **Documentation:** Updated `README.md` significantly with:
    * Clear options for Stockfish binary setup (`ENGINE_PATH`, `engines/` directory + `ENGINE_OS`, package managers).
    * Instructions for running all tests vs. only unit tests (`pytest -m "not integration"`).
    * Reference to `engines/README.md` for directory structure.
* **Dependencies:** Added `python-chess` as a core dependency.

### Fixed

* Corrected fallback logic in `engine_wrapper._get_engine_path`: Removed the default OS ("linux") and now requires the `ENGINE_OS` environment variable to be explicitly set if `ENGINE_PATH` is not used.
