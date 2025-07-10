# Contributing to Ollama-OpenAI Proxy

Thank you for your interest in contributing to the Ollama-OpenAI Proxy project! This guide will help you get started with contributing code, documentation, and other improvements.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Quality Standards](#code-quality-standards)
- [Test Coverage Requirements](#test-coverage-requirements)
- [Submitting Changes](#submitting-changes)
- [Code Review Process](#code-review-process)
- [Documentation](#documentation)
- [Security Guidelines](#security-guidelines)

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Docker and Docker Compose
- Git
- Basic understanding of FastAPI and async Python

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/ollama_openai.git
   cd ollama_openai
   ```

## Development Environment

### Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   pip install -e .
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

4. Create environment file:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Development Workflow

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following our coding standards

3. Run tests and quality checks:
   ```bash
   make test        # Run all tests
   make lint        # Run linting
   make format      # Format code
   make typecheck   # Run type checking
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

## Code Quality Standards

### Code Formatting

We use **Black** for code formatting with a line length of 88 characters:

```bash
# Format all code
black src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

We use **Ruff** for fast Python linting:

```bash
# Run linting
ruff check src/ tests/

# Fix auto-fixable issues
ruff check --fix src/ tests/
```

### Type Checking

We use **MyPy** for static type checking:

```bash
# Run type checking
mypy src/

# Check specific files
mypy src/config.py src/models.py
```

### Import Sorting

We use **Ruff** for import sorting (compatible with isort):

```bash
# Check import order
ruff check --select I src/ tests/

# Fix import order
ruff check --fix --select I src/ tests/
```

## Test Coverage Requirements

We maintain high test coverage standards to ensure code quality and reliability.

### Coverage Thresholds

| Component | Minimum Coverage | Target Coverage |
|-----------|------------------|-----------------|
| **Overall Project** | 80% | 85% |
| **New Code (PRs)** | 85% | 90% |
| **Configuration** | 90% | 95% |
| **Data Models** | 85% | 90% |
| **Translation Layer** | 85% | 90% |
| **API Routes** | 80% | 85% |
| **Utilities** | 75% | 80% |

### Running Coverage Analysis

#### Basic Coverage

```bash
# Run tests with coverage
pytest --cov=src --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

#### Detailed Coverage Analysis

```bash
# XML report for CI
pytest --cov=src --cov-report=xml

# Generate all report formats
pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

# Check coverage with failure threshold
pytest --cov=src --cov-fail-under=80
```

#### Coverage Configuration

Coverage settings are defined in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/conftest.py",
]

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Quality Gates

Our CI/CD pipeline enforces the following quality gates:

#### Automated Checks
- **Overall Coverage**: Must be ≥ 80%
- **New Code Coverage**: Must be ≥ 85%
- **Coverage Drop**: Cannot decrease by more than 2%
- **Test Success Rate**: 100% (all tests must pass)

#### Manual Review
- **Code Style**: Must follow Black/Ruff formatting
- **Type Safety**: MyPy type checking must pass
- **Security**: No security issues in Bandit scan
- **Performance**: No significant performance regressions

### Writing Tests

#### Test Categories

1. **Unit Tests** (`tests/unit/`):
   - Test individual components in isolation
   - Fast execution (< 1ms per test)
   - Mock external dependencies
   - High coverage of edge cases

2. **Integration Tests** (`tests/integration/`):
   - Test component interactions
   - API endpoint testing
   - Database integration (if applicable)
   - Docker container testing

3. **Performance Tests** (`tests/performance/`):
   - Load testing
   - Memory usage validation
   - Response time measurement
   - Regression detection

#### Test Structure

```python
def test_function_name_expected_behavior():
    """Test description explaining what is being tested."""
    # Arrange: Set up test data and mocks
    input_data = create_test_data()
    
    # Act: Execute the function under test
    result = function_under_test(input_data)
    
    # Assert: Verify expected behavior
    assert result.status == "success"
    assert result.data == expected_data
```

#### Coverage Best Practices

1. **Test Happy Paths**: Cover normal use cases
2. **Test Edge Cases**: Empty inputs, boundary values, invalid data
3. **Test Error Conditions**: Network failures, validation errors
4. **Mock External Dependencies**: APIs, databases, file systems
5. **Use Fixtures**: Reusable test data and setup
6. **Assert Meaningful Values**: Don't just test for existence

#### Example Test with Coverage

```python
import pytest
from unittest.mock import Mock, patch
from src.translators.chat import ChatTranslator
from src.models import OpenAIChatRequest

@pytest.fixture
def chat_translator():
    """Create a ChatTranslator instance for testing."""
    return ChatTranslator()

@pytest.fixture
def sample_request():
    """Sample OpenAI chat request."""
    return OpenAIChatRequest(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )

def test_translate_request_success(chat_translator, sample_request):
    """Test successful request translation."""
    # Act
    result = chat_translator.translate_request(sample_request)
    
    # Assert
    assert result.model == "gpt-3.5-turbo"
    assert len(result.messages) == 1
    assert result.messages[0]["role"] == "user"

def test_translate_request_with_model_mapping(chat_translator):
    """Test request translation with model name mapping."""
    # Arrange
    request = OpenAIChatRequest(
        model="ollama-model",
        messages=[{"role": "user", "content": "Test"}]
    )
    
    # Act
    result = chat_translator.translate_request(request)
    
    # Assert - model should be mapped
    assert result.model == "openai-equivalent"

def test_translate_request_invalid_model(chat_translator):
    """Test translation with invalid model raises error."""
    # Arrange
    request = OpenAIChatRequest(
        model="",  # Invalid empty model
        messages=[{"role": "user", "content": "Test"}]
    )
    
    # Act & Assert
    with pytest.raises(ValidationError):
        chat_translator.translate_request(request)

@patch('src.utils.http_client.httpx.AsyncClient')
async def test_backend_request_failure(mock_client, chat_translator):
    """Test handling of backend request failures."""
    # Arrange
    mock_client.return_value.post.side_effect = HTTPError("Connection failed")
    
    # Act & Assert
    with pytest.raises(ProxyError):
        await chat_translator.make_backend_request(sample_request)
```

### Coverage Exclusions

The following patterns are excluded from coverage analysis:

- **Test Files**: `tests/`, `*test*.py`
- **Debug Code**: Lines with `pragma: no cover`
- **Representation Methods**: `__repr__`, `__str__`
- **Main Blocks**: `if __name__ == "__main__":`
- **Type Checking**: `if TYPE_CHECKING:`
- **Abstract Methods**: `@abstractmethod`
- **Not Implemented**: `raise NotImplementedError`

### Improving Coverage

If your PR reduces coverage below the threshold:

1. **Identify Missing Coverage**:
   ```bash
   pytest --cov=src --cov-report=term-missing
   # Look for lines marked with "!"
   ```

2. **Add Missing Tests**:
   - Focus on uncovered lines
   - Add edge case tests
   - Test error conditions

3. **Review Coverage Report**:
   ```bash
   pytest --cov=src --cov-report=html
   open htmlcov/index.html
   # Click through files to see uncovered lines
   ```

4. **Use Coverage Pragmas Sparingly**:
   ```python
   # Only for truly untestable code
   if sys.platform == "win32":  # pragma: no cover
       # Windows-specific code
   ```

## Submitting Changes

### Pull Request Guidelines

1. **Clear Title**: Use conventional commit format
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `test:` for test improvements
   - `refactor:` for code refactoring

2. **Detailed Description**:
   - Explain what changes were made
   - Reference any related issues
   - Include testing instructions

3. **Checklist**:
   - [ ] Tests added/updated for new functionality
   - [ ] Coverage maintained above 80%
   - [ ] Documentation updated
   - [ ] Code formatted with Black
   - [ ] Linting passes with Ruff
   - [ ] Type checking passes with MyPy
   - [ ] All tests pass

### Template

```markdown
## Description
Brief description of the changes made.

## Related Issues
Fixes #123
Related to #456

## Changes Made
- Added new feature X
- Fixed bug in component Y
- Updated documentation for Z

## Testing
- Added unit tests for new functionality
- Verified existing tests still pass
- Manual testing performed for edge cases

## Coverage Impact
- Overall coverage: 85.2% (+0.5%)
- New code coverage: 92.1%
- No files below component thresholds

## Checklist
- [x] Tests added/updated
- [x] Coverage requirements met
- [x] Documentation updated
- [x] Code quality checks passed
```

## Code Review Process

### Review Criteria

1. **Functionality**: Does the code work as intended?
2. **Quality**: Is the code clean, readable, and maintainable?
3. **Tests**: Are there adequate tests with good coverage?
4. **Performance**: No significant performance regressions?
5. **Security**: No security vulnerabilities introduced?

### Reviewer Guidelines

- Be constructive and specific in feedback
- Focus on code quality and maintainability
- Verify test coverage meets requirements
- Check for security implications
- Ensure documentation is updated

## Documentation

### Documentation Standards

- Update README.md for user-facing changes
- Add docstrings for all public functions/classes
- Update API documentation for endpoint changes
- Add examples for complex functionality

### Docstring Format

```python
def translate_request(self, request: OpenAIChatRequest) -> OllamaChatRequest:
    """Translate OpenAI chat request to Ollama format.
    
    Args:
        request: The OpenAI chat request to translate.
        
    Returns:
        OllamaChatRequest: The translated request in Ollama format.
        
    Raises:
        ValidationError: If the request is invalid.
        TranslationError: If translation fails.
        
    Example:
        >>> translator = ChatTranslator()
        >>> openai_request = OpenAIChatRequest(...)
        >>> ollama_request = translator.translate_request(openai_request)
    """
```

## Security Guidelines

### Secure Coding Practices

1. **Input Validation**: Validate all inputs with Pydantic models
2. **Error Handling**: Don't expose sensitive information in errors
3. **Secrets Management**: Never commit API keys or passwords
4. **Dependencies**: Keep dependencies updated and secure

### Security Testing

- All PRs are scanned with Bandit and TruffleHog
- Container images scanned with Trivy
- Dependencies checked for vulnerabilities
- Manual security review for sensitive changes

## Getting Help

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Security**: Email security issues to [security email]

Thank you for contributing to the Ollama-OpenAI Proxy project!