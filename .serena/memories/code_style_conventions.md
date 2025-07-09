# Code Style and Conventions

## Python Code Style

### General Guidelines
- Use Python 3.x type hints throughout the codebase
- Follow PEP 8 conventions (enforced by black formatter)
- Use docstrings for classes and methods (Google/NumPy style)
- Private methods are prefixed with underscore (e.g., `_validate_request`)

### Type Hints
- Full type annotations on all function signatures
- Use Union, Optional, Dict, List from typing module
- Generic types for translators (TypeVar usage)
- Pydantic models for request/response validation

### Class Structure
- Classes use clear docstrings explaining purpose
- Constructor (`__init__`) initializes instance variables
- Public methods come before private methods
- Private helper methods prefixed with underscore

### Error Handling
- Custom exception hierarchy in `src/utils/exceptions.py`
- Specific exceptions for different error cases (ValidationError, TranslationError, etc.)
- Always log errors with structured context
- Re-raise exceptions after logging/handling

### Logging
- Use structured logging with `get_logger(__name__)`
- Include extra context in log entries
- Log levels: DEBUG for detailed info, INFO for general flow, WARNING for issues, ERROR for failures

### Testing Conventions
- Test files mirror source structure in `tests/unit/`
- Test classes group related tests (e.g., `TestHealthEndpoints`)
- Test methods are descriptive (e.g., `test_health_check`)
- Use fixtures for common setup (client, mock_settings)
- Docstrings explain what each test validates
- Mock external dependencies appropriately

### Import Organization
1. Standard library imports
2. Third-party imports
3. Local application imports
4. Separate groups with blank lines

### Naming Conventions
- Classes: PascalCase (e.g., `ChatTranslator`)
- Functions/methods: snake_case (e.g., `translate_request`)
- Constants: UPPER_SNAKE_CASE (e.g., `PROXY_PORT`)
- Private methods: _snake_case (e.g., `_validate_request`)

### Async/Await
- Use async/await for I/O operations
- FastAPI endpoints are async by default
- HTTP client operations use httpx async client