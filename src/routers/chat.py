"""
Chat and generation endpoints for the Ollama API.
"""

from fastapi import APIRouter, HTTPException
from src.models import OllamaGenerateRequest, OllamaChatRequest

router = APIRouter()


@router.post("/api/generate")
async def generate(request: OllamaGenerateRequest):
    """Handle Ollama generate requests."""
    # TODO: Implement in later tasks
    raise HTTPException(status_code=501, detail="Not implemented yet")


@router.post("/api/chat")
async def chat(request: OllamaChatRequest):
    """Handle Ollama chat requests."""
    # TODO: Implement in later tasks
    raise HTTPException(status_code=501, detail="Not implemented yet")
