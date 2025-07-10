"""
Logging middleware for FastAPI with request ID tracking.
"""

import json
import time
import uuid
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.utils.exceptions import ProxyException
from src.utils.logging import get_logger, request_id_context


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses with request ID tracking.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        logger_name: Optional[str] = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        mask_sensitive_headers: bool = True,
        exclude_paths: Optional[set[str]] = None,
    ):
        """
        Initialize logging middleware.

        Args:
            app: The ASGI application
            logger_name: Logger name to use
            log_request_body: Whether to log request bodies
            log_response_body: Whether to log response bodies
            mask_sensitive_headers: Whether to mask sensitive headers
            exclude_paths: Set of paths to exclude from logging
        """
        super().__init__(app)
        self.logger = get_logger(logger_name or "middleware.logging")
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.mask_sensitive_headers = mask_sensitive_headers
        self.exclude_paths = exclude_paths or {"/health", "/metrics"}
        self.sensitive_headers = {
            "authorization",
            "x-api-key",
            "api-key",
            "x-auth-token",
            "cookie",
            "set-cookie",
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and response with logging.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response
        """
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate request ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request_id_context.set(request_id)

        # Start timing
        start_time = time.time()

        # Log request
        await self._log_request(request, request_id)

        # Process request
        try:
            response = await call_next(request)

            # Add request ID to response headers
            response.headers["x-request-id"] = request_id

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            await self._log_response(request, response, duration_ms, request_id)

            return response

        except Exception as exc:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            await self._log_error(request, exc, duration_ms, request_id)

            # Re-raise the exception
            raise

    async def _log_request(self, request: Request, request_id: str) -> None:
        """Log incoming request details."""
        log_data: Dict[str, Any] = {
            "event": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "headers": self._sanitize_headers(dict(request.headers)),
        }

        # Add body if configured
        if self.log_request_body and request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                # Store body for later use by route handlers
                request._body = body

                # Try to parse as JSON
                try:
                    log_data["body"] = json.loads(body)
                except json.JSONDecodeError:
                    # If not JSON, log first 1000 chars
                    log_data["body"] = body.decode("utf-8", errors="ignore")[:1000]
                    if len(body) > 1000:
                        log_data["body_truncated"] = True
            except Exception as e:
                log_data["body_error"] = str(e)

        self.logger.info("Incoming request", extra={"extra_data": log_data})

    async def _log_response(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        request_id: str,
    ) -> None:
        """Log response details."""
        log_data: Dict[str, Any] = {
            "event": "response",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "headers": self._sanitize_headers(dict(response.headers)),
        }

        # Add response body if configured and not streaming
        if self.log_response_body and not isinstance(response, StreamingResponse):
            if hasattr(response, "body"):
                try:
                    # Try to parse as JSON
                    try:
                        log_data["body"] = json.loads(response.body)
                    except json.JSONDecodeError:
                        # If not JSON, log first 1000 chars
                        body_str = response.body.decode("utf-8", errors="ignore")[:1000]
                        log_data["body"] = body_str
                        if len(response.body) > 1000:
                            log_data["body_truncated"] = True
                except Exception as e:
                    log_data["body_error"] = str(e)

        # Choose log level based on status code
        if response.status_code >= 500:
            self.logger.error(
                "Request failed with server error", extra={"extra_data": log_data}
            )
        elif response.status_code >= 400:
            self.logger.warning(
                "Request failed with client error", extra={"extra_data": log_data}
            )
        else:
            self.logger.info("Request completed", extra={"extra_data": log_data})

    async def _log_error(
        self,
        request: Request,
        exception: Exception,
        duration_ms: float,
        request_id: str,
    ) -> None:
        """Log error details."""
        log_data: Dict[str, Any] = {
            "event": "error",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "duration_ms": round(duration_ms, 2),
            "error_type": type(exception).__name__,
            "error_message": str(exception),
        }

        # Add ProxyException details if available
        if isinstance(exception, ProxyException):
            log_data["error_code"] = exception.error_code
            log_data["error_details"] = exception.details

        self.logger.error(
            "Request failed with exception",
            exc_info=exception,
            extra={"extra_data": log_data},
        )

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Sanitize headers by masking sensitive values.

        Args:
            headers: Original headers

        Returns:
            Sanitized headers
        """
        if not self.mask_sensitive_headers:
            return headers

        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                # Mask all but first 4 chars
                if len(value) > 4:
                    sanitized[key] = value[:4] + "*" * (len(value) - 4)
                else:
                    sanitized[key] = "*" * len(value)
            else:
                sanitized[key] = value

        return sanitized


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Simple middleware just for request ID injection if not using full logging middleware.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to context and response headers."""
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request_id_context.set(request_id)

        response = await call_next(request)
        response.headers["x-request-id"] = request_id

        return response
