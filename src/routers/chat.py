"""
Chat and generation endpoints for the Ollama API.

This module handles both Ollama-style (/api) and OpenAI-style (/v1) endpoints
for chat completions and text generation.
"""

import json
from collections.abc import AsyncGenerator
from typing import Union

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from src.config import get_settings
from src.models import (
    OllamaChatRequest,
    OllamaGenerateRequest,
    OpenAIChatRequest,
    OpenAIChatResponse,
)
from src.translators.chat import ChatTranslator
from src.utils.exceptions import (
    TranslationError,
    UpstreamError,
    ValidationError,
)
from src.utils.http_client import RetryClient, retry_client_context
from src.utils.logging import get_logger
from src.utils.request_body import get_body_json

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()

# Initialize translator
translator = ChatTranslator()


async def make_openai_request(
    client: RetryClient,
    openai_request: OpenAIChatRequest,
    stream: bool = False,
) -> Union[httpx.Response, httpx.Response]:
    """Make a request to the OpenAI-compatible backend."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"{settings.OPENAI_API_BASE_URL}/chat/completions"

    logger.debug(
        "Making request to OpenAI backend",
        extra={
            "extra_data": {
                "url": url,
                "model": openai_request.model,
                "stream": stream,
                "message_count": len(openai_request.messages),
            }
        },
    )

    try:
        # Use retry client for both streaming and non-streaming
        response = await client.request_with_retry(
            "POST",
            url,
            json=openai_request.model_dump(exclude_none=True),
            headers=headers,
        )

        if response.status_code != 200:
            logger.error(
                "OpenAI backend error",
                extra={
                    "extra_data": {
                        "status_code": response.status_code,
                        "response_text": response.text[:500],  # First 500 chars
                    }
                },
            )

            raise UpstreamError(
                "OpenAI backend returned error",
                status_code=response.status_code,
                service="openai",
                details={"response": response.text[:500]},
            )

        return response

    except httpx.TimeoutException:
        logger.error("Request timeout")
        raise UpstreamError(
            "Request timeout",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            service="openai",
            details={"timeout": settings.REQUEST_TIMEOUT},
        )
    except httpx.NetworkError as e:
        logger.error(f"HTTP request error: {e}")
        raise UpstreamError(
            f"HTTP request failed: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            service="openai",
        )


async def stream_response(
    client: RetryClient,
    openai_request: OpenAIChatRequest,
    original_request: Union[OllamaGenerateRequest, OllamaChatRequest],
) -> AsyncGenerator[str, None]:
    """Stream responses from OpenAI and translate them to Ollama format."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"{settings.OPENAI_API_BASE_URL}/chat/completions"

    try:
        # Use stream_with_retry for streaming requests
        async for chunk in client.stream_with_retry(
            "POST",
            url,
            json=openai_request.model_dump(exclude_none=True),
            headers=headers,
        ):
            # Process each chunk
            chunk_str = chunk.decode("utf-8")
            for line in chunk_str.split("\n"):
                if not line.strip():
                    continue

                if line == "data: [DONE]":
                    # Send final chunk
                    final_chunk = translator.translate_streaming_response(
                        "[DONE]",  # type: ignore
                        original_request,
                        is_last_chunk=True,
                    )
                    if final_chunk:
                        yield json.dumps(final_chunk) + "\n"
                    return

                if line.startswith("data: "):
                    try:
                        # Parse the JSON data
                        data = json.loads(line[6:])

                        # Translate to Ollama format
                        ollama_chunk = translator.translate_streaming_response(
                            data, original_request
                        )

                        if ollama_chunk:
                            yield json.dumps(ollama_chunk) + "\n"

                    except json.JSONDecodeError as e:
                        logger.warning(
                            "Failed to parse streaming chunk",
                            extra={"extra_data": {"line": line, "error": str(e)}},
                        )
                        continue

    except httpx.TimeoutException:
        logger.error("Request timeout while streaming")
        raise UpstreamError(
            "Request timeout",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            service="openai",
            details={"timeout": settings.REQUEST_TIMEOUT},
        )
    except httpx.NetworkError as e:
        logger.error(f"HTTP request error: {e}")
        raise UpstreamError(
            f"HTTP request failed: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            service="openai",
        )
    except Exception as e:
        logger.error(f"Unexpected streaming error: {e}", exc_info=e)
        raise


# OpenAI-style endpoints (defined first to take precedence)
@router.post("/chat/completions")  # OpenAI-style endpoint
async def openai_chat_completions(
    fastapi_request: Request,
):
    """
    Handle OpenAI-style chat completion requests.

    This endpoint accepts OpenAI-style chat requests and forwards them
    directly to the OpenAI backend without translation.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    logger.debug(
        "OpenAI endpoint handler started",
        extra={
            "extra_data": {
                "request_id": request_id,
                "path": fastapi_request.url.path,
            }
        },
    )

    # Get request body using the utility function
    try:
        request = await get_body_json(fastapi_request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}",
        )

    logger.info(
        "OpenAI chat completion request received",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model": request.get("model", "unknown"),
                "message_count": len(request.get("messages", [])),
                "stream": request.get("stream", False),
            }
        },
    )

    try:
        async with retry_client_context() as client:
            # Forward request directly to OpenAI without Pydantic validation
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            url = f"{settings.OPENAI_API_BASE_URL}/chat/completions"

            if request.get("stream", False):
                # Handle streaming
                return StreamingResponse(
                    openai_stream_response_dict(client, request),
                    media_type="text/plain",
                    headers={
                        "X-Request-ID": request_id,
                        "Cache-Control": "no-cache",
                    },
                )
            else:
                # Make non-streaming request
                response = await client.request_with_retry(
                    "POST",
                    url,
                    json=request,
                    headers=headers,
                )

                if response.status_code != 200:
                    logger.error(
                        "OpenAI backend error",
                        extra={
                            "extra_data": {
                                "status_code": response.status_code,
                                "response_text": response.text[:500],
                            }
                        },
                    )

                    raise UpstreamError(
                        "OpenAI backend returned error",
                        status_code=response.status_code,
                        service="openai",
                        details={"response": response.text[:500]},
                    )

                # Return response directly
                return JSONResponse(
                    content=response.json(),
                    headers={"X-Request-ID": request_id},
                )

    except UpstreamError as e:
        # Re-raise with appropriate status code
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Upstream error: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error in OpenAI chat completions endpoint", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/completions")  # OpenAI-style text completion endpoint
async def openai_completions(
    fastapi_request: Request,
):
    """
    Handle OpenAI-style text completion requests.

    This endpoint accepts OpenAI-style requests for text completion
    and forwards them to the chat completions endpoint.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    # Get request body using the utility function
    try:
        request = await get_body_json(fastapi_request)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}",
        )

    logger.info(
        "OpenAI text completion request received",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model": request.get("model", "unknown"),
                "message_count": len(request.get("messages", [])),
                "stream": request.get("stream", False),
            }
        },
    )

    # Forward to chat completions since OpenAI completions API is being phased out
    return await openai_chat_completions(fastapi_request)


# Ollama-style endpoints
@router.post("/generate")
async def generate(
    fastapi_request: Request,
):
    """
    Handle Ollama generate requests (text-only in Phase 1).

    This endpoint accepts Ollama-style generation requests and translates them
    to OpenAI chat completion format for processing.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    # Get request body using the utility function
    try:
        request_dict = await get_body_json(fastapi_request)
        request = OllamaGenerateRequest(**request_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}",
        )

    logger.info(
        "Generate request received",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model": request.model,
                "prompt_length": len(request.prompt),
                "stream": request.stream,
            }
        },
    )

    try:
        # Translate to OpenAI format
        openai_request = translator.translate_request(request)

        async with retry_client_context() as client:
            if request.stream:
                # Return streaming response
                return StreamingResponse(
                    stream_response(client, openai_request, request),
                    media_type="application/x-ndjson",
                    headers={
                        "X-Request-ID": request_id,
                        "Cache-Control": "no-cache",
                    },
                )
            else:
                # Make non-streaming request
                response = await make_openai_request(
                    client, openai_request, stream=False
                )

                # Parse response
                openai_response = OpenAIChatResponse(**response.json())

                # Translate response back to Ollama format
                ollama_response = translator.translate_response(
                    openai_response, request
                )

                return JSONResponse(
                    content=ollama_response.model_dump(exclude_none=True),
                    headers={"X-Request-ID": request_id},
                )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except TranslationError as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Translation error: {str(e)}",
        )
    except UpstreamError as e:
        # Re-raise with appropriate status code
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Upstream error: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error in generate endpoint", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/chat")
async def ollama_chat(
    fastapi_request: Request,
):
    """
    Handle Ollama chat requests (text-only in Phase 1).

    This endpoint accepts Ollama-style chat requests with message history
    and processes them through the OpenAI backend.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    # Get request body using the utility function
    try:
        request_dict = await get_body_json(fastapi_request)
        request = OllamaChatRequest(**request_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}",
        )

    logger.info(
        "Chat request received",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model": request.model,
                "message_count": len(request.messages),
                "stream": request.stream,
            }
        },
    )

    try:
        # Translate to OpenAI format
        openai_request = translator.translate_request(request)

        async with retry_client_context() as client:
            if request.stream:
                # Return streaming response
                return StreamingResponse(
                    stream_response(client, openai_request, request),
                    media_type="application/x-ndjson",
                    headers={
                        "X-Request-ID": request_id,
                        "Cache-Control": "no-cache",
                    },
                )
            else:
                # Make non-streaming request
                response = await make_openai_request(
                    client, openai_request, stream=False
                )

                # Parse response
                openai_response = OpenAIChatResponse(**response.json())

                # Translate response back to Ollama format
                ollama_response = translator.translate_response(
                    openai_response, request
                )

                return JSONResponse(
                    content=ollama_response.model_dump(exclude_none=True),
                    headers={"X-Request-ID": request_id},
                )

    except ValidationError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except TranslationError as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Translation error: {str(e)}",
        )
    except UpstreamError as e:
        # Re-raise with appropriate status code
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Upstream error: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error in chat endpoint", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def openai_stream_response(
    client: RetryClient,
    openai_request: OpenAIChatRequest,
) -> AsyncGenerator[str, None]:
    """Stream responses from OpenAI in OpenAI format (no translation)."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"{settings.OPENAI_API_BASE_URL}/chat/completions"

    try:
        # Use stream_with_retry for streaming requests
        async for chunk in client.stream_with_retry(
            "POST",
            url,
            json=openai_request.model_dump(exclude_none=True),
            headers=headers,
        ):
            # Pass through chunks directly without translation
            yield chunk.decode("utf-8")

    except httpx.TimeoutException:
        logger.error("Request timeout while streaming")
        raise UpstreamError(
            "Request timeout",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            service="openai",
            details={"timeout": settings.REQUEST_TIMEOUT},
        )
    except httpx.NetworkError as e:
        logger.error(f"HTTP request error: {e}")
        raise UpstreamError(
            f"HTTP request failed: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            service="openai",
        )
    except Exception as e:
        logger.error(f"Unexpected streaming error: {e}", exc_info=e)
        raise


async def openai_stream_response_dict(
    client: RetryClient,
    request_dict: dict,
) -> AsyncGenerator[str, None]:
    """Stream responses from OpenAI using dict request (no Pydantic validation)."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"{settings.OPENAI_API_BASE_URL}/chat/completions"

    try:
        # Use stream_with_retry for streaming requests
        async for chunk in client.stream_with_retry(
            "POST",
            url,
            json=request_dict,  # Pass dict directly
            headers=headers,
        ):
            # Pass through chunks directly without translation
            yield chunk.decode("utf-8")

    except httpx.TimeoutException:
        logger.error("Request timeout while streaming")
        raise UpstreamError(
            "Request timeout",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            service="openai",
            details={"timeout": settings.REQUEST_TIMEOUT},
        )
    except httpx.NetworkError as e:
        logger.error(f"HTTP request error: {e}")
        raise UpstreamError(
            f"HTTP request failed: {str(e)}",
            status_code=status.HTTP_502_BAD_GATEWAY,
            service="openai",
        )
    except Exception as e:
        logger.error(f"Unexpected streaming error: {e}", exc_info=e)
        raise
