"""
Custom exception classes for the proxy service.
"""


class ProxyError(Exception):
    """Base exception for proxy errors."""
    pass


class ConfigurationError(ProxyError):
    """Raised when there's a configuration issue."""
    pass


class TranslationError(ProxyError):
    """Raised when request/response translation fails."""
    pass


class UpstreamError(ProxyError):
    """Raised when the upstream OpenAI-compatible server returns an error."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ModelNotFoundError(ProxyError):
    """Raised when a requested model is not found."""
    pass


class UnsupportedOperationError(ProxyError):
    """Raised when an operation is not supported by the proxy."""
    pass