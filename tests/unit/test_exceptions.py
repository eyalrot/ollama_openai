"""
Unit tests for custom exceptions.
"""

import json


from src.utils.exceptions import (
    ProxyException,
    ConfigurationError,
    ValidationError,
    TranslationError,
    UpstreamError,
    ModelNotFoundError,
    AuthenticationError,
    RateLimitError,
    TimeoutError,
    UnsupportedOperationError,
    StreamingError,
    exception_from_status_code,
    STATUS_CODE_TO_EXCEPTION,
)


class TestProxyException:
    """Test the base ProxyException class."""

    def test_basic_exception(self):
        """Test basic exception creation."""
        exc = ProxyException("Test error")

        assert str(exc) == "ProxyException: Test error"
        assert exc.message == "Test error"
        assert exc.error_code == "ProxyException"
        assert exc.details == {}
        assert exc.timestamp is not None

    def test_with_error_code(self):
        """Test exception with custom error code."""
        exc = ProxyException("Test error", error_code="CUSTOM_ERROR")

        assert exc.error_code == "CUSTOM_ERROR"
        assert str(exc) == "CUSTOM_ERROR: Test error"

    def test_with_details(self):
        """Test exception with additional details."""
        details = {"field": "username", "value": "invalid"}
        exc = ProxyException("Test error", details=details)

        assert exc.details == details
        assert "invalid" in str(exc)

    def test_to_dict(self):
        """Test converting exception to dictionary."""
        exc = ProxyException(
            "Test error",
            error_code="TEST_ERROR",
            details={"key": "value"},
        )

        result = exc.to_dict()

        assert "error" in result
        assert result["error"]["type"] == "ProxyException"
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test error"
        assert result["error"]["details"] == {"key": "value"}
        assert "timestamp" in result["error"]

    def test_to_json(self):
        """Test converting exception to JSON."""
        exc = ProxyException("Test error", details={"number": 42})

        json_str = exc.to_json()
        data = json.loads(json_str)

        assert data["error"]["message"] == "Test error"
        assert data["error"]["details"]["number"] == 42


class TestConfigurationError:
    """Test ConfigurationError."""

    def test_basic_error(self):
        """Test basic configuration error."""
        exc = ConfigurationError("Invalid configuration")

        assert exc.error_code == "CONFIG_ERROR"
        assert exc.message == "Invalid configuration"

    def test_with_config_key(self):
        """Test error with config key."""
        exc = ConfigurationError("Invalid value", config_key="API_KEY")

        assert exc.details["config_key"] == "API_KEY"

    def test_with_additional_details(self):
        """Test error with additional details."""
        exc = ConfigurationError(
            "Invalid value",
            config_key="PORT",
            details={"provided": "abc", "expected": "number"},
        )

        assert exc.details["config_key"] == "PORT"
        assert exc.details["provided"] == "abc"
        assert exc.details["expected"] == "number"


class TestValidationError:
    """Test ValidationError."""

    def test_basic_error(self):
        """Test basic validation error."""
        exc = ValidationError("Invalid input")

        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.message == "Invalid input"

    def test_with_field_and_value(self):
        """Test error with field and value."""
        exc = ValidationError(
            "Invalid email format",
            field="email",
            value="not-an-email",
        )

        assert exc.details["field"] == "email"
        assert exc.details["invalid_value"] == "not-an-email"

    def test_value_conversion(self):
        """Test that values are converted to strings."""
        exc = ValidationError(
            "Invalid number", field="age", value={"complex": "object"}
        )

        assert exc.details["invalid_value"] == "{'complex': 'object'}"


class TestTranslationError:
    """Test TranslationError."""

    def test_basic_error(self):
        """Test basic translation error."""
        exc = TranslationError("Translation failed")

        assert exc.error_code == "TRANSLATION_ERROR"

    def test_with_formats(self):
        """Test error with source and target formats."""
        exc = TranslationError(
            "Cannot translate request",
            source_format="ollama",
            target_format="openai",
        )

        assert exc.details["source_format"] == "ollama"
        assert exc.details["target_format"] == "openai"


class TestUpstreamError:
    """Test UpstreamError."""

    def test_server_error(self):
        """Test upstream server error."""
        exc = UpstreamError(
            "Internal server error",
            status_code=500,
            response_data={"error": "Server crashed"},
        )

        assert exc.status_code == 500
        assert exc.error_code == "UPSTREAM_SERVER_ERROR"
        assert exc.response_data == {"error": "Server crashed"}
        assert exc.details["status_code"] == 500
        assert exc.details["upstream_response"] == {"error": "Server crashed"}

    def test_client_error(self):
        """Test upstream client error."""
        exc = UpstreamError("Bad request", status_code=400)

        assert exc.status_code == 400
        assert exc.error_code == "UPSTREAM_CLIENT_ERROR"

    def test_with_request_id(self):
        """Test error with request ID."""
        exc = UpstreamError(
            "Gateway timeout",
            status_code=504,
            request_id="req-123",
        )

        assert exc.details["request_id"] == "req-123"

    def test_other_status_code(self):
        """Test with non-4xx/5xx status code."""
        exc = UpstreamError("Redirect", status_code=302)

        assert exc.error_code == "UPSTREAM_ERROR"


class TestModelNotFoundError:
    """Test ModelNotFoundError."""

    def test_basic_error(self):
        """Test basic model not found error."""
        exc = ModelNotFoundError("gpt-5")

        assert exc.error_code == "MODEL_NOT_FOUND"
        assert exc.model_name == "gpt-5"
        assert exc.message == "Model 'gpt-5' not found"
        assert exc.details["requested_model"] == "gpt-5"

    def test_with_available_models(self):
        """Test error with available models list."""
        models = ["gpt-3.5-turbo", "gpt-4", "claude-2", "llama-2"]
        exc = ModelNotFoundError("gpt-5", available_models=models)

        assert (
            "Available models: gpt-3.5-turbo, gpt-4, claude-2, llama-2" in exc.message
        )
        assert exc.details["available_models"] == models

    def test_with_many_available_models(self):
        """Test error with many available models."""
        models = [f"model-{i}" for i in range(10)]
        exc = ModelNotFoundError("unknown", available_models=models)

        assert "and 5 more" in exc.message


class TestAuthenticationError:
    """Test AuthenticationError."""

    def test_default_message(self):
        """Test with default message."""
        exc = AuthenticationError()

        assert exc.message == "Authentication failed"
        assert exc.error_code == "AUTH_ERROR"

    def test_custom_message(self):
        """Test with custom message."""
        exc = AuthenticationError("Invalid API key")

        assert exc.message == "Invalid API key"


class TestRateLimitError:
    """Test RateLimitError."""

    def test_basic_error(self):
        """Test basic rate limit error."""
        exc = RateLimitError()

        assert exc.message == "Rate limit exceeded"
        assert exc.error_code == "RATE_LIMIT_ERROR"

    def test_with_retry_after(self):
        """Test error with retry after."""
        exc = RateLimitError(retry_after=60)

        assert exc.retry_after == 60
        assert exc.details["retry_after_seconds"] == 60

    def test_with_limit_info(self):
        """Test error with limit information."""
        exc = RateLimitError(
            "Too many requests",
            retry_after=30,
            limit=100,
            remaining=0,
        )

        assert exc.details["retry_after_seconds"] == 30
        assert exc.details["rate_limit"] == 100
        assert exc.details["remaining"] == 0


class TestTimeoutError:
    """Test TimeoutError."""

    def test_basic_error(self):
        """Test basic timeout error."""
        exc = TimeoutError()

        assert exc.message == "Request timed out"
        assert exc.error_code == "TIMEOUT_ERROR"

    def test_with_details(self):
        """Test error with timeout details."""
        exc = TimeoutError(
            "Operation timed out",
            timeout_seconds=30.5,
            operation="api_call",
        )

        assert exc.details["timeout_seconds"] == 30.5
        assert exc.details["operation"] == "api_call"


class TestUnsupportedOperationError:
    """Test UnsupportedOperationError."""

    def test_basic_error(self):
        """Test basic unsupported operation error."""
        exc = UnsupportedOperationError("create_embedding")

        assert exc.operation == "create_embedding"
        assert exc.message == "Operation 'create_embedding' is not supported"
        assert exc.error_code == "UNSUPPORTED_OPERATION"

    def test_with_reason(self):
        """Test error with reason."""
        exc = UnsupportedOperationError(
            "create_embedding",
            reason="Embeddings API not configured",
        )

        assert "Embeddings API not configured" in exc.message

    def test_with_supported_operations(self):
        """Test error with supported operations list."""
        exc = UnsupportedOperationError(
            "invalid_op",
            supported_operations=["chat", "generate", "list_models"],
        )

        assert exc.details["supported_operations"] == [
            "chat",
            "generate",
            "list_models",
        ]


class TestStreamingError:
    """Test StreamingError."""

    def test_basic_error(self):
        """Test basic streaming error."""
        exc = StreamingError("Stream interrupted")

        assert exc.error_code == "STREAMING_ERROR"

    def test_with_chunk_info(self):
        """Test error with chunk information."""
        exc = StreamingError(
            "Invalid chunk",
            chunk_index=42,
            partial_response="This is the partial resp",
        )

        assert exc.details["chunk_index"] == 42
        assert exc.details["partial_response_length"] == 24
        assert exc.details["partial_response_preview"] == "This is the partial resp"

    def test_with_long_partial_response(self):
        """Test error with long partial response."""
        long_response = "x" * 200
        exc = StreamingError("Error", partial_response=long_response)

        assert exc.details["partial_response_length"] == 200
        assert exc.details["partial_response_preview"] == "x" * 100
        assert len(exc.details["partial_response_preview"]) == 100


class TestExceptionFromStatusCode:
    """Test exception_from_status_code function."""

    def test_known_status_codes(self):
        """Test creating exceptions from known status codes."""
        # 400 -> ValidationError
        exc = exception_from_status_code(400, "Bad request")
        assert isinstance(exc, ValidationError)

        # 401 -> AuthenticationError
        exc = exception_from_status_code(401, "Unauthorized")
        assert isinstance(exc, AuthenticationError)

        # 404 -> ModelNotFoundError
        exc = exception_from_status_code(404, "Not found")
        assert isinstance(exc, ModelNotFoundError)

        # 429 -> RateLimitError
        exc = exception_from_status_code(429, "Too many requests")
        assert isinstance(exc, RateLimitError)

        # 408 -> TimeoutError
        exc = exception_from_status_code(408, "Request timeout")
        assert isinstance(exc, TimeoutError)

    def test_unknown_status_codes(self):
        """Test creating exceptions from unknown status codes."""
        # Should create UpstreamError
        exc = exception_from_status_code(502, "Bad gateway")
        assert isinstance(exc, UpstreamError)
        assert exc.status_code == 502

    def test_with_kwargs(self):
        """Test passing additional kwargs."""
        exc = exception_from_status_code(
            429,
            "Rate limited",
            retry_after=60,
            limit=100,
        )
        assert isinstance(exc, RateLimitError)
        assert exc.retry_after == 60

    def test_status_code_mapping(self):
        """Test the STATUS_CODE_TO_EXCEPTION mapping."""
        assert STATUS_CODE_TO_EXCEPTION[400] == ValidationError
        assert STATUS_CODE_TO_EXCEPTION[401] == AuthenticationError
        assert STATUS_CODE_TO_EXCEPTION[403] == AuthenticationError
        assert STATUS_CODE_TO_EXCEPTION[404] == ModelNotFoundError
        assert STATUS_CODE_TO_EXCEPTION[429] == RateLimitError
        assert STATUS_CODE_TO_EXCEPTION[408] == TimeoutError
        assert STATUS_CODE_TO_EXCEPTION[504] == TimeoutError
