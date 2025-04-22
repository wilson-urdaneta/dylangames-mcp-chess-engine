# Docker Usage Instructions

This document provides instructions for building and running the ChessPal MCP Engine service in Docker.

## Integration with Existing Orchestration

If you're using a separate repository for orchestrating multiple services:

1. **Build this image first**:
   ```bash
   # From this repository
   docker build -t chesspal-mcp-engine:latest .
   ```

2. **Add the volume and environment configuration to your existing docker-compose.yml**:
   ```yaml
   services:
     chesspal-engine:
       image: chesspal-mcp-engine:latest
       volumes:
         - stockfish-data:/app/data
       # Health check for monitoring and container orchestration
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
         interval: 30s
         timeout: 5s
         retries: 3
         start_period: 20s
       # Other configuration as needed

   volumes:
     stockfish-data:
   ```

## Local Development & Testing

The included docker-compose.yml is provided ONLY for isolated local development and testing. Use it when you need to:

1. Test changes to the ChessPal engine in isolation
2. Debug container issues without affecting other services
3. Run quick local tests during development

```bash
# Build and start the service for local testing
docker-compose up -d

# View logs
docker-compose logs -f
```

This will:
1. Build the Docker image if needed
2. Create a persistent volume for stockfish data
3. Start the service with the environment variables from `.env`

## Manual Docker Commands

If you prefer not to use Docker Compose, you can use these commands:

```bash
# Build the image
docker build -t chesspal-mcp-engine:latest .

# Create a persistent volume (once only)
docker volume create stockfish-data

# Run with the volume and env file
docker run -d --rm --name chesspal-mcp-engine \
  -p 9000:9000 \
  -p 8080:8080 \
  -v stockfish-data:/app/data \
  --env-file .env \
  chesspal-mcp-engine:latest
```

## Environment Variables

For development, create a `.env` file with these variables (this file is in .gitignore):

```
# Development settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# MCP Server settings
MCP_HOST=0.0.0.0
MCP_PORT=9000

# Health Server settings
HEALTH_HOST=0.0.0.0
HEALTH_PORT=8080
HEALTH_LOG_LEVEL=INFO

# Chess Engine specific settings
CHESSPAL_ENGINE_DEPTH=15
CHESSPAL_ENGINE_TIMEOUT_MS=3000
```

Note: Docker's env-file parser is very strict and doesn't handle comments or extra formatting. Format your .env file with KEY=value pairs only, with no inline comments.

## Health Monitoring

The service exposes two health-related endpoints:

1. `/health` - A comprehensive health check endpoint that:
   - Returns status code 200 when the service is fully operational
   - Returns status code 503 when the engine is not available
   - Includes status of the Stockfish engine
   - Returns a JSON object with detailed status information

2. `/ping` - A simple liveness check that:
   - Returns status code 200 when the service is running
   - Returns a simple {"ping": "pong"} response
   - Useful for basic liveness probes

These endpoints can be used with:
- Docker's built-in health checking
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Custom monitoring tools

Example Kubernetes probes:
```yaml
livenessProbe:
  httpGet:
    path: /ping
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 30
```

## First Run Behavior

On first run, the container will:
1. Check for the Stockfish engine binary
2. Initialize the engine with configured options
3. Start the MCP and health server services

## Connecting to the Service

The service will be available on two ports:
- MCP server: http://localhost:9000 (primary service endpoint)
- Health server: http://localhost:8080 (health monitoring)

From other containers:
- MCP server: http://chesspal-mcp-engine:9000
- Health server: http://chesspal-mcp-engine:8080

## Agent Service Connection

To connect the ChessPal MCP Agent to this engine service:

1. Create a Docker network: `docker network create chesspal-network`
2. Run both containers on this network:
   ```bash
   # Run both services on the same network
   docker-compose -f docker-compose.yml up -d --network chesspal-network
   ```
3. Configure the agent to use the container name as the engine URL:
   - Set `CHESSPAL_AGENT_ENGINE_URL=http://chesspal-engine:9000`

## Production Deployment

For production, consider:
1. Using a pre-built image with Stockfish already installed
2. Setting resource constraints appropriate for your workload:
   ```yaml
   services:
     chesspal-engine:
       image: chesspal-mcp-engine:latest
       deploy:
         resources:
           limits:
             cpus: '2'
             memory: 2G
           reservations:
             cpus: '1'
             memory: 1G
   ```
3. Setting up proper monitoring and restart policies
4. Configuring engine parameters for production performance
