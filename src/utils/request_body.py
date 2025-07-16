"""
Utility for safely reading request bodies in FastAPI when middleware might have already consumed them.
"""

import json
from typing import Any, Dict

from fastapi import HTTPException, Request, status

from src.utils.logging import get_logger

logger = get_logger(__name__)


async def get_body_bytes(request: Request) -> bytes:
    """
    Safely get request body bytes, checking multiple locations where middleware might have cached it.

    This function handles the common issue in FastAPI/Starlette where the request body
    can only be consumed once, and middleware may have already read it.

    Args:
        request: The FastAPI request object

    Returns:
        The raw request body as bytes

    Raises:
        HTTPException: If the body cannot be read
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Check if body was cached by logging middleware
    if hasattr(request, "_body"):
        logger.debug(
            "Using cached body from request._body",
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "body_length": len(request._body),
                }
            },
        )
        return request._body

    # Check if body was cached in request state by metrics middleware
    if hasattr(request.state, "body"):
        body = request.state.body
        if isinstance(body, bytes):
            logger.debug(
                "Using cached body from request.state.body",
                extra={
                    "extra_data": {"request_id": request_id, "body_length": len(body)}
                },
            )
            return body

    # Try to read the body (this will fail if already consumed)
    try:
        logger.debug(
            "No cached body found, attempting to read directly",
            extra={"extra_data": {"request_id": request_id}},
        )
        body = await request.body()
        # Cache it for potential future use
        request._body = body
        return body
    except Exception as e:
        logger.error(
            f"Failed to read request body: {e}",
            extra={"extra_data": {"request_id": request_id, "error": str(e)}},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body has already been consumed and is not available",
        )


async def get_body_json(request: Request) -> Dict[str, Any]:
    """
    Safely get request body as parsed JSON.

    Args:
        request: The FastAPI request object

    Returns:
        The parsed JSON body as a dictionary

    Raises:
        HTTPException: If the body cannot be read or is not valid JSON
    """
    body = await get_body_bytes(request)

    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(
            f"Invalid JSON in request body: {e}",
            extra={
                "extra_data": {
                    "request_id": getattr(request.state, "request_id", "unknown")
                }
            },
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in request body: {str(e)}",
        )
