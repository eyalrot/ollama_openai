"""
Model management endpoints for the Ollama API.

This module provides endpoints for listing models, showing model information,
and returning appropriate errors for unsupported model management operations.
"""

import hashlib
from datetime import datetime, timezone
from typing import List

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.config import get_settings
from src.models import (
    OllamaDeleteRequest,
    OllamaModelInfo,
    OllamaModelsResponse,
    OllamaPullRequest,
    OllamaPushRequest,
    OllamaShowRequest,
    OllamaShowResponse,
    OllamaVersionResponse,
    OpenAIModelsResponse,
)
from src.utils.exceptions import UpstreamError
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)
settings = get_settings()


@router.get("/tags")
@router.get("/models")  # OpenAI-style endpoint
async def list_models(fastapi_request: Request) -> OllamaModelsResponse:
    """
    List available models from the OpenAI-compatible backend.

    Translates OpenAI model format to Ollama format.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    logger.info(
        "Models list request received",
        extra={"extra_data": {"request_id": request_id}},
    )

    try:
        # Query OpenAI-compatible backend for models
        verify_ssl = not settings.DISABLE_SSL_VERIFICATION
        logger.info(
            f"Models router SSL verification: {verify_ssl}",
            extra={
                "extra_data": {
                    "ssl_verification": verify_ssl,
                    "disable_ssl_verification": settings.DISABLE_SSL_VERIFICATION,
                }
            },
        )

        async with httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT, verify=verify_ssl
        ) as client:
            response = await client.get(
                f"{settings.OPENAI_API_BASE_URL}/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            )

            if response.status_code != 200:
                logger.error(
                    "Backend error listing models",
                    extra={
                        "extra_data": {
                            "status_code": response.status_code,
                            "response": response.text[:500],
                        }
                    },
                )
                raise UpstreamError(
                    "Failed to list models from backend",
                    status_code=response.status_code,
                    service="openai",
                    details={"response": response.text[:500]},
                )

            # Parse OpenAI response
            openai_response = OpenAIModelsResponse(**response.json())

            # Transform to Ollama format
            ollama_models: List[OllamaModelInfo] = []
            for model in openai_response.data:
                # Generate a consistent digest from model ID
                digest_hash = hashlib.sha256(model.id.encode()).hexdigest()

                # Convert created timestamp to ISO format
                modified_at = datetime.fromtimestamp(
                    model.created, tz=timezone.utc
                ).isoformat()

                ollama_model = OllamaModelInfo(  # type: ignore[call-arg]
                    name=model.id,
                    model=model.id,
                    modified_at=modified_at,
                    size=0,  # Size not available from OpenAI API
                    digest=f"sha256:{digest_hash}",
                    details={
                        "format": "gguf",  # Default format
                        "family": model.owned_by or "unknown",
                        "families": [model.owned_by or "unknown"],
                        "parameter_size": "unknown",
                        "quantization_level": "unknown",
                    },
                )
                ollama_models.append(ollama_model)

            return OllamaModelsResponse(models=ollama_models)

    except UpstreamError:
        raise
    except httpx.TimeoutException:
        logger.error("Timeout listing models")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Timeout while listing models",
        )
    except Exception as e:
        logger.error("Error listing models", exc_info=e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list models",
        )


@router.post("/pull")
async def pull_model(
    request: OllamaPullRequest,
    fastapi_request: Request,
) -> JSONResponse:
    """
    Model pulling not supported - return appropriate error.

    This operation is not supported as models are managed by the backend.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    logger.warning(
        f"Unsupported pull request for model: {request.name}",
        extra={"extra_data": {"request_id": request_id, "model": request.name}},
    )

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": 501,
                "message": "Model management operations (pull/push/delete) are not supported by the OpenAI-compatible backend",
                "type": "not_implemented",
            }
        },
        headers={"X-Request-ID": request_id},
    )


@router.post("/push")
async def push_model(
    request: OllamaPushRequest,
    fastapi_request: Request,
) -> JSONResponse:
    """
    Model pushing not supported - return appropriate error.

    This operation is not supported as models are managed by the backend.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    logger.warning(
        f"Unsupported push request for model: {request.name}",
        extra={"extra_data": {"request_id": request_id, "model": request.name}},
    )

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": 501,
                "message": "Model management operations (pull/push/delete) are not supported by the OpenAI-compatible backend",
                "type": "not_implemented",
            }
        },
        headers={"X-Request-ID": request_id},
    )


@router.delete("/delete")
async def delete_model(
    request: OllamaDeleteRequest,
    fastapi_request: Request,
) -> JSONResponse:
    """
    Model deletion not supported - return appropriate error.

    This operation is not supported as models are managed by the backend.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    logger.warning(
        f"Unsupported delete request for model: {request.name}",
        extra={"extra_data": {"request_id": request_id, "model": request.name}},
    )

    return JSONResponse(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        content={
            "error": {
                "code": 501,
                "message": "Model management operations (pull/push/delete) are not supported by the OpenAI-compatible backend",
                "type": "not_implemented",
            }
        },
        headers={"X-Request-ID": request_id},
    )


@router.get("/version")
async def get_version(fastapi_request: Request) -> OllamaVersionResponse:
    """
    Return API version information.

    Returns both the Ollama version we're emulating and proxy information.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    logger.info(
        "Version request received",
        extra={"extra_data": {"request_id": request_id}},
    )

    return OllamaVersionResponse(
        version="0.1.42",  # Ollama version we're emulating
    )


@router.post("/show")
async def show_model(
    request: OllamaShowRequest,
    fastapi_request: Request,
) -> OllamaShowResponse:
    """
    Show model information.

    Since OpenAI API doesn't provide detailed model information like Ollama,
    we return a basic response with default values.
    """
    request_id = getattr(fastapi_request.state, "request_id", "unknown")

    logger.info(
        f"Show model request for: {request.name}",
        extra={
            "extra_data": {
                "request_id": request_id,
                "model": request.name,
                "verbose": request.verbose,
            }
        },
    )

    # First, verify the model exists by listing models
    try:
        verify_ssl = not settings.DISABLE_SSL_VERIFICATION
        logger.info(
            f"Models router SSL verification: {verify_ssl}",
            extra={
                "extra_data": {
                    "ssl_verification": verify_ssl,
                    "disable_ssl_verification": settings.DISABLE_SSL_VERIFICATION,
                }
            },
        )

        async with httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT, verify=verify_ssl
        ) as client:
            response = await client.get(
                f"{settings.OPENAI_API_BASE_URL}/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            )

            if response.status_code == 200:
                models_data = response.json()
                model_exists = any(
                    model.get("id") == request.name
                    for model in models_data.get("data", [])
                )

                if not model_exists:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Model '{request.name}' not found",
                    )
    except httpx.RequestError:
        # If we can't verify, proceed anyway
        pass

    # Return basic model information
    # Since OpenAI doesn't provide modelfile/template info, we create defaults
    modelfile = f"""FROM {request.name}

# Model parameters
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_predict 128

# System message
SYSTEM You are a helpful assistant."""

    parameters = """temperature 0.7
top_p 0.9
top_k 40
num_predict 128"""

    template = """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

    details = {
        "parent_model": "",
        "format": "gguf",
        "family": "llama" if "llama" in request.name.lower() else "unknown",
        "families": ["llama"] if "llama" in request.name.lower() else None,
        "parameter_size": "7B" if "7b" in request.name.lower() else "unknown",
        "quantization_level": "Q4_0",
    }

    return OllamaShowResponse(
        modelfile=modelfile if request.verbose else "",
        parameters=parameters,
        template=template,
        details=details,
        model_info=(
            {
                "general.architecture": (
                    "llama" if "llama" in request.name.lower() else "unknown"
                ),
                "general.file_type": 2,
                "general.parameter_count": (
                    7000000000 if "7b" in request.name.lower() else 0
                ),
                "general.quantization_version": 2,
            }
            if request.verbose
            else {}
        ),
    )
