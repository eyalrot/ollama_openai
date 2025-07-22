"""
Unit tests for the models router.
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from fastapi import HTTPException, Request
from starlette.responses import JSONResponse

from src.models import (
    OllamaDeleteRequest,
    OllamaPullRequest,
    OllamaPushRequest,
    OllamaShowRequest,
)
from src.utils.exceptions import UpstreamError


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    with patch("src.routers.models.settings") as mock:
        mock.OPENAI_API_BASE_URL = "https://api.openai.com/v1"
        mock.OPENAI_API_KEY = "test-key"
        mock.REQUEST_TIMEOUT = 30
        yield mock


@pytest.fixture
def mock_request():
    """Mock FastAPI request with request ID."""
    request = Mock(spec=Request)
    request.state = Mock()
    request.state.request_id = "test-request-123"
    return request


@pytest.fixture
def openai_models_response():
    """Sample OpenAI models response."""
    return {
        "object": "list",
        "data": [
            {
                "id": "gpt-3.5-turbo",
                "object": "model",
                "created": 1677649963,
                "owned_by": "openai",
            },
            {
                "id": "gpt-4",
                "object": "model",
                "created": 1687882411,
                "owned_by": "openai",
            },
            {
                "id": "text-embedding-ada-002",
                "object": "model",
                "created": 1671217299,
                "owned_by": "openai-internal",
            },
        ],
    }


@pytest.fixture
def openrouter_models_response():
    """Sample OpenRouter models response (without owned_by field)."""
    return {
        "object": "list",
        "data": [
            {
                "id": "anthropic/claude-3-sonnet",
                "object": "model",
                "created": 1677649963,
                # Note: OpenRouter doesn't include owned_by field
            },
            {
                "id": "openai/gpt-4",
                "object": "model",
                "created": 1687882411,
            },
            {
                "id": "meta-llama/llama-2-7b-chat",
                "object": "model",
                "created": 1671217299,
            },
        ],
    }


class TestModelListing:
    """Test model listing functionality."""

    @pytest.mark.asyncio
    async def test_list_models_success(
        self, mock_settings, mock_request, openai_models_response
    ):
        """Test successful model listing."""
        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            # Mock the async client
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = openai_models_response
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import list_models

            result = await list_models(mock_request)

            # Verify result
            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            assert "models" in response_dict
            assert len(response_dict["models"]) == 3

            # Check first model
            model = response_dict["models"][0]
            assert model["name"] == "gpt-3.5-turbo"
            assert model["model"] == "gpt-3.5-turbo"
            assert model["size"] == 0
            assert model["digest"].startswith("sha256:")
            assert model["details"]["family"] == "openai"

            # Verify API call
            mock_client.get.assert_called_once_with(
                f"{mock_settings.OPENAI_API_BASE_URL}/models",
                headers={"Authorization": f"Bearer {mock_settings.OPENAI_API_KEY}"},
            )

    @pytest.mark.asyncio
    async def test_list_models_empty(self, mock_settings, mock_request):
        """Test listing models with empty response."""
        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock empty response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"object": "list", "data": []}
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import list_models

            result = await list_models(mock_request)

            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            assert "models" in response_dict
            assert len(response_dict["models"]) == 0

    @pytest.mark.asyncio
    async def test_list_models_openrouter_without_owned_by(
        self, mock_settings, mock_request, openrouter_models_response
    ):
        """Test successful model listing with OpenRouter response (no owned_by field)."""
        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            # Mock the async client
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = openrouter_models_response
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import list_models

            result = await list_models(mock_request)

            # Verify result
            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            assert "models" in response_dict
            assert len(response_dict["models"]) == 3

            # Check first model (should handle missing owned_by gracefully)
            model = response_dict["models"][0]
            assert model["name"] == "anthropic/claude-3-sonnet"
            assert model["model"] == "anthropic/claude-3-sonnet"
            assert model["size"] == 0
            assert model["digest"].startswith("sha256:")
            # Should default to "unknown" when owned_by is missing
            assert model["details"]["family"] == "unknown"
            assert model["details"]["families"] == ["unknown"]

    @pytest.mark.asyncio
    async def test_list_models_upstream_error(self, mock_settings, mock_request):
        """Test model listing with upstream error."""
        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock error response
            mock_response = Mock()
            mock_response.status_code = 503
            mock_response.text = "Service unavailable"
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import list_models

            with pytest.raises(UpstreamError) as exc_info:
                await list_models(mock_request)

            assert exc_info.value.status_code == 503
            assert "Failed to list models" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_models_timeout(self, mock_settings, mock_request):
        """Test model listing with timeout."""
        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock timeout
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")

            # Call endpoint
            from src.routers.models import list_models

            with pytest.raises(HTTPException) as exc_info:
                await list_models(mock_request)

            assert exc_info.value.status_code == 504
            assert "Timeout" in str(exc_info.value.detail)


class TestModelManagementOperations:
    """Test unsupported model management operations."""

    @pytest.mark.asyncio
    async def test_pull_model_not_supported(self, mock_request):
        """Test pull model returns 501."""
        request = OllamaPullRequest(name="llama2:7b")

        from src.routers.models import pull_model

        response = await pull_model(request, mock_request)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 501

        # Check response content
        content = json.loads(response.body)
        assert content["error"]["code"] == 501
        assert "not supported" in content["error"]["message"]
        assert content["error"]["type"] == "not_implemented"

    @pytest.mark.asyncio
    async def test_push_model_not_supported(self, mock_request):
        """Test push model returns 501."""
        request = OllamaPushRequest(name="custom-model")

        from src.routers.models import push_model

        response = await push_model(request, mock_request)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 501

        content = json.loads(response.body)
        assert content["error"]["code"] == 501
        assert "not supported" in content["error"]["message"]

    @pytest.mark.asyncio
    async def test_delete_model_not_supported(self, mock_request):
        """Test delete model returns 501."""
        request = OllamaDeleteRequest(name="old-model")

        from src.routers.models import delete_model

        response = await delete_model(request, mock_request)

        assert isinstance(response, JSONResponse)
        assert response.status_code == 501

        content = json.loads(response.body)
        assert content["error"]["code"] == 501
        assert "not supported" in content["error"]["message"]


class TestVersionEndpoint:
    """Test version endpoint."""

    @pytest.mark.asyncio
    async def test_get_version(self, mock_request):
        """Test version endpoint returns correct format."""
        from src.routers.models import get_version

        result = await get_version(mock_request)

        assert isinstance(result, JSONResponse)

        # Get the response content
        response_data = result.body.decode("utf-8")
        import json

        response_dict = json.loads(response_data)

        assert "version" in response_dict
        assert response_dict["version"] == "0.1.42"
        assert isinstance(response_dict["version"], str)


class TestShowModel:
    """Test show model functionality."""

    @pytest.mark.asyncio
    async def test_show_model_basic(
        self, mock_settings, mock_request, openai_models_response
    ):
        """Test showing basic model information."""
        request = OllamaShowRequest(name="gpt-3.5-turbo", verbose=False)

        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock models list response for verification
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = openai_models_response
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import show_model

            result = await show_model(request, mock_request)

            # Verify result
            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            assert response_dict["modelfile"] == ""  # Not verbose
            assert response_dict["parameters"] is not None
            assert "temperature 0.7" in response_dict["parameters"]
            assert response_dict["template"] is not None
            assert response_dict["details"]["format"] == "gguf"
            assert response_dict["model_info"] == {}  # Not verbose

    @pytest.mark.asyncio
    async def test_show_model_verbose(
        self, mock_settings, mock_request, openai_models_response
    ):
        """Test showing verbose model information."""
        request = OllamaShowRequest(name="llama2:7b", verbose=True)

        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock models list response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "object": "list",
                "data": [
                    {
                        "id": "llama2:7b",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "meta",
                    }
                ],
            }
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import show_model

            result = await show_model(request, mock_request)

            # Verify verbose output
            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            assert response_dict["modelfile"] != ""
            assert "FROM llama2:7b" in response_dict["modelfile"]
            assert response_dict["details"]["family"] == "llama"
            assert response_dict["details"]["parameter_size"] == "7B"
            assert response_dict["model_info"] != {}
            assert response_dict["model_info"]["general.architecture"] == "llama"
            assert response_dict["model_info"]["general.parameter_count"] == 7000000000

    @pytest.mark.asyncio
    async def test_show_model_not_found(
        self, mock_settings, mock_request, openai_models_response
    ):
        """Test showing non-existent model."""
        request = OllamaShowRequest(name="non-existent-model", verbose=False)

        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock models list response without the requested model
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = openai_models_response
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import show_model

            with pytest.raises(HTTPException) as exc_info:
                await show_model(request, mock_request)

            assert exc_info.value.status_code == 404
            assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_show_model_verification_failure(self, mock_settings, mock_request):
        """Test show model when verification fails."""
        request = OllamaShowRequest(name="some-model", verbose=False)

        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock request error during verification
            mock_client.get.side_effect = httpx.RequestError("Connection failed")

            # Call endpoint - should proceed anyway
            from src.routers.models import show_model

            result = await show_model(request, mock_request)

            # Should still return basic info
            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            assert response_dict["parameters"] is not None
            assert response_dict["template"] is not None


class TestModelTransformation:
    """Test model format transformation."""

    @pytest.mark.asyncio
    async def test_timestamp_conversion(self, mock_settings, mock_request):
        """Test proper timestamp conversion from Unix to ISO."""
        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock response with specific timestamp
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "object": "list",
                "data": [
                    {
                        "id": "test-model",
                        "object": "model",
                        "created": 1677649963,  # 2023-03-01 12:32:43 UTC
                        "owned_by": "test",
                    }
                ],
            }
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import list_models

            result = await list_models(mock_request)

            # Check timestamp format
            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            model = response_dict["models"][0]
            # Should be ISO format with timezone
            assert "T" in model["modified_at"]
            assert model["modified_at"].endswith("+00:00") or model[
                "modified_at"
            ].endswith("Z")

            # Verify it's the correct timestamp
            parsed_time = datetime.fromisoformat(
                model["modified_at"].replace("Z", "+00:00")
            )
            assert parsed_time.timestamp() == 1677649963

    @pytest.mark.asyncio
    async def test_digest_generation(self, mock_settings, mock_request):
        """Test consistent digest generation from model ID."""
        with patch("src.routers.models.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "object": "list",
                "data": [
                    {
                        "id": "model-a",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "test",
                    },
                    {
                        "id": "model-a",
                        "object": "model",
                        "created": 1234567890,
                        "owned_by": "test",
                    },
                ],
            }
            mock_client.get.return_value = mock_response

            # Call endpoint
            from src.routers.models import list_models

            result = await list_models(mock_request)

            # Both instances of same model should have same digest
            assert isinstance(result, JSONResponse)

            # Get the response content
            response_data = result.body.decode("utf-8")
            import json

            response_dict = json.loads(response_data)

            assert (
                response_dict["models"][0]["digest"]
                == response_dict["models"][1]["digest"]
            )
            assert response_dict["models"][0]["digest"].startswith("sha256:")
