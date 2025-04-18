# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install poetry
RUN pip install poetry

# Configure poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Copy dependency definitions
COPY pyproject.toml poetry.lock ./

# Install only production dependencies
RUN poetry install --no-root --only main --no-interaction --no-ansi

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

# Set environment variable for Stockfish path
ENV ENGINE_PATH="/usr/games/stockfish"

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY src/ /app/src/

# Set ownership of the application directory to the non-root user
RUN chown -R engineuser:engineuser /app

# Switch to non-root user
USER engineuser

# Expose the MCP port (configurable via MCP_PORT env var)
ENV MCP_PORT=9000
EXPOSE ${MCP_PORT}

# Set default command to run the engine with SSE transport
CMD ["python", "-m", "dylangames_mcp_chess_engine.main", "--transport", "sse"]
