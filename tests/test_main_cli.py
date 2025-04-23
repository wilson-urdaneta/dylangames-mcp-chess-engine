"""Tests for the main_cli function in the main module."""

import pytest
from pytest_mock import MockerFixture

import chesspal_mcp_engine.main as main_module
from chesspal_mcp_engine.engine_wrapper import StockfishEngine, StockfishError


class TestMainCLI:
    """Tests for the main_cli function."""

    def test_setup_environment_success(self, mocker: MockerFixture):
        """Test setup_environment when engine initialization succeeds."""
        # Mock dependencies
        mock_stockfish = mocker.patch.object(main_module, "StockfishEngine", autospec=True)
        mock_setup_signal = mocker.patch.object(main_module, "setup_signal_handlers", autospec=True)
        mock_set_engine = mocker.patch.object(main_module, "set_engine", autospec=True)

        # Call the function
        main_module.setup_environment()

        # Assert function calls
        mock_setup_signal.assert_called_once()
        mock_stockfish.assert_called_once()
        mock_set_engine.assert_called_once()

    def test_setup_environment_stockfish_error(self, mocker: MockerFixture):
        """Test setup_environment when StockfishError occurs."""
        # Mock dependencies
        mock_engine = mocker.patch.object(main_module, "StockfishEngine", side_effect=StockfishError("Test error"))
        mock_setup_signal = mocker.patch.object(main_module, "setup_signal_handlers", autospec=True)

        # Call the function
        main_module.setup_environment()

        # Assert function calls
        mock_setup_signal.assert_called_once()
        mock_engine.assert_called_once()

    def test_setup_environment_unexpected_error(self, mocker: MockerFixture):
        """Test setup_environment when an unexpected error occurs."""
        # Mock dependencies
        mock_engine = mocker.patch.object(main_module, "StockfishEngine", side_effect=RuntimeError("Unexpected"))
        mock_setup_signal = mocker.patch.object(main_module, "setup_signal_handlers", autospec=True)

        # Call the function
        main_module.setup_environment()

        # Assert function calls
        mock_setup_signal.assert_called_once()
        mock_engine.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_create_engine(self, mocker: MockerFixture):
        """Test lifespan when engine needs to be created."""
        # Mock dependencies
        mock_engine = mocker.MagicMock(spec=StockfishEngine)
        mock_stockfish = mocker.patch.object(main_module, "StockfishEngine", return_value=mock_engine)
        mock_set_engine = mocker.patch.object(main_module, "set_engine")

        # Set _engine to None
        mocker.patch.object(main_module, "_engine", None)

        # Mock FastMCP server
        mock_server = mocker.MagicMock()

        # Create a context manager for testing
        lifespan_cm = main_module.lifespan(mock_server)

        # Test entering the context
        await lifespan_cm.__aenter__()

        # Assert function calls
        mock_stockfish.assert_called_once()
        mock_set_engine.assert_called_once_with(mock_engine)

        # Test exiting the context
        await lifespan_cm.__aexit__(None, None, None)

        # Assert engine was stopped
        mock_engine.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifespan_reuse_engine(self, mocker: MockerFixture):
        """Test lifespan when engine already exists."""
        # Mock existing engine
        existing_engine = mocker.MagicMock(spec=StockfishEngine)
        mocker.patch.object(main_module, "_engine", existing_engine)

        # Mock FastMCP server
        mock_server = mocker.MagicMock()

        # Create a context manager for testing
        lifespan_cm = main_module.lifespan(mock_server)

        # Test entering the context
        await lifespan_cm.__aenter__()

        # Mock StockfishEngine should not be called
        mock_stockfish = mocker.patch.object(main_module, "StockfishEngine")
        assert mock_stockfish.call_count == 0

        # Test exiting the context
        await lifespan_cm.__aexit__(None, None, None)

        # Assert engine was stopped
        existing_engine.stop.assert_called_once()

    def test_main_cli_with_health_server(self, mocker: MockerFixture):
        """Test main_cli with health server enabled."""
        # Mock dependencies
        mock_argparse = mocker.patch("argparse.ArgumentParser")
        mock_args = mocker.MagicMock()
        mock_args.no_health_server = False
        mock_args.transport = "sse"
        mock_argparse.return_value.parse_args.return_value = mock_args

        mock_setup_env = mocker.patch.object(main_module, "setup_environment")
        mock_process = mocker.patch("multiprocessing.Process")
        mock_app_run = mocker.patch.object(main_module.app, "run")
        mocker.patch.object(main_module, "_get_engine_path", return_value="/path/to/stockfish")

        # Run the function
        main_module.main_cli()

        # Assert function calls
        mock_setup_env.assert_called_once()
        mock_process.assert_called_once()
        mock_process.return_value.start.assert_called_once()
        mock_app_run.assert_called_once_with(transport="sse")

    def test_main_cli_no_health_server(self, mocker: MockerFixture):
        """Test main_cli with health server disabled."""
        # Mock dependencies
        mock_argparse = mocker.patch("argparse.ArgumentParser")
        mock_args = mocker.MagicMock()
        mock_args.no_health_server = True
        mock_args.transport = "stdio"
        mock_argparse.return_value.parse_args.return_value = mock_args

        mock_setup_env = mocker.patch.object(main_module, "setup_environment")
        mock_process = mocker.patch("multiprocessing.Process")
        mock_app_run = mocker.patch.object(main_module.app, "run")
        mocker.patch.object(main_module, "_get_engine_path", return_value="/path/to/stockfish")

        # Run the function
        main_module.main_cli()

        # Assert function calls
        mock_setup_env.assert_called_once()
        mock_process.assert_not_called()
        mock_app_run.assert_called_once_with(transport="stdio")

    def test_main_cli_engine_path_exception(self, mocker: MockerFixture):
        """Test main_cli when getting engine path raises an exception."""
        # Mock dependencies
        mock_argparse = mocker.patch("argparse.ArgumentParser")
        mock_args = mocker.MagicMock()
        mock_args.no_health_server = True
        mock_args.transport = "sse"
        mock_argparse.return_value.parse_args.return_value = mock_args

        mock_setup_env = mocker.patch.object(main_module, "setup_environment")
        mock_app_run = mocker.patch.object(main_module.app, "run")
        mocker.patch.object(main_module, "_get_engine_path", side_effect=Exception("Path error"))

        # Run the function
        main_module.main_cli()

        # Assert function calls
        mock_setup_env.assert_called_once()
        mock_app_run.assert_called_once_with(transport="sse")
