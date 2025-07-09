# Configuration Guide

This guide covers all configuration options for the Ollama to OpenAI proxy service.

## Configuration Methods

The proxy can be configured using:

1. **Environment Variables** (recommended)
2. **.env File** (for local development)
3. **Docker Environment** (for containerized deployments)

## Required Configuration

These settings MUST be provided for the proxy to function:

### OPENAI_API_BASE_URL

- **Type**: URL
- **Required**: Yes
- **Description**: Base URL for your OpenAI-compatible API server
- **Examples**:
  ```env
  # OpenAI
  OPENAI_API_BASE_URL=https://api.openai.com/v1
  
  # VLLM Server
  OPENAI_API_BASE_URL=http://vllm-server:8000/v1
  
  # OpenRouter
  OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
  
  # Local LLM Server
  OPENAI_API_BASE_URL=http://localhost:8000/v1
  ```

**Note**: The proxy automatically appends `/v1` if not present in the URL.

### OPENAI_API_KEY

- **Type**: String
- **Required**: Yes
- **Description**: API key for authentication with the backend server
- **Examples**:
  ```env
  # OpenAI
  OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
  
  # OpenRouter
  OPENAI_API_KEY=sk-or-v1-xxxxxxxxxxxxx
  
  # Local/VLLM (if authentication required)
  OPENAI_API_KEY=your-custom-api-key
  ```

## Optional Configuration

### Server Settings

#### PROXY_PORT

- **Type**: Integer
- **Default**: `11434`
- **Range**: 1-65535
- **Description**: Port for the proxy server to listen on
- **Example**:
  ```env
  PROXY_PORT=11434  # Ollama's default port
  ```

#### DEBUG

- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable debug mode (shows API documentation at `/docs`)
- **Example**:
  ```env
  DEBUG=true
  ```

### Logging Configuration

#### LOG_LEVEL

- **Type**: String
- **Default**: `INFO`
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Description**: Controls the verbosity of log output
- **Examples**:
  ```env
  # Development
  LOG_LEVEL=DEBUG
  
  # Production
  LOG_LEVEL=WARNING
  ```

### Request Handling

#### REQUEST_TIMEOUT

- **Type**: Integer (seconds)
- **Default**: `60`
- **Range**: 1-600
- **Description**: Maximum time to wait for a response from the backend
- **Examples**:
  ```env
  # Fast models
  REQUEST_TIMEOUT=30
  
  # Large models or slow hardware
  REQUEST_TIMEOUT=180
  ```

#### MAX_RETRIES

- **Type**: Integer
- **Default**: `3`
- **Range**: 0-10
- **Description**: Maximum number of retry attempts for failed requests
- **Examples**:
  ```env
  # No retries
  MAX_RETRIES=0
  
  # More resilient (but slower on failures)
  MAX_RETRIES=5
  ```

### Model Configuration

#### MODEL_MAPPING_FILE

- **Type**: File path
- **Default**: None
- **Description**: Path to JSON file containing model name mappings
- **Example**:
  ```env
  MODEL_MAPPING_FILE=./config/model_mappings.json
  ```

**Model Mapping File Format**:
```json
{
  "model_mappings": {
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
    "llama2:13b": "meta-llama/Llama-2-13b-chat-hf",
    "llama2:70b": "meta-llama/Llama-2-70b-chat-hf",
    "codellama": "codellama/CodeLlama-7b-Instruct-hf",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.1",
    "mixtral": "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "gemma": "google/gemma-7b-it",
    "phi": "microsoft/phi-2"
  },
  "default_model": "meta-llama/Llama-2-7b-chat-hf"
}
```

## Advanced Configuration

### Connection Pooling (Hardcoded)

These settings are currently hardcoded but may become configurable in future versions:

- **Max Connections**: 100
- **Keepalive Timeout**: 5 seconds
- **Connection Timeout**: 10 seconds

### Circuit Breaker (Hardcoded)

Protects against cascading failures:

- **Failure Threshold**: 5 consecutive failures
- **Recovery Timeout**: 60 seconds
- **Half-Open Max Calls**: 3

### Retry Logic (Hardcoded)

- **Initial Delay**: 1 second
- **Max Delay**: 60 seconds
- **Exponential Base**: 2
- **Jitter**: 0-0.1 seconds

## Configuration Examples

### Development Setup

```env
# .env.development
OPENAI_API_BASE_URL=http://localhost:8000/v1
OPENAI_API_KEY=test-key
PROXY_PORT=11434
LOG_LEVEL=DEBUG
DEBUG=true
REQUEST_TIMEOUT=30
MAX_RETRIES=1
```

### Production Setup

```env
# .env.production
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=${OPENAI_API_KEY}  # From environment
PROXY_PORT=11434
LOG_LEVEL=WARNING
DEBUG=false
REQUEST_TIMEOUT=60
MAX_RETRIES=3
MODEL_MAPPING_FILE=/app/config/model_mappings.json
```

### Testing with OpenRouter

```env
# .env.openrouter
OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-v1-your-key-here
PROXY_PORT=11434
LOG_LEVEL=INFO
REQUEST_TIMEOUT=120  # OpenRouter can be slower
MAX_RETRIES=3
```

### High-Performance Setup

```env
# .env.performance
OPENAI_API_BASE_URL=http://vllm-cluster:8000/v1
OPENAI_API_KEY=internal-key
PROXY_PORT=11434
LOG_LEVEL=ERROR  # Minimize logging overhead
DEBUG=false
REQUEST_TIMEOUT=30  # Fast local network
MAX_RETRIES=1  # Quick failure for fast recovery
```

## Docker Configuration

### Using docker-compose.yml

```yaml
version: '3.8'

services:
  ollama-proxy:
    build: .
    ports:
      - "${PROXY_PORT:-11434}:11434"
    environment:
      - OPENAI_API_BASE_URL
      - OPENAI_API_KEY
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - REQUEST_TIMEOUT=${REQUEST_TIMEOUT:-60}
      - MAX_RETRIES=${MAX_RETRIES:-3}
      - DEBUG=${DEBUG:-false}
      - MODEL_MAPPING_FILE=${MODEL_MAPPING_FILE:-}
    env_file:
      - .env
    volumes:
      - ./config:/app/config:ro  # For model mapping file
    restart: unless-stopped
```

### Using Docker Run

```bash
docker run -d \
  --name ollama-proxy \
  -p 11434:11434 \
  -e OPENAI_API_BASE_URL="https://api.openai.com/v1" \
  -e OPENAI_API_KEY="sk-..." \
  -e LOG_LEVEL="INFO" \
  -v $(pwd)/config:/app/config:ro \
  ollama-proxy:latest
```

## Kubernetes Configuration

### ConfigMap Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ollama-proxy-config
data:
  LOG_LEVEL: "INFO"
  REQUEST_TIMEOUT: "60"
  MAX_RETRIES: "3"
  DEBUG: "false"
  model_mappings.json: |
    {
      "model_mappings": {
        "llama2": "meta-llama/Llama-2-7b-chat-hf"
      }
    }
```

### Secret Example

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ollama-proxy-secrets
type: Opaque
stringData:
  OPENAI_API_BASE_URL: "https://api.openai.com/v1"
  OPENAI_API_KEY: "sk-..."
```

## Validation and Defaults

### URL Validation

- Automatically appends `/v1` if missing
- Validates URL format
- Removes trailing slashes

### Timeout Validation

- Warns if total timeout (including retries) exceeds 10 minutes
- Formula: `REQUEST_TIMEOUT * (MAX_RETRIES + 1)`

### Model Mapping Validation

- File must exist and be valid JSON
- All mappings must be string-to-string
- Invalid mappings are logged and skipped

## Environment Variable Priority

1. System environment variables (highest priority)
2. `.env` file in project root
3. Default values in code (lowest priority)

## Troubleshooting Configuration

### Check Current Configuration

```bash
# View all environment variables
docker exec ollama-proxy env | grep -E "OPENAI_|PROXY_|LOG_|DEBUG|REQUEST_|MAX_|MODEL_"

# Test configuration
curl http://localhost:11434/health
```

### Common Issues

1. **Invalid API Key Format**
   ```
   Error: OPENAI_API_KEY cannot be empty
   ```
   Solution: Ensure API key is set and not blank

2. **Model Mapping File Not Found**
   ```
   Error: Model mapping file not found: /app/config/mappings.json
   ```
   Solution: Check file path and volume mounts

3. **Port Already in Use**
   ```
   Error: Address already in use
   ```
   Solution: Change `PROXY_PORT` or stop conflicting service

4. **Timeout Too High Warning**
   ```
   Warning: Total timeout with retries could exceed 600s
   ```
   Solution: Reduce `REQUEST_TIMEOUT` or `MAX_RETRIES`

## Best Practices

1. **Use .env Files**: Keep sensitive data out of version control
2. **Set Appropriate Timeouts**: Balance between reliability and responsiveness
3. **Enable Debug Logging**: Only in development, not production
4. **Use Model Mappings**: Maintain compatibility with existing code
5. **Monitor Logs**: Set appropriate log levels for your environment

## Future Configuration Options

Planned for future releases:

- Connection pool size configuration
- Circuit breaker thresholds
- Prometheus metrics endpoint
- Request/response size limits
- Authentication methods
- TLS/SSL configuration
- Rate limiting settings

---

For specific deployment scenarios, see:
- [Docker Deployment](DEPLOYMENT.md#docker)
- [Kubernetes Deployment](DEPLOYMENT.md#kubernetes)
- [Production Setup](DEPLOYMENT.md#production)