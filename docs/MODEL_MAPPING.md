# Model Name Mapping

The Ollama-OpenAI proxy supports configurable model name mapping, allowing you to translate Ollama model names to their OpenAI/VLLM equivalents.

## Overview

When Ollama clients request models like `llama2` or `mistral`, the proxy can automatically map these to their full Hugging Face model identifiers like `meta-llama/Llama-2-7b-chat-hf` or `mistralai/Mistral-7B-Instruct-v0.1`.

## Default Mappings

The proxy includes the following default model mappings:

| Ollama Model | OpenAI/VLLM Model |
|--------------|-------------------|
| `llama2` | `meta-llama/Llama-2-7b-chat-hf` |
| `llama2:13b` | `meta-llama/Llama-2-13b-chat-hf` |
| `llama2:70b` | `meta-llama/Llama-2-70b-chat-hf` |
| `codellama` | `codellama/CodeLlama-7b-Instruct-hf` |
| `mistral` | `mistralai/Mistral-7B-Instruct-v0.1` |
| `mixtral` | `mistralai/Mixtral-8x7B-Instruct-v0.1` |
| `gemma` | `google/gemma-7b-it` |
| `phi` | `microsoft/phi-2` |

### Embedding Models

The proxy also supports mapping embedding model names for the `/embeddings` endpoint:

| Ollama Embedding Model | OpenAI/VLLM Embedding Model |
|------------------------|------------------------------|
| `mxbai-embed-large` | `text-embedding-ada-002` |
| `nomic-embed-text` | `text-embedding-ada-002` |
| `all-minilm` | `text-embedding-ada-002` |
| `bge-large` | `text-embedding-3-large` |
| `bge-small` | `text-embedding-3-small` |

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