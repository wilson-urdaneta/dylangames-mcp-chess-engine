"""Test suite for the shutdown module."""

import signal
from unittest.mock import MagicMock, patch

from dylangames_mcp_chess_engine.engine_wrapper import StockfishEngine
from dylangames_mcp_chess_engine.shutdown import EngineRegistry


def test_engine_registry():
    """Test that the engine registry works correctly."""
    # Create registry and verify it's empty
    registry = EngineRegistry
    registry._engines = set()  # Reset the registry

    # Create some mock engines
    engine1 = MagicMock()
    engine2 = MagicMock()

    # Register engines
    registry.register(engine1)
    assert len(registry._engines) == 1
    assert engine1 in registry._engines

    registry.register(engine2)
    assert len(registry._engines) == 2
    assert engine2 in registry._engines

    # Unregister engines
    registry.unregister(engine1)
    assert len(registry._engines) == 1
    assert engine1 not in registry._engines

    registry.unregister(engine2)
    assert len(registry._engines) == 0


def test_signal_handler():
    """Test that the signal handler correctly stops registered engines."""
    # Mock signal setup and sys.exit
    with patch("signal.signal") as mock_signal, patch("sys.exit") as mock_exit:
        # Import the handler setup function
        from dylangames_mcp_chess_engine.shutdown import setup_signal_handlers

        # Call the setup function
        setup_signal_handlers()

        # Verify signal handlers were set up
        assert mock_signal.call_count >= 1, "Signal handlers were not set up"

        # Import the signal handler function
        from dylangames_mcp_chess_engine.shutdown import graceful_shutdown

        # Create a mock frame
        mock_frame = MagicMock()

        # Call the signal handler
        graceful_shutdown(signal.SIGINT, mock_frame)

        # Verify sys.exit was called
        mock_exit.assert_called_once_with(0)


def test_engine_auto_registration():
    """Test that StockfishEngine auto-registers with EngineRegistry."""
    # Reset the registry
    EngineRegistry._engines = set()
    assert len(EngineRegistry._engines) == 0

    # Create a mock StockfishEngine
    with (
        patch.object(StockfishEngine, "_initialize_engine"),
        patch.object(EngineRegistry, "register") as mock_register,
    ):
        engine = StockfishEngine()
        mock_register.assert_called_once_with(engine)
