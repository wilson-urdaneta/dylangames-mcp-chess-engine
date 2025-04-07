# Chess Engine Binaries

This directory contains the chess engine binaries used by the ChessPal module. The directory is structured to support multiple engines, versions, and operating systems.

## Directory Structure

```
engines/
├── stockfish/              # Stockfish engine
│   ├── 17.1/              # Version 17.1
│   │   ├── linux/         # Linux binaries
│   │   ├── windows/       # Windows binaries
│   │   └── macos/         # macOS binaries
│   └── README.md          # Engine-specific documentation
└── README.md              # This file
```

## Usage

### Adding New Engines

1. Create a new directory for your engine under `engines/`
2. Create version-specific subdirectories
3. Add OS-specific subdirectories
4. Place the appropriate binary files in the OS directories
5. Create an engine-specific README.md with:
   - Engine version information
   - Binary compatibility notes
   - Any special configuration requirements

### Binary Naming Convention

- Linux: `stockfish`
- Windows: `stockfish.exe`
- macOS: `stockfish`

### Important Notes

1. Binary files are not tracked in git (see .gitignore)
2. Each engine version should have its own README.md
3. Binaries should be compatible with the target OS
4. Version numbers should follow semantic versioning

## Development

When developing locally:
1. Download the appropriate binary for your OS
2. Place it in the correct version/OS directory
3. Ensure the binary has execute permissions (Unix-like systems)
4. Test the binary with the engine wrapper

## CI/CD

The CI/CD pipeline will:
1. Install Stockfish on the CI environment
2. Use the system-installed binary for testing
3. Package the appropriate binary for distribution

## Troubleshooting

If you encounter issues:
1. Verify the binary exists in the correct directory
2. Check file permissions
3. Ensure the binary is compatible with your OS
4. Verify the binary version matches the expected version
