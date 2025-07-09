"""
Chat and generation endpoints for the Ollama API.

This module handles both Ollama-style (/api) and OpenAI-style (/v1) endpoints
for chat completions and text generation.
"""

import json
from typing import AsyncGenerator, Union

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

from src.models import (
    OllamaGenerateRequest,
    OllamaChatRequest,
    OpenAIChatRequest,
    OpenAIChatResponse,
)
from src.translators.chat import ChatTranslator
from src.config import get_settings
from src.utils.exceptions import (
    UpstreamError,
    TranslationError,
    ValidationError,
)
from src.utils.logging import get_logger
from src.utils.http_client import RetryClient, retry_client_context

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


@router.post("/generate")
@router.post("/completions")  # OpenAI-style endpoint
async def generate(
    request: OllamaGenerateRequest,
    fastapi_request: Request,
):
    """
    Handle Ollama generate requests (text-only in Phase 1).

    This endpoint accepts Ollama-style generation requests and translates them
    to OpenAI chat completion format for processing.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

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
@router.post("/chat/completions")  # OpenAI-style endpoint
async def chat(
    request: OllamaChatRequest,
    fastapi_request: Request,
):
    """
    Handle Ollama chat requests (text-only in Phase 1).

    This endpoint accepts Ollama-style chat requests with message history
    and processes them through the OpenAI backend.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

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
