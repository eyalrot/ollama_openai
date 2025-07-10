"""
Error handling middleware for FastAPI.
"""

import traceback
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.exceptions import (
    ProxyException,
    UpstreamError,
    ValidationError,
)
from src.utils.logging import get_logger, request_id_context


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions and converting them to appropriate HTTP responses.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        logger_name: Optional[str] = None,
        include_stacktrace: bool = False,
        debug: bool = False,
    ):
        """
        Initialize error handler middleware.

        Args:
            app: The ASGI application
            logger_name: Logger name to use
            include_stacktrace: Include stacktrace in error responses
            debug: Debug mode (shows more error details)
        """
        super().__init__(app)
        self.logger = get_logger(logger_name or "middleware.error_handler")
        self.include_stacktrace = include_stacktrace
        self.debug = debug

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and handle any exceptions.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response or error response
        """
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            return await self._handle_exception(request, exc)

    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        Handle an exception and convert it to a JSON response.

        Args:
            request: The request that caused the exception
            exc: The exception to handle

        Returns:
            JSON error response
        """
        request_id = request_id_context.get()

        # Handle Pydantic validation errors
        if isinstance(exc, PydanticValidationError):
            return await self._handle_pydantic_validation_error(exc, request_id)

        # Handle our custom exceptions
        if isinstance(exc, ProxyException):
            return await self._handle_proxy_exception(exc, request_id)

        # Handle generic exceptions
        return await self._handle_generic_exception(exc, request_id)

    async def _handle_pydantic_validation_error(
        self,
        exc: PydanticValidationError,
        request_id: Optional[str],
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        # Convert Pydantic errors to our ValidationError
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append(
                {
                    "field": field,
                    "message": error["msg"],
                    "type": error["type"],
                }
            )

        validation_error = ValidationError(
            "Request validation failed",
            details={"validation_errors": errors},
        )

        return await self._create_error_response(validation_error, 400, request_id)

    async def _handle_proxy_exception(
        self,
        exc: ProxyException,
        request_id: Optional[str],
    ) -> JSONResponse:
        """Handle our custom proxy exceptions."""
        # Determine status code
        status_code = 500  # Default

        if isinstance(exc, ValidationError):
            status_code = 400
        elif isinstance(exc, UpstreamError) or hasattr(exc, "status_code"):
            status_code = exc.status_code
        else:
            # Map error codes to status codes
            error_code_mapping = {
                "VALIDATION_ERROR": 400,
                "AUTH_ERROR": 401,
                "MODEL_NOT_FOUND": 404,
                "RATE_LIMIT_ERROR": 429,
                "TIMEOUT_ERROR": 408,
                "CONFIG_ERROR": 500,
                "TRANSLATION_ERROR": 500,
                "STREAMING_ERROR": 500,
                "UNSUPPORTED_OPERATION": 501,
            }
            status_code = error_code_mapping.get(exc.error_code, 500)

        return await self._create_error_response(exc, status_code, request_id)

    async def _handle_generic_exception(
        self,
        exc: Exception,
        request_id: Optional[str],
    ) -> JSONResponse:
        """Handle generic Python exceptions."""
        # Log the full exception
        self.logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "exception_type": type(exc).__name__,
                }
            },
        )

        # Create a generic error response
        error_dict: Dict[str, Any] = {
            "error": {
                "type": "InternalServerError",
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "request_id": request_id,
            }
        }

        # Add debug info if enabled
        if self.debug:
            error_dict["error"]["debug_message"] = str(exc)
            error_dict["error"]["exception_type"] = type(exc).__name__

        if self.include_stacktrace and self.debug:
            error_dict["error"]["stacktrace"] = traceback.format_exc().split("\n")

        return JSONResponse(
            status_code=500,
            content=error_dict,
        )

    async def _create_error_response(
        self,
        exc: ProxyException,
        status_code: int,
        request_id: Optional[str],
    ) -> JSONResponse:
        """
        Create a JSON error response from a ProxyException.

        Args:
            exc: The exception
            status_code: HTTP status code
            request_id: Request ID

        Returns:
            JSON error response
        """
        # Get the error dictionary
        error_dict = exc.to_dict()

        # Add request ID
        if request_id:
            error_dict["error"]["request_id"] = request_id

        # Add stacktrace if configured
        if self.include_stacktrace and self.debug:
            error_dict["error"]["stacktrace"] = traceback.format_exc().split("\n")

        # Log the error
        log_method = self.logger.error if status_code >= 500 else self.logger.warning
        log_method(
            f"Request failed: {exc.message}",
            extra={
                "extra_data": {
                    "status_code": status_code,
                    "error_code": exc.error_code,
                    "request_id": request_id,
                    **exc.details,
                }
            },
        )

        return JSONResponse(
            status_code=status_code,
            content=error_dict,
        )


def create_exception_handler(debug: bool = False) -> Callable:
    """
    Create an exception handler function for FastAPI.

    Args:
        debug: Whether to include debug information

    Returns:
        Exception handler function
    """
    logger = get_logger("exception_handler")

    async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle exceptions for FastAPI."""
        request_id = request_id_context.get()

        if isinstance(exc, ProxyException):
            error_dict = exc.to_dict()
            if request_id:
                error_dict["error"]["request_id"] = request_id

            # Determine status code
            if isinstance(exc, UpstreamError):
                status_code = exc.status_code
            else:
                status_code = 500

            return JSONResponse(status_code=status_code, content=error_dict)

        # Generic exception handling
        logger.error(
            "Unhandled exception",
            exc_info=exc,
            extra={"extra_data": {"request_id": request_id}},
        )

        error_content = {
            "error": {
                "type": "InternalServerError",
                "code": "INTERNAL_ERROR",
                "message": "An internal error occurred",
                "request_id": request_id,
            }
        }

        if debug:
            error_content["error"]["debug_message"] = str(exc)
            error_content["error"]["exception_type"] = type(exc).__name__

        return JSONResponse(status_code=500, content=error_content)

    return exception_handler
