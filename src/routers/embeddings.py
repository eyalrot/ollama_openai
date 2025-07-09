"""
Embeddings endpoint for the Ollama API.
"""

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/api/embeddings")
async def create_embeddings(request: dict):
    """Create embeddings."""
    # TODO: Implement in later tasks
    raise HTTPException(status_code=501, detail="Not implemented yet")
