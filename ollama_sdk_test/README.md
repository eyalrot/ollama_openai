# Ollama SDK Compatibility Test Suite

This test suite verifies compatibility between the Ollama Python SDK and the Ollama-to-OpenAI proxy server.

## Overview

The test suite ensures that applications using the Ollama SDK can seamlessly work with the proxy server, which translates Ollama API calls to OpenAI-compatible backends.

## Installation

1. Install test dependencies:
```bash
cd ollama_sdk_test
pip install -r requirements.txt
```

Or use the test runner:
```bash
python run_tests.py --install
```

## Running Tests

### Quick Start

Run all tests:
```bash
python run_tests.py
```

### Specific Test Categories

Run only embedding tests:
```bash
python run_tests.py test_embeddings.py
```

Run only basic connectivity tests:
```bash
python run_tests.py test_basic_operations.py
```

### Test Options

- **Verbose output**: `python run_tests.py -v`
- **Stop on first failure**: `python run_tests.py -x`
- **With coverage report**: `python run_tests.py --coverage`
- **Skip proxy check**: `python run_tests.py --no-check`

## Test Structure

### Core Test Files

1. **test_basic_operations.py**
   - Client initialization
   - Connection verification
   - Model listing
   - Error handling

2. **test_embeddings.py** (Comprehensive)
   - Single string embedding
   - Batch embeddings
   - Unicode and special characters
   - Long text handling
   - Model-specific dimensions
   - Performance benchmarks
   - Async operations
   - Error scenarios

### Configuration

Edit `config.py` to customize:
- Proxy host URL
- Test models
- Timeout values
- Test data

### Environment Variables

Create a `.env` file for configuration:
```env
PROXY_HOST=http://localhost:11434
LOG_LEVEL=INFO
```

## Embedding Tests

The embedding test suite includes:

### Basic Tests
- Single string embedding with `embed()`
- Deprecated `embeddings()` method compatibility
- Dimension verification for known models

### Batch Processing
- Multiple strings in single request
- Large batches (100+ items)
- Empty batch handling

### Input Validation
- String vs list[string] inputs
- Unicode and emoji support
- Very long text (>8k tokens)

### Parameters
- `truncate` option for long inputs
- `keep_alive` parameter
- Custom options pass-through

### Error Handling
- Invalid model names
- Empty/null inputs
- Malformed requests

### Performance
- Response time benchmarking
- Batch vs individual efficiency
- Concurrent request handling

### Semantic Tests
- Similar text similarity scores
- Different text distinction
- Deterministic output verification

## Expected Behavior

### Successful Tests
- ✓ Client connects to proxy
- ✓ Models are listed correctly
- ✓ Embeddings match expected dimensions
- ✓ Batch processing is efficient
- ✓ Unicode text is handled properly

### Common Issues
- Connection refused: Ensure proxy is running
- Model not found: Check model name mapping
- Dimension mismatch: Verify model configuration
- Timeout errors: Increase timeout in config

## Adding New Tests

1. Create new test file: `test_feature.py`
2. Import utilities from `utils.test_helpers`
3. Use `create_test_client()` for client setup
4. Follow existing test patterns

Example:
```python
from utils.test_helpers import create_test_client, validate_embedding_response

def test_new_feature():
    client = create_test_client()
    response = client.embed(model="text-embedding-ada-002", input="test")
    validate_embedding_response(response)
```

## Debugging

Enable debug logging:
```bash
LOG_LEVEL=DEBUG python run_tests.py -v
```

Run single test function:
```bash
pytest test_embeddings.py::TestEmbeddings::test_embed_single_string -v
```

## CI/CD Integration

Run in CI pipeline:
```bash
# Install and run with coverage
python run_tests.py --install --coverage --failfast
```

## Test Markers

Use pytest markers for test categorization:
```bash
# Skip slow tests
python run_tests.py -m "not slow"

# Run only async tests  
python run_tests.py -m "asyncio"
```

## Contributing

When adding tests:
1. Follow existing naming conventions
2. Add docstrings explaining test purpose
3. Use appropriate assertions with messages
4. Log important information for debugging
5. Handle both success and error cases

## Troubleshooting

### Proxy Connection Issues
```bash
# Check if proxy is running
curl http://localhost:11434/

# Verify with direct API call
curl http://localhost:11434/api/tags
```

### Model Availability
```bash
# List available models
curl http://localhost:11434/api/tags | jq
```

### Test Failures
1. Check proxy logs for errors
2. Verify model name mapping in proxy config
3. Ensure API keys are configured if needed
4. Check network connectivity

## License

Same as parent project (MIT)