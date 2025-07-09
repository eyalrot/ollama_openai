"""
Embeddings request/response translator between Ollama and OpenAI formats.
"""

from typing import Dict, Any
from src.translators.base import BaseTranslator


class EmbeddingsTranslator(BaseTranslator):
    """Translator for embeddings between Ollama and OpenAI formats."""
    
    def translate_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Translate Ollama embeddings request to OpenAI format."""
        # TODO: Implement in later tasks
        return {}
    
    def translate_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Translate OpenAI embeddings response to Ollama format."""
        # TODO: Implement in later tasks
        return {}