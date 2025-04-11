"""Test graceful shutdown functionality."""

import os
import signal
import time
from unittest.mock import Mock, patch

import pytest

from dylangames_mcp_chess_engine.engine_wrapper import StockfishEngine
from dylangames_mcp_chess_engine.shutdown import EngineRegistry, setup_signal_handlers


def test_engine_registry():
    """Test the engine registry can track and shutdown engines."""
    # Create mock engines
    mock_engine1 = Mock(spec=StockfishEngine)
    mock_engine2 = Mock(spec=StockfishEngine)
    
    # Register engines
    EngineRegistry.register(mock_engine1)
    EngineRegistry.register(mock_engine2)
    
    # Verify they are registered
    assert mock_engine1 in EngineRegistry._instances
    assert mock_engine2 in EngineRegistry._instances
    
    # Test shutdown all
    EngineRegistry.shutdown_all()
    
    # Verify all engines were stopped
    mock_engine1.stop.assert_called_once()
    mock_engine2.stop.assert_called_once()
    
    # Test unregister
    EngineRegistry.unregister(mock_engine1)
    assert mock_engine1 not in EngineRegistry._instances
    assert mock_engine2 in EngineRegistry._instances


def test_signal_handler():
    """Test signal handler calls shutdown_all."""
    with patch('dylangames_mcp_chess_engine.shutdown.EngineRegistry.shutdown_all') as mock_shutdown:
        with patch('sys.exit') as mock_exit:
            # Create a mock frame for signal handler
            mock_frame = Mock()
            
            # Import the signal handler function
            from dylangames_mcp_chess_engine.shutdown import graceful_shutdown
            
            # Call the signal handler
            graceful_shutdown(signal.SIGINT, mock_frame)
            
            # Verify it called shutdown_all and exit
            mock_shutdown.assert_called_once()
            mock_exit.assert_called_once_with(0)


@pytest.mark.integration
def test_engine_auto_registration():
    """Test that StockfishEngine instances are automatically registered."""
    # Clear the registry first
    EngineRegistry._instances = set()
    
    # Create a real engine (wrapped in try to ensure cleanup)
    engine = None
    try:
        engine = StockfishEngine()
        
        # Verify it was registered
        assert engine in EngineRegistry._instances
        
    except Exception as e:
        pytest.skip(f"Could not create engine: {e}")
    finally:
        # Ensure engine is stopped
        if engine:
            engine.stop()
            
    # Verify it was unregistered on stop
    assert engine not in EngineRegistry._instances 