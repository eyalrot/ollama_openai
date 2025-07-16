# PyPI Authentication Setup

## Issue Resolution for v0.6.4 Release

The v0.6.4 release failed during PyPI publishing due to authentication issues. The error was:
```
403 Invalid or non-existent authentication information
```

## Solution Options

### Option 1: Trusted Publishing (Recommended)
PyPI now supports trusted publishing using OIDC, which eliminates the need for API tokens:

1. Go to your PyPI project: https://pypi.org/project/ollama-openai-proxy/
2. Go to "Settings" → "Publishing"
3. Add a new trusted publisher with these settings:
   - **Owner**: `eyalrot`
   - **Repository name**: `ollama_openai`
   - **Workflow name**: `pypi-publish.yml`
   - **Environment name**: `pypi`

The workflow is already configured to try trusted publishing first (no password required).

### Option 2: API Token (Fallback)
If trusted publishing is not set up, the workflow will fall back to using an API token:

1. Go to PyPI Account Settings: https://pypi.org/manage/account/
2. Generate a new API token with scope limited to the `ollama-openai-proxy` project
3. Copy the token (starts with `pypi-`)
4. Go to GitHub repository settings: https://github.com/eyalrot/ollama_openai/settings/secrets/actions
5. Add/update the secret `PYPI_API_TOKEN` with the token value

## Current Workflow Configuration

The PyPI workflow now attempts both methods:
1. **First**: Try trusted publishing (no authentication required)
2. **Fallback**: If trusted publishing fails, use API token

## Verification

After setting up authentication, trigger a new release to test:
```bash
# Create a new patch release
git tag v0.6.5
git push origin v0.6.5
gh release create v0.6.5 --generate-notes
```

## Troubleshooting

### Common API Token Issues:
- Token doesn't start with `pypi-`
- Token has expired (they expire after 1 year)
- Token scope is incorrect (should be project-scoped)
- Secret name is incorrect (must be `PYPI_API_TOKEN`)

### Trusted Publishing Issues:
- Repository settings don't match exactly
- Workflow name is incorrect
- Environment name doesn't match
- OIDC permissions not configured