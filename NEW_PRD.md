# Product Requirements Document: Ollama-OpenAI Proxy Service

## Executive Summary

**Project Vision**: Build a production-ready proxy service that seamlessly translates between Ollama API format and OpenAI-compatible API backends, enabling zero-code migration for existing Ollama applications.

**Primary Use Cases**:
- **N8N Integration**: Enable N8N's Ollama model node to connect to OpenAI-compatible APIs
- **Zero-Code Migration**: Existing Ollama applications work unchanged
- **Dual API Support**: Native support for both Ollama and OpenAI API formats
- **Enterprise Deployment**: Production-ready with comprehensive monitoring and observability

**Project Scope**: Develop a sophisticated, enterprise-grade service that maintains core simplicity and reliability while providing advanced features including metrics collection, tool calling, multimodal support, and comprehensive error handling.

## High-Level Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Ollama Client  │────│  Proxy Service  │────│  OpenAI API     │
│  Applications   │    │  (Translation)  │    │  Compatible     │
│                 │    │                 │    │  Backend        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Value Proposition
- **Zero Code Changes**: Existing Ollama applications work unchanged
- **Dual API Support**: Support both Ollama and OpenAI API formats simultaneously  
- **Universal Compatibility**: Works with any OpenAI-compatible backend
- **Production Ready**: Proper logging, error handling, and monitoring

## Implementation Phases

### Phase 1: Foundation & Core Translation

#### 1.1 Project Setup & Infrastructure
**Goal**: Establish development foundation
- FastAPI project structure with proper Python packaging
- Configuration management using Pydantic Settings
- Logging infrastructure with structured logging
- Environment-based configuration (.env support)
- Docker containerization setup
- Comprehensive CI/CD pipeline (GitHub Actions)
- Test framework setup (pytest, target coverage >60%)

#### 1.2 Core API Translation Engine
**Goal**: Implement basic request/response translation
- Pydantic models for Ollama and OpenAI API formats
- Translation layer between API formats:
  - Chat completion requests/responses
  - Text generation requests/responses  
  - Model listing endpoints
  - Error response translation
- HTTP client with proper retry logic and connection pooling
- Request/response validation and sanitization

#### 1.3 Basic Endpoints Implementation
**Goal**: Implement core proxy endpoints
- `/api/chat` → `/v1/chat/completions` (Ollama chat to OpenAI chat)
- `/api/generate` → `/v1/chat/completions` (Ollama generate to OpenAI chat)
- `/api/tags` → `/v1/models` (Model listing)
- `/v1/chat/completions` (Native OpenAI format passthrough)
- `/v1/models` (Native OpenAI format passthrough)
- Health check and status endpoints

#### 1.4 Configuration & Model Mapping
**Goal**: Flexible configuration system
- Environment variable configuration
- Optional model name mapping (JSON file)
- Default model handling
- Configuration validation

### Phase 2: Production Infrastructure & Resilience

#### 2.1 Streaming Support
**Goal**: Real-time streaming responses
- Server-Sent Events (SSE) for Ollama streaming format
- OpenAI streaming format support
- Streaming response translation between formats
- Proper connection handling and cleanup
- Stream error handling and recovery

#### 2.2 Comprehensive Error Handling System
**Goal**: Production-grade error management and debugging
- Comprehensive error mapping between API formats
- Custom exception hierarchy (`ProxyException`, `UpstreamError`, `TranslationError`)
- Retry logic with exponential backoff and jitter
- Circuit breaker pattern for upstream failures
- Timeout handling and configuration
- Graceful degradation strategies
- Request correlation ID tracking for distributed tracing
- Error context preservation and detailed error reporting
- Graceful error propagation with proper HTTP status codes
- Error boundary handling for upstream service failures

#### 2.3 Production Middleware Stack & Request Processing
**Goal**: Enterprise-grade request processing and validation
- Advanced logging middleware with structured output
- Metrics collection middleware with performance tracking
- CORS handling for web application integration
- Input validation and sanitization with Pydantic
- Request size limits and rate limiting
- Parameter translation and normalization
- Content-type handling (JSON, multipart)
- Request ID tracking for debugging
- **Critical: Proper request body handling** (see implementation notes below)
- Smart request body parsing with error recovery
- Content-type validation and normalization
- Request size limits and memory management
- Input sanitization for security compliance
- Parameter validation with detailed error messages
- Request size validation and timeout enforcement
- Connection pooling with configurable limits

**🚨 Critical Implementation Note - Request Body Handling:**
- **Never call `request.json()` directly** - this consumes the body stream and prevents re-reading
- **Use `await request.body()` first** to get raw bytes, then parse with `json.loads()`
- **Implement body caching middleware** to allow multiple middleware to access the body
- **Handle empty/malformed JSON gracefully** with proper error responses
- **Example safe pattern:**
  ```python
  # ✅ CORRECT: Cache body for multiple access
  body = await request.body()
  if body:
      request_data = json.loads(body.decode('utf-8'))
  
  # ❌ WRONG: Consumes stream, blocks other middleware
  request_data = await request.json()
  ```
- **Test middleware order carefully** - body-consuming middleware must come after body-caching
- **Implement request body size limits** before parsing to prevent memory exhaustion

#### 2.4 Comprehensive Monitoring & Metrics
**Goal**: Production-grade observability and analytics
- Structured logging with correlation IDs
- Request/response logging (configurable verbosity)
- Performance metrics collection
- Health check endpoints with detailed status
- Error tracking and reporting
- `/v1/metrics` endpoint with Prometheus format support
- System metrics collection (CPU, memory, disk usage)
- Request/response performance tracking
- Custom metrics middleware with detailed analytics
- Request body size and processing time tracking
- Error rate and success rate monitoring
- Advanced observability features

#### 2.5 Version Management & API Infrastructure
**Goal**: Mature version control and API infrastructure
- Comprehensive version tracking system
- `/v1/version` endpoint with detailed build information
- API versioning support for future compatibility
- Build metadata and commit SHA tracking
- Development version detection
- API endpoint organization and routing infrastructure

### Phase 3: Advanced API Features

#### 3.1 Advanced Model Features
**Goal**: Enhanced model compatibility and capabilities
- Embeddings endpoint support (`/api/embeddings` ↔ `/v1/embeddings`)
- Model capability detection and discovery
- Dynamic model routing and selection
- Model health checking and status monitoring
- Advanced model configuration and parameter handling
- Model-specific optimization strategies

#### 3.2 Tool Calling & Multimodal Support
**Goal**: Advanced AI capabilities and rich interactions
- Function/tool calling translation between formats
- Tool definition and schema validation
- Image input support (base64, data URLs, file uploads)
- Multimodal request handling and processing
- Tool response formatting and validation
- Advanced tool calling features (parallel calls, nested calls)
- Vision model integration and optimization

#### 3.3 Performance Optimization & Security Hardening
**Goal**: Production-grade performance and security
- Connection pooling optimization and tuning
- Request/response caching strategies
- SSL/TLS configuration and certificate management
- Security headers and comprehensive CORS setup
- Advanced rate limiting and throttling
- Input sanitization for security compliance
- Authentication and authorization enhancements
- Performance profiling and optimization
- Memory management and resource optimization
- Advanced security scanning and vulnerability assessment

### Phase 4: Deployment & Production Polish

#### 4.1 Multi-Architecture Deployment
**Goal**: Comprehensive deployment packaging and distribution
- Multi-architecture Docker images (linux/amd64, linux/arm64)
- Optimized production Dockerfile with multi-stage builds
- Docker Hub and GitHub Container Registry publishing
- PyPI package distribution with proper versioning
- Automated build and release pipelines
- Container image optimization and security scanning

#### 4.2 Production Deployment Configurations
**Goal**: Easy deployment and orchestration options
- Docker Compose configurations for various scenarios
- Kubernetes deployment manifests and Helm charts
- Environment-specific configuration templates
- Production-ready environment variable documentation
- Load balancing and scaling configurations
- Health check and readiness probe configurations

#### 4.3 Final Performance Optimization
**Goal**: Production-grade performance tuning
- Connection pool optimization and tuning
- Memory usage optimization and profiling
- Response time optimization and benchmarking
- Resource usage monitoring and optimization
- Caching strategy implementation and tuning
- Performance regression testing and monitoring

#### 4.4 Security Audit & Final Hardening
**Goal**: Enterprise security compliance and audit readiness
- Comprehensive security vulnerability scanning
- Security configuration review and hardening
- SSL/TLS configuration optimization
- Authentication and authorization audit
- Input validation and sanitization review
- Security documentation and compliance reporting

#### 4.5 Production Documentation & Support
**Goal**: Complete deployment and operational documentation
- Comprehensive deployment guides for different environments
- Operational runbooks and troubleshooting guides
- Performance tuning and optimization guides
- Security configuration and best practices documentation
- Monitoring and alerting setup guides
- API compatibility matrix and migration guides

### Phase 5: Documentation Enhancement & Developer Experience

**Goal**: Transform basic documentation into comprehensive, production-ready API reference that significantly improves developer onboarding and integration experience.

**Priority**: High - Critical for developer adoption and ecosystem growth

#### 5.1 Comprehensive API Documentation
**Goal**: Complete documentation for all endpoints with examples and usage guidance
- Document all available endpoints (`/api/*` and `/v1/*`) with comprehensive examples
- Include detailed request/response examples for every endpoint
- Document all supported parameters with validation rules and constraints
- Add endpoint descriptions explaining purpose, use cases, and best practices
- Create interactive examples that developers can test directly

#### 5.2 Production Documentation Access
**Goal**: Enable comprehensive documentation in production environments
- Enable Swagger/OpenAPI documentation access in production
- Add configurable documentation visibility controls
- Implement proper access controls and security considerations
- Create schema export capabilities (JSON/YAML) for CI/CD integration
- Add documentation performance optimizations

#### 5.3 Error Code & Authentication Documentation
**Goal**: Complete reference for error handling and authentication flows
- Document all possible HTTP status codes with context and examples
- Include error response examples with proper error structures
- Add troubleshooting guidance for common error scenarios
- Document API key requirements, format, and usage patterns
- Include authentication examples for different endpoint types
- Add security best practices and guidelines

#### 5.4 Developer Experience Enhancements
**Goal**: Reduce integration complexity and improve developer onboarding
- Add code samples for popular programming languages (Python, JavaScript, cURL)
- Document model compatibility and mapping strategies
- Create quick start guides and common usage patterns
- Add integration examples for popular frameworks (LangChain, N8N)
- Implement schema validation in test suite for documentation consistency

#### 5.5 Advanced Documentation Features
**Goal**: Professional-grade documentation infrastructure
- Dynamic versioning integration from `_version.py`
- Contact information, license, and terms of service integration
- Operation IDs for better client SDK generation
- Pre-generated schema files for version control
- CI/CD integration for schema consistency validation

## Technical Requirements

### Core Technologies
- **Framework**: FastAPI 0.104.0+ (modern, async, comprehensive auto-docs)
- **Validation**: Pydantic v2.5.0+ (advanced request/response models with custom validators)
- **HTTP Client**: httpx 0.25.0+ (async HTTP with advanced retry logic and connection pooling)
- **Logging**: structlog 23.2.0+ (structured logging with correlation IDs)
- **Deployment**: Multi-platform Docker + uvicorn with production optimizations
- **Testing**: pytest + pytest-asyncio + pytest-cov with target coverage >60%
- **Metrics**: Custom middleware with Prometheus format support
- **Security**: Comprehensive input validation, CORS, SSL/TLS support

### Key Configuration Parameters
```env
# Required
OPENAI_API_BASE_URL=https://api.openai.com/v1    # Your OpenAI-compatible API URL
OPENAI_API_KEY=sk-your-api-key                   # API key for authentication

# Core Optional Settings
PROXY_PORT=11434                                 # Port for proxy service
LOG_LEVEL=INFO                                   # Logging verbosity (DEBUG, INFO, WARNING, ERROR)
REQUEST_TIMEOUT=60                               # Request timeout in seconds
MAX_RETRIES=3                                    # Maximum retry attempts
DEBUG=false                                      # Enable debug mode

# Advanced Configuration
MODEL_MAPPING_FILE=./config/model_mapping.json  # Optional model name mapping
DISABLE_SSL_VERIFICATION=false                  # Disable SSL verification (not recommended)
ENABLE_METRICS=true                             # Enable metrics collection
CORS_ORIGINS=*                                  # CORS allowed origins
REQUEST_MAX_SIZE=10485760                       # Max request size (10MB)

# Production Features
ENABLE_PROMETHEUS_METRICS=true                  # Prometheus format metrics
METRICS_PATH=/v1/metrics                        # Metrics endpoint path
VERSION_ENDPOINT_ENABLED=true                   # Enable version endpoint
HEALTH_CHECK_TIMEOUT=30                         # Health check timeout
```

### Target Deployment Options
- **Docker Hub**: Multi-architecture container images
- **GitHub Container Registry**: Enterprise container hosting
- **PyPI Package**: `pip install` distribution
- **Source Installation**: Direct from GitHub repository
- **Multi-Architecture**: linux/amd64, linux/arm64 support

### API Endpoints to Implement

#### Ollama Format Endpoints
- `POST /api/chat` - Chat completion (Ollama style) with streaming support
- `POST /api/generate` - Text generation (Ollama style) with streaming support
- `GET /api/tags` - List available models with caching
- `POST /api/embeddings` - Generate embeddings with batch support

#### OpenAI Format Endpoints  
- `POST /v1/chat/completions` - Chat completion (OpenAI style) with tool calling and multimodal
- `GET /v1/models` - List available models with detailed metadata
- `POST /v1/embeddings` - Generate embeddings with OpenAI compatibility

#### Utility & Monitoring Endpoints
- `GET /health` - Health check with upstream status
- `GET /ready` - Readiness check with dependency validation
- `GET /` - Service information and available endpoints
- `GET /v1/version` - Version information and build metadata
- `GET /v1/metrics` - Prometheus format metrics (CPU, memory, requests)

#### Documentation Endpoints
- `GET /docs` - Interactive Swagger UI (production access)
- `GET /redoc` - ReDoc documentation interface
- `GET /openapi.json` - OpenAPI schema export
- `GET /openapi.yaml` - YAML schema export

## Success Criteria

### Phase 1 Success Metrics
- All core endpoints functional with basic translation
- Test coverage >60%
- Docker deployment working (multi-architecture)
- Basic documentation complete

### Phase 2 Success Metrics
- Streaming responses working for both API formats
- Comprehensive error handling system with custom exception hierarchy
- Production middleware stack with comprehensive logging and metrics
- Advanced monitoring with Prometheus format support (/v1/metrics endpoint)
- Version management and API versioning system functional
- Request processing and validation system robust and secure

### Phase 3 Success Metrics
- Embeddings endpoints functional with full compatibility
- Tool calling and multimodal support working with advanced features
- Performance optimization achieving <100ms translation overhead
- Security hardening with comprehensive input validation and authentication
- Advanced model features including capability detection and routing

### Phase 4 Success Metrics
- Multi-architecture Docker deployment working (Docker Hub + GHCR)
- Production deployment configurations complete (Docker Compose, K8s)
- Final performance optimization and resource tuning complete
- Security audit passed with comprehensive vulnerability scanning
- Complete operational documentation and deployment guides

### Phase 5 Success Metrics
- Production-accessible Swagger/OpenAPI documentation
- Complete API reference with examples and error codes
- Developer onboarding time reduced by 50%
- Schema export functionality for CI/CD integration
- Multi-language code samples and integration guides

## Quality Requirements

### Performance Targets
- Translation overhead: <100ms for non-streaming requests
- Memory usage: <100MB base memory footprint
- Concurrent connections: Support 100+ simultaneous requests
- Streaming latency: <10ms first token time overhead
- System metrics: CPU, memory, and disk usage monitoring

### Reliability Targets
- Uptime: 99.9% availability target with health checks
- Error recovery: Graceful handling of upstream failures
- Retry logic: Exponential backoff with jitter and configurable timeouts
- Timeouts: Fully configurable with intelligent defaults
- Circuit breaker: Failure detection and recovery

### Security Requirements
- Input validation: Comprehensive request sanitization
- API key handling: Secure forwarding with no logging exposure
- SSL/TLS: Full certificate handling and HTTPS support
- CORS: Configurable cross-origin support with security headers
- Security scanning: Vulnerability detection in CI/CD

### Maintainability Requirements
- Test coverage: >60% overall, >90% for core translation logic
- Code quality: Full type hints, linting, formatting, type checking
- Documentation: Comprehensive API docs, deployment guides, examples
- Monitoring: Structured logging, health checks, metrics
- CI/CD: Automated testing and deployment pipeline

### Developer Experience Goals
- API Documentation: Production-accessible comprehensive documentation
- Integration Examples: Multi-language code samples and framework integrations
- Schema Export: JSON/YAML schema export for automated tooling
- Developer Onboarding: Streamlined getting-started experience

## Implementation Guidelines

### Development Principles
1. **Simplicity First**: Keep architecture simple and maintainable
2. **Test-Driven**: Write tests before implementation
3. **Configuration-Driven**: Avoid hardcoded values
4. **Error-Friendly**: Provide clear error messages
5. **Performance-Conscious**: Optimize for low latency
6. **Security-Aware**: Validate all inputs, handle secrets properly
7. **🚨 Body-Stream-Aware**: Never consume request body streams multiple times

### Critical Implementation Patterns

#### Request Body Handling (Essential for FastAPI Middleware)
**Problem**: FastAPI request bodies are streams that can only be read once. Multiple middleware attempting to read the body will cause `StreamClosedError`.

**Solution Pattern**:
```python
# ✅ CORRECT: Body caching middleware (implement first in chain)
@app.middleware("http")
async def cache_request_body(request: Request, call_next):
    # Cache the body for multiple access
    body = await request.body()
    
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    
    # Store body for other middleware/handlers
    request.state.body = body
    request._receive = receive
    
    response = await call_next(request)
    return response

# ✅ CORRECT: Safe body access in other middleware
async def get_request_data(request: Request) -> dict:
    try:
        if hasattr(request.state, 'body') and request.state.body:
            return json.loads(request.state.body.decode('utf-8'))
        return {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid JSON in request body")

# ❌ WRONG: Direct json() calls in middleware
async def broken_middleware(request: Request, call_next):
    data = await request.json()  # This will break other middleware!
```

**Testing Requirements**:
- Test middleware order and body access patterns
- Verify empty body handling
- Test malformed JSON error cases
- Ensure body size limits work correctly

### Recommended Code Organization

```text
ollama_openai/
├── src/                           # Main application source
│   ├── main.py                    # FastAPI app with production setup
│   ├── config.py                  # Pydantic Settings configuration
│   ├── models.py                  # Comprehensive Pydantic models
│   ├── _version.py                # Version management and metadata
│   ├── routers/                   # API endpoint handlers
│   │   ├── chat.py                # Chat and generation endpoints
│   │   ├── models.py              # Model listing endpoints
│   │   ├── embeddings.py          # Embeddings endpoints
│   │   ├── metrics.py             # Metrics and monitoring
│   │   └── version.py             # Version information
│   ├── translators/               # Format translation logic
│   │   ├── base.py                # Base translation interfaces
│   │   ├── chat.py                # Chat format translation
│   │   └── embeddings.py          # Embeddings translation
│   ├── middleware/                # Request processing middleware
│   │   ├── error_handler.py       # Global error handling
│   │   ├── logging_middleware.py  # Structured logging
│   │   └── metrics_middleware.py  # Performance tracking
│   └── utils/                     # Shared utilities
│       ├── exceptions.py          # Custom exception hierarchy
│       ├── http_client.py         # Advanced HTTP client
│       ├── logging.py             # Logging configuration
│       ├── metrics.py             # Metrics collection
│       └── request_body.py        # Request processing utilities
├── tests/                         # Comprehensive test suite
│   ├── unit/                      # Unit tests
│   │   ├── routers/               # Router-specific tests
│   │   ├── translators/           # Translation logic tests
│   │   └── utils/                 # Utility function tests
│   ├── performance/               # Performance and load tests
│   └── test_docker.py             # Docker integration tests
├── docs/                          # Comprehensive documentation
│   ├── QUICK_START.md             # Getting started guide
│   ├── CONFIGURATION.md           # Configuration reference
│   ├── API_COMPATIBILITY.md       # API compatibility matrix
│   ├── TESTING.md                 # Testing documentation
│   └── SECURITY.md                # Security guidelines
├── docker/                        # Docker configurations
│   ├── Dockerfile.prod            # Production Dockerfile
│   ├── docker-compose.*.yml       # Various deployment configs
│   └── build.sh                   # Build automation
├── examples/                      # Usage examples
│   ├── python/                    # Python SDK examples
│   ├── javascript/                # JavaScript examples
│   └── advanced/                  # Advanced feature examples
├── pyproject.toml                 # Python project configuration
├── Makefile                       # Development automation
└── ARCHITECTURE.md                # System architecture documentation
```

### Quality Gates
- All tests must pass before merge
- Code coverage must not decrease (target >60%)
- Linting and formatting checks must pass (ruff, black, mypy)
- Security scan must pass (Trivy, Bandit, TruffleHog)
- Docker build must succeed (multi-architecture builds)
- Performance benchmarks must meet thresholds
- Documentation must be updated for new features

### Development Practices
- **Automated CI/CD**: Complete GitHub Actions pipeline
- **Multi-Architecture Builds**: AMD64 and ARM64 Docker images
- **Package Distribution**: PyPI package with semantic versioning
- **Container Registries**: Docker Hub and GitHub Container Registry
- **Test Coverage**: Comprehensive unit, integration, and performance tests
- **Security Scanning**: Automated vulnerability detection
- **Code Quality**: Enforced linting, formatting, and type checking

## Conclusion

This PRD outlines the development of a production-ready Ollama-OpenAI proxy service that will provide:

### **Target Goals**
- **Seamless Integration**: Zero-code migration for existing Ollama applications
- **Universal Compatibility**: Works with all major OpenAI-compatible backends
- **Production Excellence**: Enterprise-grade reliability, performance, and security
- **Advanced Features**: Tool calling, multimodal support, comprehensive metrics
- **Developer Experience**: Extensive documentation, examples, and deployment options

### **Success Metrics**
- Target >60% test coverage with comprehensive test suite
- Multi-architecture Docker deployment on container registries
- PyPI package distribution for easy installation
- Enterprise security standards with automated vulnerability scanning
- Advanced monitoring with Prometheus metrics and structured logging

The Ollama-OpenAI Proxy will transform from a simple translation concept into a mature, enterprise-ready service that maintains simplicity while providing comprehensive functionality for production deployments.