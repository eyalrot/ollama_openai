"""
Metrics collection middleware for FastAPI applications.

This middleware tracks request metrics including duration, status codes,
response sizes, and model usage for performance monitoring.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.logging import get_logger
from src.utils.metrics import RequestMetrics, get_metrics_collector

logger = get_logger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics.

    Tracks:
    - Request duration
    - Response status codes
    - Request/response sizes
    - Model usage (from request context)
    - Error rates
    """

    def __init__(
        self, app, track_request_body: bool = True, track_response_body: bool = True
    ):
        super().__init__(app)
        self.track_request_body = track_request_body
        self.track_response_body = track_response_body
        self.metrics_collector = get_metrics_collector()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Generate request ID if not already present
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Increment active requests counter
        await self.metrics_collector.increment_active_requests()

        # Start timing
        start_time = time.time()

        # Extract model from request if available
        model = await self._extract_model_from_request(request)

        # Get request size
        request_size = await self._get_request_size(request)

        # Initialize metrics object
        metric = RequestMetrics(
            endpoint=request.url.path,
            method=request.method,
            model=model,
            request_size=request_size,
        )

        try:
            # Process request
            response = await call_next(request)

            # Set response details
            metric.status_code = response.status_code
            metric.response_size = self._get_response_size(response)

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Record error
            metric.error = str(e)
            metric.status_code = 500
            logger.error(f"Request failed: {str(e)}", extra={"request_id": request_id})
            raise

        finally:
            # Calculate duration and record metrics
            metric.duration_ms = (time.time() - start_time) * 1000

            # Record metrics asynchronously
            await self.metrics_collector.record_request(metric)

            # Decrement active requests counter
            await self.metrics_collector.decrement_active_requests()

    async def _extract_model_from_request(self, request: Request) -> str:
        """Extract model name from request body if available."""
        if not self.track_request_body:
            return ""

        try:
            # Only process JSON requests
            if request.headers.get("content-type", "").startswith("application/json"):
                # For chat endpoints, model is typically in the body
                if "chat" in request.url.path or "completions" in request.url.path:
                    # Check if body was already read by another middleware
                    if hasattr(request, "_body"):
                        body = request._body
                    else:
                        # We need to read the body carefully to avoid consuming it
                        body = await request.body()
                        # Store body for later use by other handlers
                        request._body = body

                    if body:
                        import json

                        try:
                            data = json.loads(body)
                            model = data.get("model", "")
                            # Also store in state for backward compatibility
                            request.state.body = body
                            return model
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            logger.debug(f"Could not extract model from request: {e}")

        return ""

    async def _get_request_size(self, request: Request) -> int:
        """Get request body size in bytes."""
        if not self.track_request_body:
            return 0

        try:
            # First check if body was stored in _body by another middleware
            if hasattr(request, "_body"):
                return len(request._body)

            # Then check if we stored it in state
            if hasattr(request.state, "body"):
                return len(request.state.body)

            # Otherwise, get content-length header
            content_length = request.headers.get("content-length")
            if content_length:
                return int(content_length)
        except (ValueError, AttributeError):
            pass

        return 0

    def _get_response_size(self, response: Response) -> int:
        """Get response size in bytes."""
        if not self.track_response_body:
            return 0

        try:
            # Try to get content-length from headers
            content_length = response.headers.get("content-length")
            if content_length:
                return int(content_length)

            # For streaming responses, we can't easily get the size
            # without consuming the stream
            if hasattr(response, "body"):
                if isinstance(response.body, bytes):
                    return len(response.body)
                elif isinstance(response.body, str):
                    return len(response.body.encode("utf-8"))
        except (ValueError, AttributeError):
            pass

        return 0


# Custom middleware factory for easier integration
def create_metrics_middleware(
    track_request_body: bool = True, track_response_body: bool = True
) -> type:
    """
    Factory function to create a metrics middleware with custom configuration.

    Args:
        track_request_body: Whether to track request body size and extract model info
        track_response_body: Whether to track response body size

    Returns:
        Configured MetricsMiddleware class
    """

    class ConfiguredMetricsMiddleware(MetricsMiddleware):
        def __init__(self, app):
            super().__init__(app, track_request_body, track_response_body)

    return ConfiguredMetricsMiddleware
