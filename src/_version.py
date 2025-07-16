"""
Version management for Ollama-OpenAI Proxy.

This module provides centralized version information for the application.
"""

__version__ = "0.6.3"
__version_info__ = tuple(int(part) for part in __version__.split("."))

# Build and release information
BUILD_DATE = "2025-07-16"
COMMIT_SHA = "TBD"  # Will be populated by CI/CD

# Version metadata
VERSION_MAJOR = __version_info__[0]
VERSION_MINOR = __version_info__[1]
VERSION_PATCH = __version_info__[2]

# API version (for API compatibility)
API_VERSION = "v1"

# Project information
PROJECT_NAME = "Ollama-OpenAI Proxy"
PROJECT_DESCRIPTION = (
    "A proxy service that translates between Ollama and OpenAI API formats"
)
PROJECT_URL = "https://github.com/eyalrot/ollama_openai"


def get_version() -> str:
    """Get the current version string."""
    return __version__


def get_version_info() -> dict:
    """Get detailed version information."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "major": VERSION_MAJOR,
        "minor": VERSION_MINOR,
        "patch": VERSION_PATCH,
        "build_date": BUILD_DATE,
        "commit_sha": COMMIT_SHA,
        "api_version": API_VERSION,
        "project_name": PROJECT_NAME,
        "project_description": PROJECT_DESCRIPTION,
        "project_url": PROJECT_URL,
    }


def get_short_version() -> str:
    """Get a short version string for display."""
    return f"v{__version__}"


def is_development_version() -> bool:
    """Check if this is a development version."""
    return (
        "dev" in __version__
        or "rc" in __version__
        or "alpha" in __version__
        or "beta" in __version__
    )
