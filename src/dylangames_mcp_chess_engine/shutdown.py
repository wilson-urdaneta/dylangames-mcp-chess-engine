"""Graceful shutdown utilities for the chess engine service."""

import atexit
import logging
import signal
import sys
from typing import Set, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EngineRegistry:
    """Registry to track and manage engine processes.
    
    This registry keeps track of all running engine instances and provides
    a centralized way to shut them all down gracefully when needed.
    """
    
    _instances: Set[T] = set()
    
    @classmethod
    def register(cls, engine: T) -> None:
        """Register an engine instance with the registry.
        
        Args:
            engine: The engine instance to register
        """
        logger.debug(f"Registering engine instance: {id(engine)}")
        cls._instances.add(engine)
        
    @classmethod
    def unregister(cls, engine: T) -> None:
        """Unregister an engine instance from the registry.
        
        Args:
            engine: The engine instance to unregister
        """
        if engine in cls._instances:
            logger.debug(f"Unregistering engine instance: {id(engine)}")
            cls._instances.remove(engine)
    
    @classmethod
    def shutdown_all(cls) -> None:
        """Stop all registered engines."""
        logger.info(f"Shutting down {len(cls._instances)} engine instances")
        for engine in list(cls._instances):
            try:
                logger.debug(f"Stopping engine instance: {id(engine)}")
                engine.stop()
            except Exception as e:
                logger.error(f"Error stopping engine instance {id(engine)}: {e}")


def graceful_shutdown(signum, frame) -> None:
    """Handle shutdown signals gracefully.
    
    This function is called when a termination signal is received.
    It ensures all engine processes are stopped cleanly.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    signal_name = signal.Signals(signum).name
    logger.info(f"Received {signal_name} signal, shutting down gracefully...")
    
    # Shutdown all registered engines
    EngineRegistry.shutdown_all()
    
    logger.info("Graceful shutdown complete")
    sys.exit(0)


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown.
    
    This function registers handlers for common termination signals
    to ensure the application shuts down gracefully.
    """
    logger.info("Setting up signal handlers for graceful shutdown")
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    # Register shutdown_all with atexit to ensure it's called on normal exit
    atexit.register(EngineRegistry.shutdown_all)
    logger.debug("Signal handlers and atexit hooks registered") 