# Stockfish Engine

This directory contains Stockfish chess engine binaries. Stockfish is a powerful open-source chess engine that supports the UCI protocol.

## Version Information

Current version: 17.1
- Released: January 2024
- UCI protocol support: Yes
- Multi-threading: Yes
- NNUE support: Yes

## Binary Compatibility

### Linux
- Binary name: `stockfish`
- Architecture: x86_64
- Dependencies: None
- Required permissions: Execute (chmod +x)

### Windows
- Binary name: `stockfish.exe`
- Architecture: x64
- Dependencies: None
- UAC requirements: None

### macOS
- Binary name: `stockfish`
- Architecture: x86_64, arm64
- Dependencies: None
- Required permissions: Execute (chmod +x)

## Configuration

Default configuration:
- Hash: 16MB
- Threads: 1
- MultiPV: 1
- Skill Level: 20 (maximum)

## UCI Options

Key UCI options supported:
- Hash: Memory hash table size
- Threads: Number of threads
- MultiPV: Number of principal variations
- Skill Level: Engine strength (0-20)
- Ponder: Think on opponent's time
- UCI_ShowCurrLine: Show current line
- UCI_LimitStrength: Limit engine strength
- UCI_Elo: Set Elo rating

## Troubleshooting

Common issues:
1. Binary not found
   - Check file permissions
   - Verify binary exists in correct OS directory
   - Ensure binary name matches OS convention

2. Binary not executable
   - Run `chmod +x stockfish` on Unix-like systems
   - Verify Windows binary is not blocked

3. Version mismatch
   - Ensure binary version matches expected version
   - Check engine wrapper compatibility
