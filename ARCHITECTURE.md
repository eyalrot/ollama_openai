# Ollama to OpenAI Proxy Service - Architecture Document

## Overview

This document describes the architecture of the Ollama to OpenAI Proxy Service, which provides a transparent translation layer between Ollama API clients and OpenAI-compatible backends (such as VLLM, OpenAI, or other providers).

## Architecture Diagram

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  Ollama Client  │────▶│  Ollama-OpenAI      │────▶│ OpenAI-Compatible│
│  (Python SDK)   │     │  Proxy Service      │     │  Backend Server  │
└─────────────────┘     └─────────────────────┘     └──────────────────┘
       │                         │                            │
       │ Ollama API             │ Translation Layer         │ OpenAI API
       │ (port 11434)           │ - Request mapping         │ (configurable)
       │                        │ - Response mapping        │
       │                        │ - Model name mapping      │
       └────────────────────────┴────────────────────────────┘
```

## Core Components

### 1. Configuration Management (`src/config.py`)
- **Purpose**: Centralized configuration using Pydantic settings
- **Features**:
  - Environment variable validation
  - Type safety with Pydantic V2
  - Singleton pattern for global access
  - Model name mapping support
  - URL validation and normalization

### 2. API Models (`src/models.py`)
- **Purpose**: Define request/response models for both Ollama and OpenAI APIs
- **Components**:
  - Ollama models: `OllamaGenerateRequest`, `OllamaChatRequest`, etc.
  - OpenAI models: `OpenAIChatRequest`, `OpenAIChatResponse`, etc.
  - Model listing structures

### 3. Translation Layer (`src/translators/`)
- **Purpose**: Convert between Ollama and OpenAI formats
- **Components**:
  - Base translator class for common functionality
  - Chat translator: Ollama chat ↔ OpenAI chat completions
  - Embeddings translator: Ollama embeddings ↔ OpenAI embeddings
  - Generate translator: Ollama generate → OpenAI completions

### 4. API Routers (`src/routers/`)
- **Purpose**: FastAPI route handlers for each endpoint
- **Endpoints**:
  - `/api/chat` - Chat completions
  - `/api/generate` - Text generation
  - `/api/embeddings` - Text embeddings
  - `/api/tags` - Model listing
  - `/api/show` - Model information

### 5. Utilities (`src/utils/`)
- **Logging**: Structured JSON logging with request tracking
- **Exceptions**: Custom exception hierarchy for error handling
- **HTTP Client**: Async HTTP client with retry logic

## Requirements

### Functional Requirements
1. **API Compatibility**
   - Full compatibility with Ollama Python SDK
   - Support for all major Ollama endpoints
   - Transparent request/response translation

2. **Model Management**
   - Configurable model name mapping
   - Dynamic model listing from backend
   - Model information retrieval

3. **Streaming Support**
   - Server-sent events (SSE) for streaming responses
   - Proper chunk handling and transformation
   - Error handling during streams

4. **Error Handling**
   - Graceful error translation
   - Meaningful error messages to clients
   - Proper HTTP status code mapping

### Non-Functional Requirements
1. **Performance**
   - Minimal translation overhead (<10ms)
   - Efficient streaming with low memory footprint
   - Connection pooling for backend requests

2. **Scalability**
   - Stateless design for horizontal scaling
   - Async/await for concurrent request handling
   - Configurable timeouts and retry policies

3. **Reliability**
   - Automatic retry with exponential backoff
   - Circuit breaker pattern for backend failures
   - Health check endpoints

4. **Security**
   - API key validation and forwarding
   - No credential storage in logs
   - Secure configuration management

5. **Observability**
   - Structured JSON logging
   - Request ID tracking
   - Performance metrics
   - Error tracking and reporting

## Assumptions

1. **Client Behavior**
   - Clients use standard Ollama Python SDK
   - Clients handle streaming responses appropriately
   - Clients respect rate limits and timeouts

2. **Backend Compatibility**
   - Backend supports OpenAI API v1 format
   - Backend provides compatible model names
   - Backend handles authentication via API keys

3. **Deployment Environment**
   - Docker/Kubernetes deployment preferred
   - Environment variables for configuration
   - Reverse proxy handles TLS termination

4. **Network**
   - Low latency connection to backend
   - Stable network connectivity
   - Sufficient bandwidth for streaming

## Constraints

1. **Technical Constraints**
   - Python 3.9+ required
   - FastAPI framework for API implementation
   - Pydantic V2 for data validation
   - Must maintain Ollama API compatibility

2. **Operational Constraints**
   - Single backend URL per deployment
   - Model mapping configuration is static
   - No request/response caching
   - No built-in authentication (relies on backend)

3. **Development Constraints**
   - Test coverage must exceed 80%
   - All code must pass linting and type checking
   - Docker image size under 200MB
   - CI/CD pipeline for all changes

## Implementation Status

### ✅ Completed

1. **Project Structure** (Task 1)
   - Created directory structure
   - Set up Python package configuration
   - Initialized Git repository
   - Created GitHub repository

2. **Configuration Management** (Task 2)
   - Implemented Pydantic V2 settings
   - Added environment variable validation
   - Created singleton pattern
   - Implemented model mapping loader
   - Added comprehensive test suite (15 tests)

3. **GitHub CI/CD** (Task 16)
   - Created CI pipeline for PR checks
   - Added multi-Python version testing (3.9-3.12)
   - Integrated linting (ruff), formatting (black), type checking (mypy)
   - Set up Docker build testing
   - Configured Dependabot for dependency updates

### 🚧 In Progress

None currently

### 📋 To Do

1. **Logging and Exception Handling** (Task 3)
   - JSON structured logging
   - Custom exception classes
   - Request ID tracking
   - FastAPI middleware integration

2. **Core Translation Logic** (Task 4-7)
   - Base translator implementation
   - Chat endpoint translation
   - Generate endpoint translation
   - Embeddings endpoint translation

3. **API Implementation** (Task 8-11)
   - FastAPI application setup
   - Route handlers for all endpoints
   - Streaming response support
   - Error handling middleware

4. **Testing** (Task 12-13)
   - Unit tests for translators
   - Integration tests with mock servers
   - End-to-end testing
   - Performance benchmarking

5. **Docker Deployment** (Task 14)
   - Multi-stage Dockerfile
   - Compose configuration
   - Kubernetes manifests
   - Helm chart

6. **Documentation** (Task 15)
   - API documentation
   - Deployment guide
   - Migration guide
   - Performance tuning guide

## Design Decisions

1. **FastAPI over Flask**
   - Native async/await support
   - Built-in OpenAPI documentation
   - Pydantic integration
   - Better performance

2. **Pydantic V2**
   - Improved performance
   - Better validation features
   - Native JSON schema support
   - Type safety

3. **Singleton Configuration**
   - Centralized configuration access
   - Immutable after initialization
   - Testable with reset capability

4. **Separate Translator Classes**
   - Single responsibility principle
   - Easier testing and maintenance
   - Extensible for new endpoints

5. **Structured Logging**
   - JSON format for log aggregation
   - Request ID correlation
   - Machine-readable format
   - Consistent field structure

## Future Enhancements

1. **Multi-Backend Support**
   - Route to different backends by model
   - Load balancing across backends
   - Failover mechanisms

2. **Caching Layer**
   - Response caching for repeated requests
   - Model information caching
   - Configurable TTL

3. **Advanced Features**
   - Request/response transformation plugins
   - Custom authentication mechanisms
   - Rate limiting per client
   - Usage analytics

4. **Monitoring**
   - Prometheus metrics
   - OpenTelemetry tracing
   - Custom dashboards
   - Alerting rules

## Security Considerations

1. **API Key Management**
   - Keys never logged
   - Secure forwarding to backend
   - No local storage

2. **Input Validation**
   - Strict request validation
   - SQL injection prevention
   - XSS protection

3. **Network Security**
   - TLS for backend connections
   - Configurable timeouts
   - DDoS protection at proxy level

## Performance Targets

- **Latency**: < 10ms translation overhead
- **Throughput**: > 1000 requests/second
- **Memory**: < 100MB base footprint
- **CPU**: < 5% for translation logic
- **Streaming**: < 1ms per chunk overhead

## Maintenance and Operations

1. **Logging**
   - JSON structured logs
   - Log rotation policies
   - Centralized log aggregation

2. **Monitoring**
   - Health check endpoints
   - Readiness/liveness probes
   - Performance metrics

3. **Updates**
   - Rolling updates supported
   - Backward compatibility
   - Feature flags for gradual rollout

---

*Last Updated: 2025-07-09*