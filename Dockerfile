# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install poetry
RUN pip install --no-cache-dir poetry

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy project files needed for install
COPY pyproject.toml poetry.lock ./
COPY README.md ./
COPY src/ /app/src/

# Install dependencies first (faster layer caching)
RUN poetry install --no-root --only main --no-interaction --no-ansi

# Install the project itself (including scripts)
RUN poetry install --no-interaction --no-ansi

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Create a non-root user
RUN groupadd -r engineuser && useradd -r -g engineuser engineuser

# Install Stockfish - required by the engine
RUN apt-get update && \
    apt-get install -y --no-install-recommends stockfish && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set environment variable for Stockfish path (can be overridden)
ENV ENGINE_PATH="/usr/games/stockfish"

# Copy installed dependencies AND scripts from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code (needed for runtime imports)
COPY src/ /app/src/

# Set ownership of the application directory to the non-root user
RUN chown -R engineuser:engineuser /app

# Switch to non-root user
USER engineuser

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9000

# Expose the MCP port (configurable via MCP_PORT env var)
# Default set in config.py, but can be overridden
EXPOSE ${MCP_PORT}

# Use the standardized script entry point via ENTRYPOINT
# Allows passing arguments like --transport via docker run
ENTRYPOINT ["chesspal-mcp-engine"]
# Default arguments (can be overridden)
CMD []
