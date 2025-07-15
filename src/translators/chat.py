"""
Chat translator for converting between Ollama and OpenAI chat formats.

This module handles the translation of chat completion requests and responses
between Ollama and OpenAI formats for Phase 2 (including tool calling and image support).
"""

import json
from typing import Any, Dict, List, Optional, Union

from src.models import (
    OllamaChatMessage,
    OllamaChatRequest,
    OllamaChatResponse,
    # Ollama models
    OllamaGenerateRequest,
    OllamaGenerateResponse,
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIFunction,
    OpenAIMessage,
    OpenAIStreamResponse,
    OpenAITool,
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

            # Handle tools (Phase 2 feature)
            tools = None
            if isinstance(ollama_request, OllamaChatRequest) and ollama_request.tools:
                tools = self._translate_tools(ollama_request.tools)

            # Build OpenAI request
            openai_request = OpenAIChatRequest(
                model=model,
                messages=messages,
                stream=ollama_request.stream or False,
                tools=tools,
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
            tool_calls = None

            if "choices" in openai_chunk and openai_chunk["choices"]:
                choice = openai_chunk["choices"][0]
                delta = choice.get("delta", {})
                content = delta.get("content", "")
                finish_reason = choice.get("finish_reason")

                # Handle tool calls in streaming (Phase 2 feature)
                if "tool_calls" in delta and delta["tool_calls"]:
                    tool_calls = self._translate_tool_calls(delta["tool_calls"])
                elif "function_call" in delta and delta["function_call"]:
                    tool_calls = self._translate_function_call(delta["function_call"])

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

            # Add tool calls if present (Phase 2 feature)
            if tool_calls:
                response["tool_calls"] = tool_calls

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

    def _translate_tools(self, ollama_tools: List[Dict[str, Any]]) -> List[OpenAITool]:
        """
        Translate Ollama tools format to OpenAI tools format.

        Args:
            ollama_tools: List of Ollama tool definitions

        Returns:
            List of OpenAI tool definitions

        Raises:
            TranslationError: If tool translation fails
        """
        try:
            openai_tools = []
            for tool in ollama_tools:
                if not isinstance(tool, dict):
                    continue

                # Handle both direct function objects and tool wrappers
                if "function" in tool:
                    # Tool is wrapped: {"type": "function", "function": {...}}
                    function_def = tool["function"]
                else:
                    # Tool is direct function definition
                    function_def = tool

                # Create OpenAI function object
                openai_function = OpenAIFunction(
                    name=function_def.get("name", ""),
                    description=function_def.get("description", ""),
                    parameters=function_def.get("parameters", {}),
                )

                # Create OpenAI tool object
                openai_tool = OpenAITool(type="function", function=openai_function)
                openai_tools.append(openai_tool)

            self.logger.debug(
                f"Translated {len(ollama_tools)} tools to OpenAI format",
                extra={"extra_data": {"tool_count": len(openai_tools)}},
            )
            return openai_tools

        except Exception as e:
            self.logger.error(f"Failed to translate tools: {e}")
            raise TranslationError(f"Tool translation failed: {e}")

    def _translate_tool_calls(
        self, openai_tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Translate OpenAI tool calls to Ollama format.

        Args:
            openai_tool_calls: List of OpenAI tool call objects

        Returns:
            List of Ollama tool call objects
        """
        try:
            ollama_tool_calls = []
            for tool_call in openai_tool_calls:
                if not isinstance(tool_call, dict):
                    continue

                ollama_tool_call = {
                    "id": tool_call.get("id", ""),
                    "type": tool_call.get("type", "function"),
                    "function": {
                        "name": tool_call.get("function", {}).get("name", ""),
                        "arguments": tool_call.get("function", {}).get(
                            "arguments", "{}"
                        ),
                    },
                }
                ollama_tool_calls.append(ollama_tool_call)

            self.logger.debug(
                f"Translated {len(openai_tool_calls)} tool calls to Ollama format",
                extra={"extra_data": {"tool_call_count": len(ollama_tool_calls)}},
            )
            return ollama_tool_calls

        except Exception as e:
            self.logger.error(f"Failed to translate tool calls: {e}")
            raise TranslationError(f"Tool call translation failed: {e}")

    def _translate_function_call(
        self, openai_function_call: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Translate OpenAI function call (legacy) to Ollama tool calls format.

        Args:
            openai_function_call: OpenAI function call object

        Returns:
            List with single Ollama tool call object
        """
        try:
            ollama_tool_call = {
                "id": "call_legacy",
                "type": "function",
                "function": {
                    "name": openai_function_call.get("name", ""),
                    "arguments": openai_function_call.get("arguments", "{}"),
                },
            }

            self.logger.debug(
                "Translated legacy function call to Ollama format",
                extra={
                    "extra_data": {
                        "function_name": ollama_tool_call["function"]["name"]
                    }
                },
            )
            return [ollama_tool_call]

        except Exception as e:
            self.logger.error(f"Failed to translate function call: {e}")
            raise TranslationError(f"Function call translation failed: {e}")

    def _convert_message_content(
        self, message: OllamaChatMessage
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Convert Ollama message content to OpenAI multimodal format.

        Args:
            message: Ollama chat message

        Returns:
            Either string content or list of content objects for multimodal

        Raises:
            TranslationError: If content conversion fails
        """
        try:
            # Check if message has images (multimodal)
            if hasattr(message, "images") and message.images:
                # Create multimodal content array
                content_parts = []

                # Add text content if present
                if message.content:
                    content_parts.append({"type": "text", "text": message.content})

                # Add image content
                for image_data in message.images:
                    # Validate base64 image data
                    if not isinstance(image_data, str):
                        self.logger.warning(
                            f"Invalid image data type: {type(image_data)}"
                        )
                        continue

                    # Create image content object
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": self._format_image_url(image_data)},
                    }
                    content_parts.append(image_content)

                self.logger.debug(
                    f"Converted multimodal message with {len(content_parts)} content parts",
                    extra={
                        "extra_data": {
                            "text_parts": 1 if message.content else 0,
                            "image_parts": len(message.images),
                        }
                    },
                )

                return content_parts
            else:
                # Simple text content
                return message.content or ""

        except Exception as e:
            self.logger.error(f"Failed to convert message content: {e}")
            raise TranslationError(f"Message content conversion failed: {e}")

    def _format_image_url(self, image_data: str) -> str:
        """
        Format image data as data URL for OpenAI API.

        Args:
            image_data: Base64 encoded image data

        Returns:
            Formatted data URL
        """
        # If already a data URL, return as-is
        if image_data.startswith("data:"):
            return image_data

        # Assume JPEG by default (common for Ollama)
        # TODO: Add image type detection based on header
        return f"data:image/jpeg;base64,{image_data}"

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
                if role not in ["system", "user", "assistant", "tool"]:
                    # Default unknown roles to 'user'
                    self.logger.warning(f"Unknown role '{role}', defaulting to 'user'")
                    role = "user"

                # Handle multimodal content (Phase 2 feature)
                content = self._convert_message_content(msg)

                # Handle tool calls if present
                tool_calls = None
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls = msg.tool_calls

                messages.append(
                    OpenAIMessage(role=role, content=content, tool_calls=tool_calls)
                )  # type: ignore[call-arg]

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
        tool_calls = None

        if openai_response.choices:
            choice = openai_response.choices[0]
            if choice.message:
                content = choice.message.content or ""  # type: ignore[assignment]

                # Handle tool calls (Phase 2 feature)
                if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                    tool_calls = self._translate_tool_calls(choice.message.tool_calls)
                elif (
                    hasattr(choice.message, "function_call")
                    and choice.message.function_call
                ):
                    # Handle legacy function_call format
                    tool_calls = self._translate_function_call(
                        choice.message.function_call
                    )

            finish_reason = choice.finish_reason or "stop"

        # Build response - use appropriate response type
        if tool_calls:
            # For responses with tool calls, use OllamaChatResponse with message
            message = OllamaChatMessage(
                role="assistant", content=content, tool_calls=tool_calls
            )
            response = OllamaChatResponse(  # type: ignore[call-arg]
                model=self.reverse_map_model_name(openai_response.model),
                created_at=self.get_iso_timestamp(),
                message=message,
                done=True,
                done_reason=finish_reason,
            )
        else:
            # For regular responses, use OllamaGenerateResponse
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
