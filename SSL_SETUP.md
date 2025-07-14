# SSL Certificate Setup for Docker Compose

This guide explains how to use the SSL-enabled Docker Compose configuration to handle private SSL certificates with your OpenAI-compatible server.

## Quick Start

1. **Copy the environment template:**
   ```bash
   cp .env.ssl.example .env
   ```

2. **Configure your environment:**
   ```bash
   # Edit .env and set your values
   OPENAI_API_BASE_URL=https://your-private-ssl-server.com/v1
   OPENAI_API_KEY=your-api-key-here
   SSL_CERTS_PATH=/etc/ssl/certs
   ```

3. **Run with SSL support:**
   ```bash
   docker-compose -f docker/docker-compose.ssl.yml up -d
   ```

## Configuration Options

### Enable SSL Certificate Mounting
```bash
# In .env file
SSL_CERTS_PATH=/etc/ssl/certs
```

### Disable SSL Certificate Mounting
```bash
# In .env file - leave empty or comment out
SSL_CERTS_PATH=
# OR
# SSL_CERTS_PATH=
```

## Usage Commands

### Start with SSL support
```bash
docker-compose -f docker/docker-compose.ssl.yml up -d
```

### Stop the service
```bash
docker-compose -f docker/docker-compose.ssl.yml down
```

### View logs
```bash
docker-compose -f docker/docker-compose.ssl.yml logs -f ollama-proxy
```

### Check status
```bash
docker-compose -f docker/docker-compose.ssl.yml ps
```

## Security Considerations

- **Read-only mounting**: SSL certificates are mounted as read-only (`:ro`)
- **Certificate access**: The container has access to all system SSL certificates
- **Alternative approach**: For higher security, consider mounting only specific certificates:
  ```yaml
  volumes:
    - /path/to/specific/cert.pem:/etc/ssl/certs/custom.pem:ro
  ```

## Troubleshooting

### SSL Certificate Not Found
- Verify `SSL_CERTS_PATH` points to the correct directory
- Check that the directory exists on the host system
- Ensure the certificates are in the expected format

### Connection Still Fails
- Verify your OpenAI server's SSL certificate is in the mounted directory
- Check if the certificate chain is complete
- Test SSL connection from the host first

### Permission Issues
- Ensure the user running Docker has read access to the SSL certificate directory
- Consider using `sudo` if needed for certificate directory access

## File Structure

```
project/
├── docker/
│   └── docker-compose.ssl.yml # SSL-enabled Docker Compose configuration
├── .env.ssl.example          # Environment template with SSL settings
├── .env                      # Your actual environment configuration
└── SSL_SETUP.md             # This documentation file
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `SSL_CERTS_PATH` | Path to SSL certificates directory | (empty - disabled) |
| `OPENAI_API_BASE_URL` | Your OpenAI-compatible server URL | Required |
| `OPENAI_API_KEY` | API key for authentication | Required |
| `PROXY_PORT` | Port for the proxy service | 11434 |
| `LOG_LEVEL` | Logging level | INFO |
| `REQUEST_TIMEOUT` | Request timeout in seconds | 60 |
| `MAX_RETRIES` | Maximum retry attempts | 3 |