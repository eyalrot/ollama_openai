#!/bin/bash
# Script to test CI pipeline locally using Docker

set -e

echo "🔨 Building CI Docker image..."
docker build -f docker/Dockerfile.ci -t ollama-openai-proxy-ci:local .

echo "🔍 Running linting checks..."
docker run --rm -v $(pwd):/app -w /app ollama-openai-proxy-ci:local \
    sh -c "ruff check src/ tests/ && echo '✅ Ruff check passed'"

echo "🎨 Running black formatter check..."
docker run --rm -v $(pwd):/app -w /app ollama-openai-proxy-ci:local \
    black --check src/ tests/ && echo "✅ Black check passed"

echo "🔎 Running mypy type checker..."
docker run --rm -v $(pwd):/app -w /app ollama-openai-proxy-ci:local \
    mypy src/ --ignore-missing-imports --allow-untyped-defs --allow-incomplete-defs && echo "✅ Mypy check passed"

echo "🧪 Running tests with coverage..."
docker run --rm \
    -v $(pwd):/app \
    -w /app \
    -e OPENAI_API_BASE_URL=https://api.test.com \
    -e OPENAI_API_KEY=test-key \
    --user $(id -u):$(id -g) \
    ollama-openai-proxy-ci:local \
    pytest tests/unit/ -v --cov=src --cov-report=term-missing --ignore=tests/unit/test_main.py

echo "✅ All CI checks passed locally!"