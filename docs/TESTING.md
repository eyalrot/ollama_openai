# Testing Guide

![Test Coverage](https://codecov.io/gh/eyalrot/ollama_openai/branch/master/graph/badge.svg)

This comprehensive guide covers all aspects of testing the Ollama-OpenAI proxy service, from unit tests to performance validation.

## Overview

Our testing strategy follows the test pyramid approach with a focus on fast, reliable unit tests complemented by integration and performance tests. We maintain high test coverage while ensuring tests are maintainable and provide meaningful feedback.

### Testing Philosophy

- **Fast Feedback**: Unit tests run in milliseconds for immediate developer feedback
- **Comprehensive Coverage**: >85% code coverage with meaningful assertions
- **Test Pyramid**: More unit tests, fewer integration tests, minimal end-to-end tests
- **Reliability**: Tests are deterministic and don't rely on external services
- **Documentation**: Tests serve as living documentation for expected behavior

## Current Test Coverage

**Test Results** (Last Updated: 2025-07-16):
- ✅ **321 tests passed**
- ⏭️ **1 test skipped** 
- ❌ **0 tests failed**
- **Total execution time:** 8.06 seconds

**Coverage Metrics**:
- **Overall Coverage**: 59.48% (exceeds minimum 10% requirement)
- **Target Coverage**: Working toward 85% overall coverage  
- **New Code Coverage**: >85% (enforced on PRs)
- **Critical Components**: >90% (config, models, translators)

**Coverage by Module** (Current):
- Configuration: 97.7%
- Models & Validation: 98.9%
- Translation Layer: 88.0%
- API Routers: 51.1% - 58.5% (varies by module)
- Utilities: 59.6% - 97.2% (varies by module)
- Request Body Utility: 97.2% (new in v2.1)

## Running Tests

### Quick Start

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term-missing
```

### Test Categories

#### Unit Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific module tests
pytest tests/unit/test_config.py -v
pytest tests/unit/routers/ -v
pytest tests/unit/translators/ -v
```

#### Integration Tests  
```bash
# Run integration tests (requires Docker)
pytest tests/test_docker.py -v

# Run with real backend (optional)
OPENAI_API_BASE_URL=https://api.openai.com/v1 \
OPENAI_API_KEY=your-key \
pytest tests/unit/test_main.py::TestIntegration -v
```

#### Performance Tests
```bash
# Run performance tests
pytest tests/performance/ -v

# Run with detailed metrics
pytest tests/performance/ -v -s --tb=short
```

### Coverage Analysis

#### Generate Coverage Reports
```bash
# HTML report (opens in browser)
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=src --cov-report=term-missing

# XML report (for CI)
pytest --cov=src --cov-report=xml
```

#### Coverage Configuration
```bash
# Check coverage config in pytest.ini
cat pytest.ini
```

## Test Structure

### Directory Organization

```
tests/
├── __init__.py
├── unit/                           # Unit tests (fast, isolated)
│   ├── __init__.py
│   ├── test_config.py             # Configuration management
│   ├── test_models.py             # Pydantic model validation
│   ├── test_main.py               # FastAPI application
│   ├── test_model_mapping.py      # Model name mapping
│   ├── test_exceptions.py         # Custom exceptions
│   ├── test_logging.py            # Logging functionality
│   ├── routers/                   # API endpoint tests
│   │   ├── test_chat.py          # Chat completion endpoints
│   │   ├── test_models.py        # Model management endpoints
│   │   └── test_embeddings.py    # Embeddings endpoints
│   ├── translators/               # Translation logic tests
│   │   ├── test_base.py          # Base translator functionality
│   │   └── test_chat.py          # Chat translation logic
│   └── utils/                     # Utility function tests
│       ├── test_http_client.py   # HTTP client functionality
│       └── test_http_client_streaming.py  # Streaming support
├── performance/                    # Performance and load tests
│   └── test_metrics_performance.py # Metrics system performance
└── test_docker.py                 # Docker integration tests
```

### Test Categories by Type

#### Unit Tests (300+ tests)

| Module | Test File | Tests | Coverage | Description |
|--------|-----------|-------|----------|-------------|
| **Configuration** | `test_config.py` | 15 | 97.7% | Environment validation, settings loading |
| **Models** | `test_models.py` | 62 | 98.9% | Pydantic model validation, serialization |
| **Main App** | `test_main.py` | 20 | 100% | FastAPI application, middleware, lifecycle |
| **Model Mapping** | `test_model_mapping.py` | 12 | 98.9% | Custom model name translation |
| **Exceptions** | `test_exceptions.py` | 8 | 100% | Custom exception hierarchy |
| **Logging** | `test_logging.py` | 18 | 91.8% | Structured logging, request tracking |
| **Request Body Utility** | `utils/test_request_body.py` | 15 | 97.2% | Request body caching, dual API support |

##### Router Tests (85+ tests)
| Router | Test File | Tests | Coverage | Description |
|--------|-----------|-------|----------|-------------|
| **Chat** | `routers/test_chat.py` | 35 | 51.1% | Chat completions, streaming, error handling, dual API |
| **Models** | `routers/test_models.py` | 25 | 95.6% | Model listing, show, version endpoints |
| **Embeddings** | `routers/test_embeddings.py` | 25 | 58.5% | Text embeddings, validation, errors, dual API |

##### Translator Tests (45+ tests)
| Translator | Test File | Tests | Coverage | Description |
|------------|-----------|-------|----------|-------------|
| **Base** | `translators/test_base.py` | 20 | 98.9% | Abstract base class, common functionality |
| **Chat** | `translators/test_chat.py` | 25 | 88.0% | Chat translation, streaming, options mapping |

##### Utility Tests (85+ tests)
| Utility | Test File | Tests | Coverage | Description |
|---------|-----------|-------|----------|-------------|
| **HTTP Client** | `utils/test_http_client.py` | 60 | 89.3% | Request handling, retry logic, timeouts |
| **Streaming** | `utils/test_http_client_streaming.py` | 25 | 89.3% | Streaming responses, chunked transfer |

#### Integration Tests (15+ tests)

| Test Suite | Test File | Tests | Coverage | Description |
|------------|-----------|-------|----------|-------------|
| **Docker Integration** | `test_docker.py` | 8 | N/A | Container functionality, health checks |
| **End-to-End API** | `test_main.py` (integration) | 7 | 100% | Full request/response cycle testing |

#### Performance Tests (5+ tests)

| Test Type | Test File | Tests | Coverage | Description |
|-----------|-----------|-------|----------|-------------|
| **Metrics Performance** | `performance/test_metrics_performance.py` | 4 | 59.6% | Monitoring overhead validation |
| **Load Testing** | Built-in load testing framework | 1 | N/A | High-load scenario validation |

## Testing Strategy

### 1. Unit Testing

**Approach**: Test individual components in isolation with mocked dependencies.

**Key Principles**:
- Fast execution (< 1ms per test)
- No external dependencies
- Clear arrange-act-assert structure
- Comprehensive edge case coverage

**Example Test Structure**:
```python
def test_chat_translation_success():
    """Test successful chat message translation."""
    # Arrange
    translator = ChatTranslator()
    request = OpenAIChatRequest(...)
    
    # Act
    result = translator.translate_request(request)
    
    # Assert
    assert result.model == "expected-model"
    assert len(result.messages) == 1
```

### 2. Integration Testing

**Approach**: Test component interactions and API contracts.

**Key Areas**:
- FastAPI routing and middleware
- Request/response serialization
- Error handling across layers
- Container deployment validation

**Mock Strategy**:
- Mock external HTTP calls
- Use test databases/fixtures
- Simulate various response conditions

### 3. Performance Testing

**Approach**: Validate system performance under various load conditions.

**Test Scenarios**:
- Metrics collection overhead
- Concurrent request handling
- Memory usage under load
- Streaming response performance

**Thresholds**:
- Simple tracking: < 10% overhead
- Concurrent tracking: < 50% overhead
- Memory usage: < 10MB for tests
- Response time: < 100ms average

### 4. Security Testing

**Approach**: Validate input validation and error handling security.

**Key Areas**:
- Input sanitization
- Authentication flow
- Error message safety
- Resource exhaustion protection

## Continuous Integration

### Automated Testing

All tests run automatically on:

#### Pull Requests
- Full unit test suite
- Integration tests
- Performance regression tests
- Coverage analysis and reporting

#### Main Branch Commits
- Complete test suite
- Docker build validation
- Security scanning
- Performance benchmarking

#### Scheduled Runs
- Nightly comprehensive testing
- Dependency vulnerability scans
- Long-running performance tests
- Integration with external services

### CI Pipeline Configuration

```yaml
# .github/workflows/ci.yml (excerpt)
- name: Run Unit Tests
  run: pytest tests/unit/ -v --cov=src

- name: Run Integration Tests  
  run: pytest tests/test_docker.py -v

- name: Run Performance Tests
  run: pytest tests/performance/ -v

- name: Generate Coverage Report
  run: pytest --cov=src --cov-report=xml --cov-report=html
```

### Quality Gates

- **Coverage Threshold**: Minimum 10% overall coverage (currently 65.40%)
- **Target Coverage**: Working toward 85% overall coverage
- **Performance Regression**: No degradation >10% from baseline
- **Security Scans**: No high/critical vulnerabilities
- **Test Success Rate**: 100% test pass rate required (currently achieved)

## Test Data and Fixtures

### Mock Data Strategy

```python
# Example fixture setup
@pytest.fixture
def sample_chat_request():
    """Sample OpenAI chat request for testing."""
    return OpenAIChatRequest(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Hello"}
        ]
    )

@pytest.fixture
def mock_backend_response():
    """Mock successful backend response."""
    return {
        "choices": [{"message": {"content": "Hi there!"}}],
        "usage": {"total_tokens": 10}
    }
```

### Test Environment Setup

```bash
# Environment variables for testing
export OPENAI_API_BASE_URL="http://mock-server:8000"
export OPENAI_API_KEY="test-key"
export LOG_LEVEL="DEBUG"
export TESTING="true"
```

## Debugging and Troubleshooting

### Common Issues

#### Test Failures
```bash
# Run with detailed output
pytest -vvv --tb=long

# Run specific failing test
pytest tests/unit/test_config.py::test_specific_function -vvv

# Run with pdb debugging
pytest --pdb tests/unit/test_config.py::test_specific_function
```

#### Coverage Issues
```bash
# Identify uncovered lines
pytest --cov=src --cov-report=term-missing

# Generate detailed HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

#### Performance Test Issues
```bash
# Run with detailed metrics
pytest tests/performance/ -v -s

# Check system resources during tests
htop # In separate terminal
```

### Test Development Guidelines

#### Writing New Tests

1. **Follow Naming Conventions**:
   ```python
   def test_function_name_expected_behavior():
   def test_function_name_edge_case():
   def test_function_name_error_condition():
   ```

2. **Use Descriptive Docstrings**:
   ```python
   def test_chat_translation_invalid_model():
       """Test that invalid model names raise ValidationError."""
   ```

3. **Arrange-Act-Assert Structure**:
   ```python
   def test_example():
       # Arrange: Set up test data
       input_data = create_test_data()
       
       # Act: Execute the function under test
       result = function_under_test(input_data)
       
       # Assert: Verify expected behavior
       assert result.status == "success"
   ```

4. **Test Edge Cases**:
   - Empty inputs
   - Maximum/minimum values
   - Invalid data types
   - Network timeouts
   - Resource exhaustion

#### Mocking Best Practices

```python
# Mock external dependencies
@patch('src.utils.http_client.httpx.AsyncClient')
async def test_backend_request(mock_client):
    """Test HTTP client request handling."""
    # Configure mock
    mock_client.return_value.post.return_value.json.return_value = {...}
    
    # Test implementation
    result = await make_request(...)
    
    # Verify mock interactions
    mock_client.return_value.post.assert_called_once()
```

## Testing Tools and Dependencies

### Core Testing Framework
- **pytest**: Primary testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities

### Assertion Libraries
- **pytest**: Built-in assertions
- **assertpy**: Fluent assertions (optional)

### Mock and Fixture Tools
- **unittest.mock**: Python standard mocking
- **httpx-mock**: HTTP request mocking
- **pytest-factoryboy**: Test data factories

### Performance Testing
- **time**: Basic timing measurements
- **psutil**: System resource monitoring
- **memory_profiler**: Memory usage analysis

### Coverage Tools
- **coverage.py**: Code coverage measurement
- **codecov**: Coverage reporting service
- **coverage-badge**: Coverage badge generation

## Contributing to Tests

### Adding New Tests

1. **Identify Test Requirements**:
   - What functionality needs testing?
   - What edge cases should be covered?
   - What performance characteristics matter?

2. **Choose Test Category**:
   - Unit test for isolated functionality
   - Integration test for component interactions
   - Performance test for resource usage

3. **Follow Project Conventions**:
   - Use existing fixture patterns
   - Follow naming conventions
   - Maintain coverage standards

4. **Validate Test Quality**:
   - Tests should be fast and reliable
   - Clear failure messages
   - No flaky behavior

### Test Review Checklist

- [ ] **Clear Purpose**: Test has clear, single responsibility
- [ ] **Good Coverage**: Tests cover happy path and edge cases
- [ ] **Fast Execution**: Unit tests complete quickly
- [ ] **Reliable**: Tests don't depend on timing or external factors
- [ ] **Maintainable**: Tests are easy to understand and modify
- [ ] **Proper Mocking**: External dependencies appropriately mocked

## Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

### Testing Best Practices
- [Test-Driven Development](https://martinfowler.com/articles/practical-test-pyramid.html)
- [Python Testing 101](https://realpython.com/python-testing/)
- [API Testing Strategies](https://www.postman.com/api-testing/)

## Recent Test Improvements

### Fixed Tests (2025-07-16)

**Dual API Support Testing**: Complete test suite update for v2.1 dual API format support
- **Issue**: Tests failing due to function signature changes in dual API refactoring
- **Solution**: Updated all router tests for new function signatures and imports
- **Components Updated**: 
  - Chat router tests: Updated function calls and imports
  - Embeddings router tests: Updated function names and imports  
  - Created comprehensive request body utility tests
- **Location**: `tests/unit/routers/`, `tests/unit/utils/test_request_body.py`

**Request Body Utility Testing**: Added comprehensive test coverage for new request body handling
- **Purpose**: Test the new request body caching system for dual API support
- **Coverage**: 97.2% with 15 test cases covering all scenarios
- **Location**: `tests/unit/utils/test_request_body.py`

### Current Test Status
- ✅ All 321 tests passing
- ✅ 59.48% code coverage (exceeds minimum requirement)
- ✅ Zero failing tests
- ✅ Performance tests validated
- ✅ Docker integration tests working
- ✅ Dual API format support fully tested

---

**Last Updated**: 2025-07-16  
**Maintainer**: Development Team

For questions about testing or to contribute improvements to our test suite, please see our [Contributing Guidelines](../CONTRIBUTING.md) or open an issue.