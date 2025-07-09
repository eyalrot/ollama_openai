# Project Structure

## Directory Layout

```
ollama_openai/
├── src/                     # Main application source code
│   ├── __init__.py
│   ├── main.py             # FastAPI application entry point
│   ├── config.py           # Configuration management with Pydantic
│   ├── models.py           # Request/response models for Ollama and OpenAI
│   ├── middleware/         # Custom middleware components
│   │   ├── error_handler.py
│   │   └── logging_middleware.py
│   ├── routers/            # API endpoint handlers
│   │   ├── chat.py         # Chat and generate endpoints
│   │   ├── models.py       # Model listing and management
│   │   └── embeddings.py   # Embeddings endpoint
│   ├── translators/        # Format conversion logic
│   │   ├── base.py         # Base translator class
│   │   ├── chat.py         # Chat/generate translator
│   │   └── embeddings.py   # Embeddings translator
│   └── utils/              # Utility modules
│       ├── exceptions.py   # Custom exception classes
│       ├── http_client.py  # HTTP client with retry logic
│       └── logging.py      # Structured logging setup
├── tests/                  # Test suite
│   ├── unit/              # Unit tests mirroring src structure
│   └── test_docker.py     # Docker integration tests
├── docker/                # Docker configurations
│   ├── Dockerfile.ci      # CI-specific Docker image
│   └── docker-compose.ci.yml
├── scripts/               # Utility scripts
│   └── test-ci-local.sh   # Local CI testing script
├── config/                # Configuration files
│   ├── model_map.json     # Model name mappings
│   └── model_map.example.json
├── docs/                  # Documentation
│   └── MODEL_MAPPING.md   # Model mapping documentation
├── .github/               # GitHub specific files
│   └── workflows/         # GitHub Actions workflows
│       └── ci.yml         # CI pipeline configuration
├── .taskmaster/           # Task Master project management
│   ├── tasks/            # Task tracking files
│   ├── docs/             # Project documentation (PRD, etc.)
│   └── config.json       # Task Master configuration
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── Dockerfile            # Production Docker image
├── docker-compose.yml    # Docker compose configuration
├── .env.example          # Environment variable template
├── README.md             # Project documentation
├── ARCHITECTURE.md       # Architecture documentation
└── CLAUDE.md             # Claude Code context (auto-loaded)
```

## Key Components

### Entry Points
- `src/main.py` - FastAPI application with lifespan management
- Health check endpoints: `/health`, `/ready`, `/`

### API Endpoints
- **Ollama Format**: `/api/generate`, `/api/chat`, `/api/tags`, `/api/embeddings`
- **OpenAI Format**: `/v1/chat/completions`, `/v1/models`, `/v1/embeddings`

### Core Logic Flow
1. Request arrives at FastAPI router
2. Middleware adds request ID and logging
3. Router validates and passes to translator
4. Translator converts Ollama → OpenAI format
5. HTTP client makes request to upstream
6. Response translated back to Ollama format
7. Streaming handled via Server-Sent Events

### Configuration
- Environment variables loaded via `.env` file
- Pydantic Settings for validation
- Model mappings in `config/model_map.json`