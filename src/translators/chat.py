"""
Chat translator for converting between Ollama and OpenAI chat formats.

This module handles the translation of chat completion requests and responses
between Ollama and OpenAI formats for Phase 1 (text-only support).
"""

import json
from typing import Any, Dict, List, Optional, Union

from src.models import (
    OllamaChatRequest,
    OllamaChatResponse,
    # Ollama models
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIMessage,
    OpenAIStreamResponse,
)
from src.translators.base import BaseTranslator
from src.utils.exceptions import TranslationError, ValidationError
from src.utils.logging import get_logger

# Type aliases for clarity
OllamaResponse = Union[OllamaGenerateResponse, OllamaChatResponse]
OllamaStreamResponse = OllamaGenerateResponse  # They use the same format for streaming


class ChatTranslator(
    BaseTranslator[
        Union[OllamaGenerateRequest, OllamaChatRequest],
        OpenAIChatRequest,
        Union[OpenAIChatResponse, OpenAIStreamResponse],
        Union[OllamaResponse, OllamaStreamResponse],
    ]
):
    """
    Translator for chat completion requests and responses.

    Handles conversion between Ollama's generate/chat formats and
    OpenAI's chat completion format. Phase 1 supports text-only.
    """

    def __init__(self, model_mappings: Optional[Dict[str, str]] = None):
        """Initialize the chat translator."""
        super().__init__(model_mappings)
        self.logger = get_logger(__name__)

    def translate_request(
        self, ollama_request: Union[OllamaGenerateRequest, OllamaChatRequest]
    ) -> OpenAIChatRequest:
        """
        Translate Ollama request to OpenAI chat completion format.

        Args:
            ollama_request: Either a generate or chat request from Ollama

        Returns:
            OpenAI chat completion request

        Raises:
            TranslationError: If translation fails
            ValidationError: If request contains unsupported features
        """
        try:
            # Validate request
            self._validate_ollama_request(ollama_request)

            # Convert to messages format
            messages = self._convert_to_messages(ollama_request)

            # Map model name
            model = self.map_model_name(ollama_request.model)

            # Extract options
            options = {}
            if ollama_request.options:
                options = self.extract_options(ollama_request.options)

            # Build OpenAI request
            openai_request = OpenAIChatRequest(
                model=model,
                messages=messages,
                stream=ollama_request.stream or False,
                **options,
            )

            self.logger.debug(
                "Translated Ollama request to OpenAI format",
                extra={
                    "extra_data": {
                        "model": model,
                        "message_count": len(messages),
                        "stream": openai_request.stream,
                    }
                },
            )

            return openai_request

        except (TranslationError, ValidationError):
            raise
        except Exception as e:
            self.handle_translation_error(e, "translate_request")
            raise  # Re-raise the error after handling

    def translate_response(
        self,
        openai_response: Union[OpenAIChatResponse, OpenAIStreamResponse],
        original_request: Union[OllamaGenerateRequest, OllamaChatRequest],
    ) -> Union[OllamaResponse, OllamaStreamResponse]:
        """
        Translate OpenAI response back to Ollama format.

        Args:
            openai_response: OpenAI chat completion response
            original_request: The original Ollama request for context

        Returns:
            Ollama format response

        Raises:
            TranslationError: If translation fails
        """
        try:
            # Handle streaming response
            if isinstance(openai_response, OpenAIStreamResponse):
                return self._translate_streaming_response(
                    openai_response, original_request
                )

            # Handle non-streaming response
            return self._translate_non_streaming_response(
                openai_response, original_request
            )

        except TranslationError:
            raise
        except Exception as e:
            self.handle_translation_error(e, "translate_response")
            raise  # Re-raise the error after handling

    def translate_streaming_response(
        self,
        openai_chunk: Dict[str, Any],
        original_request: Union[OllamaGenerateRequest, OllamaChatRequest],
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
        try:
            # Parse the chunk if it's a string (SSE data)
            if isinstance(openai_chunk, str):
                if openai_chunk.strip() == "[DONE]":
                    # Final chunk - return done response
                    return {
                        "model": original_request.model,
                        "created_at": self.get_iso_timestamp(),
                        "response": "",
                        "done": True,
                        "done_reason": "stop",
                    }

                # Skip empty chunks
                if not openai_chunk.strip():
                    return None

                # Parse JSON chunk
                try:
                    openai_chunk = json.loads(openai_chunk)
                except json.JSONDecodeError:
                    self.logger.warning(
                        f"Failed to parse streaming chunk: {openai_chunk}"
                    )
                    return None

            # Extract content from delta
            content = ""
            finish_reason = None

            if "choices" in openai_chunk and openai_chunk["choices"]:
                choice = openai_chunk["choices"][0]
                delta = choice.get("delta", {})
                content = delta.get("content", "")
                finish_reason = choice.get("finish_reason")

            # Build Ollama streaming response
            response = {
                "model": self.reverse_map_model_name(
                    openai_chunk.get("model", original_request.model)
                ),
                "created_at": self.get_iso_timestamp(),
                "response": content,
                "done": finish_reason is not None,
            }

            # Add finish reason if present
            if finish_reason:
                response["done_reason"] = finish_reason

            return response

        except Exception as e:
            self.handle_translation_error(e, "translate_streaming_response")
            raise  # Re-raise the error after handling

    def _validate_ollama_request(
        self, request: Union[OllamaGenerateRequest, OllamaChatRequest]
    ) -> None:
        """
        Validate Ollama request for Phase 2 support.

        Args:
            request: The Ollama request to validate

        Raises:
            ValidationError: If request contains invalid data
        """
        # Validate model name
        self.validate_model_name(request.model)

    def _convert_to_messages(
        self, request: Union[OllamaGenerateRequest, OllamaChatRequest]
    ) -> List[OpenAIMessage]:
        """
        Convert Ollama request to OpenAI message format.

        Args:
            request: Ollama request (generate or chat)

        Returns:
            List of OpenAI format messages
        """
        messages = []

        if isinstance(request, OllamaGenerateRequest):
            # For generate requests, create a single user message
            if request.system:
                messages.append(OpenAIMessage(role="system", content=request.system))  # type: ignore[call-arg]

            # Add the prompt as a user message
            messages.append(OpenAIMessage(role="user", content=request.prompt))  # type: ignore[call-arg]

        else:  # OllamaChatRequest
            # Convert each message
            for msg in request.messages or []:
                # Map Ollama roles to OpenAI roles
                role = msg.role
                if role not in ["system", "user", "assistant"]:
                    # Default unknown roles to 'user'
                    self.logger.warning(f"Unknown role '{role}', defaulting to 'user'")
                    role = "user"

                messages.append(OpenAIMessage(role=role, content=msg.content))  # type: ignore[call-arg]

        return messages

    def _translate_streaming_response(
        self,
        openai_response: OpenAIStreamResponse,
        original_request: Union[OllamaGenerateRequest, OllamaChatRequest],
    ) -> OllamaStreamResponse:
        """
        Translate streaming OpenAI response to Ollama format.

        Args:
            openai_response: OpenAI streaming response
            original_request: Original Ollama request

        Returns:
            Ollama streaming response
        """
        # Extract content from the first choice
        content = ""
        finish_reason = None

        if openai_response.choices:
            choice = openai_response.choices[0]
            if choice.delta and choice.delta.content:
                content = choice.delta.content
            finish_reason = choice.finish_reason

        # Build streaming response - use OllamaGenerateResponse for streaming
        response = OllamaGenerateResponse(  # type: ignore[call-arg]
            model=self.reverse_map_model_name(openai_response.model),
            created_at=self.get_iso_timestamp(),
            response=content,
            done=finish_reason is not None,
        )

        # Add finish reason if present
        if finish_reason:
            response.done_reason = finish_reason

        return response

    def _translate_non_streaming_response(
        self,
        openai_response: OpenAIChatResponse,
        original_request: Union[OllamaGenerateRequest, OllamaChatRequest],
    ) -> OllamaResponse:
        """
        Translate non-streaming OpenAI response to Ollama format.

        Args:
            openai_response: OpenAI chat completion response
            original_request: Original Ollama request

        Returns:
            Ollama response
        """
        # Extract content from the first choice
        content = ""
        finish_reason = "stop"

        if openai_response.choices:
            choice = openai_response.choices[0]
            if choice.message:
                content = choice.message.content or ""  # type: ignore[assignment]
            finish_reason = choice.finish_reason or "stop"

        # Build response - use OllamaGenerateResponse which matches Ollama's generate API
        response = OllamaGenerateResponse(  # type: ignore[call-arg]
            model=self.reverse_map_model_name(openai_response.model),
            created_at=self.get_iso_timestamp(),
            response=content,
            done=True,
            done_reason=finish_reason,
        )

        # Add token usage if available
        if openai_response.usage:
            response.prompt_eval_count = openai_response.usage.prompt_tokens
            response.eval_count = openai_response.usage.completion_tokens

            # Calculate duration (approximate)
            response.total_duration = int(1e9)  # 1 second in nanoseconds
            response.prompt_eval_duration = int(0.5e9)  # 0.5 seconds
            response.eval_duration = int(0.5e9)  # 0.5 seconds

        return response
