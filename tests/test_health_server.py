"""Tests for the health server module."""

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture

from chesspal_mcp_engine.health_server import create_health_api, run_health_server, set_engine, start_health_server


class MockEngine:
    """Mock engine for testing health server."""

    def __init__(self, is_initialized_return=True):
        """Initialize mock engine.

        Args:
            is_initialized_return: Value to return from is_initialized()
        """
        self._is_initialized_return = is_initialized_return

    def is_initialized(self):
        """Mock is_initialized method.

        Returns:
            The configured return value
        """
        return self._is_initialized_return


class TestHealthServer:
    """Tests for the health server functionality."""

    def test_create_health_api(self):
        """Test creating the health API."""
        api = create_health_api(title="Test API")
        client = TestClient(api)

        # Test ping endpoint
        response = client.get("/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}

    def test_health_check_no_engine(self):
        """Test health check with no engine set."""
        # Make sure no engine is set
        set_engine(None)

        api = create_health_api()
        client = TestClient(api)

        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["status"] == "degraded"
        assert response.json()["dependencies"]["engine"] == "error"

    def test_health_check_engine_ready(self):
        """Test health check with a ready engine."""
        engine = MockEngine(is_initialized_return=True)
        set_engine(engine)

        api = create_health_api()
        client = TestClient(api)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["dependencies"]["engine"] == "ok"

    def test_health_check_engine_not_ready(self):
        """Test health check with engine that's not ready."""
        engine = MockEngine(is_initialized_return=False)
        set_engine(engine)

        api = create_health_api()
        client = TestClient(api)

        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["status"] == "degraded"
        assert response.json()["dependencies"]["engine"] == "error"

    def test_health_check_engine_exception(self, mocker: MockerFixture):
        """Test health check when engine raises an exception."""
        # Create a mock engine that raises an exception
        engine = MockEngine()
        mocker.patch.object(engine, "is_initialized", side_effect=Exception("Test exception"))
        set_engine(engine)

        api = create_health_api()
        client = TestClient(api)

        response = client.get("/health")
        assert response.status_code == 503
        assert response.json()["status"] == "degraded"
        assert response.json()["dependencies"]["engine"] == "error"

    def test_run_health_server(self, mocker: MockerFixture):
        """Test run_health_server function."""
        # Mock uvicorn.run to avoid actually starting a server
        mock_uvicorn_run = mocker.patch("uvicorn.run")
        # Mock setup_logging to avoid side effects
        mock_setup_logging = mocker.patch("chesspal_mcp_engine.health_server.setup_logging")

        # Run the function
        run_health_server("127.0.0.1", 8080, "info")

        # Assert setup_logging was called with expected args
        mock_setup_logging.assert_called_once_with("INFO")

        # Assert uvicorn.run was called with expected args
        mock_uvicorn_run.assert_called_once()
        args, kwargs = mock_uvicorn_run.call_args
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 8080
        assert kwargs["log_level"] == "info"

    def test_start_health_server(self, mocker: MockerFixture):
        """Test start_health_server function."""
        # Mock run_health_server to avoid actually starting a server
        mock_run_health_server = mocker.patch("chesspal_mcp_engine.health_server.run_health_server")

        # Call the function
        start_health_server("127.0.0.1", 8080, "info")

        # Assert run_health_server was called with expected args
        mock_run_health_server.assert_called_once_with("127.0.0.1", 8080, "info")
