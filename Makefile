# Makefile for Ollama-OpenAI Proxy Development

.PHONY: help install dev-install clean test test-unit test-integration test-performance coverage lint format typecheck security docker build run stop logs all-checks ci

# Default target
help:
	@echo "Available targets:"
	@echo "  install          Install production dependencies"
	@echo "  dev-install      Install development dependencies"
	@echo "  clean           Clean up build artifacts and cache"
	@echo "  test            Run all tests"
	@echo "  test-unit       Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  coverage        Generate coverage report"
	@echo "  lint            Run code linting"
	@echo "  format          Format code with black"
	@echo "  typecheck       Run type checking with mypy"
	@echo "  security        Run security scans"
	@echo "  docker          Build and run Docker container"
	@echo "  build           Build Docker image"
	@echo "  run             Run application locally"
	@echo "  stop            Stop running containers"
	@echo "  logs            Show Docker logs"
	@echo "  all-checks      Run all quality checks"
	@echo "  ci              Run CI pipeline locally"

# Installation targets
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt
	pip install -e .
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
	docker-compose -f docker/docker-compose.dev.yml up -d

run-prod:
	docker-compose -f docker/docker-compose.prod.yml up -d

stop:
	docker stop ollama-openai-proxy || true
	docker rm ollama-openai-proxy || true

stop-dev:
	docker-compose -f docker/docker-compose.dev.yml down

stop-prod:
	docker-compose -f docker/docker-compose.prod.yml down

logs:
	docker logs -f ollama-openai-proxy

logs-dev:
	docker-compose -f docker/docker-compose.dev.yml logs -f

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