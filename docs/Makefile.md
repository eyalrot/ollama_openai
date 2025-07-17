# Makefile Documentation

This comprehensive guide covers all 50+ Makefile commands available for the Ollama-OpenAI Proxy project. The Makefile provides intelligent automation for development, testing, deployment, and CI/CD workflows.

## Table of Contents

- [Quick Start](#quick-start)
- [Smart Environment Detection](#smart-environment-detection)
- [Command Categories](#command-categories)
- [Package Management](#package-management)
- [Environment Setup](#environment-setup)
- [Testing Commands](#testing-commands)
- [Code Quality](#code-quality)
- [Docker Commands](#docker-commands)
- [Docker Compose Integration](#docker-compose-integration)
- [Documentation](#documentation)
- [Monitoring & Performance](#monitoring--performance)
- [Configuration Management](#configuration-management)
- [Git & Release Management](#git--release-management)
- [Workflows](#workflows)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Get Help
```bash
# Show all available commands with descriptions
make help

# Check environment detection status
make compose-version
```

### First-Time Setup
```bash
# Complete setup for new developers
make first-time-setup
# Equivalent to: make venv-create dev-install setup-env
```

### Daily Development Workflow
```bash
# Setup development environment
make dev

# Start development server
make run-local

# Run tests
make test

# Code quality checks
make lint typecheck

# Build and test Docker container
make docker
```

## Smart Environment Detection

The Makefile automatically detects your development environment and adapts accordingly:

### Virtual Environment Detection
```bash
# The Makefile automatically finds and uses:
# 1. ./venv (highest priority)
# 2. ./.venv
# 3. ./env
# 4. ./.env
# 5. ./venv-dev
# 6. Active VIRTUAL_ENV (if set)
# 7. System Python (fallback)

# Check detected environment
make help  # Shows detected venv in output
```

### Docker Compose Version Detection
```bash
# Automatically detects and uses:
# 1. docker compose (Docker Compose v2)
# 2. docker-compose (Docker Compose v1)

# Check detected version
make compose-version
```

### Python Version Detection
```bash
# Automatically uses best available:
# 1. python3 (preferred)
# 2. python (fallback)
# Same logic for pip3/pip
```

## Command Categories

### 📦 Package Management

| Command | Description | Example |
|---------|-------------|---------|
| `make dist` | Build distribution packages | `make dist` |
| `make dist-check` | Validate distribution packages | `make dist-check` |
| `make upload-test` | Upload to Test PyPI | `make upload-test` |
| `make upload-prod` | Upload to Production PyPI | `make upload-prod` |
| `make install-from-dist` | Install from local distribution | `make install-from-dist` |

#### Example: Package Release Workflow
```bash
# Build and validate package
make dist dist-check

# Test upload to PyPI
make upload-test

# Production release
make upload-prod
```

### 🏗️ Environment Setup

| Command | Description | Example |
|---------|-------------|---------|
| `make install` | Install production dependencies | `make install` |
| `make dev-install` | Install development dependencies | `make dev-install` |
| `make venv-create` | Create virtual environment | `make venv-create` |
| `make first-time-setup` | Complete first-time setup | `make first-time-setup` |
| `make reset-env` | Reset development environment | `make reset-env` |
| `make requirements-freeze` | Freeze current requirements | `make requirements-freeze` |
| `make pip-audit` | Security audit of dependencies | `make pip-audit` |

#### Example: Environment Management
```bash
# Create new environment from scratch
make venv-create
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install development dependencies
make dev-install

# Reset everything and start fresh
make reset-env
```

### 🧪 Testing Commands

| Command | Description | Coverage | Performance |
|---------|-------------|----------|-------------|
| `make test` | Run all tests | ✅ | Fast |
| `make test-unit` | Unit tests only | ✅ | Fastest |
| `make test-integration` | Integration tests | ✅ | Medium |
| `make test-performance` | Performance tests | ✅ | Slow |
| `make test-watch` | Watch mode for TDD | ✅ | Continuous |
| `make test-parallel` | Parallel test execution | ✅ | Fastest |
| `make test-stress` | Stress testing (100 iterations) | ✅ | Slowest |
| `make coverage` | Generate coverage report | ✅ | Medium |
| `make coverage-html` | HTML coverage report | ✅ | Medium |
| `make coverage-check` | Enforce coverage threshold | ✅ | Fast |

#### Example: Testing Workflow
```bash
# Development testing
make test-watch  # Continuous testing during development

# Pre-commit testing
make test coverage

# Performance validation
make test-performance

# Stress testing
make test-stress

# Parallel execution for speed
make test-parallel
```

### ✨ Code Quality

| Command | Description | Speed | Auto-fix |
|---------|-------------|-------|----------|
| `make lint` | Run code linting | Fast | ❌ |
| `make lint-fix` | Run linting with auto-fix | Fast | ✅ |
| `make format` | Format code with black | Fast | ✅ |
| `make format-check` | Check formatting only | Fast | ❌ |
| `make typecheck` | Run type checking | Medium | ❌ |
| `make complexity` | Analyze code complexity | Medium | ❌ |
| `make duplicates` | Find duplicate code | Slow | ❌ |
| `make dead-code` | Find unused code | Medium | ❌ |
| `make imports-fix` | Organize imports | Fast | ✅ |
| `make quick-check` | Fast quality checks | Fast | ❌ |
| `make full-check` | All quality checks | Slow | ❌ |

#### Example: Code Quality Workflow
```bash
# Daily development
make quick-check  # lint + typecheck

# Before commit
make format imports-fix
make full-check

# Code analysis
make complexity duplicates dead-code
```

### 🐳 Docker Commands

| Command | Description | Use Case |
|---------|-------------|----------|
| `make docker` | Build and run container | Quick test |
| `make build` | Build Docker image | Development |
| `make build-dev` | Build development image | Development |
| `make build-ci` | Build CI image | CI/CD |
| `make run` | Run container | Testing |
| `make run-local` | Run locally (no Docker) | Development |
| `make stop` | Stop container | Cleanup |
| `make logs` | Show container logs | Debugging |
| `make docker-shell` | Interactive shell | Debugging |
| `make docker-cleanup` | Clean Docker resources | Maintenance |

#### Example: Docker Development
```bash
# Build and test
make build run

# Debug issues
make docker-shell
make logs

# Cleanup
make stop docker-cleanup
```

### 🐳 Docker Compose Integration

The Makefile provides comprehensive Docker Compose support with automatic version detection:

#### Environment Commands

| Command | Description | Environment | Features |
|---------|-------------|-------------|----------|
| `make compose-dev` | Development environment | Development | Hot-reload, debugging |
| `make compose-prod` | Production environment | Production | Optimized, secure |
| `make compose-ssl` | SSL-enabled production | Production | SSL certificates |
| `make compose-debug` | Debug environment | Development | debugpy, tools |
| `make compose-cluster` | Load-balanced cluster | Production | 3 instances, nginx |

#### CI/CD Commands

| Command | Description | Speed | Output |
|---------|-------------|-------|---------|
| `make compose-ci` | Full CI pipeline | Medium | Test results |
| `make compose-test` | Run tests | Fast | Test output |
| `make compose-lint` | Run linting | Fast | Lint results |
| `make compose-typecheck` | Type checking | Medium | Type errors |
| `make compose-security` | Security scan | Medium | Security report |

#### Multi-Stack Commands

| Command | Description | Components | Use Case |
|---------|-------------|------------|----------|
| `make compose-full-stack` | Production + monitoring | Proxy + Prometheus/Grafana | Production |
| `make compose-dev-debug` | Development + debugging | Proxy + debug tools | Development |

#### Lifecycle Management

| Command | Description | Scope |
|---------|-------------|-------|
| `make compose-down-all` | Stop all environments | All compose files |
| `make compose-status` | Show environment status | All environments |
| `make compose-health` | Check container health | Running containers |
| `make compose-logs-dev` | Development logs | Dev environment |
| `make compose-logs-prod` | Production logs | Prod environment |
| `make compose-restart-dev` | Restart development | Dev environment |
| `make compose-restart-prod` | Restart production | Prod environment |

#### Example: Docker Compose Workflows

```bash
# Development workflow
make compose-dev
make compose-logs-dev
make compose-health
make compose-down-all

# Production deployment
make compose-prod
make compose-status

# CI/CD pipeline
make compose-ci

# Full production stack
make compose-full-stack

# Debug issues
make compose-dev-debug
make compose-logs-dev

# Cluster deployment
make compose-cluster
make compose-status
```

### 📚 Documentation

| Command | Description | Output |
|---------|-------------|--------|
| `make docs-serve` | Serve API documentation | HTTP server |
| `make docs-build` | Build documentation | Static files |
| `make openapi-spec` | Generate OpenAPI JSON | openapi.json |
| `make openapi-yaml` | Generate OpenAPI YAML | openapi.yaml |
| `make docs-validate` | Validate OpenAPI spec | Validation report |

#### Example: Documentation Workflow
```bash
# Serve interactive docs
make docs-serve
# Access at http://localhost:8000/docs

# Generate API specs
make openapi-spec openapi-yaml

# Validate spec
make docs-validate
```

### 📊 Monitoring & Performance

| Command | Description | Output | Duration |
|---------|-------------|--------|----------|
| `make benchmark` | Performance benchmarks | Metrics | 30s |
| `make load-test` | Load testing | Performance data | 60s |
| `make memory-profile` | Memory profiling | Memory usage | 30s |
| `make cpu-profile` | CPU profiling | CPU metrics | 30s |
| `make performance-suite` | Complete suite | All metrics | 2-3 mins |
| `make monitor-health` | Health check | Health status | 5s |
| `make monitor-metrics` | Prometheus metrics | Metrics data | 5s |

#### Example: Performance Analysis
```bash
# Quick performance check
make benchmark

# Comprehensive analysis
make performance-suite

# Memory issues
make memory-profile

# Production monitoring
make monitor-health monitor-metrics
```

### ⚙️ Configuration Management

| Command | Description | Scope |
|---------|-------------|-------|
| `make config-validate` | Validate configuration | All config files |
| `make backup-config` | Backup configuration | Config + env files |
| `make restore-config` | List available backups | Backup directory |
| `make setup-env` | Setup environment file | .env creation |

#### Example: Configuration Management
```bash
# Validate settings
make config-validate

# Backup before changes
make backup-config

# Setup new environment
make setup-env
```

### 🔀 Git & Release Management

| Command | Description | Impact |
|---------|-------------|--------|
| `make git-hooks-update` | Update git hooks | Development |
| `make version-bump-patch` | Bump patch version | Version file |
| `make version-bump-minor` | Bump minor version | Version file |
| `make version-bump-major` | Bump major version | Version file |
| `make tag-release` | Tag current version | Git repository |
| `make changelog-generate` | Generate changelog | CHANGELOG_AUTO.md |

#### Example: Release Workflow
```bash
# Bump version
make version-bump-minor

# Generate changelog
make changelog-generate

# Tag release
make tag-release

# Build and distribute
make dist upload-prod
```

### 🚀 Workflows

| Command | Description | Steps Included |
|---------|-------------|----------------|
| `make dev` | Development setup | clean + dev-install |
| `make prod` | Production build | clean + install + build |
| `make ci` | CI pipeline | clean + lint + typecheck + test + coverage |
| `make all-checks` | All quality checks | lint + typecheck + test + coverage + security |
| `make quick-check` | Fast checks | lint + typecheck |
| `make full-check` | Complete validation | clean + all-checks |

#### Example: Workflow Usage
```bash
# Start new feature development
make dev

# Pre-commit validation
make quick-check

# Pre-push validation
make all-checks

# CI simulation
make ci

# Production build
make prod
```

## Advanced Usage

### Environment Variables

The Makefile respects these environment variables:

```bash
# Python environment
VIRTUAL_ENV=/path/to/venv
PYTHON=/usr/bin/python3.11
PIP=/usr/bin/pip3.11

# Docker Compose
COMPOSE_FILE=docker-compose.override.yml
COMPOSE_PROJECT_NAME=ollama-proxy

# Application
DEBUG=true
LOG_LEVEL=DEBUG
PROXY_PORT=11434
```

### Custom Configurations

#### Using Custom Docker Compose Files
```bash
# Set custom compose file
export COMPOSE_FILE=docker-compose.custom.yml
make compose-dev

# Or specify directly (not supported by current Makefile)
# Use: docker compose -f custom.yml up -d
```

#### Using Different Python Versions
```bash
# Force specific Python version
export PYTHON=/usr/bin/python3.11
export PIP=/usr/bin/pip3.11
make dev-install
```

### Performance Optimization

#### Parallel Test Execution
```bash
# Use all CPU cores
make test-parallel

# Specify core count
pytest -n 4  # 4 cores
```

#### Incremental Testing
```bash
# Watch mode for rapid development
make test-watch

# Test specific modules
pytest tests/unit/test_models.py -v
```

## Troubleshooting

### Common Issues

#### Docker Compose Version Issues
```bash
# Check detected version
make compose-version

# If detection fails, install Docker Compose
# v2 (recommended): Install Docker Desktop or Docker CLI plugin
# v1 (legacy): pip install docker-compose
```

#### Virtual Environment Issues
```bash
# Check detected environment
make help  # Shows venv info

# Create new environment
make venv-create

# Reset everything
make reset-env
```

#### Permission Issues
```bash
# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
newgrp docker

# Fix Python permissions
make venv-create
source venv/bin/activate
make dev-install
```

#### Performance Issues
```bash
# Skip slow tests
pytest -m "not slow"

# Use parallel execution
make test-parallel

# Profile performance
make memory-profile cpu-profile
```

### Debug Commands

#### Verbose Output
```bash
# Add -v flag to make for verbose output
make -v test

# Enable shell debugging
bash -x Makefile  # Not applicable to Makefile
# Instead: make test VERBOSE=1 (if implemented)
```

#### Environment Debugging
```bash
# Check all detected variables
make help  # Shows environment info

# Test specific commands
make compose-version
```

### Getting Help

```bash
# Show all commands
make help

# Command-specific help
make test --help  # For pytest options
make compose-dev --help  # For docker compose options

# Makefile documentation
cat Makefile  # View source
grep -n "^[a-zA-Z].*:" Makefile  # List all targets
```

## Best Practices

### Development Workflow
1. **Start with setup**: `make first-time-setup`
2. **Daily development**: `make dev run-local`
3. **Before commits**: `make quick-check`
4. **Before push**: `make all-checks`
5. **Testing**: `make test-watch` during development

### Docker Workflow
1. **Development**: `make compose-dev`
2. **Testing**: `make compose-ci`
3. **Production**: `make compose-prod`
4. **Debugging**: `make compose-debug`
5. **Cleanup**: `make compose-down-all`

### Release Workflow
1. **Version bump**: `make version-bump-*`
2. **Testing**: `make ci`
3. **Build**: `make dist`
4. **Release**: `make upload-prod`
5. **Tag**: `make tag-release`

### Performance Tips
- Use `make test-parallel` for faster testing
- Use `make quick-check` for rapid feedback
- Use `make compose-dev` instead of manual Docker commands
- Use `make reset-env` when dependencies get corrupted

## Integration with IDEs

### VS Code
Add to `.vscode/tasks.json`:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Test",
            "type": "shell",
            "command": "make test",
            "group": "test"
        },
        {
            "label": "Dev Setup",
            "type": "shell",
            "command": "make dev"
        }
    ]
}
```

### PyCharm
1. Go to **Run** → **Edit Configurations**
2. Add **Shell Script** configuration
3. Set **Script path** to `make`
4. Set **Script options** to desired command (e.g., `test`)

## Contributing to Makefile

### Adding New Commands
1. Follow existing naming conventions
2. Add to `.PHONY` target
3. Include in help documentation
4. Add to this documentation
5. Test on different environments

### Testing Makefile Changes
```bash
# Test all commands work
make help
make compose-version

# Test environment detection
unset VIRTUAL_ENV
make help

# Test Docker Compose detection
docker compose version || docker-compose --version
```

This comprehensive Makefile provides a robust foundation for development, testing, and deployment workflows. The intelligent environment detection ensures it works across different development setups while maintaining consistency and reliability.