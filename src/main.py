"""
Main entry point for the Ollama to OpenAI proxy service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.config import get_settings
from src.utils.logging import setup_logging

# Initialize settings and logging
settings = get_settings()
logger = setup_logging(level=settings.LOG_LEVEL)

# Create FastAPI app
app = FastAPI(
    title="Ollama to OpenAI Proxy",
    description="A proxy service that translates Ollama API calls to OpenAI-compatible endpoints",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ollama-openai-proxy"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=settings.PROXY_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
