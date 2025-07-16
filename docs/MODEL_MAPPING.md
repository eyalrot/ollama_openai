# Model Name Mapping

The Ollama-OpenAI proxy supports configurable model name mapping, allowing you to translate Ollama model names to their OpenAI/VLLM equivalents.

**New in v2.1**: Enhanced provider compatibility with support for OpenAI, vLLM, LiteLLM, OpenRouter, Ollama, and any OpenAI-compatible API provider.

## Overview

When Ollama clients request models like `llama2` or `mistral`, the proxy can automatically map these to their full provider-specific model identifiers like `meta-llama/Llama-2-7b-chat-hf` or `mistralai/Mistral-7B-Instruct-v0.1`. The same mapping works for OpenAI format clients using the `/v1/*` endpoints.

## Provider Compatibility

The proxy supports model name mapping for all OpenAI-compatible providers:

### Supported Providers
- **OpenAI**: Direct model names (`gpt-3.5-turbo`, `gpt-4`, etc.)
- **vLLM**: Hugging Face model identifiers (`meta-llama/Llama-2-7b-chat-hf`)
- **LiteLLM**: Model routing format (`openai/gpt-3.5-turbo`, `anthropic/claude-3-sonnet`)
- **OpenRouter**: Provider-specific names (`google/gemma-2-9b-it:free`, `anthropic/claude-3-sonnet`)
- **Ollama**: Local model names (`llama2`, `mistral`, `codellama`)
- **Custom APIs**: Any OpenAI-compatible model names

### Model Mapping Examples

| Ollama Model | OpenAI | vLLM | LiteLLM | OpenRouter |
|--------------|--------|------|---------|------------|
| `llama2` | `gpt-3.5-turbo` | `meta-llama/Llama-2-7b-chat-hf` | `ollama/llama2` | `meta-llama/llama-2-7b-chat` |
| `codellama` | `gpt-4` | `codellama/CodeLlama-7b-Instruct-hf` | `ollama/codellama` | `codellama/codellama-7b-instruct` |
| `mistral` | `gpt-3.5-turbo` | `mistralai/Mistral-7B-Instruct-v0.1` | `mistral/mistral-7b-instruct` | `mistralai/mistral-7b-instruct` |
| `gemma` | `gpt-3.5-turbo` | `google/gemma-7b-it` | `google/gemma-7b-it` | `google/gemma-2-9b-it:free` |

### Embedding Models

The proxy also supports mapping embedding model names for both `/api/embeddings` and `/v1/embeddings` endpoints:

| Ollama Embedding Model | OpenAI | vLLM | LiteLLM | OpenRouter |
|------------------------|--------|------|---------|------------|
| `mxbai-embed-large` | `text-embedding-ada-002` | `sentence-transformers/all-MiniLM-L6-v2` | `openai/text-embedding-ada-002` | `openai/text-embedding-ada-002` |
| `nomic-embed-text` | `text-embedding-ada-002` | `nomic-ai/nomic-embed-text-v1` | `nomic-ai/nomic-embed-text-v1` | `nomic-ai/nomic-embed-text-v1` |
| `all-minilm` | `text-embedding-ada-002` | `sentence-transformers/all-MiniLM-L6-v2` | `huggingface/all-MiniLM-L6-v2` | `huggingface/all-MiniLM-L6-v2` |
| `bge-large` | `text-embedding-3-large` | `BAAI/bge-large-en-v1.5` | `huggingface/bge-large-en-v1.5` | `huggingface/bge-large-en-v1.5` |
| `bge-small` | `text-embedding-3-small` | `BAAI/bge-small-en-v1.5` | `huggingface/bge-small-en-v1.5` | `huggingface/bge-small-en-v1.5` |

**Note**: Your OpenAI-compatible backend must support the embedding models you map to.

## Custom Mapping Configuration

### 1. Create a Mapping File

Create a JSON file with your custom model mappings:

```json
{
  "my-custom-model": "organization/my-custom-model-v1",
  "llama2": "my-org/custom-llama2-finetune",
  "local-model": "/path/to/local/model"
}
```

See `config/model_map.example.json` for a complete example.

### 2. Configure the Proxy

Set the `MODEL_MAPPING_FILE` environment variable to point to your mapping file:

```bash
# Using environment variable
export MODEL_MAPPING_FILE=/path/to/model_map.json
python -m src.main

# Using .env file
echo "MODEL_MAPPING_FILE=/path/to/model_map.json" >> .env
python -m src.main

# Using Docker
docker run -e MODEL_MAPPING_FILE=/app/config/model_map.json \
  -v /path/to/model_map.json:/app/config/model_map.json:ro \
  ollama-proxy
```

### 3. Docker Compose Configuration

```yaml
services:
  ollama-proxy:
    image: ollama-proxy
    environment:
      - MODEL_MAPPING_FILE=/app/config/model_map.json
    volumes:
      - ./config/model_map.json:/app/config/model_map.json:ro
```

## Mapping Behavior

1. **Custom mappings override defaults**: If your mapping file contains a key that exists in the default mappings, your value will be used.

2. **Unmapped models pass through**: If a model name is not found in the mappings, it will be passed through unchanged to the OpenAI/VLLM backend.

3. **Reverse mapping for responses**: The proxy automatically handles reverse mapping when returning responses to maintain consistency.

## Example Use Cases

### 1. Organization-Specific Models

Map simple names to your organization's fine-tuned models:

```json
{
  "chatbot": "myorg/customer-service-llama-7b-v2",
  "coder": "myorg/code-assistant-codellama-13b",
  "analyzer": "myorg/data-analyzer-mistral-7b"
}
```

### 2. Version Management

Map generic names to specific model versions:

```json
{
  "llama-latest": "meta-llama/Llama-2-70b-chat-hf",
  "llama-stable": "meta-llama/Llama-2-13b-chat-hf",
  "llama-fast": "meta-llama/Llama-2-7b-chat-hf"
}
```

### 3. Local Model Paths

Map to local model paths for VLLM:

```json
{
  "local-llama": "/models/llama2-7b-custom",
  "local-mistral": "/models/mistral-7b-finetuned"
}
```

## Validation

The proxy validates mapping files on startup:

- File must be valid JSON
- All mappings must be string-to-string
- File must exist and be readable

If validation fails, the proxy will exit with an error message.

## Monitoring

Model mappings are logged at startup:

```
INFO: Loaded 15 model mappings from /app/config/model_map.json
```

When debug logging is enabled, individual mappings are logged:

```
DEBUG: Mapped model 'llama2' to 'meta-llama/Llama-2-7b-chat-hf'
```

## Best Practices

1. **Use descriptive names**: Choose Ollama model names that are meaningful to your users.

2. **Document your mappings**: Include comments in your mapping file (JSON allows fields starting with `_`):

```json
{
  "_comment": "Production model mappings for ACME Corp",
  "_updated": "2024-01-15",
  "chat": "acme/production-chat-model-v3",
  "code": "acme/production-code-model-v2"
}
```

3. **Version your mapping files**: Keep mapping files in version control to track changes.

4. **Test mappings**: Use the health check endpoint to verify models are accessible:

```bash
curl http://localhost:11434/health
```

5. **Plan for updates**: Design your mapping strategy to handle model updates without breaking client applications.