# Ollama to OpenAI Proxy

[![Version](https://img.shields.io/github/v/release/eyalrot/ollama_openai?label=version)](https://github.com/eyalrot/ollama_openai/releases)
[![PyPI](https://img.shields.io/pypi/v/ollama-openai-proxy)](https://pypi.org/project/ollama-openai-proxy/)
[![CI Status](https://github.com/eyalrot/ollama_openai/actions/workflows/ci.yml/badge.svg)](https://github.com/eyalrot/ollama_openai/actions/workflows/ci.yml)
[![Test Coverage](https://img.shields.io/badge/coverage-65.4%25-green.svg)](https://codecov.io/gh/eyalrot/ollama_openai)
[![Security Scan](https://github.com/eyalrot/ollama_openai/actions/workflows/security.yml/badge.svg)](https://github.com/eyalrot/ollama_openai/actions/workflows/security.yml)
[![Docker Build](https://github.com/eyalrot/ollama_openai/actions/workflows/docker.yml/badge.svg)](https://github.com/eyalrot/ollama_openai/actions/workflows/docker.yml)
[![GHCR](https://img.shields.io/badge/ghcr.io-available-blue)](https://github.com/eyalrot/ollama_openai/pkgs/container/ollama_openai)
[![Docker Image Size](https://img.shields.io/badge/docker%20image-271MB-blue)](https://github.com/eyalrot/ollama_openai/pkgs/container/ollama_openai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A transparent proxy service that allows applications to use both Ollama and OpenAI API formats seamlessly with OpenAI-compatible LLM servers like **OpenAI**, **vLLM**, **LiteLLM**, **OpenRouter**, **Ollama**, and any other OpenAI-compatible API provider.

**New in v0.6.0**: Enhanced version management system with automated Docker publishing! Full dual API format support! Use your existing Ollama clients OR OpenAI clients - both work with the same proxy instance.

## Features

- ✅ Drop-in replacement for Ollama server
- ✅ Zero changes required to existing code
- ✅ **Dual API format support**: Both Ollama and OpenAI endpoints
- ✅ Supports text generation and chat endpoints
- ✅ Streaming and non-streaming responses
- ✅ Model listing from backend
- ✅ Configurable model name mapping
- ✅ Docker and standalone deployment
- ✅ Automatic retry with exponential backoff
- ✅ Comprehensive logging and monitoring
- ✅ Request ID tracking for debugging
- ✅ Phase 1: Text-only chat and embeddings (completed)
- ✅ Phase 2: Tool calling support (completed)
- ✅ Phase 2: Image input support (completed)

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Images](#docker-images)
- [Configuration](#configuration)
- [API Compatibility](#api-compatibility)
- [Model Mapping](#model-mapping)
- [Deployment](#deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Documentation](#documentation)
- [Security & Compliance](#security--compliance)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

Get started in under 5 minutes! See the [Quick Start Guide](docs/QUICK_START.md) for detailed instructions.

### Using Docker (Recommended)

```bash
# Clone and configure
git clone https://github.com/eyalrot/ollama_openai.git
cd ollama_openai
cp .env.example .env

# Edit .env with your API details
nano .env

# Start the proxy
docker-compose up -d

# Verify it's working
curl http://localhost:11434/health
```

### Using PyPI Package (Recommended)

```bash
# Install from PyPI
pip install ollama-openai-proxy

# Create configuration file
cat > .env << EOF
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here
EOF

# Run the proxy (method 1: using installed command)
ollama-openai-proxy

# Or run using Python module (method 2)
python -c "from src.main import main; main()"
```

### Using Python Source

```bash
# Setup
git clone https://github.com/eyalrot/ollama_openai.git
cd ollama_openai
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env

# Run
python -m uvicorn src.main:app --host 0.0.0.0 --port 11434
```

### Quick Test

```bash
# Check version and health
curl http://localhost:11434/v1/version
curl http://localhost:11434/v1/health
```

```python
# Option 1: Use Ollama client (existing code works unchanged)
from ollama import Client
client = Client(host='http://localhost:11434')

response = client.generate(model='gpt-3.5-turbo', prompt='Hello!')
print(response['response'])

# Option 2: Use OpenAI client (new in v0.6.0!)
import openai
openai.api_base = "http://localhost:11434/v1"
openai.api_key = "your-api-key"

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

For more examples and detailed setup instructions, see the [Quick Start Guide](docs/QUICK_START.md).

## Docker Images

### Pre-built Docker Images

Ready-to-use production images are available on GitHub Container Registry:

#### GitHub Container Registry 📦
```bash
# Pull and run latest
docker pull ghcr.io/eyalrot/ollama_openai:latest
docker run -d -p 11434:11434 \
  -e OPENAI_API_BASE_URL=https://openrouter.ai/api/v1 \
  -e OPENAI_API_KEY=your_key \
  ghcr.io/eyalrot/ollama_openai:latest

# Or use specific version
docker pull ghcr.io/eyalrot/ollama_openai:0.6.0
# Available tags: latest, 0.6.0, 0.6, 0
```

#### Multi-Architecture Support 🏗️
- **linux/amd64** (Intel/AMD processors)
- **linux/arm64** (ARM processors, Apple Silicon, Raspberry Pi)

### Docker Compose with Pre-built Images

```yaml
services:
  ollama-proxy:
    image: ghcr.io/eyalrot/ollama_openai:latest
    ports:
      - "11434:11434"
    environment:
      - OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
      - OPENAI_API_KEY=your_openrouter_key
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

### Image Features

- **Size**: 271MB (optimized production build)
- **Security**: Non-root user, read-only filesystem, no-new-privileges
- **Performance**: Multi-stage build with optimized dependencies
- **Compatibility**: Supports **OpenAI**, **vLLM**, **LiteLLM**, **OpenRouter**, **Ollama**, and any OpenAI-compatible API provider
- **SSL Support**: System SSL certificates included for private endpoints

### Available Tags

| Tag | Description | Registry |
|-----|-------------|----------|
| `latest` | Latest stable build | Docker Hub & GHCR |
| `prod` | Production-ready build | Docker Hub & GHCR |

### Quick Test with Pre-built Image

```bash
# Start with OpenRouter free models
docker run -d --name ollama-proxy -p 11434:11434 \
  -e OPENAI_API_BASE_URL=https://openrouter.ai/api/v1 \
  -e OPENAI_API_KEY=your_key \
  eyalrot2/ollama-openai-proxy:latest

# Test with free model (Ollama format)
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "google/gemma-2-9b-it:free", "prompt": "Hello!"}'

# Or test with OpenAI format
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_key" \
  -d '{"model": "google/gemma-2-9b-it:free", "messages": [{"role": "user", "content": "Hello!"}]}'
```

## Configuration

See the [Configuration Guide](docs/CONFIGURATION.md) for detailed setup instructions.

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_BASE_URL` | URL of your OpenAI-compatible server | `https://api.openai.com/v1` |
| `OPENAI_API_KEY` | API key for authentication | `sk-...` |

### Key Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `PROXY_PORT` | Port to run proxy on | `11434` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `REQUEST_TIMEOUT` | Request timeout in seconds | `60` |
| `MODEL_MAPPING_FILE` | **Optional**: Path to model mapping JSON. When not set, model names pass through unchanged to your provider | `None` (recommended) |

For all configuration options, validation rules, and examples, see the [Configuration Guide](docs/CONFIGURATION.md).

### Quick Testing with Different Providers

#### OpenRouter (Free Models Available)
```env
OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-v1-your-key
```
Free models: `google/gemma-2-9b-it:free`, `meta-llama/llama-3.2-3b-instruct:free`

#### OpenAI
```env
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-proj-your-key
```

#### vLLM Server
```env
OPENAI_API_BASE_URL=http://your-vllm-server:8000/v1
OPENAI_API_KEY=your-api-key-or-none
```

#### LiteLLM Proxy
```env
OPENAI_API_BASE_URL=http://your-litellm-proxy:4000
OPENAI_API_KEY=your-litellm-key
```

#### Local Ollama Server
```env
OPENAI_API_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama  # or any value
```

## API Compatibility

See the [API Compatibility Matrix](docs/API_COMPATIBILITY.md) for detailed endpoint mappings and parameter translations.

### Supported Endpoints

| Endpoint | Method | Status | Description |
|----------|--------|---------|-------------|
| `/api/generate` | POST | ✅ Full Support | Text generation (Ollama-style) |
| `/api/chat` | POST | ✅ Full Support | Chat completion (Ollama-style) |
| `/api/tags` | GET | ✅ Full Support | List models |
| `/api/embeddings` | POST | ✅ Full Support | Generate embeddings (Ollama-style) |

### Dual API Format Support ✨

The proxy now supports **both Ollama and OpenAI API formats simultaneously**:

#### Ollama-Style Endpoints
- `/api/generate` - Text generation
- `/api/chat` - Chat completion  
- `/api/embeddings` - Generate embeddings

#### OpenAI-Style Endpoints
- `/v1/chat/completions` - Chat completions
- `/v1/models` - List models  
- `/v1/embeddings` - Generate embeddings

**Choose the format that works best for your application!** The proxy automatically detects the API format based on the URL path (`/api/*` vs `/v1/*`) and routes accordingly.

For detailed parameter mappings, response formats, and examples, see the [API Compatibility Matrix](docs/API_COMPATIBILITY.md).

## Phase 2 Features

### Tool Calling Support ✅

The proxy now supports full tool/function calling capabilities, allowing your AI models to execute tools and functions. This enables:

- **Function Definitions**: Define functions with JSON schema parameters
- **Tool Invocation**: Models can request to call tools during conversation
- **Bidirectional Translation**: Seamless translation between Ollama and OpenAI tool formats
- **Streaming Support**: Tool calls work with both streaming and non-streaming responses

```python
from ollama import Client

client = Client(host='http://localhost:11434')

# Define tools
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"]
        }
    }
}]

# Chat with tool support
response = client.chat(
    model='gpt-4',
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools
)
```

### Image Input Support ✅

The proxy supports multimodal inputs, allowing you to send images along with text messages:

- **Base64 Images**: Send images as base64-encoded strings
- **Data URLs**: Support for data URL formatted images
- **Multiple Images**: Send multiple images in a single message
- **Mixed Content**: Combine text and images in conversations

```python
from ollama import Client
import base64

client = Client(host='http://localhost:11434')

# Load and encode image
with open("image.jpg", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Send multimodal message
response = client.chat(
    model='gpt-4-vision-preview',
    messages=[{
        "role": "user", 
        "content": "What do you see in this image?",
        "images": [image_data]
    }]
)
```

For comprehensive Phase 2 examples and integration guides, see the [examples/phase2/](examples/phase2/) directory.

## Examples

See the [examples/](examples/) directory for:
- Python client examples (Ollama SDK, OpenAI SDK, streaming, batch processing, LangChain)
- JavaScript/Node.js examples (both Ollama and OpenAI formats)
- Configuration templates
- Docker and Nginx setup examples
- Dual API format usage patterns

## Model Mapping

**Model mapping is completely optional.** By default, the proxy passes all model names through unchanged to your OpenAI-compatible provider, allowing direct use of provider-specific model names.

### Default Behavior: No Mapping Required ✅

**When `MODEL_MAPPING_FILE` is not configured (recommended for most users):**
- Model names are passed directly to your provider as-is
- No configuration needed - just use your provider's exact model names
- Perfect for **OpenAI**, **vLLM**, **LiteLLM**, **OpenRouter**, **Ollama**, and any OpenAI-compatible API

```bash
# Direct model usage (no mapping file needed)
# Ollama format:
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "google/gemma-2-9b-it:free", "prompt": "Hello!"}'

# OpenAI format:
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_key" \
  -d '{"model": "gpt-4", "messages": [{"role": "user", "content": "Hello!"}]}'

# Both send model names directly to your OpenAI-compatible provider
```

### Optional: Custom Model Mapping

**Only configure model mapping if you want to create custom aliases:**

```json
{
  "model_mappings": {
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
    "gpt4": "gpt-4",
    "free-gemma": "google/gemma-2-9b-it:free"
  },
  "default_model": "gpt-3.5-turbo"
}
```

Then set in environment:
```env
MODEL_MAPPING_FILE=./config/model_mapping.json
```

With mapping enabled, you can use aliases in both formats:
```bash
# Ollama format with alias "free-gemma" -> maps to "google/gemma-2-9b-it:free"
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "free-gemma", "prompt": "Hello!"}'

# OpenAI format with same alias
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_key" \
  -d '{"model": "free-gemma", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### When to Use Model Mapping

✅ **Use model mapping when:**
- You want shorter, memorable aliases for long model names
- Migrating from Ollama and want to keep existing model names
- Need consistent model names across different environments

❌ **Skip model mapping when:**
- Using **OpenAI**, **vLLM**, **LiteLLM**, **OpenRouter**, **Ollama**, or similar APIs directly (most common)
- You prefer using the provider's exact model names
- You want simpler configuration

For advanced mapping strategies and examples, see the [Model Mapping Guide](docs/MODEL_MAPPING.md).

## Deployment

### Docker Deployment

Using the provided `docker-compose.yml`:

```yaml
services:
  ollama-proxy:
    build: .
    ports:
      - "11434:11434"
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./config:/app/config:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes Deployment

See `deployment/kubernetes/` for example manifests:
- `deployment.yaml` - Deployment configuration
- `service.yaml` - Service exposure
- `configmap.yaml` - Configuration management
- `secrets.yaml` - Sensitive data storage

### Production Considerations

1. **Reverse Proxy**: Use nginx/traefik for SSL termination
2. **Rate Limiting**: Implement rate limiting to prevent abuse
3. **Monitoring**: Enable Prometheus metrics (coming soon)
4. **Logging**: Configure structured logging with log aggregation
5. **High Availability**: Run multiple replicas behind a load balancer

## Testing

![Test Coverage](https://codecov.io/gh/eyalrot/ollama_openai/branch/master/graph/badge.svg)

This project maintains comprehensive test coverage across unit, integration, and performance tests. For detailed testing documentation, see our **[Testing Guide](docs/TESTING.md)**.

### Quick Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run specific test categories
pytest tests/unit/ -v          # Unit tests
pytest tests/performance/ -v   # Performance tests
```

### Test Categories

- **Unit Tests**: 290+ tests covering individual components with comprehensive coverage
- **Integration Tests**: End-to-end API testing with mock backends
- **Performance Tests**: Load testing and benchmarking with metrics validation
- **Security Tests**: Input validation and error handling verification

### Current Test Status (Updated: 2025-07-15)

✅ **All tests passing**: 290 tests passed, 1 skipped, 0 failed
✅ **Code coverage**: 65.40% (exceeds minimum 10% requirement)
✅ **Performance validated**: All benchmarks within thresholds
✅ **Zero failing tests**: Complete test suite reliability

### Coverage Requirements

Our coverage standards ensure code quality and reliability:

- **Current Coverage**: 65.40% (minimum 10% requirement exceeded)
- **Target Coverage**: Working toward 85% overall coverage
- **New Code Coverage**: ≥85% (enforced on PRs)
- **Critical Components**: ≥90% (config, models, translators)
- **Quality Gates**: Automatic PR blocking below thresholds

```bash
# Generate coverage reports
make coverage                    # All formats
make coverage-html              # HTML report only
pytest --cov=src --cov-fail-under=80  # With threshold check
```

### CI/CD Testing

All tests run automatically on:
- Pull requests and commits to main branch
- Nightly scheduled runs for regression detection
- Docker image builds for container testing

For complete testing instructions, coverage reports, and test strategy details, see the **[Testing Guide](docs/TESTING.md)**.

## Troubleshooting

See the [Troubleshooting Guide](docs/TROUBLESHOOTING.md) for comprehensive debugging help.

### Quick Fixes

#### Connection Issues
- **Connection refused**: Check if proxy is running on port 11434
- **Backend unreachable**: Verify `OPENAI_API_BASE_URL` is correct
- **Authentication failed**: Ensure `OPENAI_API_KEY` is valid

#### Common Problems
- **Model not found**: Add model mapping or use exact name
- **Timeout errors**: Increase `REQUEST_TIMEOUT` 
- **CORS errors**: Proxy includes CORS headers by default

### Debug Mode

```env
LOG_LEVEL=DEBUG
DEBUG=true
```

For detailed solutions and error codes, see the [Troubleshooting Guide](docs/TROUBLESHOOTING.md).

## Development

### Project Structure

```
ollama_openai/
├── src/
│   ├── main.py              # FastAPI application
│   ├── models.py             # Pydantic models
│   ├── config.py             # Configuration management
│   ├── routers/              # API endpoints
│   │   ├── chat.py
│   │   ├── models.py
│   │   └── embeddings.py
│   ├── translators/          # Format converters
│   │   ├── chat.py
│   │   └── embeddings.py
│   ├── middleware/           # Request/response processing
│   └── utils/                # Utilities
├── tests/                    # Test suite
├── docker/                   # Docker configurations
├── deployment/               # Deployment manifests
└── docs/                     # Additional documentation
```

### Code Style

This project uses:
- `black` for code formatting
- `isort` for import sorting
- `mypy` for type checking
- `pylint` for linting

Run all checks:
```bash
make lint
```

### Adding New Features

1. Create a feature branch
2. Write tests first
3. Implement the feature
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

## Documentation

### Comprehensive Guides

- 📚 **[Architecture](ARCHITECTURE.md)** - System design and implementation details
- 🧪 **[Testing Guide](docs/TESTING.md)** - Comprehensive testing documentation and coverage reports
- 🔒 **[Security](docs/SECURITY.md)** - Security standards, best practices, and vulnerability reporting
- 📊 **[Performance Benchmarks](docs/PERFORMANCE_BENCHMARKS.md)** - Performance testing and optimization guide
- 🔧 **[Monitoring Integration](docs/MONITORING_INTEGRATION.md)** - Prometheus/Grafana setup and metrics

### Quick Reference

- [Quick Start Guide](docs/QUICK_START.md) - Get running in 5 minutes
- [Configuration Guide](docs/CONFIGURATION.md) - Environment variables and settings
- [API Compatibility Matrix](docs/API_COMPATIBILITY.md) - Supported endpoints and parameters
- [Model Mapping Guide](docs/MODEL_MAPPING.md) - Custom model name configuration
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md) - Common issues and solutions

## Security & Compliance

This project follows industry security standards and best practices:

### 🔒 Security Standards
- **OWASP Compliance**: Follows [OWASP Top 10](https://owasp.org/www-project-top-ten/) and [OWASP API Security Top 10](https://owasp.org/www-project-api-security/) guidelines
- **Input Validation**: All API inputs validated using Pydantic models with strict type checking
- **Secure Configuration**: Environment-based configuration with no hardcoded credentials
- **Error Handling**: Generic error messages prevent information leakage

### 🛡️ Security Features
- API key validation and secure forwarding
- Request size limits and timeout enforcement
- Connection pooling with configurable limits
- Graceful degradation under load
- Comprehensive audit logging with request IDs

### 📋 Security Scanning
- **Trivy**: Container vulnerability scanning
- **Bandit**: Python security linting
- **TruffleHog**: Secret detection in code
- **GitHub Security**: Automated dependency scanning

For detailed security information, see our [Security Policy](docs/SECURITY.md).

### 🚨 Vulnerability Reporting
Please report security vulnerabilities responsibly by following our [Security Policy](docs/SECURITY.md#vulnerability-reporting).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Areas for Contribution

- 📊 Prometheus metrics integration
- 🔐 Additional authentication methods
- 🌐 Multi-language SDK examples
- 📚 Additional documentation and tutorials
- 🔄 Phase 3: Advanced features and optimizations
- 🧪 Additional testing and benchmarking

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for seamless integration between Ollama and OpenAI API formats
- Supports major LLM providers: **OpenAI**, **vLLM**, **LiteLLM**, **OpenRouter**, **Ollama**
- Inspired by the need to preserve existing codebases during infrastructure changes
- Thanks to all contributors and users providing feedback

---

For more detailed documentation, see the [docs/](docs/) directory.