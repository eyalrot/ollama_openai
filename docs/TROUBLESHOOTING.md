# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the Ollama to OpenAI proxy.

**New in v2.1**: Added troubleshooting for dual API format support and request body handling issues.

## Table of Contents

- [Connection Issues](#connection-issues)
- [Authentication Errors](#authentication-errors)
- [Model Problems](#model-problems)
- [Dual API Format Issues](#dual-api-format-issues)
- [Request Body Issues](#request-body-issues)
- [Performance Issues](#performance-issues)
- [Response Errors](#response-errors)
- [Docker Issues](#docker-issues)
- [Debugging Tools](#debugging-tools)
- [Error Code Reference](#error-code-reference)
- [FAQ](#faq)
- [Getting Help](#getting-help)

## Connection Issues

### Problem: Connection Refused

**Error Message:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```

**Causes & Solutions:**

1. **Proxy not running**
   ```bash
   # Check if proxy is running
   curl http://localhost:11434/health
   
   # Start the proxy
   docker-compose up -d
   # OR
   python -m uvicorn src.main:app --host 0.0.0.0 --port 11434
   ```

2. **Wrong port**
   ```bash
   # Check configured port
   echo $PROXY_PORT
   
   # Or check docker-compose.yml
   grep -A2 ports docker-compose.yml
   ```

3. **Firewall blocking**
   ```bash
   # Check firewall rules (Linux)
   sudo ufw status
   
   # Allow port if needed
   sudo ufw allow 11434
   ```

### Problem: Cannot Connect to Backend

**Error Message:**
```
UpstreamError: Connection to OpenAI backend failed
```

**Solutions:**

1. **Verify backend URL**
   ```bash
   # Test backend directly
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. **Check network connectivity**
   ```bash
   # From Docker container
   docker exec ollama-proxy ping api.openai.com
   ```

3. **Proxy settings**
   ```env
   # If behind corporate proxy
   HTTP_PROXY=http://proxy.company.com:8080
   HTTPS_PROXY=http://proxy.company.com:8080
   ```

## Authentication Errors

### Problem: 401 Unauthorized

**Error Message:**
```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": 401
  }
}
```

**Solutions:**

1. **Check API key format**
   ```bash
   # OpenAI keys start with 'sk-'
   echo $OPENAI_API_KEY | head -c 3
   
   # OpenRouter keys start with 'sk-or-'
   echo $OPENAI_API_KEY | head -c 6
   ```

2. **Verify key is set**
   ```bash
   # In Docker
   docker exec ollama-proxy env | grep OPENAI_API_KEY
   
   # In local environment
   echo $OPENAI_API_KEY
   ```

3. **Test key directly**
   ```bash
   # OpenAI
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   
   # OpenRouter
   curl https://openrouter.ai/api/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

### Problem: Rate Limit Exceeded

**Error Message:**
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "code": 429
  }
}
```

**Solutions:**

1. **Implement request throttling**
2. **Increase retry delays**
3. **Use multiple API keys**
4. **Upgrade API plan**

## Model Problems

### Problem: Model Not Found

**Error Message:**
```json
{
  "error": {
    "message": "Model 'llama2' not found",
    "type": "model_not_found",
    "code": "MODEL_NOT_FOUND"
  }
}
```

**Solutions:**

1. **List available models**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Add model mapping**
   ```json
   // model_mapping.json
   {
     "model_mappings": {
       "llama2": "meta-llama/Llama-2-7b-chat-hf",
       "mistral": "mistralai/Mistral-7B-Instruct-v0.1"
     }
   }
   ```

3. **Use exact model name**
   ```python
   # Instead of
   client.generate(model='llama2', ...)
   
   # Use
   client.generate(model='meta-llama/Llama-2-7b-chat-hf', ...)
   ```

### Problem: Model Mapping Not Working

**Symptoms:**
- Model mapping file exists but mappings aren't applied
- Getting "model not found" despite mapping

**Solutions:**

1. **Verify file path**
   ```bash
   # Check if file exists
   ls -la $MODEL_MAPPING_FILE
   
   # Check file is valid JSON
   jq . $MODEL_MAPPING_FILE
   ```

2. **Check Docker volume mount**
   ```yaml
   # docker-compose.yml
   volumes:
     - ./config:/app/config:ro
   ```

3. **Validate JSON format**
   ```bash
   # Test parsing
   python -m json.tool model_mapping.json
   ```

## Dual API Format Issues

### Problem: OpenAI Client Not Working

**Error Message:**
```
404 Not Found: /v1/chat/completions
```

**Causes & Solutions:**

1. **Using wrong endpoint URL**
   ```python
   # Wrong - points to Ollama endpoint
   openai.api_base = "http://localhost:11434"
   
   # Correct - points to OpenAI-compatible endpoint
   openai.api_base = "http://localhost:11434/v1"
   ```

2. **Missing Authorization header**
   ```python
   # Ensure API key is set
   openai.api_key = "your-api-key"
   
   # Or use environment variable
   export OPENAI_API_KEY="your-api-key"
   ```

### Problem: Ollama Client Format Issues

**Error Message:**
```
422 Unprocessable Entity: Invalid request format
```

**Solutions:**

1. **Verify endpoint path**
   ```python
   # Correct Ollama client usage
   client = Client(host='http://localhost:11434')  # No /v1 suffix
   
   # Use Ollama format endpoints
   response = client.generate(model='gpt-3.5-turbo', prompt='Hello')
   ```

2. **Check request body format**
   ```bash
   # Test Ollama format
   curl -X POST http://localhost:11434/api/generate \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-3.5-turbo", "prompt": "Hello"}'
   ```

### Problem: Mixed API Format Confusion

**Symptoms:**
- Ollama client trying to use OpenAI format
- OpenAI client trying to use Ollama format

**Solutions:**

1. **Use correct client for format**
   ```python
   # For Ollama format - use Ollama client
   from ollama import Client
   client = Client(host='http://localhost:11434')
   
   # For OpenAI format - use OpenAI client
   import openai
   openai.api_base = "http://localhost:11434/v1"
   ```

2. **Verify endpoint mapping**
   - Ollama endpoints: `/api/generate`, `/api/chat`, `/api/embeddings`
   - OpenAI endpoints: `/v1/chat/completions`, `/v1/embeddings`

## Request Body Issues

### Problem: Request Body Already Consumed

**Error Message:**
```
400 Bad Request: Request body has already been consumed and is not available
```

**Causes & Solutions:**

1. **Middleware conflict** (Fixed in v2.1)
   - This was a common issue in v2.0 and earlier
   - Fixed by implementing request body caching
   - Upgrade to v2.1 if experiencing this issue

2. **Custom middleware interference**
   ```python
   # If using custom middleware, ensure it doesn't consume request body
   # Use request body caching utility if needed
   from src.utils.request_body import get_body_json
   
   async def custom_middleware(request: Request, call_next):
       # Use cached body reading
       body = await get_body_json(request)
       # Process body without consuming it
       return await call_next(request)
   ```

### Problem: Invalid JSON in Request Body

**Error Message:**
```
400 Bad Request: Invalid JSON in request body
```

**Solutions:**

1. **Validate JSON format**
   ```bash
   # Test with curl
   curl -X POST http://localhost:11434/api/generate \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-3.5-turbo", "prompt": "Hello"}'  # Valid JSON
   ```

2. **Check for escape characters**
   ```bash
   # Avoid invalid escape sequences
   # Wrong:
   curl -d '{"prompt": "Hello \"world\""}'
   
   # Correct:
   curl -d '{"prompt": "Hello \"world\""}'
   ```

3. **Verify content-type header**
   ```bash
   # Always include content-type
   curl -H "Content-Type: application/json" ...
   ```

## Performance Issues

### Problem: Slow Response Times

**Symptoms:**
- Requests take longer than expected
- Timeouts on large prompts

**Solutions:**

1. **Increase timeout**
   ```env
   REQUEST_TIMEOUT=180  # 3 minutes
   ```

2. **Check backend latency**
   ```bash
   # Time a direct request
   time curl -X POST https://api.openai.com/v1/chat/completions \
     -H "Authorization: Bearer $OPENAI_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hi"}]}'
   ```

3. **Enable connection pooling**
   - Already enabled by default
   - Max 100 concurrent connections

4. **Monitor resource usage**
   ```bash
   # Docker stats
   docker stats ollama-proxy
   
   # System resources
   htop
   ```

### Problem: High Memory Usage

**Solutions:**

1. **Limit concurrent requests**
2. **Reduce log verbosity**
   ```env
   LOG_LEVEL=WARNING  # Instead of DEBUG
   ```
3. **Restart periodically**
   ```yaml
   # docker-compose.yml
   restart: unless-stopped
   ```

## Response Errors

### Problem: Incomplete Streaming Responses

**Symptoms:**
- Stream cuts off mid-response
- Missing final chunk

**Solutions:**

1. **Check timeout settings**
   ```env
   REQUEST_TIMEOUT=300  # 5 minutes for long streams
   ```

2. **Monitor for errors**
   ```bash
   # Check logs
   docker logs -f ollama-proxy | grep ERROR
   ```

3. **Test with non-streaming**
   ```python
   # Temporarily disable streaming
   response = client.generate(
       model='gpt-3.5-turbo',
       prompt='Test',
       stream=False  # Debug without streaming
   )
   ```

### Problem: JSON Decode Errors

**Error Message:**
```
JSONDecodeError: Expecting value: line 1 column 1
```

**Solutions:**

1. **Enable debug logging**
   ```env
   LOG_LEVEL=DEBUG
   ```

2. **Check response format**
   ```bash
   # Raw response
   curl -v http://localhost:11434/api/generate \
     -d '{"model": "gpt-3.5-turbo", "prompt": "Test"}'
   ```

3. **Verify content-type headers**
   - Should be `application/json` or `application/x-ndjson`

## Docker Issues

### Problem: Container Won't Start

**Solutions:**

1. **Check logs**
   ```bash
   docker-compose logs ollama-proxy
   ```

2. **Verify environment**
   ```bash
   # Check .env file
   cat .env
   
   # Validate docker-compose
   docker-compose config
   ```

3. **Port conflicts**
   ```bash
   # Check if port is in use
   lsof -i :11434
   # OR
   netstat -tulpn | grep 11434
   ```

### Problem: Can't Access Files in Container

**Solutions:**

1. **Check volume mounts**
   ```bash
   docker inspect ollama-proxy | jq '.[0].Mounts'
   ```

2. **File permissions**
   ```bash
   # Make files readable
   chmod 644 config/model_mapping.json
   ```

## Debugging Tools

### Enable Debug Mode

```env
# .env
LOG_LEVEL=DEBUG
DEBUG=true
```

### View Detailed Logs

```bash
# Docker
docker-compose logs -f ollama-proxy | grep -E 'ERROR|WARNING|DEBUG'

# Standalone
tail -f logs/app.log | jq '.'
```

### Test Endpoints

```bash
# Health check
curl -v http://localhost:11434/health

# List models
curl -v http://localhost:11434/api/tags

# Test generation
curl -v -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "prompt": "Test", "stream": false}'
```

### Monitor Performance

```bash
# Request timing
time curl http://localhost:11434/api/generate -d '{"model": "gpt-3.5-turbo", "prompt": "Hi"}'

# Watch logs
watch -n 1 'docker logs --tail 50 ollama-proxy'
```

## Error Code Reference

### Proxy-Specific Errors

| Code | Error | Description | Solution |
|------|-------|-------------|----------|
| `MODEL_NOT_FOUND` | Model not found | Requested model doesn't exist | Check model name/mapping |
| `INVALID_REQUEST` | Invalid request format | Malformed JSON or missing fields | Validate request structure |
| `UPSTREAM_ERROR` | Backend error | OpenAI/backend returned error | Check backend logs |
| `TIMEOUT_ERROR` | Request timeout | Request exceeded timeout | Increase `REQUEST_TIMEOUT` |
| `TRANSLATION_ERROR` | Format translation failed | Cannot convert between formats | Report bug |

### HTTP Status Codes

| Status | Meaning | Common Causes |
|--------|---------|---------------|
| 400 | Bad Request | Invalid JSON, missing parameters |
| 401 | Unauthorized | Invalid or missing API key |
| 404 | Not Found | Invalid endpoint or model |
| 413 | Payload Too Large | Request/prompt too big |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Proxy error (check logs) |
| 502 | Bad Gateway | Backend unreachable |
| 503 | Service Unavailable | Backend down or overloaded |
| 504 | Gateway Timeout | Backend timeout |

## FAQ

### Q: Can I use this with LocalAI/Oobabooga?

**A:** Yes, if they provide an OpenAI-compatible API. Set:
```env
OPENAI_API_BASE_URL=http://localhost:5000/v1
OPENAI_API_KEY=dummy-key-if-not-required
```

### Q: Why am I getting CORS errors?

**A:** The proxy sets CORS headers. If still having issues:
1. Check browser console for specific errors
2. Ensure you're accessing from allowed origin
3. Try with `curl` to bypass CORS

### Q: How do I add custom headers?

**A:** Currently not supported. Consider using a reverse proxy like nginx:
```nginx
location / {
    proxy_pass http://localhost:11434;
    proxy_set_header X-Custom-Header "value";
}
```

### Q: Can I use multiple backends?

**A:** Not in current version. Consider:
1. Running multiple proxy instances
2. Using a load balancer
3. Waiting for multi-backend support (planned)

### Q: How do I monitor the proxy?

**A:** Several options:
1. Health endpoint: `GET /health`
2. Logs: `docker logs -f ollama-proxy`
3. Metrics: Prometheus support coming soon

## Getting Help

### Before Asking for Help

1. **Check this guide thoroughly**
2. **Enable debug logging** and collect logs
3. **Test with `curl`** to isolate client issues
4. **Try with a known-good model** like `gpt-3.5-turbo`

### Information to Provide

When reporting issues, include:

1. **Environment**
   - OS and version
   - Docker version (if using)
   - Python version (if standalone)

2. **Configuration**
   ```bash
   # Sanitized config (hide API key)
   env | grep -E 'OPENAI_|PROXY_|LOG_' | sed 's/=.*key.*/=REDACTED/'
   ```

3. **Error Details**
   - Full error message
   - Request that caused error
   - Relevant log entries

4. **Steps to Reproduce**
   - Minimal example
   - Expected vs actual behavior

### Support Channels

1. **GitHub Issues**: [github.com/eyalrot/ollama_openai/issues](https://github.com/eyalrot/ollama_openai/issues)
2. **Discussions**: [github.com/eyalrot/ollama_openai/discussions](https://github.com/eyalrot/ollama_openai/discussions)
3. **Email**: support@example.com (for critical issues)

### Quick Fixes Checklist

- [ ] API key is set and valid
- [ ] Backend URL is correct and accessible  
- [ ] Proxy is running on expected port
- [ ] Model name exists or is mapped
- [ ] No firewall blocking connections
- [ ] Sufficient timeout for large requests
- [ ] Valid JSON in requests
- [ ] Docker has sufficient resources

---

For development and contribution guidelines, see [CONTRIBUTING.md](../CONTRIBUTING.md).