"""
Main entry point for the Ollama to OpenAI proxy service.
"""

import os
import uuid
import atexit
from typing import Any, Dict

from flask import Flask, request, jsonify, g
from flask_cors import CORS

from src.config import get_settings
from src.utils.exceptions import ProxyException, UpstreamError
from src.utils.http_client import close_global_client
from src.utils.logging import get_logger, setup_logging

# Initialize settings and logging
settings = get_settings()
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Log environment variables for debugging
logger.info(
    "Environment variables for SSL",
    extra={
        "extra_data": {
            "env_DISABLE_SSL_VERIFICATION": os.getenv("DISABLE_SSL_VERIFICATION", "not_set"),
            "env_DEBUG": os.getenv("DEBUG", "not_set"),
        }
    },
)

logger.info(
    "Starting Ollama-OpenAI Proxy",
    extra={
        "extra_data": {
            "proxy_port": settings.PROXY_PORT,
            "target_url": settings.OPENAI_API_BASE_URL,
            "log_level": settings.LOG_LEVEL,
            "version": "1.0.0",
            "disable_ssl_verification": settings.DISABLE_SSL_VERIFICATION,
            "ssl_verification_enabled": not settings.DISABLE_SSL_VERIFICATION,
            "debug": settings.DEBUG,
        }
    },
)

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, 
     origins=["*"],
     allow_headers=["*"],
     methods=["*"],
     expose_headers=["X-Request-ID"])


# Request ID middleware
@app.before_request
def add_request_id():
    """Add unique request ID to each request."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    g.request_id = request_id


@app.after_request
def add_request_id_to_response(response):
    """Add request ID to response headers."""
    response.headers["X-Request-ID"] = getattr(g, "request_id", "unknown")
    return response


# Error handlers
@app.exception_handler(ProxyException)
async def proxy_exception_handler(
    request: Request, exc: ProxyException
) -> JSONResponse:
    """Handle proxy-specific exceptions."""
    return JSONResponse(
        status_code=400,  # ProxyException doesn't have a status_code attribute
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "code": exc.error_code,
                "details": exc.details,
            }
        },
        headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")},
    )


@app.exception_handler(UpstreamError)
async def upstream_error_handler(request: Request, exc: UpstreamError) -> JSONResponse:
    """Handle upstream service errors."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": "upstream_error",
                "status_code": exc.status_code,
                "service": (
                    exc.details.get("service") if "service" in exc.details else None
                ),
                "details": exc.details,
            }
        },
        headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(
        f"Unexpected error: {str(exc)}",
        exc_info=exc,
        extra={
            "extra_data": {
                "request_id": getattr(request.state, "request_id", "unknown"),
                "path": request.url.path,
                "method": request.method,
            }
        },
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "type": "internal_error",
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
        headers={"X-Request-ID": getattr(request.state, "request_id", "unknown")},
    )


# Include routers
app.include_router(chat.router, prefix="/v1", tags=["chat"])
app.include_router(models.router, prefix="/v1", tags=["models"])
app.include_router(embeddings.router, prefix="/v1", tags=["embeddings"])
app.include_router(metrics.router, prefix="/v1", tags=["metrics"])

# Also include Ollama-style endpoints
app.include_router(chat.router, prefix="/api", tags=["ollama-chat"])
app.include_router(models.router, prefix="/api", tags=["ollama-mode"])
app.include_router(embeddings.router, prefix="/api", tags=["ollama-embeddings"])
app.include_router(metrics.router, prefix="/api", tags=["ollama-metrics"])


# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "ollama-openai-proxy", "version": "1.0.0"}


@app.get("/ready", tags=["health"])
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.

    Verifies the service is ready to handle requests.
    """
    # In the future, this could check:
    # - Database connections
    # - External service availability
    # - Model loading status

    return {
        "status": "ready",
        "service": "ollama-openai-proxy",
        "checks": {"config": "ok", "logging": "ok"},
    }


# Root endpoint
@app.get("/", tags=["info"])
async def root() -> Dict[str, Any]:
    """Root endpoint with service information."""
    return {
        "service": "Ollama-OpenAI Proxy",
        "version": "1.0.0",
        "description": "Proxy service to translate Ollama API calls to OpenAI format",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs" if settings.DEBUG else None,
            "openai": {
                "chat": "/v1/chat/completions",
                "models": "/v1/models",
                "embeddings": "/v1/embeddings",
                "metrics": "/v1/metrics",
            },
            "ollama": {
                "generate": "/api/generate",
                "chat": "/api/chat",
                "models": "/api/tags",
                "embeddings": "/api/embeddings",
                "metrics": "/api/metrics",
            },
        },
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PROXY_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
