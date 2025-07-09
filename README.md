# Ollama to OpenAI Proxy Service

A transparent proxy service that maintains the Ollama API interface while forwarding requests to OpenAI-compatible endpoints (such as VLLM).

## Overview

This proxy allows you to migrate from Ollama to OpenAI-compatible LLM servers without modifying existing code that uses the Ollama Python SDK.

## Features

- Drop-in replacement for Ollama server
- Full compatibility with Ollama Python SDK
- Supports text generation and chat endpoints
- Configurable model name mapping
- Docker and standalone Python deployment options

## Quick Start

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ollama_openai.git
   cd ollama_openai
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI-compatible server details
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the proxy:
   ```bash
   python -m src.main
   ```

The proxy will start on port 11434 (Ollama's default port).

## Configuration

See `.env.example` for all available configuration options.

## Development

Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

Run tests:
```bash
pytest
```

## License

MIT