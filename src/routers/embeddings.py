"""
Embeddings endpoint for the Ollama API.

This module handles both Ollama-style (/api) and OpenAI-style (/v1) endpoints
for text embeddings.
"""

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.models import (
    OllamaEmbeddingRequest,
    OpenAIEmbeddingRequest,
    OpenAIEmbeddingResponse,
)
from src.translators.embeddings import EmbeddingsTranslator
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
translator = EmbeddingsTranslator()


async def make_openai_embedding_request(
    client: RetryClient,
    openai_request: OpenAIEmbeddingRequest,
) -> httpx.Response:
    """Make an embedding request to the OpenAI-compatible backend."""
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    url = f"{settings.OPENAI_API_BASE_URL}/embeddings"

    logger.debug(
        "Making embedding request to OpenAI backend",
        extra={
            "extra_data": {
                "url": url,
                "model": openai_request.model,
                "input_count": (
                    len(openai_request.input)
                    if isinstance(openai_request.input, list)
                    else 1
                ),
                "encoding_format": openai_request.encoding_format,
            }
        },
    )

    try:
        # Use retry client for embeddings request
        response = await client.request_with_retry(
            "POST",
            url,
            json=openai_request.model_dump(exclude_none=True),
            headers=headers,
        )

        if response.status_code != 200:
            logger.error(
                "OpenAI embedding backend error",
                extra={
                    "extra_data": {
                        "status_code": response.status_code,
                        "response_text": response.text[:500],  # First 500 chars
                    }
                },
            )

            raise UpstreamError(
                "OpenAI embedding backend returned error",
                status_code=response.status_code,
                service="openai",
                details={"response": response.text[:500]},
            )

        return response

    except httpx.TimeoutException:
        logger.error("Embedding request timeout")
        raise UpstreamError(
            "Embedding request timeout",
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            service="openai",
        )
    except httpx.ConnectError:
        logger.error("Connection error to OpenAI backend")
        raise UpstreamError(
            "Cannot connect to OpenAI backend",
            status_code=status.HTTP_502_BAD_GATEWAY,
            service="openai",
        )
    except Exception as e:
        logger.error(f"Unexpected error in embedding request: {e}", exc_info=e)
        raise


@router.post("/embeddings")
async def embeddings_handler(
    fastapi_request: Request,
) -> JSONResponse:
    """Route to the appropriate embeddings handler based on the path prefix."""
    path = fastapi_request.url.path

    # Check if this is an Ollama-style request (/api/embeddings)
    if path.startswith("/api/"):
        return await create_embeddings_ollama_style(fastapi_request)
    else:
        # Default to OpenAI-style for /v1/embeddings
        return await create_embeddings_openai_style(fastapi_request)


async def create_embeddings_openai_style(
    fastapi_request: Request,
) -> JSONResponse:
    """
    Create embeddings using OpenAI-style format.

    This endpoint accepts OpenAI-style embedding requests and forwards them
    directly to the OpenAI backend without translation.
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
        "OpenAI embedding request received",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model": request.get("model", "unknown"),
                "input_type": type(request.get("input", "")).__name__,
            }
        },
    )

    try:
        async with retry_client_context() as client:
            # Forward request directly to OpenAI
            headers = {
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            }

            url = f"{settings.OPENAI_API_BASE_URL}/embeddings"

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
        raise HTTPException(
            status_code=e.status_code,
            detail=f"Upstream error: {str(e)}",
        )
    except Exception as e:
        logger.error("Unexpected error in OpenAI embeddings endpoint", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


async def create_embeddings_ollama_style(
    fastapi_request: Request,
) -> JSONResponse:
    """
    Create embeddings for the given text input.

    Supports both single string and batch string inputs through Ollama format,
    translates to OpenAI embeddings API, and returns in Ollama format.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    # Get request body using the utility function
    try:
        request_dict = await get_body_json(fastapi_request)
        request = OllamaEmbeddingRequest(**request_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse request body: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request body: {str(e)}",
        )

    logger.info(
        "Processing embedding request",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model": request.model,
                "prompt_type": "list" if isinstance(request.prompt, list) else "string",
                "prompt_count": (
                    len(request.prompt) if isinstance(request.prompt, list) else 1
                ),
            }
        },
    )

    try:
        # Validate model name
        translator.validate_model_name(request.model)

        # Translate Ollama request to OpenAI format
        openai_request = translator.translate_request(request)

        # Make request to OpenAI backend
        async with retry_client_context() as client:
            response = await make_openai_embedding_request(client, openai_request)

        # Parse OpenAI response
        try:
            openai_response_data = response.json()
            openai_response = OpenAIEmbeddingResponse(**openai_response_data)
        except Exception as e:
            logger.error(f"Failed to parse OpenAI embedding response: {e}")
            raise UpstreamError(
                "Invalid response from OpenAI backend",
                status_code=status.HTTP_502_BAD_GATEWAY,
                service="openai",
            )

        # Translate response back to Ollama format
        ollama_response = translator.translate_response(openai_response, request)

        logger.info(
            "Embedding request completed",
            extra={
                "extra_data": {
                    "request_id": request_id,
                    "embedding_dimension": len(ollama_response.embedding),
                    "tokens_used": (
                        openai_response.usage.total_tokens
                        if openai_response.usage
                        else 0
                    ),
                }
            },
        )

        return JSONResponse(
            content=ollama_response.model_dump(),
            headers={"X-Request-ID": request_id},
        )

    except ValidationError as e:
        logger.warning(
            f"Validation error in embedding request: {e}",
            extra={"extra_data": {"request_id": request_id}},
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    except TranslationError as e:
        logger.error(
            f"Translation error in embedding request: {e}",
            extra={"extra_data": {"request_id": request_id}},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process embedding request",
        )

    except UpstreamError as e:
        logger.error(
            f"Upstream error in embedding request: {e}",
            extra={"extra_data": {"request_id": request_id}},
        )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )

    except Exception as e:
        logger.error(
            "Unexpected error in embedding endpoint",
            exc_info=e,
            extra={"extra_data": {"request_id": request_id}},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
