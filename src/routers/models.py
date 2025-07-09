"""
Model management endpoints for the Ollama API.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/api/tags")
async def list_models():
    """List available models."""
    # TODO: Implement in later tasks
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/api/pull")
async def pull_model(model: dict):
    """Pull model endpoint - not supported."""
    raise HTTPException(
        status_code=501,
        detail="Model management operations (pull/push/delete) are not supported by the VLLM backend",
    )


@router.post("/api/push")
async def push_model(model: dict):
    """Push model endpoint - not supported."""
    raise HTTPException(
        status_code=501,
        detail="Model management operations (pull/push/delete) are not supported by the VLLM backend",
    )


@router.delete("/api/delete")
async def delete_model(model: dict):
    """Delete model endpoint - not supported."""
    raise HTTPException(
        status_code=501,
        detail="Model management operations (pull/push/delete) are not supported by the VLLM backend",
    )


@router.get("/api/version")
async def get_version():
    """Get version information."""
    return {"version": "0.1.0"}


@router.post("/api/show")
async def show_model(model: dict):
    """Show model information."""
    # TODO: Implement in later tasks
    raise HTTPException(status_code=501, detail="Not implemented yet")
