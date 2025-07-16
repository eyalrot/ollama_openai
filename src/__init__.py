"""
Ollama-OpenAI Proxy Service

A transparent proxy service that allows applications to use both Ollama and OpenAI API
formats seamlessly with OpenAI-compatible LLM servers.
"""

from ._version import __version__, get_version, get_version_info

__all__ = ["__version__", "get_version", "get_version_info"]
