"""Graceful shutdown utilities for the chess engine service."""

import atexit
import logging
import signal
import sys
from typing import Generic, Protocol, Set, TypeVar

logger = logging.getLogger(__name__)


class Stoppable(Protocol):
    """Protocol for objects that can be stopped."""

    def stop(self) -> None:
        """Stop the object."""
        pass


T = TypeVar("T", bound=Stoppable)


class EngineRegistry(Generic[T]):
    """Registry to track and manage engine processes.

    This registry keeps track of all running engine instances and provides
    a centralized way to shut them all down gracefully when needed.
    """

    _engines: Set[T] = set()

    @classmethod
    def register(cls, engine: T) -> None:
        """Register an engine instance with the registry.

        Args:
            engine: The engine instance to register
        """
        logger.debug(f"Registering engine instance: {id(engine)}")
        cls._engines.add(engine)

    @classmethod
    def unregister(cls, engine: T) -> None:
        """Unregister an engine instance from the registry.

        Args:
            engine: The engine instance to unregister
        """
        if engine in cls._engines:
            logger.debug(f"Unregistering engine instance: {id(engine)}")
            cls._engines.remove(engine)

    @classmethod
    def shutdown_all(cls) -> None:
        """Stop all registered engines."""
        engine_count = len(cls._engines)
        logger.info(f"Shutting down {engine_count} engine instances")
        for engine in list(cls._engines):
            try:
                logger.debug(f"Stopping engine instance: {id(engine)}")
                engine.stop()
            except Exception as e:
                logger.error(
                    f"Error stopping engine instance {id(engine)}: {e}"
                )


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
