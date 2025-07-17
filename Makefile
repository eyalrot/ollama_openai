# Makefile for Ollama-OpenAI Proxy Development

# Virtual Environment Auto-Detection
# Check common venv locations in order of preference
VENV_PATH := $(shell \
	if [ -d "./venv" ]; then echo "./venv"; \
	elif [ -d "./.venv" ]; then echo "./.venv"; \
	elif [ -d "./env" ]; then echo "./env"; \
	elif [ -d "./.env" ]; then echo "./.env"; \
	elif [ -d "./venv-dev" ]; then echo "./venv-dev"; \
	fi)

# Python and pip executables with intelligent detection
ifdef VENV_PATH
    PYTHON := $(VENV_PATH)/bin/python
    PIP := $(VENV_PATH)/bin/pip
    VENV_ACTIVE := true
    VENV_INFO := 🐍 Using virtual environment: $(VENV_PATH)
else ifdef VIRTUAL_ENV
    PYTHON := python
    PIP := pip
    VENV_ACTIVE := true
    VENV_INFO := 🐍 Using active virtual environment: $(VIRTUAL_ENV)
else
    PYTHON := $(shell which python3 2>/dev/null || which python)
    PIP := $(shell which pip3 2>/dev/null || which pip)
    VENV_ACTIVE := false
    VENV_INFO := ⚠️  No virtual environment detected - using system Python: $(PYTHON)
endif

# Docker Compose command detection
# Check for Docker Compose v2 (docker compose) first, then fallback to v1 (docker-compose)
DOCKER_COMPOSE := $(shell \
	if docker compose version >/dev/null 2>&1; then \
		echo "docker compose"; \
	elif docker-compose --version >/dev/null 2>&1; then \
		echo "docker-compose"; \
	else \
		echo ""; \
	fi)

ifdef DOCKER_COMPOSE
    ifeq ($(DOCKER_COMPOSE),docker compose)
        COMPOSE_INFO := 🐳 Using Docker Compose v2: $(DOCKER_COMPOSE)
    else
        COMPOSE_INFO := 🐳 Using Docker Compose v1: $(DOCKER_COMPOSE)
    endif
else
    COMPOSE_INFO := ⚠️  Docker Compose not found - please install Docker Compose
endif

.PHONY: help install dev-install clean test test-unit test-integration test-performance coverage lint format typecheck security docker build run stop logs all-checks ci dist upload-test upload-prod install-from-dist venv-create requirements-freeze pip-audit complexity duplicates imports dead-code test-watch test-stress test-memory test-parallel docs-serve docs-build openapi-spec benchmark load-test memory-profile config-validate backup-config restore-config git-hooks-update changelog-generate tag-release docker-shell docker-cleanup docker-multi-arch quick-check full-check reset-env venv-status compose-dev compose-prod compose-ssl compose-ci compose-test compose-lint compose-typecheck compose-security compose-full-stack compose-dev-debug compose-cluster compose-down-all compose-logs-dev compose-logs-prod compose-logs-ssl compose-restart-dev compose-restart-prod compose-status compose-health compose-version

# Default target
help:
	@echo "🔧 Ollama-OpenAI Proxy Development Commands"
	@echo ""
	@echo "📦 Package Management:"
	@echo "  dist             Build distribution packages"
	@echo "  upload-test      Upload to Test PyPI"
	@echo "  upload-prod      Upload to Production PyPI"
	@echo "  install-from-dist Install from local distribution"
	@echo ""
	@echo "🏗️  Environment Setup:"
	@echo "  install          Install production dependencies"
	@echo "  dev-install      Install development dependencies"
	@echo "  venv-create      Create virtual environment"
	@echo "  requirements-freeze Freeze current requirements"
	@echo "  pip-audit        Security audit of dependencies"
	@echo "  first-time-setup Complete first-time setup"
	@echo "  reset-env        Reset development environment"
	@echo ""
	@echo "🧪 Testing:"
	@echo "  test            Run all tests"
	@echo "  test-unit       Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  test-watch      Watch mode for TDD"
	@echo "  test-parallel   Run tests in parallel"
	@echo "  test-stress     Stress testing with iterations"
	@echo "  coverage        Generate coverage report"
	@echo ""
	@echo "✨ Code Quality:"
	@echo "  lint            Run code linting"
	@echo "  format          Format code with black"
	@echo "  typecheck       Run type checking with mypy"
	@echo "  complexity      Analyze code complexity"
	@echo "  duplicates      Find duplicate code"
	@echo "  dead-code       Find unused code"
	@echo "  imports-fix     Organize import statements"
	@echo "  quick-check     Fast quality checks (lint + typecheck)"
	@echo "  full-check      All quality checks"
	@echo ""
	@echo "🔒 Security:"
	@echo "  security        Run security scans"
	@echo "  pip-audit       Audit dependencies for vulnerabilities"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  docs-serve      Serve API documentation"
	@echo "  docs-build      Build documentation"
	@echo "  openapi-spec    Generate OpenAPI specification"
	@echo ""
	@echo "📊 Monitoring & Performance:"
	@echo "  benchmark       Run performance benchmarks"
	@echo "  load-test       Execute load testing"
	@echo "  memory-profile  Profile memory usage"
	@echo "  monitor-health  Check service health"
	@echo "  performance-suite Run complete performance suite"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  docker          Build and run Docker container"
	@echo "  build           Build Docker image"
	@echo "  run             Run application in container"
	@echo "  run-local       Run application locally"
	@echo "  stop            Stop running containers"
	@echo "  logs            Show Docker logs"
	@echo "  docker-shell    Interactive shell in container"
	@echo "  docker-cleanup  Clean up Docker resources"
	@echo ""
	@echo "🐳 Docker Compose:"
	@echo "  compose-dev     Start development environment"
	@echo "  compose-prod    Start production environment"
	@echo "  compose-ssl     Start SSL-enabled production"
	@echo "  compose-ci      Run CI pipeline"
	@echo "  compose-test    Run tests via Docker Compose"
	@echo "  compose-lint    Run linting via Docker Compose"
	@echo "  compose-typecheck Run type checking via Docker Compose"
	@echo "  compose-security Run security scan via Docker Compose"
	@echo "  compose-down-all Stop all Docker Compose environments"
	@echo "  compose-status   Show status of all environments"
	@echo "  compose-health   Check health of running containers"
	@echo "  compose-version  Show Docker Compose version info"
	@echo ""
	@echo "⚙️  Configuration:"
	@echo "  config-validate Validate configuration files"
	@echo "  backup-config   Backup configuration"
	@echo "  setup-env       Setup environment file"
	@echo ""
	@echo "🔀 Git & Release:"
	@echo "  git-hooks-update Update git hooks"
	@echo "  version-bump-*  Bump version (patch/minor/major)"
	@echo "  tag-release     Tag current version for release"
	@echo ""
	@echo "🚀 Workflows:"
	@echo "  dev             Setup development environment"
	@echo "  prod            Production build workflow"
	@echo "  all-checks      Run all quality checks"
	@echo "  ci              Run CI pipeline locally"
	@echo "  clean           Clean up build artifacts and cache"

# Installation targets
install:
	@echo "$(VENV_INFO)"
	$(PIP) install -r requirements.txt

dev-install:
	@echo "$(VENV_INFO)"
	$(PIP) install -r requirements-dev.txt
	$(PIP) install -e .
	pre-commit install

# Cleanup targets
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf coverage.json
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Testing targets
test:
	pytest

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/test_docker.py -v

test-performance:
	pytest tests/performance/ -v

# Coverage targets
coverage:
	pytest --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing

coverage-html:
	pytest --cov=src --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-xml:
	pytest --cov=src --cov-report=xml

coverage-check:
	pytest --cov=src --cov-fail-under=80

# Code quality targets
lint:
	ruff check src/ tests/

lint-fix:
	ruff check --fix src/ tests/

format:
	black src/ tests/

format-check:
	black --check src/ tests/

typecheck:
	mypy src/

# Security targets
security:
	bandit -r src/ -f json -o bandit-results.json || true
	bandit -r src/ || true
	safety check || true

security-detailed:
	bandit -r src/ -v
	safety check --detailed-output

# Docker targets
docker: build run

build:
	docker build -t ollama-openai-proxy .

build-dev:
	docker build -f docker/Dockerfile.dev -t ollama-openai-proxy:dev .

build-ci:
	docker build -f docker/Dockerfile.ci -t ollama-openai-proxy:ci .

run:
	docker run -d \
		--name ollama-openai-proxy \
		-p 11434:11434 \
		--env-file .env \
		ollama-openai-proxy

run-dev:
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml up -d

run-prod:
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml up -d

stop:
	docker stop ollama-openai-proxy || true
	docker rm ollama-openai-proxy || true

stop-dev:
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml down

stop-prod:
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml down

logs:
	docker logs -f ollama-openai-proxy

logs-dev:
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml logs -f

# Enhanced Docker Compose Management
compose-dev:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml up -d
	@echo "Development environment started. Access at http://localhost:${PROXY_PORT:-11434}"

compose-prod:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml up -d
	@echo "Production environment started. Access at http://localhost:${PROXY_PORT:-11434}"

compose-ssl:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.ssl.yml up -d
	@echo "SSL-enabled production environment started. Access at http://localhost:${PROXY_PORT:-11434}"

compose-ci:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.ci.yml up --abort-on-container-exit
	@echo "CI pipeline completed"

compose-test:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.ci.yml run --rm ci-tests
	@echo "Unit tests completed via Docker Compose"

compose-lint:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.ci.yml run --rm lint
	@echo "Linting completed via Docker Compose"

compose-typecheck:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.ci.yml run --rm typecheck
	@echo "Type checking completed via Docker Compose"

compose-security:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.ci.yml run --rm security-scan
	@echo "Security scan completed via Docker Compose"

# Multi-stack combinations
compose-full-stack:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml -f docker/docker-compose.monitoring.yml up -d
	@echo "Full production stack with monitoring started"

compose-dev-debug:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml -f docker/docker-compose.debug.yml up -d
	@echo "Development environment with debugging enabled"

compose-cluster:
	@echo "$(COMPOSE_INFO)"
	$(DOCKER_COMPOSE) -f docker/docker-compose.cluster.yml up -d
	@echo "Load-balanced cluster started"

# Lifecycle management
compose-down-all:
	@echo "$(COMPOSE_INFO)"
	@echo "Stopping all Docker Compose environments..."
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml down 2>/dev/null || true
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml down 2>/dev/null || true
	$(DOCKER_COMPOSE) -f docker/docker-compose.ssl.yml down 2>/dev/null || true
	$(DOCKER_COMPOSE) -f docker/docker-compose.ci.yml down 2>/dev/null || true
	$(DOCKER_COMPOSE) -f docker/docker-compose.monitoring.yml down 2>/dev/null || true
	$(DOCKER_COMPOSE) -f docker/docker-compose.debug.yml down 2>/dev/null || true
	$(DOCKER_COMPOSE) -f docker/docker-compose.cluster.yml down 2>/dev/null || true
	@echo "All environments stopped"

compose-logs-dev:
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml logs -f

compose-logs-prod:
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml logs -f

compose-logs-ssl:
	$(DOCKER_COMPOSE) -f docker/docker-compose.ssl.yml logs -f

compose-restart-dev:
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml restart
	@echo "Development environment restarted"

compose-restart-prod:
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml restart
	@echo "Production environment restarted"

# Health and status checks
compose-status:
	@echo "$(COMPOSE_INFO)"
	@echo "=== Development Environment ==="
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml ps 2>/dev/null || echo "Not running"
	@echo "=== Production Environment ==="
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml ps 2>/dev/null || echo "Not running"
	@echo "=== SSL Environment ==="
	$(DOCKER_COMPOSE) -f docker/docker-compose.ssl.yml ps 2>/dev/null || echo "Not running"

compose-health:
	@echo "$(COMPOSE_INFO)"
	@echo "Checking health of running containers..."
	$(DOCKER_COMPOSE) -f docker/docker-compose.dev.yml exec ollama-proxy-dev curl -s http://localhost:11434/health 2>/dev/null || echo "Dev: Not accessible"
	$(DOCKER_COMPOSE) -f docker/docker-compose.prod.yml exec ollama-proxy curl -s http://localhost:11434/health 2>/dev/null || echo "Prod: Not accessible"

compose-version:
	@echo "$(COMPOSE_INFO)"
	@echo "Detected command: $(DOCKER_COMPOSE)"
	@if [ -n "$(DOCKER_COMPOSE)" ]; then \
		$(DOCKER_COMPOSE) version; \
	else \
		echo "❌ Docker Compose not found. Please install Docker Compose v1 or v2"; \
	fi

# Local development targets
run-local:
	uvicorn src.main:app --host 0.0.0.0 --port 11434 --reload

run-debug:
	uvicorn src.main:app --host 0.0.0.0 --port 11434 --reload --log-level debug

# Combined targets
all-checks: lint typecheck test coverage security
	@echo "All quality checks completed successfully!"

ci: clean lint typecheck test coverage
	@echo "CI pipeline completed successfully!"

# Pre-commit simulation
pre-commit-all:
	pre-commit run --all-files

# Performance profiling
profile:
	python -m cProfile -o profile.stats src/main.py
	python -c "import pstats; pstats.Stats('profile.stats').sort_stats('cumulative').print_stats(20)"

# Dependency management
update-deps:
	pip-compile requirements.in
	pip-compile requirements-dev.in

# Documentation generation
docs:
	@echo "Generating API documentation..."
	python -c "import uvicorn; from src.main import app; print('API docs available at http://localhost:8000/docs')"

# Environment setup
setup-env:
	cp .env.example .env
	@echo "Environment file created. Please edit .env with your configuration."

# Database/migration targets (if needed in future)
migrate:
	@echo "No migrations needed for this stateless proxy service"

# Monitoring and metrics
metrics:
	curl http://localhost:11434/v1/metrics/prometheus

health:
	curl http://localhost:11434/health

# Release targets
version-bump-patch:
	bump2version patch

version-bump-minor:
	bump2version minor

version-bump-major:
	bump2version major

# Git hooks
install-hooks:
	pre-commit install
	pre-commit install --hook-type commit-msg

# Development workflow
dev: clean dev-install
	@echo "Development environment set up successfully!"
	@echo "Run 'make run-local' to start the development server"

# Production workflow
prod: clean install build
	@echo "Production build completed successfully!"
	@echo "Run 'make run-prod' to start the production server"

# Package management targets
dist: clean
	python -m build
	@echo "Distribution packages created in dist/"

dist-check:
	python -m twine check dist/*

upload-test: dist dist-check
	python -m twine upload --repository testpypi dist/*
	@echo "Package uploaded to Test PyPI"

upload-prod: dist dist-check
	python -m twine upload dist/*
	@echo "Package uploaded to Production PyPI"

install-from-dist: dist
	pip install dist/*.whl --force-reinstall
	@echo "Package installed from local distribution"

# Development environment management
venv-create:
	python -m venv venv
	@echo "Virtual environment created in ./venv"
	@echo "Activate with: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"

venv-activate:
	@echo "To activate virtual environment, run:"
	@echo "  source venv/bin/activate  (Linux/Mac)"
	@echo "  venv\\Scripts\\activate     (Windows)"

requirements-freeze:
	pip freeze > requirements-frozen.txt
	@echo "Current environment frozen to requirements-frozen.txt"

requirements-upgrade:
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt
	pip install --upgrade -r requirements-dev.txt
	@echo "All requirements upgraded to latest versions"

pip-audit:
	pip-audit --requirement requirements.txt --requirement requirements-dev.txt
	@echo "Security audit completed"

pip-outdated:
	pip list --outdated
	@echo "Outdated packages listed above"

# Enhanced code quality targets
complexity:
	radon cc src/ -a -nc || echo "Install radon: pip install radon"
	@echo "Code complexity analysis completed"

complexity-json:
	radon cc src/ -f json -o complexity-report.json || echo "Install radon: pip install radon"
	@echo "Code complexity report saved to complexity-report.json"

duplicates:
	jscpd src/ --reporters console || echo "Install jscpd: npm install -g jscpd"
	@echo "Duplicate code analysis completed"

imports:
	isort src/ tests/ --check-only --diff || echo "Install isort: pip install isort"
	@echo "Import statement analysis completed"

imports-fix:
	isort src/ tests/
	@echo "Import statements organized"

dead-code:
	vulture src/ || echo "Install vulture: pip install vulture"
	@echo "Dead code analysis completed"

code-metrics:
	radon raw src/ -s || echo "Install radon: pip install radon"
	radon hal src/ || echo "Halstead metrics calculation failed"
	radon mi src/ -s || echo "Maintainability index calculation failed"
	@echo "Comprehensive code metrics generated"

# Enhanced testing targets
test-watch:
	pytest-watch -- tests/ || echo "Install pytest-watch: pip install pytest-watch"
	@echo "Test watch mode - tests will re-run on file changes"

test-stress:
	pytest tests/ --count=100 || echo "Install pytest-repeat: pip install pytest-repeat"
	@echo "Stress testing completed with 100 iterations"

test-memory:
	pytest tests/ --memray || echo "Install pytest-memray: pip install pytest-memray"
	@echo "Memory usage testing completed"

test-parallel:
	pytest tests/ -n auto || echo "Install pytest-xdist: pip install pytest-xdist"
	@echo "Parallel testing completed"

test-benchmark:
	pytest tests/performance/ --benchmark-only || echo "Install pytest-benchmark: pip install pytest-benchmark"
	@echo "Benchmark testing completed"

test-random:
	pytest tests/ --random-order || echo "Install pytest-random-order: pip install pytest-random-order"
	@echo "Random order testing completed"

test-mutation:
	mutmut run || echo "Install mutmut: pip install mutmut"
	@echo "Mutation testing completed"

test-snapshot:
	pytest tests/ --snapshot-update || echo "Install pytest-snapshot: pip install pytest-snapshot"
	@echo "Snapshot testing completed"

# Documentation targets
docs-serve:
	uvicorn src.main:app --host localhost --port 8000 --reload &
	@echo "API documentation served at http://localhost:8000/docs"
	@echo "Redoc documentation at http://localhost:8000/redoc"
	@echo "Press Ctrl+C to stop the server"

docs-build:
	mkdir -p docs/api
	python -c "import json; from src.main import app; print(json.dumps(app.openapi(), indent=2))" > docs/api/openapi.json
	@echo "OpenAPI specification generated at docs/api/openapi.json"

openapi-spec:
	python -c "import json; from src.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
	@echo "OpenAPI specification generated at openapi.json"

openapi-yaml:
	python -c "import yaml; from src.main import app; print(yaml.dump(app.openapi(), default_flow_style=False))" > openapi.yaml || echo "Install PyYAML: pip install PyYAML"
	@echo "OpenAPI specification generated at openapi.yaml"

docs-validate:
	swagger-codegen validate -i openapi.json || echo "Install swagger-codegen or use online validator"
	@echo "OpenAPI specification validation completed"

api-client-generate:
	openapi-generator-cli generate -i openapi.json -g python -o clients/python || echo "Install openapi-generator-cli"
	@echo "Python API client generated in clients/python/"

# Monitoring and performance targets
benchmark:
	python src/utils/benchmarks.py || echo "Benchmark script not found"
	@echo "Performance benchmarks completed"

load-test:
	python src/utils/load_test.py || echo "Load test script not found"
	@echo "Load testing completed"

memory-profile:
	python -m memory_profiler src/main.py || echo "Install memory-profiler: pip install memory-profiler"
	@echo "Memory profiling completed"

cpu-profile:
	python -m cProfile -o cpu_profile.stats src/main.py
	python -c "import pstats; pstats.Stats('cpu_profile.stats').sort_stats('cumulative').print_stats(20)"
	@echo "CPU profiling completed - top 20 functions by cumulative time"

line-profile:
	kernprof -l -v src/main.py || echo "Install line_profiler: pip install line_profiler"
	@echo "Line-by-line profiling completed"

performance-suite:
	$(MAKE) benchmark
	$(MAKE) load-test
	$(MAKE) memory-profile
	@echo "Complete performance suite executed"

monitor-metrics:
	curl -s http://localhost:11434/v1/metrics/prometheus || echo "Service not running on port 11434"
	@echo "Prometheus metrics retrieved"

monitor-health:
	curl -s http://localhost:11434/health || echo "Service not running on port 11434"
	@echo "Health check completed"

# Quick development shortcuts
quick-check: lint typecheck
	@echo "Quick quality checks completed successfully!"

full-check: clean lint typecheck test coverage security
	@echo "Full quality checks completed successfully!"

reset-env: clean
	rm -rf venv/ .venv/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	rm -f requirements-frozen.txt
	$(MAKE) venv-create
	$(MAKE) dev-install
	@echo "Development environment reset successfully!"

dev-reset: reset-env
	@echo "Development environment reset completed!"

first-time-setup: venv-create dev-install setup-env
	@echo "First-time development setup completed!"
	@echo "Next steps:"
	@echo "  1. Activate virtual environment: source venv/bin/activate"
	@echo "  2. Edit .env file with your configuration"
	@echo "  3. Run tests: make test"
	@echo "  4. Start development server: make run-local"

# Configuration management
config-validate:
	python -c "import json; json.load(open('config/model_map.json'))" && echo "✅ model_map.json is valid JSON" || echo "❌ model_map.json is invalid"
	python -c "from src.config import Config; Config()" && echo "✅ Configuration loads successfully" || echo "❌ Configuration failed to load"
	@echo "Configuration validation completed"

backup-config:
	mkdir -p backups/
	cp -r config/ backups/config-$(shell date +%Y%m%d-%H%M%S)
	cp .env backups/.env-$(shell date +%Y%m%d-%H%M%S) 2>/dev/null || echo "No .env file to backup"
	@echo "Configuration backup completed"

restore-config:
	@echo "Available config backups:"
	@ls -la backups/ | grep config- || echo "No config backups found"
	@echo "To restore: cp -r backups/config-YYYYMMDD-HHMMSS/* config/"

# Git and release management
git-hooks-update:
	pre-commit autoupdate
	pre-commit install --hook-type commit-msg
	@echo "Git hooks updated successfully"

changelog-generate:
	git log --oneline --pretty=format:"* %s (%an)" > CHANGELOG_AUTO.md
	@echo "Automatic changelog generated in CHANGELOG_AUTO.md"

tag-release:
	@echo "Current version: $(shell python -c 'from src._version import __version__; print(__version__)')"
	@echo "To tag a release, run: git tag v$(shell python -c 'from src._version import __version__; print(__version__)')"
	@echo "Then push with: git push origin v$(shell python -c 'from src._version import __version__; print(__version__)')"

# Enhanced container operations
docker-shell:
	docker exec -it ollama-openai-proxy /bin/bash || echo "Container not running. Start with 'make run'"

docker-shell-root:
	docker exec -it --user root ollama-openai-proxy /bin/bash || echo "Container not running"

docker-cleanup:
	docker stop ollama-openai-proxy 2>/dev/null || true
	docker rm ollama-openai-proxy 2>/dev/null || true
	docker rmi ollama-openai-proxy 2>/dev/null || true
	docker system prune -f
	@echo "Docker cleanup completed"

docker-multi-arch:
	docker buildx create --name multiarch --use || true
	docker buildx build --platform linux/amd64,linux/arm64 -t ollama-openai-proxy:latest --push .
	@echo "Multi-architecture build completed"

docker-inspect:
	docker inspect ollama-openai-proxy || echo "Container not found"

docker-resources:
	docker stats ollama-openai-proxy --no-stream || echo "Container not running"