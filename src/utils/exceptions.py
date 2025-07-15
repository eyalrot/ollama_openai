"""
Custom exception classes for the proxy service.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union


class ProxyException(Exception):
    """
    Base exception for all proxy-related errors.

    Attributes:
        message: Human-readable error message
        error_code: Application-specific error code
        details: Additional error details
        timestamp: When the error occurred
    """

    def __init__(
        self,
        message: str,
        *,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize proxy exception.

        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": {
                "type": self.__class__.__name__,
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
                "timestamp": self.timestamp,
            }
        }

    def to_json(self) -> str:
        """Convert exception to JSON string."""
        return json.dumps(self.to_dict(), default=str)

    def __str__(self) -> str:
        """String representation of the exception."""
        if self.details:
            return f"{self.error_code}: {self.message} - {self.details}"
        return f"{self.error_code}: {self.message}"


class ConfigurationError(ProxyException):
    """Raised when there's a configuration issue."""

    def __init__(
        self, message: str, *, config_key: Optional[str] = None, **kwargs: Any
    ):
        """
        Initialize configuration error.

        Args:
            message: Error message
            config_key: The configuration key that caused the error
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key
        super().__init__(message, error_code="CONFIG_ERROR", details=details)


class ValidationError(ProxyException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        value: Any = None,
        **kwargs: Any,
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            field: The field that failed validation
            value: The invalid value
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        if field:
            details["field"] = field
        if value is not None:
            details["invalid_value"] = str(value)
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)


class TranslationError(ProxyException):
    """Raised when request/response translation fails."""

    def __init__(
        self,
        message: str,
        *,
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize translation error.

        Args:
            message: Error message
            source_format: Source API format (e.g., "ollama")
            target_format: Target API format (e.g., "openai")
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        if source_format:
            details["source_format"] = source_format
        if target_format:
            details["target_format"] = target_format
        super().__init__(message, error_code="TRANSLATION_ERROR", details=details)


class UpstreamError(ProxyException):
    """Raised when the upstream OpenAI-compatible server returns an error."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        response_data: Optional[Union[Dict[str, Any], str]] = None,
        request_id: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize upstream error.

        Args:
            message: Error message
            status_code: HTTP status code from upstream
            response_data: Response data from upstream
            request_id: Request ID for tracing
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        details["status_code"] = status_code
        if response_data:
            details["upstream_response"] = response_data
        if request_id:
            details["request_id"] = request_id

        # Include all other kwargs in details
        for key, value in kwargs.items():
            if key != "details":
                details[key] = value

        # Set error code based on status code
        if status_code >= 500:
            error_code = "UPSTREAM_SERVER_ERROR"
        elif status_code >= 400:
            error_code = "UPSTREAM_CLIENT_ERROR"
        else:
            error_code = "UPSTREAM_ERROR"

        super().__init__(message, error_code=error_code, details=details)
        self.status_code = status_code
        self.response_data = response_data


class ModelNotFoundError(ProxyException):
    """Raised when a requested model is not found."""

    def __init__(
        self, model_name: str, *, available_models: Optional[list[str]] = None
    ):
        """
        Initialize model not found error.

        Args:
            model_name: The requested model name
            available_models: Optional list of available models
        """
        message = f"Model '{model_name}' not found"
        details: Dict[str, Any] = {"requested_model": model_name}
        if available_models:
            details["available_models"] = list(available_models)
            message += f". Available models: {', '.join(available_models[:5])}"
            if len(available_models) > 5:
                message += f" and {len(available_models) - 5} more"

        super().__init__(message, error_code="MODEL_NOT_FOUND", details=details)
        self.model_name = model_name


class AuthenticationError(ProxyException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any):
        """Initialize authentication error."""
        super().__init__(
            message, error_code="AUTH_ERROR", details=kwargs.get("details", {})
        )


class RateLimitError(ProxyException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        **kwargs: Any,
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            limit: Rate limit
            remaining: Remaining requests
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        if retry_after is not None:
            details["retry_after_seconds"] = retry_after
        if limit is not None:
            details["rate_limit"] = limit
        if remaining is not None:
            details["remaining"] = remaining

        super().__init__(message, error_code="RATE_LIMIT_ERROR", details=details)
        self.retry_after = retry_after


class TimeoutError(ProxyException):
    """Raised when a request times out."""

    def __init__(
        self,
        message: str = "Request timed out",
        *,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize timeout error.

        Args:
            message: Error message
            timeout_seconds: Timeout duration
            operation: Operation that timed out
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        if timeout_seconds is not None:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation

        super().__init__(message, error_code="TIMEOUT_ERROR", details=details)


class UnsupportedOperationError(ProxyException):
    """Raised when an operation is not supported by the proxy."""

    def __init__(
        self,
        operation: str,
        *,
        reason: Optional[str] = None,
        supported_operations: Optional[list[str]] = None,
        **kwargs: Any,
    ):
        """
        Initialize unsupported operation error.

        Args:
            operation: The unsupported operation
            reason: Reason why it's not supported
            supported_operations: List of supported operations
            **kwargs: Additional details
        """
        message = f"Operation '{operation}' is not supported"
        if reason:
            message += f": {reason}"

        details = kwargs.get("details", {})
        details["unsupported_operation"] = operation
        if supported_operations:
            details["supported_operations"] = supported_operations

        super().__init__(message, error_code="UNSUPPORTED_OPERATION", details=details)
        self.operation = operation


class StreamingError(ProxyException):
    """Raised when there's an error during streaming responses."""

    def __init__(
        self,
        message: str,
        *,
        chunk_index: Optional[int] = None,
        partial_response: Optional[str] = None,
        **kwargs: Any,
    ):
        """
        Initialize streaming error.

        Args:
            message: Error message
            chunk_index: Index of the chunk that caused error
            partial_response: Partial response received before error
            **kwargs: Additional details
        """
        details = kwargs.get("details", {})
        if chunk_index is not None:
            details["chunk_index"] = chunk_index
        if partial_response:
            details["partial_response_length"] = len(partial_response)
            # Include first 100 chars of partial response
            details["partial_response_preview"] = partial_response[:100]

        super().__init__(message, error_code="STREAMING_ERROR", details=details)


# Mapping of HTTP status codes to exception classes
STATUS_CODE_TO_EXCEPTION: Dict[int, type[ProxyException]] = {
    400: ValidationError,
    401: AuthenticationError,
    403: AuthenticationError,
    404: ModelNotFoundError,
    429: RateLimitError,
    408: TimeoutError,
    504: TimeoutError,
}


def exception_from_status_code(
    status_code: int,
    message: str,
    **kwargs: Any,
) -> ProxyException:
    """
    Create an appropriate exception based on HTTP status code.

    Args:
        status_code: HTTP status code
        message: Error message
        **kwargs: Additional exception arguments

    Returns:
        Appropriate exception instance
    """
    exception_class = STATUS_CODE_TO_EXCEPTION.get(status_code, UpstreamError)

    if exception_class == UpstreamError:
        return UpstreamError(message, status_code=status_code, **kwargs)
    else:
        return exception_class(message, **kwargs)
