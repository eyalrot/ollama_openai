# Docker Configuration for Ollama-OpenAI Proxy

This directory contains Docker configurations for building and running the Ollama-OpenAI proxy service.

## Quick Start

### Using Docker Compose (Recommended)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your configuration:
   ```bash
   OPENAI_API_BASE_URL=https://api.openai.com/v1
   OPENAI_API_KEY=your-api-key-here
   ```

3. Run the service:
   ```bash
   # Production
   docker-compose up -d

   # Development (with hot-reload)
   docker-compose -f docker/docker-compose.dev.yml up
   ```

### Using Docker Build Script

```bash
# Build production image
./docker/build.sh

# Build development image
./docker/build.sh --type dev

# Build and push to registry
./docker/build.sh --push --registry docker.io/yourusername
```

## Available Configurations

### Production (`Dockerfile.prod`)
- Multi-stage build for minimal image size
- Non-root user execution
- Security hardening
- Read-only filesystem
- Resource limits
- Optimized for production use

### Development (`Dockerfile.dev`)
- Hot-reload support
- Volume mounting for live code changes
- Debug mode enabled
- Development tools included

## Docker Compose Files

### `docker-compose.yml` (Root directory)
Basic production setup with default configuration.

### `docker/docker-compose.prod.yml`
Production-optimized configuration with:
- Resource limits
- Security options
- Read-only filesystem
- Persistent logging
- Network isolation

### `docker/docker-compose.dev.yml`
Development configuration with:
- Source code mounting
- Hot-reload enabled
- Debug logging
- Interactive terminal

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_BASE_URL` | OpenAI-compatible API endpoint | Required |
| `OPENAI_API_KEY` | API authentication key | Required |
| `PROXY_PORT` | Port to expose the proxy | 11434 |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `REQUEST_TIMEOUT` | Request timeout in seconds | 60 |
| `MAX_RETRIES` | Maximum retry attempts | 3 |
| `MODEL_MAPPING_FILE` | Path to model mapping config | None |
| `DEBUG` | Enable debug mode | false |

## Volume Mounts

### Production
- `/app/config`: Configuration files (read-only)
- `/app/logs`: Application logs

### Development
- `/app/src`: Source code (for hot-reload)
- `/app/tests`: Test files
- `/app/config`: Configuration files
- `/app/logs`: Application logs

## Health Checks

The containers include health checks that verify:
- Service is responding on the configured port
- `/health` endpoint returns 200 OK

Health check configuration:
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 10 seconds

## Security Considerations

Production images include:
- Non-root user execution (UID 1000)
- Read-only root filesystem
- No new privileges flag
- Minimal base image
- Security updates applied during build
- Resource limits enforced

## Building Images

### Manual Build
```bash
# Production
docker build -f docker/Dockerfile.prod -t ollama-openai-proxy:prod .

# Development
docker build -f docker/Dockerfile.dev -t ollama-openai-proxy:dev .
```

### Using BuildKit (Recommended)
```bash
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile.prod -t ollama-openai-proxy:prod .
```

## Running Containers

### Standalone Docker
```bash
docker run -d \
  --name ollama-proxy \
  -p 11434:11434 \
  -e OPENAI_API_BASE_URL=https://api.openai.com/v1 \
  -e OPENAI_API_KEY=your-key \
  ollama-openai-proxy:prod
```

### With Custom Configuration
```bash
docker run -d \
  --name ollama-proxy \
  -p 11434:11434 \
  -v ./config:/app/config:ro \
  -v ./logs:/app/logs \
  --env-file .env \
  ollama-openai-proxy:prod
```

## Troubleshooting

### Container won't start
1. Check logs: `docker logs ollama-proxy`
2. Verify environment variables are set
3. Ensure port 11434 is not already in use

### Health check failures
1. Verify the service is running: `docker exec ollama-proxy curl http://localhost:11434/health`
2. Check for startup errors in logs
3. Ensure PROXY_PORT matches the exposed port

### Permission issues
1. Ensure config files are readable by UID 1000
2. Check volume mount permissions
3. Verify SELinux contexts if applicable

## Monitoring

### View logs
```bash
# All logs
docker logs ollama-proxy

# Follow logs
docker logs -f ollama-proxy

# Last 100 lines
docker logs --tail 100 ollama-proxy
```

### Check health status
```bash
docker inspect ollama-proxy --format='{{.State.Health.Status}}'
```

### Resource usage
```bash
docker stats ollama-proxy
```