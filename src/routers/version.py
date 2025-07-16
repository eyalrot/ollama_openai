"""
Version endpoint for the Ollama-OpenAI Proxy API.

This module provides version information about the running service.
"""

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src._version import get_version, get_version_info
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


def get_build_info() -> Dict[str, Any]:
    """Get build and runtime information."""
    return {
        "python_version": os.sys.version.split()[0],
        "platform": os.sys.platform,
        "architecture": os.uname().machine if hasattr(os, "uname") else "unknown",
        "build_timestamp": datetime.now().isoformat(),
        "commit_sha": os.getenv("GITHUB_SHA", "development"),
        "build_ref": os.getenv("GITHUB_REF", "development"),
    }


@router.get("/version")
async def get_version_endpoint() -> JSONResponse:
    """
    Get version information about the service.

    Returns detailed version information including:
    - Application version
    - Build information
    - API version
    - Project metadata
    """
    try:
        version_info = get_version_info()
        build_info = get_build_info()

        response_data = {
            **version_info,
            "build_info": build_info,
            "status": "healthy",
            "uptime": "running",  # Could be enhanced with actual uptime tracking
        }

        logger.info(
            "Version endpoint accessed",
            extra={
                "extra_data": {
                    "version": get_version(),
                    "client_request": True,
                }
            },
        )

        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error in version endpoint: {e}", exc_info=True)
        return JSONResponse(
            content={
                "error": "Failed to retrieve version information",
                "status": "error",
                "version": get_version(),  # Still try to provide basic version
            },
            status_code=500,
        )


@router.get("/health")
async def health_check() -> JSONResponse:
    """
    Simple health check endpoint.

    Returns basic health status with version information.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "version": get_version(),
            "timestamp": datetime.now().isoformat(),
            "service": "ollama-openai-proxy",
        }
    )
