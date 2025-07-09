# Ollama OpenAI Proxy Examples

This directory contains example scripts and configuration files to help you get started with the Ollama to OpenAI proxy.

## Directory Structure

```
examples/
├── python/                 # Python client examples
│   ├── basic_generation.py      # Simple text generation
│   ├── streaming_chat.py        # Interactive chat with streaming
│   ├── batch_processing.py      # Concurrent batch processing
│   └── langchain_integration.py # LangChain framework integration
├── javascript/            # JavaScript/Node.js examples  
│   ├── basic_usage.js          # Basic SDK usage
│   └── interactive_chat.js     # Interactive chat interface
└── config/               # Configuration templates
    ├── model_mapping.json      # Model name mappings
    ├── openrouter_models.json  # OpenRouter-specific mappings
    ├── .env.development        # Development environment
    ├── .env.production         # Production environment
    ├── .env.openrouter         # OpenRouter configuration
    ├── docker-compose.override.yml  # Docker overrides
    └── nginx.conf              # Nginx reverse proxy setup
```

## Python Examples

### Prerequisites

```bash
# Basic examples
pip install ollama

# For async batch processing
pip install aiohttp

# For LangChain example
pip install langchain langchain-community
```

### Running Python Examples

```bash
# Basic generation
python examples/python/basic_generation.py

# Interactive streaming chat
python examples/python/streaming_chat.py

# Batch processing with concurrency
python examples/python/batch_processing.py

# LangChain integration
python examples/python/langchain_integration.py
```

## JavaScript Examples

### Prerequisites

```bash
# Install dependencies
npm install ollama readline

# Or using yarn
yarn add ollama readline
```

### Running JavaScript Examples

```bash
# Basic usage examples
node examples/javascript/basic_usage.js

# Interactive chat interface
node examples/javascript/interactive_chat.js
```

## Configuration Examples

### Model Mapping

The `model_mapping.json` file shows how to map Ollama model names to OpenAI-compatible model names:

```json
{
  "model_mappings": {
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
    "codellama": "codellama/CodeLlama-7b-Instruct-hf"
  }
}
```

### Environment Configurations

Different `.env` templates for various scenarios:

- `.env.development` - Local development with debug settings
- `.env.production` - Production-ready configuration
- `.env.openrouter` - Settings for OpenRouter integration

### Docker Override

Use `docker-compose.override.yml` to customize the Docker deployment:

```bash
# Copy to project root
cp examples/config/docker-compose.override.yml .

# Start with overrides
docker-compose up -d
```

### Nginx Reverse Proxy

The `nginx.conf` example shows how to:
- Set up SSL termination
- Implement rate limiting
- Add security headers
- Configure for streaming responses

## Common Patterns

### Error Handling

All examples include proper error handling:

```python
try:
    response = client.generate(model='gpt-3.5-turbo', prompt='Hello')
except Exception as e:
    print(f"Error: {e}")
```

### Streaming Responses

Examples show how to handle streaming:

```python
stream = client.generate(model='gpt-3.5-turbo', prompt='Tell a story', stream=True)
for chunk in stream:
    print(chunk['response'], end='', flush=True)
```

### Model Mapping

Using mapped model names:

```python
# With mapping: "llama2" -> "meta-llama/Llama-2-7b-chat-hf"
response = client.generate(model='llama2', prompt='Hello')
```

## Tips and Best Practices

1. **Start Simple**: Begin with `basic_generation.py` or `basic_usage.js`
2. **Check Connection**: Ensure the proxy is running at `http://localhost:11434`
3. **Use Free Models**: Test with OpenRouter's free models first
4. **Enable Debug Logs**: Set `LOG_LEVEL=DEBUG` when troubleshooting
5. **Handle Timeouts**: Increase `REQUEST_TIMEOUT` for large models

## Troubleshooting Examples

If examples aren't working:

1. **Verify proxy is running**:
   ```bash
   curl http://localhost:11434/health
   ```

2. **Check available models**:
   ```bash
   curl http://localhost:11434/api/tags
   ```

3. **Test with curl**:
   ```bash
   curl -X POST http://localhost:11434/api/generate \
     -d '{"model": "gpt-3.5-turbo", "prompt": "Test"}'
   ```

## Contributing Examples

We welcome new examples! Please:

1. Follow the existing structure
2. Include error handling
3. Add helpful comments
4. Test with multiple backends
5. Update this README

## Additional Resources

- [Main Documentation](../README.md)
- [API Compatibility](../docs/API_COMPATIBILITY.md)
- [Configuration Guide](../docs/CONFIGURATION.md)
- [Troubleshooting](../docs/TROUBLESHOOTING.md)