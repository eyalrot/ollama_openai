# Ollama to OpenAI Proxy Service

## Project Purpose
This project is a transparent proxy service that maintains the Ollama API interface while forwarding requests to OpenAI-compatible endpoints (such as VLLM). It allows users to migrate from Ollama to OpenAI-compatible LLM servers without modifying existing code that uses the Ollama Python SDK.

## Key Features
- Drop-in replacement for Ollama server
- Full compatibility with Ollama Python SDK
- Supports text generation, chat, and embeddings endpoints
- Configurable model name mapping
- Streaming response support
- Automatic retry with exponential backoff
- Docker and standalone Python deployment options

## Tech Stack
- **Framework**: FastAPI with Uvicorn ASGI server
- **Language**: Python 3.x
- **Core Dependencies**:
  - fastapi==0.104.1
  - uvicorn[standard]==0.24.0
  - httpx==0.25.0 (async HTTP client)
  - pydantic==2.5.0 (data validation)
  - pydantic-settings==2.1.0 (configuration management)
  - langchain-openai==0.0.5

## Development Stack
- **Testing**: pytest with pytest-asyncio, pytest-cov, pytest-mock, pytest-httpx
- **Linting**: ruff
- **Formatting**: black
- **Type Checking**: mypy
- **Mocking**: respx for HTTP mocking
- **CI/CD**: GitHub Actions with Docker-based testing

## Default Ports
- Proxy service runs on port 11434 (Ollama's default port)
- Configurable via PROXY_PORT environment variable