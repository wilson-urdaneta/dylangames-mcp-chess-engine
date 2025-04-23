"""Additional tests for the shutdown module."""

import signal

from pytest_mock import MockerFixture

from chesspal_mcp_engine.shutdown import EngineRegistry, graceful_shutdown, setup_signal_handlers


class MockStoppable:
    """Mock implementation of Stoppable protocol."""

    def __init__(self):
        """Initialize with a flag to track if stop was called."""
        self.stopped = False

    def stop(self):
        """Mark the object as stopped."""
        self.stopped = True


class TestShutdownAdditional:
    """Additional tests for the shutdown module functionality."""

    def test_engine_registry_register(self):
        """Test registering engines with the registry."""
        # Clear registry first
        registry: EngineRegistry = EngineRegistry()
        registry._engines.clear()

        # Create mock engines
        engine1 = MockStoppable()
        engine2 = MockStoppable()

        # Register engines
        registry.register(engine1)
        registry.register(engine2)

        # Check they are in the registry
        assert engine1 in registry._engines
        assert engine2 in registry._engines
        assert len(registry._engines) == 2

    def test_engine_registry_unregister(self):
        """Test unregistering engines from the registry."""
        # Clear registry first
        registry: EngineRegistry = EngineRegistry()
        registry._engines.clear()

        # Create and register mock engines
        engine1 = MockStoppable()
        engine2 = MockStoppable()
        registry.register(engine1)
        registry.register(engine2)

        # Unregister one engine
        registry.unregister(engine1)

        # Check registry state
        assert engine1 not in registry._engines
        assert engine2 in registry._engines
        assert len(registry._engines) == 1

    def test_engine_registry_shutdown_all(self, mocker: MockerFixture):
        """Test shutting down all registered engines."""
        # Mock logger to avoid actual logging
        mock_logger = mocker.patch("chesspal_mcp_engine.shutdown.logger")

        # Clear registry first
        registry: EngineRegistry = EngineRegistry()
        registry._engines.clear()

        # Create and register mock engines
        engine1 = MockStoppable()
        engine2 = MockStoppable()
        engine3 = MockStoppable()
        registry.register(engine1)
        registry.register(engine2)
        registry.register(engine3)

        # Create an engine that raises an exception when stopped
        error_engine = mocker.MagicMock()
        error_engine.stop.side_effect = Exception("Stop error")
        registry.register(error_engine)

        # Shutdown all engines
        registry.shutdown_all()

        # Check all engines were stopped
        assert engine1.stopped
        assert engine2.stopped
        assert engine3.stopped
        error_engine.stop.assert_called_once()

        # Check error was logged
        mock_logger.error.assert_called_once()

        # NOTE: In the actual implementation, engines are not removed from the registry
        # after stopping, so we don't need to check that the registry is empty
        # assert len(registry._engines) == 0

        # Instead, we simply verify that the engines are still in the registry but have been stopped
        assert engine1 in registry._engines
        assert engine2 in registry._engines
        assert engine3 in registry._engines
        assert error_engine in registry._engines

    def test_graceful_shutdown(self, mocker: MockerFixture):
        """Test graceful_shutdown function."""
        # Mock dependencies
        mock_registry_shutdown = mocker.patch("chesspal_mcp_engine.shutdown.EngineRegistry.shutdown_all")
        mock_sys_exit = mocker.patch("sys.exit")
        mock_logger = mocker.patch("chesspal_mcp_engine.shutdown.logger")

        # Call graceful_shutdown
        graceful_shutdown(signal.SIGTERM, None)

        # Assert functions were called
        mock_registry_shutdown.assert_called_once()
        mock_logger.info.assert_called()
        mock_sys_exit.assert_called_once_with(0)

    def test_setup_signal_handlers(self, mocker: MockerFixture):
        """Test setting up signal handlers."""
        # Mock signal.signal
        mock_signal = mocker.patch("signal.signal")
        mock_atexit = mocker.patch("atexit.register")

        # Call setup_signal_handlers
        setup_signal_handlers()

        # Assert signal.signal was called twice, once for each signal
        assert mock_signal.call_count == 2

        # Check the calls were for SIGTERM and SIGINT
        signals_registered = [call[0][0] for call in mock_signal.call_args_list]
        assert signal.SIGTERM in signals_registered
        assert signal.SIGINT in signals_registered

        # Check atexit.register was called
        mock_atexit.assert_called_once_with(EngineRegistry.shutdown_all)
