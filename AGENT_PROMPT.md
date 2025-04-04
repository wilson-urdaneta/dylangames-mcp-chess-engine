# Chess Engine Module Implementation Guide

## Overview
This guide details how to implement a Chess Engine module for the PlayPal gaming platform using Stockfish, FastAPI, and FastMCP. The module provides a robust interface to the Stockfish chess engine, handling initialization, communication, and error cases effectively.

## Project Structure
```
dylangames-mcp-chess-engine/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastMCP server implementation
│   ├── engine_wrapper.py    # Stockfish engine wrapper
│   └── stockfish/           # Directory for packaged Stockfish binary
│       └── stockfish        # The binary (copied from system)
├── tests/
│   └── tests.py            # Unit tests
├── pyproject.toml          # Poetry dependency management
└── README.md              # Project documentation
```

## Key Components

### 1. Dependency Management (pyproject.toml)
- Use Poetry for dependency management
- Required dependencies:
  - FastAPI for API handling
  - FastMCP for PlayPal integration
  - pytest for testing
  - setuptools for binary packaging
- Example configuration:
```toml
[tool.poetry]
name = "chess_engine"
version = "0.1.0"
description = "Chess Engine module for PlayPal using Stockfish and FastMCP"
authors = ["PlayPal Team"]
packages = [{ include = "src" }]

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.109.2"
mcp = {version = "^1.2.0", extras = ["cli"]}
python-chess = "^1.999"
pytest = "^7.4.0"
setuptools = "^69.2.0"
```

### 2. Stockfish Engine Wrapper (src/engine_wrapper.py)

#### Important Learnings
1. **Process Communication**:
   - Use bytes mode (`text=False`) instead of text mode for process communication
   - Disable buffering (`bufsize=0`) to prevent hanging
   - Use `select` to check for available data before reading
   - Handle both stdout and stderr
   - Encode commands to bytes before sending
   - Decode responses with error handling

2. **UCI Protocol Handling**:
   - Send commands with newline: `command\n`
   - Wait for specific responses:
     - `uciok` after `uci` command
     - `readyok` after `isready` command
     - `bestmove` after `go` command
   - Use `startswith()` instead of exact matching for responses
   - Read all available output, don't stop at first match
   - Handle timeouts appropriately

3. **Error Handling**:
   - Create custom `StockfishError` exception
   - Handle process termination
   - Handle communication errors
   - Handle timeouts
   - Implement graceful shutdown

#### Implementation Details

1. **Global State**:
```python
_engine_process: Optional[subprocess.Popen] = None
_initialized = False
```

2. **Stockfish Path Handling**:
```python
def _get_stockfish_path() -> str:
    path = os.environ.get("STOCKFISH_PATH", "/default/path/to/stockfish")
    if not os.path.isfile(path):
        raise EnvironmentError("Stockfish binary not found")
    return path
```

3. **Process Communication**:
```python
def _send_command(command: str) -> None:
    _engine_process.stdin.write(f"{command}\n".encode())
    _engine_process.stdin.flush()

def _read_response(until: str = None, timeout: float = 2.0) -> List[str]:
    # Use select for non-blocking reads
    # Read all available output
    # Handle timeouts
    # Return list of response lines
```

4. **Engine Initialization**:
```python
def initialize_engine():
    # Start process with proper parameters
    # Send UCI command and wait for uciok
    # Set standard options
    # Verify engine is ready
```

5. **Move Generation**:
```python
def get_best_move(fen: str, move_history: List[str]) -> str:
    # Set position using FEN and move history
    # Request best move with timeout
    # Handle engine responses
    # Parse and return best move
```

### 3. FastMCP Server (src/main.py)

#### Important Notes
- Recent FastMCP API changes removed lifecycle methods
- Use direct initialization instead of decorators
- Handle engine initialization at startup
- Implement proper error handling and responses

#### Implementation Details
1. **Request/Response Models**:
```python
class ChessMoveRequest(BaseModel):
    fen: str
    move_history: List[str]

class ChessMoveResponse(BaseModel):
    best_move_uci: str
```

2. **Server Setup**:
```python
mcp = FastMCP("chess_engine")

@mcp.tool()
async def get_best_move_tool(request: ChessMoveRequest) -> ChessMoveResponse:
    try:
        best_move = get_best_move(request.fen, request.move_history)
        return ChessMoveResponse(best_move_uci=best_move)
    except StockfishError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4. Testing (tests/tests.py)

#### Key Testing Strategies
1. **Test Fixtures**:
   - Use session scope for engine initialization
   - Ensure engine is running before each test
   - Clean up properly after tests

2. **Test Cases**:
   - Engine initialization
   - Basic move generation
   - Invalid FEN handling
   - Position with move history
   - Error cases

#### Implementation Details
1. **Session Fixture**:
```python
@pytest.fixture(scope="session", autouse=True)
def engine():
    try:
        initialize_engine()
        yield
    finally:
        stop_engine()
```

2. **Per-test Fixture**:
```python
@pytest.fixture(autouse=True)
def ensure_engine_running():
    if not _initialized or not _engine_process or _engine_process.poll() is not None:
        initialize_engine()
```

3. **Test Cases**:
```python
def test_get_best_move_basic():
    fen = "starting position FEN"
    move = get_best_move(fen, [])
    assert valid_move(move)
```

## Common Pitfalls to Avoid
1. Don't use text mode for process communication
2. Don't stop reading after first response match
3. Don't forget to handle process termination
4. Don't use long thinking times in tests
5. Don't ignore engine cleanup
6. Don't assume engine state persists between tests

## Best Practices
1. Always verify engine is running before commands
2. Use appropriate timeouts for different operations
3. Implement robust error handling
4. Clean up resources properly
5. Validate engine responses
6. Use fixtures for test setup/teardown
7. Keep test execution time reasonable

## Testing Instructions
1. Install dependencies: `poetry install`
2. Run tests: `poetry run pytest tests/tests.py -v`
3. Verify all test cases pass
4. Check error handling works as expected

## Claude Desktop Integration

### Configuration Setup
The key to successful Claude Desktop integration is proper configuration in `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "chess_engine": {
      "command": "/opt/homebrew/bin/poetry",
      "args": [
        "run",
        "-C",
        "/path/to/project",
        "python",
        "-m",
        "src.main"
      ],
      "cwd": "/path/to/project",
      "transport": "stdio",
      "env": {
        "PYTHONPATH": "/path/to/project",
        "STOCKFISH_PATH": "/path/to/stockfish"
      }
    }
  }
}
```

Key configuration points:
1. Use `-C` flag with Poetry to specify project directory
2. Use Python module format (`-m src.main`) instead of file path
3. Set correct working directory in `cwd`
4. Configure environment variables directly in config
5. Use absolute paths throughout

### Environment Setup
The server needs proper environment validation:

```python
def setup_environment():
    """Setup and validate the environment."""
    project_root = Path(__file__).parent.parent.absolute()

    # Configure logging
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler(project_root / 'chess_engine.log')
        ]
    )

    # Verify critical paths and configurations
    verify_pyproject_toml(project_root)
    verify_stockfish_path()

    return logger
```

### Python Package Structure
Proper package structure is critical:

```
src/
├── __init__.py      # Makes src a package
├── main.py          # Entry point
└── engine_wrapper.py # Core functionality
```

Key points:
1. Use `src` layout for better package isolation
2. Keep `__init__.py` in all directories
3. Use relative imports within the package
4. Configure `pyproject.toml` correctly:

```toml
[tool.poetry]
packages = [
    { include = "src", from = "." }
]
```

### Logging and Debugging
Implement comprehensive logging:

1. Log to both stderr (for Claude Desktop) and file:
```python
handlers=[
    logging.StreamHandler(sys.stderr),
    logging.FileHandler('chess_engine.log')
]
```

2. Log critical information:
- Project root directory
- Current working directory
- PYTHONPATH
- Poetry environment status
- Stockfish path
- Server startup/shutdown events
- All chess moves and responses

### Error Handling
Implement robust error handling:

1. Environment validation
2. Path verification
3. Process management
4. Communication errors
5. Chess engine errors

Example:
```python
try:
    initialize_engine()
except StockfishError as e:
    logger.error(f"Engine error: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### Remote Server Deployment
For remote server deployment:

1. Logging Configuration:
   - Use rotating file handler
   - Configure log levels
   - Set up log aggregation
   - Monitor stderr output

2. Process Management:
   - Use systemd service
   - Configure auto-restart
   - Set up health checks

3. Environment Setup:
   - Use environment files
   - Configure paths correctly
   - Set up monitoring

### Best Practices

1. Package Management:
   - Use Poetry for dependency management
   - Pin dependency versions
   - Use virtual environments

2. Code Organization:
   - Follow src layout
   - Use proper imports
   - Implement clear separation of concerns

3. Error Handling:
   - Implement comprehensive error handling
   - Use custom exceptions
   - Provide clear error messages

4. Logging:
   - Log all critical operations
   - Use appropriate log levels
   - Implement structured logging

5. Testing:
   - Write comprehensive tests
   - Use pytest fixtures
   - Test error conditions

6. Documentation:
   - Document all functions
   - Provide usage examples
   - Include deployment guides

### Common Issues and Solutions

1. Poetry Path Issues:
   - Use `-C` flag to specify project directory
   - Set PYTHONPATH correctly
   - Use module imports

2. Stockfish Integration:
   - Verify binary path
   - Handle process communication
   - Implement timeout handling

3. Claude Desktop Integration:
   - Configure transport correctly
   - Set up environment variables
   - Handle logging properly

This implementation provides a robust and reliable chess engine module that can be easily integrated into the PlayPal gaming platform.