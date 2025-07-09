# Quick Start Guide

Get the Ollama to OpenAI proxy running in under 5 minutes!

## Prerequisites

- Python 3.8+ OR Docker
- An OpenAI-compatible API endpoint (OpenAI, VLLM, OpenRouter, etc.)
- API key for your chosen provider

## Option 1: Docker (Fastest)

### 1. Clone and Configure

```bash
# Clone the repository
git clone https://github.com/eyalrot/ollama_openai.git
cd ollama_openai

# Create your configuration
cp .env.example .env
```

### 2. Edit `.env` file

```env
# Minimal configuration
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. Start the Proxy

```bash
docker-compose up -d
```

### 4. Verify It's Working

```bash
# Check health
curl http://localhost:11434/health

# List models
curl http://localhost:11434/api/tags

# Test generation
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "prompt": "Hello, world!"
  }'
```

## Option 2: Python (Development)

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/eyalrot/ollama_openai.git
cd ollama_openai

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

### 3. Run the Server

```bash
# Start on default Ollama port (11434)
python -m uvicorn src.main:app --host 0.0.0.0 --port 11434

# Or with auto-reload for development
python -m uvicorn src.main:app --host 0.0.0.0 --port 11434 --reload
```

## Quick Test with Python

```python
from ollama import Client

# Point to your proxy (instead of Ollama)
client = Client(host='http://localhost:11434')

# Use exactly as you would with Ollama
response = client.generate(
    model='gpt-3.5-turbo',  # Or your mapped model name
    prompt='Tell me a joke'
)
print(response['response'])
```

## Using with OpenRouter (Free Testing)

### 1. Get OpenRouter API Key

Visit [OpenRouter](https://openrouter.ai/) and sign up for a free API key.

### 2. Configure for OpenRouter

```env
OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
OPENAI_API_KEY=sk-or-v1-your-openrouter-key
```

### 3. Test with Free Models

```bash
# List available models
curl http://localhost:11434/api/tags

# Use a free model
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-2-9b-it:free",
    "prompt": "Explain quantum computing in simple terms"
  }'
```

## Common Use Cases

### Chat Completion

```bash
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "What is the capital of France?"}
    ]
  }'
```

### Streaming Response

```python
from ollama import Client

client = Client(host='http://localhost:11434')

# Stream the response
for chunk in client.generate(
    model='gpt-3.5-turbo',
    prompt='Write a short story',
    stream=True
):
    print(chunk['response'], end='', flush=True)
```

### With Model Mapping

Create `model_mapping.json`:
```json
{
  "model_mappings": {
    "llama2": "meta-llama/Llama-2-7b-chat-hf",
    "gpt4": "gpt-4-turbo-preview"
  }
}
```

Set in `.env`:
```env
MODEL_MAPPING_FILE=./model_mapping.json
```

Now use familiar names:
```python
response = client.generate(model='llama2', prompt='Hello!')
```

## Verification Checklist

✅ **Health Check**: `curl http://localhost:11434/health` returns `{"status":"healthy"}`

✅ **Model List**: `curl http://localhost:11434/api/tags` shows available models

✅ **Generation Works**: Test prompts return expected responses

✅ **Logs Clean**: Check `docker-compose logs` or console for errors

## Next Steps

- 📖 Read the full [Configuration Guide](CONFIGURATION.md)
- 🗺️ Set up [Model Mapping](MODEL_MAPPING.md)
- 🚀 Learn about [Production Deployment](DEPLOYMENT.md)
- 🔍 Check [Troubleshooting](TROUBLESHOOTING.md) if you hit issues

## Need Help?

- Check the [FAQ](FAQ.md)
- Review [Common Issues](TROUBLESHOOTING.md#common-issues)
- Open an [Issue](https://github.com/eyalrot/ollama_openai/issues) on GitHub

---

**Pro Tip**: Enable debug mode (`LOG_LEVEL=DEBUG`) to see detailed request/response logs during development!