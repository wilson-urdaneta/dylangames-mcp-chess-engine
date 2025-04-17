# Chess Engine Binaries

This directory contains the chess engine binaries used by the ChessPal module. The directory is structured to support multiple engines, versions, and operating systems.

## Directory Structure

```
engines/
├── stockfish/              # Stockfish engine
│   ├── 17.1/              # Version 17.1
│   │   ├── linux/         # Linux binaries
│   │   │   └── stockfish  # Linux executable
│   │   ├── windows/       # Windows binaries
│   │   │   └── stockfish.exe
│   │   └── macos/         # macOS binaries
│   │       └── stockfish  # macOS executable
│   └── README.md          # Engine-specific documentation
└── README.md              # This file
```

## Stockfish Setup

### Binary Requirements

1. **Version**: Stockfish 17.1 (recommended) or compatible version
2. **Permissions**: Must be executable (`chmod +x` on Unix systems)
3. **Architecture**: Must match your system architecture (x86_64, ARM64, etc.)

### Installation Methods

1. **Download Official Binary** (Recommended):
   - Visit [Stockfish Releases](https://github.com/official-stockfish/Stockfish/releases)
   - Download the appropriate binary for your system
   - Place in the correct directory structure (see below)

2. **Package Manager**:
   ```bash
   # Ubuntu/Debian
   sudo apt install stockfish

   # macOS
   brew install stockfish

   # Windows (using Chocolatey)
   choco install stockfish
   ```

3. **Build from Source**:
   - Clone [Stockfish repository](https://github.com/official-stockfish/Stockfish)
   - Follow build instructions in their README
   - Place compiled binary in appropriate directory

### Directory Placement

1. **Determine Your OS Directory**:
   - Linux: `engines/stockfish/17.1/linux/`
   - macOS: `engines/stockfish/17.1/macos/`
   - Windows: `engines/stockfish/17.1/windows/`

2. **Binary Naming**:
   - Linux/macOS: `stockfish`
   - Windows: `stockfish.exe`

3. **Set Permissions** (Unix systems):
   ```bash
   chmod +x engines/stockfish/17.1/<os>/stockfish
   ```

### Environment Variables

If not using `ENGINE_PATH`, set:
```bash
export ENGINE_OS=linux    # or macos, windows
export ENGINE_VERSION=17.1  # optional, defaults to 17.1
```

## Troubleshooting

1. **Binary Not Found**:
   - Verify correct directory structure
   - Check file name matches convention
   - Ensure `ENGINE_OS` matches your system

2. **Permission Denied**:
   - Check file permissions (`ls -l`)
   - Run `chmod +x` on Unix systems
   - Verify binary matches system architecture

3. **Version Mismatch**:
   - Check `ENGINE_VERSION` environment variable
   - Verify binary version in correct directory

4. **Integration Test Failures**:
   - Confirm binary is executable
   - Check engine initialization logs
   - Verify binary compatibility with your system

## Development Notes

- Binary files are not tracked in git
- Each engine version should have its own documentation
- Test binaries before committing directory structure
- Keep binary versions consistent with project requirements

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
