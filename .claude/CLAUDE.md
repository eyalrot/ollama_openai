# Ollama OpenAI Proxy - Claude Code Integration Guide

## Python Virtual Environment Setup

**IMPORTANT**: All Python commands in this project must be executed within the virtual environment.

### Activate Virtual Environment

```bash
# Always activate the virtual environment first
source venv/bin/activate

# Verify activation (should show venv path)
which python
which pip

# Check installed packages
pip list
```

### Development Workflow

```bash
# 1. Activate venv first
source venv/bin/activate

# 2. Install dependencies (if needed)
pip install -r requirements.txt

# 3. Run tests
python -m pytest tests/

# 4. Run linting
python -m ruff check .

# 5. Run type checking
python -m mypy src/

# 6. Run the application
python -m uvicorn src.main:app --reload
```

## Project Structure

```
ollama_openai/
├── src/                    # Source code
│   ├── main.py            # FastAPI application entry point
│   ├── config.py          # Configuration management
│   ├── models.py          # Pydantic models
│   ├── routers/           # API route handlers
│   ├── translators/       # API translation logic
│   ├── middleware/        # FastAPI middleware
│   └── utils/             # Utility functions
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── performance/      # Performance tests
├── venv/                 # Virtual environment (activate first!)
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
└── README.md            # Project documentation
```

## Core Components

### Configuration (src/config.py)
- Environment-based settings using Pydantic
- API key validation and URL normalization
- Model mapping file support
- Singleton pattern for global settings

### Models (src/models.py)
- Pydantic models for Ollama and OpenAI APIs
- Request/response validation
- Streaming support
- Error handling models

### HTTP Client (src/utils/http_client.py)
- Retry logic with exponential backoff
- Circuit breaker pattern
- Connection pooling
- Timeout handling

## Testing

### Running Tests

```bash
# Activate venv first!
source venv/bin/activate

# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/test_models.py

# Run with coverage
python -m pytest --cov=src tests/

# Run with verbose output
python -m pytest -v

# Run specific test class
python -m pytest tests/unit/test_models.py::TestOllamaOptions

# Run specific test method
python -m pytest tests/unit/test_models.py::TestOllamaOptions::test_validation_ranges
```

### Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for full workflows
- `tests/performance/` - Performance and load testing

## Common Development Tasks

### Code Quality

```bash
# Activate venv first!
source venv/bin/activate

# Linting
python -m ruff check .
python -m ruff format .

# Type checking
python -m mypy src/

# Security scanning
python -m bandit -r src/
```

### Database/Migration Tasks

```bash
# Activate venv first!
source venv/bin/activate

# If using Alembic for migrations
python -m alembic upgrade head
python -m alembic revision --autogenerate -m "description"
```

### Running the Application

```bash
# Activate venv first!
source venv/bin/activate

# Development server
python -m uvicorn src.main:app --reload --port 8000

# Production server
python -m gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Required
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=your-api-key-here

# Optional
PROXY_PORT=11434
LOG_LEVEL=INFO
REQUEST_TIMEOUT=60
MAX_RETRIES=3
DEBUG=False
MODEL_MAPPING_FILE=./model_mappings.json
DISABLE_SSL_VERIFICATION=False
```

## Docker Support

```bash
# Build image
docker build -t ollama-openai-proxy .

# Run container
docker run -p 11434:11434 --env-file .env ollama-openai-proxy

# Docker compose
docker-compose up -d
```

## Debugging

### Common Issues

1. **Import errors**: Ensure venv is activated and dependencies installed
2. **Test failures**: Check environment variables and test data
3. **API errors**: Verify API keys and endpoints in `.env`
4. **Performance issues**: Check connection pooling and timeout settings

### Debug Commands

```bash
# Activate venv first!
source venv/bin/activate

# Debug mode
python -m uvicorn src.main:app --reload --log-level debug

# Profile performance
python -m cProfile -o profile.out src/main.py
python -m pstats profile.out

# Memory profiling
python -m memory_profiler src/main.py
```

## Claude Code Integration

### Tool Allowlist

Add to `.claude/settings.json`:

```json
{
  "allowedTools": [
    "Edit",
    "Read",
    "Bash(source venv/bin/activate *)",
    "Bash(python -m pytest *)",
    "Bash(python -m ruff *)",
    "Bash(python -m mypy *)",
    "Bash(python -m uvicorn *)"
  ]
}
```

### Custom Commands

Create `.claude/commands/test-with-venv.md`:

```markdown
Run tests in virtual environment: $ARGUMENTS

Steps:
1. Activate virtual environment: `source venv/bin/activate`
2. Run tests: `python -m pytest $ARGUMENTS`
3. Deactivate if needed: `deactivate`
```

## Important Reminders

1. **Always activate venv first**: `source venv/bin/activate`
2. **Use python -m**: Run modules with `python -m` for proper path resolution
3. **Check dependencies**: Run `pip list` to verify installed packages
4. **Environment variables**: Ensure `.env` file is properly configured
5. **Test before commit**: Run full test suite before committing changes

---

*This guide ensures all Python operations are performed within the proper virtual environment context.*