# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.9] - 2025-07-21

### Added
- **New `/api/embed` endpoint**: Added support for Ollama SDK's new `embed()` method
  - Created `OllamaEmbedRequest` model to handle the new format
  - Maps 'input' field from new format to existing embedding logic
  - Returns response in new format: `{"embeddings": [[...]], "model": "..."}`

### Fixed
- **Ollama SDK compatibility**: Fixed show model validation to accept both 'name' and 'model' fields
  - Modified `OllamaShowRequest` to support both field names
  - Added model validator for backwards compatibility
  - Enables Ollama SDK's `client.show()` method to work without errors

### Changed
- Updated version to 0.6.9 to reflect Ollama SDK compatibility improvements

## [0.6.8] - 2025-07-17

### Fixed
- Docker Hub authentication and token management improvements
- Enhanced token handling for Docker image publishing

## [0.6.7] - 2025-07-17

### Fixed
- Enable version tags for Docker images on release
- Improved Docker image tagging strategy

## [0.6.6] - 2025-07-17

### Fixed
- All failing tests and enhanced development infrastructure
- Improved test reliability and coverage

### Added
- Enhanced Docker Compose integration with auto-detection
- New Docker Compose configurations for easier deployment

## [0.6.5] - 2025-07-17

### Fixed
- Improve PyPI authentication with trusted publishing support
- Enhanced release pipeline reliability

## [0.6.0] - 2025-07-16

### Added
- **Version Management System**: Complete version management with centralized control
- **Version API Endpoint**: `/v1/version` endpoint providing detailed service information
- **Health Check Endpoint**: `/v1/health` for service monitoring and uptime checks
- **Enhanced Release Pipeline**: Automated Docker image building and publishing
- **GitHub Releases**: Automated release notes and GitHub release creation
- **Multi-Architecture Support**: Docker images for linux/amd64 and linux/arm64

### Changed
- **Dynamic Versioning**: Moved from static version in `pyproject.toml` to dynamic versioning
- **Startup Logging**: Enhanced with detailed version and build information
- **Docker Tagging**: Improved tagging strategy with version, major.minor, and latest tags
- **Release Process**: Streamlined release workflow with semantic versioning

### Technical Improvements
- **Code Quality**: Fixed flake8 issues including unused imports and variables
- **Formatting**: Applied consistent black code formatting across codebase
- **CI/CD**: Enhanced continuous integration with better codecov integration
- **Documentation**: Updated architecture documentation to reflect v2.1 changes

### Infrastructure
- **Docker Publishing**: Automated multi-architecture Docker image publishing to GHCR
- **Version Control**: Centralized version management with `src/_version.py`
- **API Versioning**: Consistent API versioning strategy across all endpoints
- **Monitoring**: Enhanced service monitoring with version and health endpoints
- **Container Registry**: Migrated to GitHub Container Registry (ghcr.io)

## [2.1.0] - 2025-07-10 (Previous Architecture Version)

### Added
- **Dual API Format Support**: Full support for both Ollama and OpenAI API formats
- **Path-based Routing**: Automatic detection and routing based on URL path patterns
- **Request Body Caching**: Middleware-level caching for dual-format endpoint support
- **Pass-through Optimization**: Minimal processing overhead for OpenAI requests

### Changed
- **Enhanced Architecture**: Now supports both Ollama and OpenAI simultaneously
- **Request Handling**: Improved request body handling for dual-format support
- **Performance**: Optimized for sub-second response times across all endpoints

### Fixed
- **Embeddings Support**: Fixed OpenAI usage field compatibility for embeddings
- **Hanging Issues**: Resolved request hanging problems with proper body caching
- **JSON Parsing**: Fixed JSON parsing errors in curl commands and API responses

## [1.0.0] - 2025-07-01 (Initial Release)

### Added
- **Complete Ollama API Compatibility**: Full support for Ollama Python SDK
- **OpenAI Backend Integration**: Seamless integration with OpenAI-compatible servers
- **Translation Layer**: Robust translation between Ollama and OpenAI formats
- **Streaming Support**: Full streaming support for chat and generation endpoints
- **Model Management**: Dynamic model listing and information retrieval
- **Comprehensive Monitoring**: 28+ metrics across 4 categories
- **Docker Support**: Production-ready Docker containers
- **CI/CD Pipeline**: Complete GitHub Actions workflow

### Features
- **Chat Endpoints**: `/api/chat` and `/v1/chat/completions`
- **Generation Endpoints**: `/api/generate` for text generation
- **Embeddings Endpoints**: `/api/embeddings` and `/v1/embeddings`
- **Model Endpoints**: `/api/tags`, `/api/show` for model management
- **Metrics Endpoints**: Comprehensive monitoring and metrics collection

### Technical Foundation
- **FastAPI Framework**: High-performance async API framework
- **Pydantic V2**: Type-safe data validation and serialization
- **Structured Logging**: JSON-formatted logging with request correlation
- **Error Handling**: Comprehensive error handling and recovery
- **Security**: OWASP-compliant security practices
- **Performance**: Sub-10ms translation overhead, 1000+ req/sec throughput

---

## Release Process

### Creating a New Release

1. **Update Version**: Edit `src/_version.py` with new version number
2. **Update Changelog**: Add release notes to this file
3. **Commit Changes**: `git commit -m "bump: version X.Y.Z"`
4. **Create Tag**: `git tag vX.Y.Z`
5. **Push**: `git push origin master && git push origin vX.Y.Z`
6. **Automated Release**: CI will automatically build and publish Docker images

### Docker Images

Each release publishes Docker images with the following tags:
- `eyalrot2/ollama-openai-proxy:X.Y.Z` (specific version)
- `eyalrot2/ollama-openai-proxy:X.Y` (major.minor)
- `eyalrot2/ollama-openai-proxy:latest` (latest stable)

### Version Scheme

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes, API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, minor improvements