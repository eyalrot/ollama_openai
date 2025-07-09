"""
Base translator class for request/response translation.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Dict, Any, Optional

# Generic types for input/output
TInput = TypeVar("TInput")
TOutput = TypeVar("TOutput")


class BaseTranslator(ABC, Generic[TInput, TOutput]):
    """Abstract base class for translators between Ollama and OpenAI formats."""

    def __init__(self, model_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize translator with optional model mapping.

        Args:
            model_mapping: Dictionary mapping Ollama model names to OpenAI model names
        """
        self.model_mapping = model_mapping or {}

    @abstractmethod
    def translate_request(self, request: TInput) -> TOutput:
        """
        Translate a request from one format to another.

        Args:
            request: The input request object

        Returns:
            The translated output request object
        """
        pass

    @abstractmethod
    def translate_response(self, response: Any) -> Any:
        """
        Translate a response from one format to another.

        Args:
            response: The input response object

        Returns:
            The translated output response object
        """
        pass

    def map_model_name(self, model_name: str) -> str:
        """
        Map a model name using the configured mapping.

        Args:
            model_name: The input model name

        Returns:
            The mapped model name, or the original if no mapping exists
        """
        return self.model_mapping.get(model_name, model_name)

    def extract_options(self, options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract and transform options between formats.

        Args:
            options: The input options dictionary

        Returns:
            The transformed options dictionary
        """
        if not options:
            return {}

        # Common option mappings
        transformed = {}

        if "temperature" in options:
            transformed["temperature"] = options["temperature"]
        if "top_p" in options:
            transformed["top_p"] = options["top_p"]
        if "top_k" in options:
            transformed["top_k"] = options["top_k"]
        if "num_predict" in options:
            transformed["max_tokens"] = options["num_predict"]
        if "stop" in options:
            transformed["stop"] = options["stop"]

        return transformed
