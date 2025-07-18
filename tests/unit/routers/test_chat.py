"""
Unit tests for the chat router.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi import HTTPException, Request

from src.models import (
    OllamaChatMessage,
    OllamaChatRequest,
    OllamaGenerateRequest,
    OllamaOptions,
)
from src.utils.exceptions import ValidationError


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    with patch("src.routers.chat.settings") as mock:
        mock.OPENAI_API_BASE_URL = "https://api.openai.com/v1"
        mock.OPENAI_API_KEY = "test-key"
        mock.REQUEST_TIMEOUT = 30
        mock.MAX_RETRIES = 3
        yield mock


@pytest.fixture
def mock_translator():
    """Mock translator for tests."""
    with patch("src.routers.chat.translator") as mock:
        yield mock


@pytest.fixture
def mock_request():
    """Mock FastAPI request with request ID."""
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.request_id = "test-request-123"
    return request


@pytest.fixture
def ollama_generate_request():
    """Sample Ollama generate request."""
    return OllamaGenerateRequest(
        model="llama2",
        prompt="Hello, world!",
        stream=False,
        options=OllamaOptions(temperature=0.7),
    )


@pytest.fixture
def ollama_chat_request():
    """Sample Ollama chat request."""
    return OllamaChatRequest(
        model="mistral",
        messages=[
            OllamaChatMessage(role="user", content="Hello"),
            OllamaChatMessage(role="assistant", content="Hi there!"),
            OllamaChatMessage(role="user", content="How are you?"),
        ],
        stream=False,
    )


@pytest.fixture
def openai_response_data():
    """Sample OpenAI response data."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "I'm doing well, thank you!",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


class TestChatRouterGenerate:
    """Test generate endpoint functionality."""

    @pytest.mark.asyncio
    async def test_generate_non_streaming_success(
        self,
        mock_settings,
        mock_translator,
        mock_request,
        ollama_generate_request,
        openai_response_data,
    ):
        """Test successful non-streaming generate request."""
        # Setup mocks
        mock_openai_request = Mock()
        mock_openai_request.model_dump.return_value = {"model": "gpt-3.5-turbo"}
        mock_openai_request.model = "gpt-3.5-turbo"
        mock_openai_request.messages = [{"role": "user", "content": "Hello"}]

        mock_translator.translate_request.return_value = mock_openai_request

        mock_ollama_response = Mock()
        mock_ollama_response.model_dump.return_value = {
            "model": "llama2",
            "response": "I'm doing well, thank you!",
            "done": True,
        }
        mock_translator.translate_response.return_value = mock_ollama_response

        # Mock HTTP client
        with patch("src.routers.chat.retry_client_context") as mock_client_ctx:
            mock_client = AsyncMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client

            # Mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = openai_response_data
            mock_client.request_with_retry.return_value = mock_response

            # Call endpoint
            from src.routers.chat import generate

            # Mock request body handling
            with patch("src.routers.chat.get_body_json") as mock_get_body:
                mock_get_body.return_value = ollama_generate_request.model_dump()
                response = await generate(mock_request)

            # Verify
            assert response.status_code == 200
            body = json.loads(response.body)
            assert body["model"] == "llama2"
            assert body["response"] == "I'm doing well, thank you!"
            assert body["done"] is True

            # Verify calls
            mock_translator.translate_request.assert_called_once_with(
                ollama_generate_request
            )
            mock_client.request_with_retry.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_streaming_success(
        self, mock_settings, mock_translator, mock_request
    ):
        """Test successful streaming generate request."""
        # Create streaming request
        request = OllamaGenerateRequest(
            model="llama2", prompt="Tell me a story", stream=True
        )

        # Setup mocks
        mock_openai_request = Mock()
        mock_openai_request.model_dump.return_value = {"model": "gpt-3.5-turbo"}
        mock_translator.translate_request.return_value = mock_openai_request

        # Mock streaming chunks
        mock_translator.translate_streaming_response.side_effect = [
            {"response": "Once", "done": False},
            {"response": " upon", "done": False},
            {"response": " a", "done": False},
            {"response": " time", "done": False},
            {"response": "", "done": True, "done_reason": "stop"},
        ]

        # Mock HTTP client with streaming
        with patch("src.routers.chat.retry_client_context") as mock_client_ctx:
            mock_client = AsyncMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client

            # Mock streaming response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.aiter_lines = AsyncMock()
            mock_response.aiter_lines.return_value = [
                'data: {"choices": [{"delta": {"content": "Once"}}]}',
                'data: {"choices": [{"delta": {"content": " upon"}}]}',
                'data: {"choices": [{"delta": {"content": " a"}}]}',
                'data: {"choices": [{"delta": {"content": " time"}}]}',
                "data: [DONE]",
            ]
            mock_client.request_with_retry.return_value = mock_response

            # Call endpoint
            from src.routers.chat import generate

            # Mock request body handling
            with patch("src.routers.chat.get_body_json") as mock_get_body:
                mock_get_body.return_value = request.model_dump()
                response = await generate(mock_request)

            # Verify streaming response
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/x-ndjson"
            assert response.headers["x-request-id"] == "test-request-123"

    @pytest.mark.asyncio
    async def test_generate_validation_error(
        self, mock_settings, mock_translator, mock_request, ollama_generate_request
    ):
        """Test generate with validation error."""
        # Setup mock to raise validation error
        mock_translator.translate_request.side_effect = ValidationError(
            "Model name cannot be empty"
        )

        # Call endpoint
        from src.routers.chat import generate

        # Mock request body handling
        with patch("src.routers.chat.get_body_json") as mock_get_body:
            mock_get_body.return_value = ollama_generate_request.model_dump()
            with pytest.raises(HTTPException) as exc_info:
                await generate(mock_request)

        assert exc_info.value.status_code == 400
        assert "Model name cannot be empty" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_generate_upstream_error(
        self, mock_settings, mock_translator, mock_request, ollama_generate_request
    ):
        """Test generate with upstream error."""
        # Setup mocks
        mock_openai_request = Mock()
        mock_openai_request.model_dump.return_value = {"model": "gpt-3.5-turbo"}
        mock_openai_request.model = "gpt-3.5-turbo"
        mock_openai_request.messages = [{"role": "user", "content": "Hello"}]
        mock_translator.translate_request.return_value = mock_openai_request

        # Mock HTTP client to return error
        with patch("src.routers.chat.retry_client_context") as mock_client_ctx:
            mock_client = AsyncMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client

            # Mock error response
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_client.request_with_retry.return_value = mock_response

            # Call endpoint
            from src.routers.chat import generate

            # Mock request body handling
            with patch("src.routers.chat.get_body_json") as mock_get_body:
                mock_get_body.return_value = ollama_generate_request.model_dump()
                with pytest.raises(HTTPException) as exc_info:
                    await generate(mock_request)

            assert exc_info.value.status_code == 503
            assert "Upstream error" in str(exc_info.value.detail)


class TestChatRouterChat:
    """Test chat endpoint functionality."""

    @pytest.mark.asyncio
    async def test_chat_non_streaming_success(
        self,
        mock_settings,
        mock_translator,
        mock_request,
        ollama_chat_request,
        openai_response_data,
    ):
        """Test successful non-streaming chat request."""
        # Setup mocks
        mock_openai_request = Mock()
        mock_openai_request.model_dump.return_value = {"model": "gpt-4"}
        mock_openai_request.model = "gpt-4"
        mock_openai_request.messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

        mock_translator.translate_request.return_value = mock_openai_request

        mock_ollama_response = Mock()
        mock_ollama_response.model_dump.return_value = {
            "model": "mistral",
            "message": {"role": "assistant", "content": "I'm doing well, thank you!"},
            "done": True,
        }
        mock_translator.translate_response.return_value = mock_ollama_response

        # Mock HTTP client
        with patch("src.routers.chat.retry_client_context") as mock_client_ctx:
            mock_client = AsyncMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client

            # Mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = openai_response_data
            mock_client.request_with_retry.return_value = mock_response

            # Call endpoint
            from src.routers.chat import ollama_chat

            # Mock request body handling
            with patch("src.routers.chat.get_body_json") as mock_get_body:
                mock_get_body.return_value = ollama_chat_request.model_dump()
                response = await ollama_chat(mock_request)

            # Verify
            assert response.status_code == 200
            body = json.loads(response.body)
            assert body["model"] == "mistral"
            assert body["done"] is True

    @pytest.mark.asyncio
    async def test_chat_with_timeout(
        self, mock_settings, mock_translator, mock_request, ollama_chat_request
    ):
        """Test chat request with timeout."""
        # Setup mocks
        mock_openai_request = Mock()
        mock_openai_request.model_dump.return_value = {"model": "gpt-4"}
        mock_openai_request.model = "gpt-4"
        mock_openai_request.messages = [{"role": "user", "content": "How are you?"}]
        mock_translator.translate_request.return_value = mock_openai_request

        # Mock HTTP client to raise timeout
        with patch("src.routers.chat.retry_client_context") as mock_client_ctx:
            mock_client = AsyncMock()
            mock_client_ctx.return_value.__aenter__.return_value = mock_client

            # Mock timeout error
            mock_client.request_with_retry.side_effect = httpx.TimeoutException(
                "Request timeout"
            )

            # Call endpoint
            from src.routers.chat import ollama_chat

            # Mock request body handling
            with patch("src.routers.chat.get_body_json") as mock_get_body:
                mock_get_body.return_value = ollama_chat_request.model_dump()
                with pytest.raises(HTTPException) as exc_info:
                    await ollama_chat(mock_request)

            assert exc_info.value.status_code == 504
            assert "Request timeout" in str(exc_info.value.detail)


class TestHTTPClient:
    """Test HTTP client configuration."""

    @pytest.mark.asyncio
    async def test_http_client_configuration(self, mock_settings):
        """Test HTTP client is configured correctly."""
        # Test that retry client is created successfully
        from src.routers.chat import retry_client_context
        from src.utils.http_client import RetryClient

        async with retry_client_context() as client:
            assert client is not None
            assert isinstance(client, RetryClient)

            # Verify client has expected attributes
            assert hasattr(client, "request_with_retry")
            assert hasattr(client, "stream_with_retry")
            assert client.max_retries > 0
            assert client.timeout > 0


class TestStreamingResponse:
    """Test streaming response handling."""

    @pytest.mark.asyncio
    async def test_stream_response_parsing(
        self, mock_settings, mock_translator, ollama_generate_request
    ):
        """Test parsing of streaming response chunks."""
        from src.routers.chat import stream_response

        # Mock translator
        chunks_received = []

        def capture_chunk(chunk, request, **kwargs):
            chunks_received.append(chunk)
            if chunk == "[DONE]":
                return {"response": "", "done": True}
            return {
                "response": chunk.get("choices", [{}])[0]
                .get("delta", {})
                .get("content", "")
            }

        mock_translator.translate_streaming_response.side_effect = capture_chunk

        # Mock client with streaming response
        mock_client = AsyncMock()

        # Create async iterator for raw chunks
        async def mock_stream_chunks(*args, **kwargs):
            chunks = [
                b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
                b'data: {"choices": [{"delta": {"content": " world"}}]}\n',
                b"\n",  # Empty line
                b'data: {"invalid": "json}\n',  # Invalid JSON
                b"data: [DONE]\n",
            ]
            for chunk in chunks:
                yield chunk

        # Mock stream_with_retry to return our async generator
        mock_client.stream_with_retry = mock_stream_chunks

        mock_openai_request = Mock()
        mock_openai_request.model_dump.return_value = {"model": "gpt-3.5-turbo"}
        mock_openai_request.model = "gpt-3.5-turbo"
        mock_openai_request.messages = [{"role": "user", "content": "Hello"}]

        # Stream response
        chunks = []
        async for chunk in stream_response(
            mock_client, mock_openai_request, ollama_generate_request
        ):
            chunks.append(chunk)

        # Verify chunks
        assert len(chunks) == 3  # Two content chunks + done
        assert json.loads(chunks[0])["response"] == "Hello"
        assert json.loads(chunks[1])["response"] == " world"
        assert json.loads(chunks[2])["done"] is True

        # Verify invalid JSON was skipped
        assert len(chunks_received) == 3  # Only valid chunks
