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

This implementation provides a robust and reliable chess engine module that can be easily integrated into the PlayPal gaming platform.