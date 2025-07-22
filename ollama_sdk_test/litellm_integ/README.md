# LiteLLM Integration for Ollama SDK Testing

This directory contains the Docker Compose setup for running LiteLLM as a backend for the ollama_openai proxy to test the full integration chain with OpenAI models.

## Architecture

```
Ollama SDK → ollama_openai proxy (11434) → LiteLLM (4000) → OpenAI API
```

## Overview

LiteLLM acts as the OpenAI backend that:
- Receives requests from the ollama_openai proxy
- Runs on port 4000
- Forwards requests to OpenAI with proper authentication
- Provides OpenAI models (gpt-3.5-turbo, text-embedding-3-small, etc.)

## Quick Start

### Prerequisites

1. Docker and Docker Compose installed
2. Go installed (for running ollama_openai proxy)
3. Python 3.8+ with pip

### Step-by-Step Setup

#### 1. Set up your OpenAI API Key

```bash
cd ollama_sdk_test/litellm_integ
cp .env.example .env
# Edit .env and add your OpenAI API key (already provided in .env.example)
```

#### 2. Start LiteLLM Backend

```bash
# From litellm_integ directory
docker-compose up -d

# Verify it's running
docker-compose ps
curl http://localhost:4000/health
```

#### 3. Start the ollama_openai Proxy

In a new terminal:

```bash
# From the ollama_openai root directory
export OPENAI_API_URL=http://localhost:4000/v1
go run . serve
```

You should see the proxy start on port 11434.

#### 4. Run the Tests

In another terminal:

```bash
# From ollama_sdk_test directory
cd ollama_sdk_test/
python run_tests.py
```

### Complete Flow

1. **LiteLLM** (port 4000) - Handles OpenAI API calls
2. **ollama_openai proxy** (port 11434) - Translates Ollama API to OpenAI API
3. **Ollama SDK tests** - Uses standard Ollama SDK to test compatibility

Or run specific test suites:

```bash
# Test embeddings specifically
python run_tests.py test_embeddings.py

# Test basic operations
python run_tests.py test_basic_operations.py
```

## Configuration Details

### Docker Compose Services

The `docker-compose.yml` defines:
- **litellm**: The main LiteLLM proxy service
  - Port: 4000
  - Config: Mounted from `litellm_config.yaml`
  - Health check: Automatic container health monitoring

### LiteLLM Configuration

The `litellm_config.yaml` includes:

1. **Chat Models**:
   - gpt-3.5-turbo
   - gpt-4

2. **Embedding Models**:
   - text-embedding-ada-002
   - text-embedding-3-small
   - text-embedding-3-large

3. **Settings**:
   - OpenAI-compatible endpoints enabled
   - Custom routes for Ollama compatibility
   - Streaming support
   - Request timeout: 600 seconds

### Environment Variables

Required in `.env`:
- `OPENAI_API_KEY`: Your OpenAI API key

Optional:
- `LITELLM_LOG`: Log level (default: INFO)
- `LITELLM_TELEMETRY`: Telemetry setting (default: False)

## Testing Workflow

### 1. Direct API Testing

Test LiteLLM directly before running SDK tests:

```bash
# Test chat completion
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'

# Test embeddings
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-3-small",
    "input": "Hello, world!"
  }'
```

### 2. Ollama SDK Testing

The test flow:

```python
# Ollama SDK connects to ollama_openai proxy:
# - http://localhost:11434/api/chat
# - http://localhost:11434/api/embeddings
# - http://localhost:11434/api/tags

# ollama_openai proxy forwards to LiteLLM:
# - http://localhost:4000/v1/chat/completions
# - http://localhost:4000/v1/embeddings
# - http://localhost:4000/v1/models
```

### 3. Debugging Failed Tests

If tests fail:

1. Check LiteLLM logs:
   ```bash
   docker-compose logs -f litellm
   ```

2. Verify API key is set:
   ```bash
   docker-compose exec litellm env | grep OPENAI_API_KEY
   ```

3. Test model availability:
   ```bash
   curl http://localhost:4000/v1/models
   ```

## Common Issues and Solutions

### Connection Refused

- Ensure Docker is running
- Check if port 4000 is available: `lsof -i :4000`
- Verify container is healthy: `docker-compose ps`

### Authentication Errors

- Verify your OpenAI API key is valid
- Check if the key is properly set in `.env`
- Ensure the key has the necessary permissions

### Model Not Found

- The model name in tests must match those in `litellm_config.yaml`
- Check LiteLLM logs for model loading errors

### Timeout Errors

- Increase timeout in `litellm_config.yaml`
- Check your internet connection for API calls
- Consider using a faster model (e.g., gpt-3.5-turbo)

## Stopping the Service

```bash
# Stop the container
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Advanced Configuration

### Adding More Models

Edit `litellm_config.yaml` to add more models:

```yaml
- model_name: claude-3-opus
  litellm_params:
    model: anthropic/claude-3-opus-20240229
    api_key: os.environ/ANTHROPIC_API_KEY
```

### Changing Ports

To use a different port, update:
1. `docker-compose.yml`: Change port mapping
2. Parent `config.py`: Update `PROXY_HOST`

### Enable Debug Logging

Set in `.env`:
```bash
LITELLM_LOG=DEBUG
```

Or in `litellm_config.yaml`:
```yaml
general_settings:
  debug: true
```

## Integration with CI/CD

For automated testing:

```bash
# Start LiteLLM backend
docker-compose up -d
docker-compose exec litellm curl -f http://localhost:4000/health || exit 1

# Start ollama_openai proxy with LiteLLM backend
export OPENAI_API_URL=http://localhost:4000/v1
cd ../../
./ollama_openai serve &
PROXY_PID=$!

# Wait for proxy to be ready
sleep 5

# Run tests
cd ollama_sdk_test/
python run_tests.py --failfast

# Cleanup
kill $PROXY_PID
cd litellm_integ/
docker-compose down
```

## Security Notes

- Never commit `.env` files with real API keys
- Use environment-specific keys for different environments
- Consider using Docker secrets for production deployments
- Rotate API keys regularly

## Support

For issues:
1. Check LiteLLM documentation: https://docs.litellm.ai/
2. Review test logs: `docker-compose logs`
3. Check the parent project's issues