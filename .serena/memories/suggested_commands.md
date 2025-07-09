# Development Commands

## Running the Application
```bash
# Run the proxy service (from project root)
python -m src.main

# With environment variables
OPENAI_API_BASE_URL=https://api.openai.com/v1 OPENAI_API_KEY=your-key python -m src.main

# Using Docker
docker-compose up

# Build Docker image
docker build -t ollama-openai-proxy .
```

## Testing Commands
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run tests with coverage
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_main.py -v

# Run tests excluding main.py tests (for CI)
pytest tests/unit/ -v --ignore=tests/unit/test_main.py

# Run CI tests locally using Docker
./scripts/test-ci-local.sh
```

## Code Quality Commands
```bash
# Run linting with ruff
ruff check src/ tests/

# Format code with black
black src/ tests/

# Check formatting without changes
black --check src/ tests/

# Run type checking with mypy
mypy src/ --ignore-missing-imports --allow-untyped-defs --allow-incomplete-defs

# Run all quality checks (linting, formatting, type checking)
ruff check src/ tests/ && black --check src/ tests/ && mypy src/
```

## Git Commands
```bash
# Common git operations
git status
git add -A
git commit -m "feat: description of feature"
git push origin master

# Create pull request with GitHub CLI
gh pr create --title "Title" --body "Description"
```

## Docker Commands
```bash
# Build CI Docker image
docker build -f docker/Dockerfile.ci -t ollama-openai-proxy-ci:local .

# Run CI container for testing
docker run --rm -v $(pwd):/app -w /app ollama-openai-proxy-ci:local pytest tests/unit/ -v

# Docker compose commands
docker-compose up -d      # Start in background
docker-compose logs -f    # View logs
docker-compose down       # Stop services
```

## Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment example
cp .env.example .env
# Then edit .env with your configuration
```

## Task Management (via Task Master)
```bash
# View next task
task-master next

# Show task details
task-master show <id>

# Mark task as complete
task-master set-status --id=<id> --status=done

# Update task with progress
task-master update-subtask --id=<id> --prompt="implementation notes"
```