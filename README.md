# PlayPal Chess Engine Module

A robust chess engine module for the PlayPal gaming platform, powered by Stockfish and FastMCP. This module provides a reliable interface to the Stockfish chess engine through a FastAPI server, making it easy to integrate chess functionality into your applications.

## Features

- Robust Stockfish engine integration with proper process management
- FastMCP server for easy integration with PlayPal platform
- UCI protocol implementation for chess move generation
- Comprehensive test suite
- Error handling and recovery mechanisms
- Support for FEN positions and move history

## Prerequisites

- Python 3.10 or higher
- Poetry for dependency management
- Stockfish chess engine binary (version 17.1 recommended)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dylangames-mcp-chess-engine.git
cd dylangames-mcp-chess-engine
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up the Stockfish binary:
   - Download Stockfish 17.1 from the official website
   - Place the binary in `src/stockfish/` directory
   - Make it executable: `chmod +x src/stockfish/stockfish`
   - Set the environment variable: `export STOCKFISH_PATH=/path/to/stockfish`

## Usage

### Starting the Server

1. Activate the Poetry environment:
```bash
poetry shell
```

2. Run the FastMCP server:
```bash
python -m src.main
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

### Using with Claude Desktop

1. Install Claude Desktop and set up your API key
2. Create a new conversation
3. Use the following prompt template:

```
I want to use the chess engine module. Here's my code:

[Your code here]

Please help me:
1. Set up the connection to the chess engine
2. Generate moves for my chess position
3. Handle any errors that occur
```

Example interaction:
```python
# Example code to share with Claude
from mcp import FastMCP

async def get_chess_move(fen: str, history: List[str]) -> str:
    mcp = FastMCP("chess_engine")
    response = await mcp.get_best_move_tool({
        "fen": fen,
        "move_history": history
    })
    return response.best_move_uci

# Claude can help you use this code and handle errors
```

## Development

### Project Structure

```
dylangames-mcp-chess-engine/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # FastMCP server
│   ├── engine_wrapper.py  # Stockfish wrapper
│   └── stockfish/         # Stockfish binary
├── tests/                 # Test suite
│   └── tests.py
├── pyproject.toml        # Dependencies
├── README.md            # This file
└── AGENT_PROMPT.md      # Detailed implementation guide
```

### Running Tests

```bash
poetry run pytest tests/tests.py -v
```

### Code Quality

The codebase follows these standards:
- Type hints for all functions
- Comprehensive error handling
- Detailed docstrings
- PEP 8 compliance
- Proper resource management

### Version Control

1. Initialize git repository (if not already done):
```bash
git init
```

2. Add files to version control:
```bash
git add .
git commit -m "Initial commit: Chess engine module implementation"
```

3. Push to remote repository:
```bash
git remote add origin https://github.com/yourusername/dylangames-mcp-chess-engine.git
git push -u origin main
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Stockfish Chess Engine team
- FastMCP developers
- PlayPal gaming platform team

## Support

For issues and feature requests, please use the GitHub issue tracker.