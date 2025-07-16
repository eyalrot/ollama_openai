"""
Base translator class for converting between Ollama and OpenAI formats.

This module provides the abstract base class and common functionality
for all request/response translators.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from src.config import get_settings
from src.models import OllamaOptions
from src.utils.exceptions import TranslationError, ValidationError
from src.utils.logging import get_logger

# Type variables for generic translator
OllamaRequestType = TypeVar("OllamaRequestType")
OpenAIRequestType = TypeVar("OpenAIRequestType")
OpenAIResponseType = TypeVar("OpenAIResponseType")
OllamaResponseType = TypeVar("OllamaResponseType")


class BaseTranslator(
    ABC,
    Generic[
        OllamaRequestType, OpenAIRequestType, OpenAIResponseType, OllamaResponseType
    ],
):
    """
    Abstract base class for translating between Ollama and OpenAI formats.

    This class provides common functionality for all translators including:
    - Model name mapping
    - Options extraction and transformation
    - Error handling
    - Logging
    """

    def __init__(self, model_mappings: Optional[Dict[str, str]] = None):
        """
        Initialize the base translator.

        Args:
            model_mappings: Optional dictionary mapping Ollama model names to OpenAI model names
        """
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()

        # Load model mappings from config or use provided ones
        if model_mappings is not None:
            self.model_mappings = model_mappings
        else:
            self.model_mappings = self.settings.load_model_mappings()

        self.logger.debug(
            f"Initialized {self.__class__.__name__} with {len(self.model_mappings)} model mappings"
        )

    @abstractmethod
    def translate_request(self, ollama_request: OllamaRequestType) -> OpenAIRequestType:
        """
        Translate an Ollama request to OpenAI format.

        Args:
            ollama_request: The Ollama format request

        Returns:
            The equivalent OpenAI format request

        Raises:
            TranslationError: If translation fails
            ValidationError: If request validation fails
        """
        pass

    @abstractmethod
    def translate_response(
        self, openai_response: OpenAIResponseType, original_request: OllamaRequestType
    ) -> OllamaResponseType:
        """
        Translate an OpenAI response back to Ollama format.

        Args:
            openai_response: The OpenAI format response
            original_request: The original Ollama request (for context)

        Returns:
            The equivalent Ollama format response

        Raises:
            TranslationError: If translation fails
        """
        pass

    @abstractmethod
    def translate_streaming_response(
        self,
        openai_chunk: Dict[str, Any],
        original_request: OllamaRequestType,
        is_first_chunk: bool = False,
        is_last_chunk: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Translate a streaming response chunk from OpenAI to Ollama format.

        Args:
            openai_chunk: The OpenAI format streaming chunk
            original_request: The original Ollama request
            is_first_chunk: Whether this is the first chunk
            is_last_chunk: Whether this is the last chunk

        Returns:
            The equivalent Ollama format chunk, or None to skip

        Raises:
            TranslationError: If translation fails
        """
        pass

    def map_model_name(self, ollama_model: str) -> str:
        """
        Map an Ollama model name to its OpenAI equivalent.

        Args:
            ollama_model: The Ollama model name

        Returns:
            The mapped OpenAI model name, or the original if no mapping exists
        """
        mapped = self.model_mappings.get(ollama_model, ollama_model)
        if mapped != ollama_model:
            self.logger.debug(f"Mapped model '{ollama_model}' to '{mapped}'")
        return mapped

    def reverse_map_model_name(self, openai_model: str) -> str:
        """
        Reverse map an OpenAI model name back to Ollama format.

        Args:
            openai_model: The OpenAI model name

        Returns:
            The original Ollama model name, or the OpenAI name if no mapping exists
        """
        # Create reverse mapping
        reverse_mappings = {v: k for k, v in self.model_mappings.items()}
        return reverse_mappings.get(openai_model, openai_model)

    def extract_options(
        self, ollama_options: Optional[OllamaOptions]
    ) -> Dict[str, Any]:
        """
        Extract and transform Ollama options to OpenAI parameters.

        Args:
            ollama_options: The Ollama options object

        Returns:
            Dictionary of OpenAI-compatible parameters
        """
        if not ollama_options:
            return {}

        # Convert to dict, excluding None values
        options_dict = ollama_options.model_dump(exclude_none=True)

        # Map Ollama options to OpenAI parameters
        mapping = {
            "temperature": "temperature",
            "top_p": "top_p",
            "top_k": "top_k",  # Note: OpenAI doesn't have top_k
            "num_predict": "max_tokens",
            "stop": "stop",
            "seed": "seed",
            "presence_penalty": "presence_penalty",
            "frequency_penalty": "frequency_penalty",
        }

        result = {}
        for ollama_key, openai_key in mapping.items():
            if ollama_key in options_dict:
                value = options_dict[ollama_key]

                # Special handling for certain parameters
                if ollama_key == "top_k" and openai_key == "top_k":
                    # OpenAI doesn't support top_k, skip it
                    self.logger.debug(
                        f"Skipping unsupported parameter 'top_k': {value}"
                    )
                    continue
                elif ollama_key == "num_predict" and value == 0:
                    # Ollama num_predict=0 means unlimited, which should be None in OpenAI
                    self.logger.debug(
                        "Converting num_predict=0 (unlimited) to max_tokens=None"
                    )
                    continue  # Skip setting max_tokens, leaving it as None

                result[openai_key] = value

        return result

    def extract_ollama_options(self, openai_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract OpenAI parameters and convert to Ollama options.

        Args:
            openai_params: OpenAI request parameters

        Returns:
            Dictionary of Ollama-compatible options
        """
        # Reverse mapping
        mapping = {
            "temperature": "temperature",
            "top_p": "top_p",
            "max_tokens": "num_predict",
            "stop": "stop",
            "seed": "seed",
            "presence_penalty": "presence_penalty",
            "frequency_penalty": "frequency_penalty",
        }

        result = {}
        for openai_key, ollama_key in mapping.items():
            if openai_key in openai_params:
                result[ollama_key] = openai_params[openai_key]

        return result

    def generate_message_id(self) -> str:
        """Generate a unique message ID."""
        return f"msg-{uuid.uuid4().hex[:8]}"

    def generate_request_id(self) -> str:
        """Generate a unique request ID."""
        return f"chatcmpl-{uuid.uuid4().hex[:8]}"

    def get_timestamp(self) -> int:
        """Get current Unix timestamp."""
        return int(datetime.now().timestamp())

    def get_iso_timestamp(self) -> str:
        """Get current ISO format timestamp."""
        return datetime.now().isoformat() + "Z"

    def validate_model_name(self, model: str) -> None:
        """
        Validate that a model name is allowed.

        Args:
            model: The model name to validate

        Raises:
            ValidationError: If the model is not allowed
        """
        # This can be extended with actual validation logic
        if not model:
            raise ValidationError("Model name cannot be empty")

    def calculate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.

        This is a rough approximation. Actual token counting would require
        the specific tokenizer for the model being used.

        Args:
            text: The text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough approximation: ~4 characters per token
        return len(text) // 4

    def handle_translation_error(self, error: Exception, context: str) -> None:
        """
        Handle and log translation errors.

        Args:
            error: The exception that occurred
            context: Context about where the error occurred

        Raises:
            TranslationError: Always raises with enhanced error information
        """
        self.logger.error(
            f"Translation error in {context}: {str(error)}",
            exc_info=error,
            extra={
                "extra_data": {"context": context, "error_type": type(error).__name__}
            },
        )

        if isinstance(error, (TranslationError, ValidationError)):
            raise error

        raise TranslationError(
            f"Failed to translate in {context}: {str(error)}",
            details={"original_error": str(error), "error_type": type(error).__name__},
        )
