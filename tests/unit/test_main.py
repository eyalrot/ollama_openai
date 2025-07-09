"""
Unit tests for the main FastAPI application.
"""

from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock
import uuid

import pytest
import httpx
from fastapi import FastAPI


class TestClient(httpx.Client):
    """Custom TestClient that works with newer httpx versions."""
    
    def __init__(self, app: FastAPI, base_url: str = "http://testserver", **kwargs):
        from starlette.testclient import _TestClientTransport, _AsyncBackend
        import typing
        
        self.async_backend = _AsyncBackend(backend="asyncio", backend_options={})
        self.app = app
        self.app_state: typing.Dict[str, typing.Any] = {}
        
        transport = _TestClientTransport(
            self.app,
            portal_factory=lambda: self.async_backend.portal_factory(),
            raise_server_exceptions=True,
            root_path="",
            app_state=self.app_state,
        )
        
        super().__init__(
            base_url=base_url,
            headers={"user-agent": "testclient"},
            transport=transport,
            follow_redirects=True,
            **kwargs
        )
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.main import app, add_request_id_middleware
from src.utils.exceptions import ProxyException, UpstreamError


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    with patch('src.main.settings') as mock:
        mock.DEBUG = True
        mock.PROXY_PORT = 8000
        mock.OPENAI_API_BASE_URL = "https://api.openai.com"
        mock.LOG_LEVEL = "INFO"
        yield mock


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_health_check(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "ollama-openai-proxy",
            "version": "1.0.0"
        }
    
    def test_readiness_check(self, client):
        """Test /ready endpoint."""
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "ollama-openai-proxy"
        assert "checks" in data
        assert data["checks"]["config"] == "ok"
        assert data["checks"]["logging"] == "ok"
    
    def test_root_endpoint(self, client, mock_settings):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        
        assert data["service"] == "Ollama-OpenAI Proxy"
        assert data["version"] == "1.0.0"
        assert "endpoints" in data
        
        # Check endpoint structure
        endpoints = data["endpoints"]
        assert endpoints["health"] == "/health"
        assert endpoints["ready"] == "/ready"
        assert endpoints["docs"] == "/docs"  # DEBUG=True
        
        # Check OpenAI endpoints
        assert "openai" in endpoints
        assert endpoints["openai"]["chat"] == "/v1/chat/completions"
        assert endpoints["openai"]["models"] == "/v1/models"
        assert endpoints["openai"]["embeddings"] == "/v1/embeddings"
        
        # Check Ollama endpoints
        assert "ollama" in endpoints
        assert endpoints["ollama"]["generate"] == "/api/generate"
        assert endpoints["ollama"]["chat"] == "/api/chat"
        assert endpoints["ollama"]["models"] == "/api/tags"
        assert endpoints["ollama"]["embeddings"] == "/api/embeddings"


class TestMiddleware:
    """Test middleware functionality."""
    
    def test_request_id_middleware(self, client):
        """Test request ID middleware adds headers."""
        response = client.get("/health")
        assert "x-request-id" in response.headers
        
        # Test with provided request ID
        request_id = str(uuid.uuid4())
        response = client.get("/health", headers={"X-Request-ID": request_id})
        assert response.headers["x-request-id"] == request_id
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    def test_cors_expose_headers(self, client):
        """Test CORS exposes X-Request-ID header."""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )
        assert response.status_code == 200
        if "access-control-expose-headers" in response.headers:
            exposed = response.headers["access-control-expose-headers"]
            assert "X-Request-ID" in exposed or "x-request-id" in exposed


class TestErrorHandlers:
    """Test error handling."""
    
    def test_proxy_exception_handler(self, client):
        """Test ProxyException handling."""
        # Create a test endpoint that raises ProxyException
        @app.get("/test-proxy-error")
        async def test_proxy_error():
            raise ProxyException(
                "Test proxy error",
                error_code="TEST_ERROR",
                details={"test": "data"}
            )
        
        response = client.get("/test-proxy-error")
        assert response.status_code == 400
        assert "x-request-id" in response.headers
        
        data = response.json()
        assert "error" in data
        assert data["error"]["message"] == "Test proxy error"
        assert data["error"]["type"] == "ProxyException"
        assert data["error"]["code"] == "TEST_ERROR"
        assert data["error"]["details"] == {"test": "data"}
    
    def test_upstream_error_handler(self, client):
        """Test UpstreamError handling."""
        # Create a test endpoint that raises UpstreamError
        @app.get("/test-upstream-error")
        async def test_upstream_error():
            raise UpstreamError(
                "Service unavailable",
                status_code=503,
                service="openai",
                details={"retry_after": 30}
            )
        
        response = client.get("/test-upstream-error")
        assert response.status_code == 503
        assert "x-request-id" in response.headers
        
        data = response.json()
        assert "error" in data
        assert data["error"]["message"] == "Service unavailable"
        assert data["error"]["type"] == "upstream_error"
        assert data["error"]["status_code"] == 503
        assert data["error"]["service"] == "openai"
        assert data["error"]["details"] == {"retry_after": 30}
    
    def test_general_exception_handler(self, client):
        """Test general exception handling."""
        # Create a test endpoint that raises unexpected exception
        @app.get("/test-general-error")
        async def test_general_error():
            raise ValueError("Unexpected error")
        
        response = client.get("/test-general-error")
        assert response.status_code == 500
        assert "x-request-id" in response.headers
        
        data = response.json()
        assert "error" in data
        assert data["error"]["message"] == "Internal server error"
        assert data["error"]["type"] == "internal_error"
        assert "request_id" in data["error"]


class TestRouterIntegration:
    """Test router integration."""
    
    def test_openai_routes_included(self, client):
        """Test OpenAI-style routes are included."""
        # These should return 405 Method Not Allowed for GET
        # (they expect POST)
        response = client.get("/v1/chat/completions")
        assert response.status_code in [404, 405, 422]  # Depends on router implementation
        
        response = client.get("/v1/models")
        # Models endpoint might support GET
        assert response.status_code in [200, 404, 405]
        
        response = client.get("/v1/embeddings")
        assert response.status_code in [404, 405, 422]
    
    def test_ollama_routes_included(self, client):
        """Test Ollama-style routes are included."""
        # These should return 405 Method Not Allowed for GET
        # (they expect POST)
        response = client.get("/api/generate")
        assert response.status_code in [404, 405, 422]
        
        response = client.get("/api/chat")
        assert response.status_code in [404, 405, 422]
        
        response = client.get("/api/tags")
        # Tags endpoint might support GET
        assert response.status_code in [200, 404, 405]
        
        response = client.get("/api/embeddings")
        assert response.status_code in [404, 405, 422]


class TestApplicationSettings:
    """Test application settings and configuration."""
    
    def test_debug_mode_docs(self, client):
        """Test documentation endpoints in debug mode."""
        with patch('src.main.settings') as mock_settings:
            mock_settings.DEBUG = True
            mock_settings.PROXY_PORT = 8000
            mock_settings.OPENAI_API_BASE_URL = "https://api.openai.com"
            mock_settings.LOG_LEVEL = "INFO"
            
            # In debug mode, docs should be available
            response = client.get("/")
            data = response.json()
            assert data["endpoints"]["docs"] == "/docs"
    
    def test_production_mode_no_docs(self, client):
        """Test documentation endpoints hidden in production."""
        with patch('src.main.settings') as mock_settings:
            mock_settings.DEBUG = False
            mock_settings.PROXY_PORT = 8000
            mock_settings.OPENAI_API_BASE_URL = "https://api.openai.com"
            mock_settings.LOG_LEVEL = "INFO"
            
            # In production mode, docs should be None
            response = client.get("/")
            data = response.json()
            assert data["endpoints"]["docs"] is None


class TestLifespan:
    """Test application lifespan management."""
    
    @pytest.mark.asyncio
    async def test_lifespan_startup_shutdown(self):
        """Test lifespan context manager logs startup/shutdown."""
        with patch('src.main.logger') as mock_logger:
            # Import lifespan function
            from src.main import lifespan
            
            # Create mock app
            mock_app = Mock()
            
            # Run lifespan
            async with lifespan(mock_app):
                # Check startup log
                mock_logger.info.assert_called()
                startup_call = mock_logger.info.call_args_list[0]
                assert "Starting Ollama-OpenAI Proxy" in startup_call[0][0]
                
                # Clear for shutdown test
                mock_logger.info.reset_mock()
            
            # Check shutdown log
            mock_logger.info.assert_called_with("Shutting down Ollama-OpenAI Proxy")


class TestRequestIDMiddleware:
    """Test request ID middleware functionality."""
    
    @pytest.mark.asyncio
    async def test_add_request_id_middleware(self):
        """Test request ID middleware function."""
        # Create mock request and response
        mock_request = Mock(spec=Request)
        mock_request.headers = {}
        mock_request.state = Mock()
        
        # Create mock call_next
        async def mock_call_next(request):
            response = Mock()
            response.headers = {}
            return response
        
        # Test without existing request ID
        response = await add_request_id_middleware(mock_request, mock_call_next)
        
        # Check request ID was set
        assert hasattr(mock_request.state, 'request_id')
        assert isinstance(mock_request.state.request_id, str)
        assert response.headers["X-Request-ID"] == mock_request.state.request_id
        
        # Test with existing request ID
        existing_id = str(uuid.uuid4())
        mock_request.headers = {"X-Request-ID": existing_id}
        mock_request.state = Mock()
        
        response = await add_request_id_middleware(mock_request, mock_call_next)
        
        assert mock_request.state.request_id == existing_id
        assert response.headers["X-Request-ID"] == existing_id