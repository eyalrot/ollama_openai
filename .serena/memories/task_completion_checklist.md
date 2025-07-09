# Task Completion Checklist

When completing any coding task, follow these steps:

## 1. Code Quality Checks
Run these commands to ensure code quality:

```bash
# Linting check
ruff check src/ tests/

# Code formatting
black src/ tests/

# Type checking
mypy src/ --ignore-missing-imports --allow-untyped-defs --allow-incomplete-defs
```

## 2. Run Tests
Ensure all tests pass:

```bash
# Run unit tests with coverage
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# If tests fail, fix the issues before proceeding
```

## 3. Update Documentation
- Update docstrings if you modified function/class behavior
- Update README.md if you added new features or changed usage
- Update ARCHITECTURE.md if you made architectural changes

## 4. Commit Changes
If explicitly asked to commit:
```bash
# Stage changes
git add -A

# Create descriptive commit message following conventions:
# feat: for new features
# fix: for bug fixes
# refactor: for code refactoring
# test: for test additions/changes
# docs: for documentation updates

git commit -m "feat: implement specific feature (task X.Y)"
```

## 5. Task Master Updates
```bash
# Update task progress
task-master update-subtask --id=<task-id> --prompt="implementation complete, tests passing"

# Mark task as done
task-master set-status --id=<task-id> --status=done

# Check next task
task-master next
```

## 6. Final Verification
Before considering a task complete:
- ✓ All tests pass
- ✓ Code is properly formatted (black)
- ✓ No linting errors (ruff)
- ✓ Type checking passes (mypy)
- ✓ Documentation is updated if needed
- ✓ Task status is updated in Task Master

## Notes
- Never commit if tests are failing
- Always run the quality checks before marking a task as done
- If you encounter blockers, update the task with details before stopping