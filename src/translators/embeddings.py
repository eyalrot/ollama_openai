"""
Embeddings request/response translator between Ollama and OpenAI formats.
"""

from typing import Any, Dict, List, Optional, Union

from src.models import (
    OllamaEmbeddingRequest,
    OllamaEmbeddingResponse,
    OpenAIEmbeddingRequest,
    OpenAIEmbeddingResponse,
)
from src.translators.base import BaseTranslator
from src.utils.exceptions import TranslationError


class EmbeddingsTranslator(
    BaseTranslator[
        OllamaEmbeddingRequest,
        OpenAIEmbeddingRequest,
        OpenAIEmbeddingResponse,
        OllamaEmbeddingResponse,
    ]
):
    """Translator for embeddings between Ollama and OpenAI formats."""

    def translate_request(
        self, ollama_request: OllamaEmbeddingRequest
    ) -> OpenAIEmbeddingRequest:
        """
        Translate Ollama embeddings request to OpenAI format.

        Args:
            ollama_request: The Ollama embedding request

        Returns:
            OpenAI embedding request

        Raises:
            TranslationError: If translation fails
        """
        try:
            # Map model name using base translator functionality
            mapped_model = self.map_model_name(ollama_request.model)

            # Ensure input is always a list for batch processing
            input_data = (
                ollama_request.prompt
                if isinstance(ollama_request.prompt, list)
                else [ollama_request.prompt]
            )

            # Extract any dimensions setting from options if available
            dimensions = None
            if ollama_request.options and hasattr(ollama_request.options, "dimensions"):
                dimensions = ollama_request.options.dimensions

            return OpenAIEmbeddingRequest(
                model=mapped_model,
                input=input_data,
                encoding_format="float",  # Default to float format
                dimensions=dimensions,
                user=None,  # Ollama doesn't have user tracking
            )

        except Exception as e:
            self.handle_translation_error(e, "translate_request")

    def translate_response(
        self,
        openai_response: OpenAIEmbeddingResponse,
        original_request: OllamaEmbeddingRequest,
    ) -> OllamaEmbeddingResponse:
        """
        Translate OpenAI embeddings response to Ollama format.

        Args:
            openai_response: The OpenAI embedding response
            original_request: The original Ollama request for context

        Returns:
            Ollama embedding response

        Raises:
            TranslationError: If translation fails
        """
        try:
            # For single prompt requests, return the first embedding
            # For batch requests, we need to handle this differently
            if not openai_response.data:
                raise TranslationError("OpenAI response contains no embedding data")

            # If original request was a single string, return single embedding
            if isinstance(original_request.prompt, str):
                first_embedding = openai_response.data[0]
                return OllamaEmbeddingResponse(embedding=first_embedding.embedding)

            # For batch requests, return the first embedding (Ollama format doesn't handle batch)
            # In a real implementation, you might want to handle batch differently
            first_embedding = openai_response.data[0]
            return OllamaEmbeddingResponse(embedding=first_embedding.embedding)

        except Exception as e:
            self.handle_translation_error(e, "translate_response")

    def translate_streaming_response(
        self,
        openai_chunk: Dict[str, Any],
        original_request: OllamaEmbeddingRequest,
        is_first_chunk: bool = False,
        is_last_chunk: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Embeddings don't support streaming, so this always returns None.

        Args:
            openai_chunk: The OpenAI streaming chunk (not used)
            original_request: The original request (not used)
            is_first_chunk: Whether this is the first chunk (not used)
            is_last_chunk: Whether this is the last chunk (not used)

        Returns:
            None (embeddings don't stream)
        """
        return None

    def translate_batch_request(
        self, ollama_request: OllamaEmbeddingRequest
    ) -> List[OpenAIEmbeddingRequest]:
        """
        Helper method to split batch requests if needed.

        For now, OpenAI API handles batch embeddings natively,
        so this returns a single request.

        Args:
            ollama_request: The Ollama embedding request

        Returns:
            List containing a single OpenAI request
        """
        return [self.translate_request(ollama_request)]

    def calculate_embedding_tokens(self, text: Union[str, List[str]]) -> int:
        """
        Calculate token usage for embedding text.

        Args:
            text: The text to calculate tokens for

        Returns:
            Estimated token count
        """
        if isinstance(text, list):
            return sum(self.calculate_tokens(t) for t in text)
        return self.calculate_tokens(text)
