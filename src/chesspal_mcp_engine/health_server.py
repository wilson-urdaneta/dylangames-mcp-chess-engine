"""Health server for the ChessPal Engine."""

from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse

from .logging_config import get_logger, setup_logging

logger = get_logger(__name__)

# Global reference to engine for health checks
_engine: Optional[Any] = None


def create_health_api(title: str = "ChessPal MCP Engine Health API") -> FastAPI:
    """Create a FastAPI app for health endpoints.

    Args:
        title: Title for the FastAPI app

    Returns:
        FastAPI app for health endpoints
    """
    health_api = FastAPI(title=title)

    @health_api.get("/health")
    async def health_check() -> JSONResponse:
        """Health check endpoint for the ChessPal MCP Engine."""
        status_data: Dict[str, Any] = {
            "status": "ok",
            "service": "chesspal-mcp-engine",
            "version": "1.0.0",
        }

        # Check if engine is ready if available
        engine_ready = False
        if _engine is not None:
            try:
                engine_ready = _engine.is_initialized()
            except Exception as e:
                logger.error(f"Failed to check engine: {e}")
                engine_ready = False
        else:
            logger.warning("Engine not available for health check")

        # Add dependency statuses
        status_data["dependencies"] = {
            "engine": "ok" if engine_ready else "error",
        }

        # Overall status is only ok if all dependencies are ok
        dependencies = status_data["dependencies"]
        if not all(v == "ok" for v in dependencies.values()):
            status_data["status"] = "degraded"
            return JSONResponse(status_data, status_code=503)

        return JSONResponse(status_data, status_code=200)

    @health_api.get("/ping")
    async def ping() -> JSONResponse:
        """Simple liveness check endpoint."""
        return JSONResponse({"ping": "pong"}, status_code=200)

    return health_api


def set_engine(engine: Any) -> None:
    """Set the engine instance for health checks.

    Args:
        engine: Engine instance
    """
    global _engine
    _engine = engine


def run_health_server(host: str, port: int, log_level: str = "info") -> None:
    """Run the health server.

    Args:
        host: Host to bind to
        port: Port to bind to
        log_level: Logging level
    """
    # Configure logging
    setup_logging(log_level.upper())

    # Create and run the health API
    health_api = create_health_api()
    logger.info(f"Starting health server on {host}:{port}")
    uvicorn.run(health_api, host=host, port=port, log_level=log_level)


# This function needs to be at module level for multiprocessing
def start_health_server(host: str, port: int, log_level: str) -> None:
    """Start the health server in a separate process.

    Args:
        host: Host to bind to
        port: Port to bind to
        log_level: Logging level
    """
    run_health_server(host, port, log_level)
