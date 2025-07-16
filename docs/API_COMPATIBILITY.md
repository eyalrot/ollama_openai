# API Compatibility Matrix

This document provides a detailed mapping between Ollama API endpoints and their OpenAI equivalents, including support status, parameter differences, and usage examples.

## Overview

The Ollama to OpenAI proxy supports **dual API formats** simultaneously:
- **Ollama API**: Used by the Ollama Python/JS SDKs (`/api/*` endpoints)
- **OpenAI API**: Used by OpenAI clients and compatible libraries (`/v1/*` endpoints)

**New in v2.1**: The proxy now supports both formats simultaneously! You can use either Ollama clients OR OpenAI clients against the same proxy instance, with automatic format detection based on the URL path.

## Endpoint Compatibility Matrix

### ✅ Dual API Format Support

The proxy now supports both Ollama and OpenAI endpoints simultaneously:

| Ollama Endpoint | OpenAI Endpoint | Method | Status | Notes |
|-----------------|-----------------|---------|---------|--------|
| `/api/generate` | `/v1/chat/completions` | POST | ✅ Full Support | Text generation with streaming |
| `/api/chat` | `/v1/chat/completions` | POST | ✅ Full Support | Chat with message history |
| `/api/tags` | `/v1/models` | GET | ✅ Full Support | List available models |
| `/api/embeddings` | `/v1/embeddings` | POST | ✅ Full Support | Generate embeddings |

**Usage**: Choose the endpoint style that matches your client:
- Use `/api/*` endpoints with Ollama clients
- Use `/v1/*` endpoints with OpenAI clients  
- Both route to the same backend with format translation

### ℹ️ Informational Endpoints

| Endpoint | Method | Status | Response |
|----------|---------|---------|----------|
| `/api/version` | GET | ✅ Mocked | Returns proxy version info |
| `/health` | GET | ✅ Implemented | Health check endpoint |
| `/ready` | GET | ✅ Implemented | Readiness check endpoint |
| `/` | GET | ✅ Implemented | Service information |

### ❌ Unsupported Endpoints

| Ollama Endpoint | Method | Status | Reason |
|-----------------|---------|---------|---------|
| `/api/pull` | POST | ❌ Returns 501 | Model management not applicable |
| `/api/push` | POST | ❌ Returns 501 | Model management not applicable |
| `/api/delete` | DELETE | ❌ Returns 501 | Model management not applicable |
| `/api/copy` | POST | ❌ Returns 501 | Model management not applicable |
| `/api/show` | POST | ❌ Returns 501 | Model info via `/api/tags` |

## Parameter Mapping

### Generate Endpoint (`/api/generate`)

#### Ollama Request Format
```json
{
  "model": "llama2",
  "prompt": "Why is the sky blue?",
  "stream": false,
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "num_predict": 100
  }
}
```

#### Translated to OpenAI Format
```json
{
  "model": "meta-llama/Llama-2-7b-chat-hf",
  "messages": [
    {"role": "user", "content": "Why is the sky blue?"}
  ],
  "stream": false,
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 100
}
```

#### Parameter Mappings
| Ollama Parameter | OpenAI Parameter | Notes |
|------------------|------------------|--------|
| `model` | `model` | Can be mapped via configuration |
| `prompt` | `messages[0].content` | Converted to user message |
| `stream` | `stream` | Direct mapping |
| `options.temperature` | `temperature` | Direct mapping |
| `options.top_p` | `top_p` | Direct mapping |
| `options.top_k` | N/A | Not supported by OpenAI |
| `options.num_predict` | `max_tokens` | Direct mapping |
| `options.stop` | `stop` | Direct mapping |
| `options.seed` | `seed` | Direct mapping |
| `context` | N/A | Handled internally |

### Chat Endpoint (`/api/chat`)

#### Ollama Request Format
```json
{
  "model": "llama2",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": true
}
```

#### Translated to OpenAI Format
```json
{
  "model": "meta-llama/Llama-2-7b-chat-hf",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Hello!"}
  ],
  "stream": true
}
```

#### Message Role Mapping
| Ollama Role | OpenAI Role | Notes |
|-------------|-------------|--------|
| `system` | `system` | Direct mapping |
| `user` | `user` | Direct mapping |
| `assistant` | `assistant` | Direct mapping |

### Models Endpoint (`/api/tags`)

#### Ollama Response Format
```json
{
  "models": [
    {
      "name": "llama2",
      "modified_at": "2024-01-01T00:00:00Z",
      "size": 3825819519,
      "digest": "sha256:abc123..."
    }
  ]
}
```

#### From OpenAI Format
```json
{
  "data": [
    {
      "id": "meta-llama/Llama-2-7b-chat-hf",
      "object": "model",
      "created": 1234567890,
      "owned_by": "meta"
    }
  ]
}
```

### Embeddings Endpoint (`/api/embeddings`)

#### Ollama Request Format
```json
{
  "model": "llama2",
  "prompt": "The quick brown fox"
}
```

#### Translated to OpenAI Format
```json
{
  "model": "meta-llama/Llama-2-7b-chat-hf",
  "input": "The quick brown fox"
}
```

## Response Format Differences

### Generate/Chat Response

#### Ollama Streaming Format
```json
{"response": "The", "done": false}
{"response": " sky", "done": false}
{"response": " is", "done": false}
{"response": "", "done": true, "total_duration": 1234567890}
```

#### OpenAI Streaming Format
```
data: {"choices": [{"delta": {"content": "The"}, "index": 0}]}
data: {"choices": [{"delta": {"content": " sky"}, "index": 0}]}
data: {"choices": [{"delta": {"content": " is"}, "index": 0}]}
data: [DONE]
```

### Non-Streaming Response

#### Ollama Format
```json
{
  "response": "The sky is blue because...",
  "done": true,
  "context": [1, 2, 3],
  "total_duration": 1234567890,
  "prompt_eval_count": 10,
  "eval_count": 50
}
```

#### From OpenAI Format
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "The sky is blue because..."
    },
    "finish_reason": "stop",
    "index": 0
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

## Feature Support Matrix

| Feature | Ollama API | OpenAI API | Proxy Support |
|---------|------------|------------|---------------|
| Text Generation | ✅ | ✅ | ✅ Fully Supported |
| Chat Completion | ✅ | ✅ | ✅ Fully Supported |
| Streaming | ✅ | ✅ | ✅ Fully Supported |
| Embeddings | ✅ | ✅ | ✅ Fully Supported |
| Model Listing | ✅ | ✅ | ✅ Fully Supported |
| Temperature Control | ✅ | ✅ | ✅ Fully Supported |
| Max Tokens | ✅ | ✅ | ✅ Fully Supported |
| Stop Sequences | ✅ | ✅ | ✅ Fully Supported |
| System Messages | ✅ | ✅ | ✅ Fully Supported |
| Tool/Function Calling | ✅ | ✅ | ❌ Phase 2 |
| Image Input | ✅ | ✅ | ❌ Phase 2 |
| JSON Mode | ✅ | ✅ | ⚠️ Partial (via prompting) |
| Context Preservation | ✅ | ❌ | ⚠️ Limited Support |

## Usage Examples

### Basic Generation

**Ollama-style request:**
```bash
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Explain quantum computing",
    "stream": false
  }'
```

**OpenAI-style request (same backend):**
```bash
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "model": "llama2",
    "messages": [{"role": "user", "content": "Explain quantum computing"}],
    "stream": false
  }'
```

### Chat with History

**Using Ollama client:**
```python
from ollama import Client

client = Client(host='http://localhost:11434')

response = client.chat(
    model='llama2',
    messages=[
        {'role': 'system', 'content': 'You are a physics teacher'},
        {'role': 'user', 'content': 'What is quantum entanglement?'}
    ]
)
```

**Using OpenAI client (same backend):**
```python
import openai

openai.api_base = "http://localhost:11434/v1"
openai.api_key = "your-api-key"

response = openai.ChatCompletion.create(
    model="llama2",
    messages=[
        {"role": "system", "content": "You are a physics teacher"},
        {"role": "user", "content": "What is quantum entanglement?"}
    ]
)
```

### Streaming Response

```javascript
// Using Ollama JS SDK
import { Ollama } from 'ollama'

const ollama = new Ollama({ host: 'http://localhost:11434' })

const stream = await ollama.generate({
  model: 'llama2',
  prompt: 'Write a haiku about programming',
  stream: true
})

for await (const chunk of stream) {
  process.stdout.write(chunk.response)
}
```

### Embeddings

**Using Ollama client:**
```python
response = client.embeddings(
    model='llama2',
    prompt='Machine learning is fascinating'
)
embedding_vector = response['embedding']
```

**Using OpenAI client (same backend):**
```python
response = openai.Embedding.create(
    model="llama2",
    input="Machine learning is fascinating"
)
embedding_vector = response['data'][0]['embedding']
```

## Model Name Resolution

The proxy resolves model names in the following order:

1. **Exact Match**: If the model exists on the backend as-is
2. **Mapped Name**: If defined in model mapping configuration
3. **Default Model**: If configured and no match found
4. **Pass-through**: Send the original name and let backend handle

Example mapping configuration:
```json
{
  "model_mappings": {
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
    "llama2:13b": "meta-llama/Llama-2-13b-chat-hf",
    "codellama": "codellama/CodeLlama-7b-Instruct-hf"
  },
  "default_model": "gpt-3.5-turbo"
}
```

## Error Handling

### API Error Mapping

| Ollama Error | HTTP Status | OpenAI Equivalent |
|--------------|-------------|-------------------|
| Model not found | 404 | Model not found |
| Invalid request | 400 | Invalid request format |
| Context too long | 413 | Context length exceeded |
| Server error | 500 | Internal server error |
| Timeout | 504 | Gateway timeout |

### Error Response Format

Both APIs return errors in JSON format:

```json
{
  "error": {
    "message": "Model 'unknown-model' not found",
    "type": "model_not_found",
    "code": "MODEL_NOT_FOUND"
  }
}
```

## Limitations and Differences

### Current Limitations (Phase 1)

1. **No Tool/Function Support**: Function calling is not yet translated
2. **No Image Support**: Multi-modal inputs are not supported
3. **Context Handling**: Ollama's context arrays are not preserved
4. **Model Management**: Pull/push/delete operations are not applicable

### Behavioral Differences

1. **Token Counting**: May differ between Ollama and OpenAI tokenizers
2. **Stop Sequences**: Handling may vary by backend
3. **Sampling Parameters**: Some Ollama parameters (like `top_k`) have no OpenAI equivalent
4. **Response Timing**: Metrics like `total_duration` are approximated

## Version Compatibility

| Ollama SDK Version | Proxy Version | Status |
|--------------------|---------------|---------|
| 0.1.x | 1.0.x | ✅ Fully Compatible |
| 0.2.x | 1.0.x | ✅ Fully Compatible |
| 0.3.x | 1.0.x | ⚠️ Tool calls unsupported |

## Future Enhancements (Phase 2)

1. **Tool/Function Calling**: Translate between Ollama and OpenAI tool formats
2. **Image Support**: Handle multi-modal inputs
3. **Advanced Parameters**: Support model-specific parameters
4. **Batch Processing**: Support batch inference endpoints
5. **Model Information**: Enhanced `/api/show` endpoint mapping

---

For implementation details, see:
- [Architecture Overview](ARCHITECTURE.md)
- [Translation Logic](../src/translators/README.md)
- [Testing Guide](TESTING.md)