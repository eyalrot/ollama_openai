# Ollama to OpenAI Proxy

[![CI Status](https://github.com/eyalrot/ollama_openai/workflows/CI%20Pipeline/badge.svg)](https://github.com/eyalrot/ollama_openai/actions)
[![Test Coverage](https://codecov.io/gh/eyalrot/ollama_openai/branch/master/graph/badge.svg)](https://codecov.io/gh/eyalrot/ollama_openai)
[![Security Scan](https://github.com/eyalrot/ollama_openai/workflows/Security%20Scan/badge.svg)](https://github.com/eyalrot/ollama_openai/security)
[![Docker Build](https://github.com/eyalrot/ollama_openai/workflows/Docker/badge.svg)](https://github.com/eyalrot/ollama_openai/actions)
[![License](https://img.shields.io/github/license/eyalrot/ollama_openai)](LICENSE)

A transparent proxy service that allows legacy applications using the Ollama Python SDK to seamlessly work with OpenAI-compatible LLM servers like VLLM.

## Features

- ✅ Drop-in replacement for Ollama server
- ✅ Zero changes required to existing code
- ✅ Supports text generation and chat endpoints
- ✅ Streaming and non-streaming responses
- ✅ Model listing from backend
- ✅ Configurable model name mapping
- ✅ Docker and standalone deployment
- ✅ Automatic retry with exponential backoff
- ✅ Comprehensive logging and monitoring
- ✅ Request ID tracking for debugging
- ⚠️ Phase 1: Text-only (no tools/images)
- 🚧 Phase 2: Tool calling support (coming soon)
- 🚧 Phase 2: Image input support (coming soon)

## Table of Contents

- [Quick Start](#quick-start)
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

### Using Python

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

```python
from ollama import Client
client = Client(host='http://localhost:11434')
response = client.generate(model='gpt-3.5-turbo', prompt='Hello!')
print(response['response'])
```

For more examples and detailed setup instructions, see the [Quick Start Guide](docs/QUICK_START.md).

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
| `MODEL_MAPPING_FILE` | Path to model mapping JSON | `None` |

For all configuration options, validation rules, and examples, see the [Configuration Guide](docs/CONFIGURATION.md).

### Quick Testing with OpenRouter

```env
OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-v1-your-key
```

Free models: `google/gemma-2-9b-it:free`, `meta-llama/llama-3.2-3b-instruct:free`

## API Compatibility

See the [API Compatibility Matrix](docs/API_COMPATIBILITY.md) for detailed endpoint mappings and parameter translations.

### Supported Endpoints

| Endpoint | Method | Status | Description |
|----------|--------|---------|-------------|
| `/api/generate` | POST | ✅ Full Support | Text generation |
| `/api/chat` | POST | ✅ Full Support | Chat completion |
| `/api/tags` | GET | ✅ Full Support | List models |
| `/api/embeddings` | POST | ✅ Full Support | Generate embeddings |

### OpenAI Compatibility

The proxy also exposes OpenAI-style endpoints:
- `/v1/chat/completions` - Chat completions
- `/v1/models` - List models  
- `/v1/embeddings` - Generate embeddings

For detailed parameter mappings, response formats, and examples, see the [API Compatibility Matrix](docs/API_COMPATIBILITY.md).

## Examples

See the [examples/](examples/) directory for:
- Python client examples (basic, streaming, batch processing, LangChain)
- JavaScript/Node.js examples
- Configuration templates
- Docker and Nginx setup examples

## Model Mapping

Configure model name mappings to use familiar Ollama names with any backend. See the [Model Mapping Guide](docs/MODEL_MAPPING.md) for detailed configuration options.

### Quick Example

```json
{
  "model_mappings": {
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
    "codellama": "codellama/CodeLlama-7b-Instruct-hf",
    "mistral": "mistralai/Mistral-7B-Instruct-v0.1"
  },
  "default_model": "gpt-3.5-turbo"
}
```

Set in environment:
```env
MODEL_MAPPING_FILE=./config/model_mapping.json
```

For advanced mapping strategies and examples, see the [Model Mapping Guide](docs/MODEL_MAPPING.md).

## Deployment

### Docker Deployment

Using the provided `docker-compose.yml`:

```yaml
version: '3.8'

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

- **Unit Tests**: 273+ tests covering individual components with >85% coverage
- **Integration Tests**: End-to-end API testing with mock backends
- **Performance Tests**: Load testing and benchmarking with metrics validation
- **Security Tests**: Input validation and error handling verification

### Coverage Requirements

Our coverage standards ensure code quality and reliability:

- **Overall Coverage**: ≥80% (enforced by CI)
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

- 🔧 Tool calling support (Phase 2)
- 🖼️ Image input support (Phase 2)
- 📊 Prometheus metrics integration
- 🔐 Additional authentication methods
- 🌐 Multi-language SDK examples
- 📚 Additional documentation and tutorials

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for seamless migration from Ollama to OpenAI-compatible servers
- Inspired by the need to preserve existing codebases during infrastructure changes
- Thanks to all contributors and users providing feedback

---

For more detailed documentation, see the [docs/](docs/) directory.