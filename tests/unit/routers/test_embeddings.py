"""
Unit tests for the embeddings router.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.models import (
    OllamaEmbeddingRequest,
    OpenAIEmbeddingData,
    OpenAIEmbeddingResponse,
    OpenAIUsage,
)
from src.routers.embeddings import create_embeddings, router
from src.utils.exceptions import ValidationError


class TestEmbeddingsEndpoint:
    """Test the embeddings endpoint."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-embeddings-123"
        return request

    @pytest.fixture
    def sample_ollama_request(self):
        """Create a sample Ollama embedding request."""
        return OllamaEmbeddingRequest(
            model="text-embedding-ada-002", prompt="Test embedding text"
        )

    @pytest.fixture
    def sample_openai_response(self):
        """Create a sample OpenAI embedding response."""
        return OpenAIEmbeddingResponse(
            object="list",
            data=[
                OpenAIEmbeddingData(
                    object="embedding", index=0, embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
                )
            ],
            model="text-embedding-ada-002",
            usage=OpenAIUsage(prompt_tokens=10, completion_tokens=0, total_tokens=10),
        )

    @pytest.mark.asyncio
    @patch("src.routers.embeddings.retry_client_context")
    @patch("src.routers.embeddings.translator")
    async def test_create_embeddings_success(
        self,
        mock_translator,
        mock_client_context,
        mock_request,
        sample_ollama_request,
        sample_openai_response,
    ):
        """Test successful embeddings creation."""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_context.return_value.__aenter__.return_value = mock_client

        # Mock successful HTTP response
        mock_http_response = Mock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = sample_openai_response.model_dump()
        mock_client.request_with_retry.return_value = mock_http_response

        # Mock translator methods
        mock_translator.validate_model_name.return_value = None
        mock_translator.translate_request.return_value = Mock()

        # Create a proper OllamaEmbeddingResponse mock
        from src.models import OllamaEmbeddingResponse

        mock_ollama_response = OllamaEmbeddingResponse(embedding=[0.1, 0.2, 0.3])
        mock_translator.translate_response.return_value = mock_ollama_response

        # Call the endpoint
        result = await create_embeddings(sample_ollama_request, mock_request)

        # Verify result
        assert isinstance(result, JSONResponse)
        assert result.headers["X-Request-ID"] == "test-embeddings-123"

        # Verify translator was called
        mock_translator.validate_model_name.assert_called_once_with(
            "text-embedding-ada-002"
        )
        mock_translator.translate_request.assert_called_once_with(sample_ollama_request)
        mock_translator.translate_response.assert_called_once()

    @pytest.mark.asyncio
    @patch("src.routers.embeddings.translator")
    async def test_create_embeddings_validation_error(
        self, mock_translator, mock_request, sample_ollama_request
    ):
        """Test embeddings endpoint with validation error."""
        # Setup mock to raise ValidationError
        mock_translator.validate_model_name.side_effect = ValidationError(
            "Invalid model"
        )

        # Call the endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_embeddings(sample_ollama_request, mock_request)

        assert exc_info.value.status_code == 422
        assert "Invalid model" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    @patch("src.routers.embeddings.retry_client_context")
    @patch("src.routers.embeddings.translator")
    async def test_create_embeddings_upstream_error(
        self, mock_translator, mock_client_context, mock_request, sample_ollama_request
    ):
        """Test embeddings endpoint with upstream error."""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_context.return_value.__aenter__.return_value = mock_client

        # Mock HTTP error response
        mock_http_response = Mock()
        mock_http_response.status_code = 500
        mock_http_response.text = "Internal server error"
        mock_client.request_with_retry.return_value = mock_http_response

        mock_translator.validate_model_name.return_value = None
        mock_translator.translate_request.return_value = Mock()

        # Call the endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_embeddings(sample_ollama_request, mock_request)

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch("src.routers.embeddings.retry_client_context")
    @patch("src.routers.embeddings.translator")
    async def test_create_embeddings_timeout_error(
        self, mock_translator, mock_client_context, mock_request, sample_ollama_request
    ):
        """Test embeddings endpoint with timeout error."""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_context.return_value.__aenter__.return_value = mock_client

        # Mock timeout exception
        mock_client.request_with_retry.side_effect = httpx.TimeoutException(
            "Request timeout"
        )

        mock_translator.validate_model_name.return_value = None
        mock_translator.translate_request.return_value = Mock()

        # Call the endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_embeddings(sample_ollama_request, mock_request)

        assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    @patch("src.routers.embeddings.retry_client_context")
    @patch("src.routers.embeddings.translator")
    async def test_create_embeddings_connection_error(
        self, mock_translator, mock_client_context, mock_request, sample_ollama_request
    ):
        """Test embeddings endpoint with connection error."""
        # Setup mocks
        mock_client = AsyncMock()
        mock_client_context.return_value.__aenter__.return_value = mock_client

        # Mock connection exception
        mock_client.request_with_retry.side_effect = httpx.ConnectError(
            "Connection failed"
        )

        mock_translator.validate_model_name.return_value = None
        mock_translator.translate_request.return_value = Mock()

        # Call the endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_embeddings(sample_ollama_request, mock_request)

        assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_create_embeddings_batch_input(self, mock_request):
        """Test embeddings endpoint with batch input."""
        batch_request = OllamaEmbeddingRequest(
            model="text-embedding-ada-002",
            prompt=["Text one", "Text two", "Text three"],
        )

        with (
            patch("src.routers.embeddings.retry_client_context") as mock_client_context,
            patch("src.routers.embeddings.translator") as mock_translator,
        ):

            # Setup mocks
            mock_client = AsyncMock()
            mock_client_context.return_value.__aenter__.return_value = mock_client

            mock_http_response = Mock()
            mock_http_response.status_code = 200
            mock_http_response.json.return_value = {
                "object": "list",
                "data": [{"object": "embedding", "index": 0, "embedding": [0.1, 0.2]}],
                "model": "text-embedding-ada-002",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 0,
                    "total_tokens": 10,
                },
            }
            mock_client.request_with_retry.return_value = mock_http_response

            mock_translator.validate_model_name.return_value = None
            mock_translator.translate_request.return_value = Mock()

            # Create a proper OllamaEmbeddingResponse mock
            from src.models import OllamaEmbeddingResponse

            mock_ollama_response = OllamaEmbeddingResponse(embedding=[0.1, 0.2])
            mock_translator.translate_response.return_value = mock_ollama_response

            # Call the endpoint
            result = await create_embeddings(batch_request, mock_request)

            # Verify result
            assert isinstance(result, JSONResponse)
            mock_translator.translate_request.assert_called_once_with(batch_request)

    def test_router_configured(self):
        """Test that the router is properly configured."""
        # Check that router has the endpoints
        routes = [route.path for route in router.routes]
        assert "/embeddings" in routes
        assert "/api/embeddings" in routes

        # Check the endpoints accept POST
        for route in router.routes:
            if route.path in ["/embeddings", "/api/embeddings"]:
                assert "POST" in route.methods
