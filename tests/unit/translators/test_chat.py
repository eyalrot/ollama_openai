"""
Unit tests for the chat translator.
"""

from typing import Dict, Any, Union
from unittest.mock import Mock, patch, MagicMock
import json
import pytest

from src.translators.chat import ChatTranslator
from src.models import (
    # Ollama models
    OllamaGenerateRequest,
    OllamaChatRequest,
    OllamaChatMessage,
    OllamaGenerateResponse,
    OllamaChatResponse,
    OllamaOptions,
    # OpenAI models
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIStreamResponse,
    OpenAIMessage,
    OpenAIChoice,
    OpenAIStreamChoice,
    OpenAIDelta,
    OpenAIUsage
)
from src.utils.exceptions import TranslationError, ValidationError

# Type aliases (same as in chat.py)
OllamaResponse = Union[OllamaGenerateResponse, OllamaChatResponse]
OllamaStreamResponse = OllamaGenerateResponse


@pytest.fixture
def chat_translator():
    """Create a chat translator instance."""
    mappings = {
        "llama2": "gpt-3.5-turbo",
        "mistral": "gpt-4",
        "codellama": "gpt-3.5-turbo-16k"
    }
    return ChatTranslator(model_mappings=mappings)


@pytest.fixture
def ollama_generate_request():
    """Create a sample Ollama generate request."""
    return OllamaGenerateRequest(
        model="llama2",
        prompt="Hello, how are you?",
        system="You are a helpful assistant.",
        stream=False,
        options=OllamaOptions(
            temperature=0.7,
            top_p=0.9,
            num_predict=100,
            seed=42
        )
    )


@pytest.fixture
def ollama_chat_request():
    """Create a sample Ollama chat request."""
    return OllamaChatRequest(
        model="mistral",
        messages=[
            OllamaChatMessage(role="system", content="You are helpful."),
            OllamaChatMessage(role="user", content="What is Python?"),
            OllamaChatMessage(role="assistant", content="Python is a programming language."),
            OllamaChatMessage(role="user", content="Tell me more.")
        ],
        stream=False,
        options=OllamaOptions(temperature=0.5)
    )


@pytest.fixture
def openai_response():
    """Create a sample OpenAI chat completion response."""
    return OpenAIChatResponse(
        id="chatcmpl-123",
        object="chat.completion",
        created=1234567890,
        model="gpt-3.5-turbo",
        choices=[
            OpenAIChoice(
                index=0,
                message=OpenAIMessage(
                    role="assistant",
                    content="Hello! I'm doing well, thank you."
                ),
                finish_reason="stop"
            )
        ],
        usage=OpenAIUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
    )


@pytest.fixture
def openai_stream_response():
    """Create a sample OpenAI streaming response."""
    return OpenAIStreamResponse(
        id="chatcmpl-123",
        object="chat.completion.chunk",
        created=1234567890,
        model="gpt-4",
        choices=[
            OpenAIStreamChoice(
                index=0,
                delta=OpenAIDelta(content="Hello"),
                finish_reason=None
            )
        ]
    )


class TestChatTranslatorRequestTranslation:
    """Test request translation functionality."""
    
    def test_translate_generate_request(self, chat_translator, ollama_generate_request):
        """Test translating an Ollama generate request to OpenAI format."""
        result = chat_translator.translate_request(ollama_generate_request)
        
        assert isinstance(result, OpenAIChatRequest)
        assert result.model == "gpt-3.5-turbo"  # Mapped from llama2
        assert len(result.messages) == 2  # System + user
        assert result.messages[0].role == "system"
        assert result.messages[0].content == "You are a helpful assistant."
        assert result.messages[1].role == "user"
        assert result.messages[1].content == "Hello, how are you?"
        assert result.stream is False
        assert result.temperature == 0.7
        assert result.top_p == 0.9
        assert result.max_tokens == 100
        assert result.seed == 42
    
    def test_translate_generate_request_no_system(self, chat_translator):
        """Test translating generate request without system prompt."""
        request = OllamaGenerateRequest(
            model="llama2",
            prompt="Just a prompt",
            stream=True
        )
        
        result = chat_translator.translate_request(request)
        
        assert len(result.messages) == 1
        assert result.messages[0].role == "user"
        assert result.messages[0].content == "Just a prompt"
        assert result.stream is True
    
    def test_translate_chat_request(self, chat_translator, ollama_chat_request):
        """Test translating an Ollama chat request to OpenAI format."""
        result = chat_translator.translate_request(ollama_chat_request)
        
        assert isinstance(result, OpenAIChatRequest)
        assert result.model == "gpt-4"  # Mapped from mistral
        assert len(result.messages) == 4
        assert result.messages[0].role == "system"
        assert result.messages[1].role == "user"
        assert result.messages[2].role == "assistant"
        assert result.messages[3].role == "user"
        assert result.temperature == 0.5
    
    def test_translate_request_unknown_role(self, chat_translator):
        """Test handling of unknown message roles."""
        # Create message with a valid role, then modify it
        # since Pydantic validates on creation
        message = OllamaChatMessage(role="user", content="Some content")
        message.__dict__['role'] = "unknown"  # Bypass validation
        
        request = OllamaChatRequest(
            model="llama2",
            messages=[message]
        )
        request.__dict__['_validated'] = True  # Mark as already validated
        
        with patch.object(chat_translator.logger, 'warning') as mock_warning:
            result = chat_translator.translate_request(request)
            
            # Should default to 'user' role
            assert result.messages[0].role == "user"
            mock_warning.assert_called_once()
    
    def test_translate_request_no_model_mapping(self, chat_translator):
        """Test request with unmapped model name."""
        request = OllamaGenerateRequest(
            model="unknown-model",
            prompt="Test"
        )
        
        result = chat_translator.translate_request(request)
        assert result.model == "unknown-model"  # No mapping, use original
    
    def test_validate_request_with_tools(self, chat_translator):
        """Test validation fails for requests with tools (Phase 1 limitation)."""
        request = OllamaChatRequest(
            model="llama2",
            messages=[OllamaChatMessage(role="user", content="Hi")],
            tools=[{"type": "function", "function": {"name": "test"}}]
        )
        
        with pytest.raises(ValidationError) as exc_info:
            chat_translator.translate_request(request)
        
        assert "Tool calling is not supported in Phase 1" in str(exc_info.value)
        assert exc_info.value.details["unsupported_feature"] == "tools"
    
    def test_validate_request_with_images(self, chat_translator):
        """Test validation fails for messages with images (Phase 1 limitation)."""
        # Create a message with images attribute
        message = OllamaChatMessage(role="user", content="Look at this")
        message.images = ["base64data"]
        
        request = OllamaChatRequest(
            model="llama2",
            messages=[message]
        )
        
        with pytest.raises(ValidationError) as exc_info:
            chat_translator.translate_request(request)
        
        assert "Image inputs are not supported in Phase 1" in str(exc_info.value)
        assert exc_info.value.details["unsupported_feature"] == "images"
    
    def test_validate_empty_model_name(self, chat_translator):
        """Test validation fails for empty model name."""
        request = OllamaGenerateRequest(
            model="",
            prompt="Test"
        )
        
        with pytest.raises(ValidationError) as exc_info:
            chat_translator.translate_request(request)
        
        assert "Model name cannot be empty" in str(exc_info.value)


class TestChatTranslatorResponseTranslation:
    """Test response translation functionality."""
    
    def test_translate_non_streaming_response(
        self, chat_translator, openai_response, ollama_generate_request
    ):
        """Test translating non-streaming OpenAI response to Ollama format."""
        result = chat_translator.translate_response(openai_response, ollama_generate_request)
        
        assert isinstance(result, OllamaResponse)
        assert result.model == "llama2"  # Reverse mapped
        assert result.response == "Hello! I'm doing well, thank you."
        assert result.done is True
        assert result.done_reason == "stop"
        assert result.prompt_eval_count == 10
        assert result.eval_count == 20
        assert result.total_duration == int(1e9)
    
    def test_translate_streaming_response(
        self, chat_translator, openai_stream_response, ollama_chat_request
    ):
        """Test translating streaming OpenAI response to Ollama format."""
        result = chat_translator.translate_response(openai_stream_response, ollama_chat_request)
        
        assert isinstance(result, OllamaStreamResponse)
        assert result.model == "mistral"  # Reverse mapped from gpt-4
        assert result.response == "Hello"
        assert result.done is False
    
    def test_translate_streaming_response_with_finish(
        self, chat_translator, ollama_chat_request
    ):
        """Test translating streaming response with finish reason."""
        response = OpenAIStreamResponse(
            id="chatcmpl-123",
            object="chat.completion.chunk",
            created=1234567890,
            model="gpt-4",
            choices=[
                OpenAIStreamChoice(
                    index=0,
                    delta=OpenAIDelta(content=""),
                    finish_reason="stop"
                )
            ]
        )
        
        result = chat_translator.translate_response(response, ollama_chat_request)
        
        assert result.done is True
        assert result.done_reason == "stop"
    
    def test_translate_response_no_choices(
        self, chat_translator, ollama_generate_request
    ):
        """Test handling response with no choices."""
        response = OpenAIChatResponse(
            id="chatcmpl-123",
            object="chat.completion",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[]
        )
        
        result = chat_translator.translate_response(response, ollama_generate_request)
        
        assert result.response == ""
        assert result.done is True
        assert result.done_reason == "stop"
    
    def test_translate_response_no_usage(
        self, chat_translator, ollama_generate_request
    ):
        """Test handling response without usage information."""
        response = OpenAIChatResponse(
            id="chatcmpl-123",
            object="chat.completion",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content="Test"),
                    finish_reason="stop"
                )
            ]
        )
        
        result = chat_translator.translate_response(response, ollama_generate_request)
        
        assert result.response == "Test"
        assert not hasattr(result, 'prompt_eval_count') or result.prompt_eval_count is None
        assert not hasattr(result, 'eval_count') or result.eval_count is None


class TestChatTranslatorStreamingChunks:
    """Test streaming chunk translation."""
    
    def test_translate_streaming_chunk_with_content(
        self, chat_translator, ollama_generate_request
    ):
        """Test translating a streaming chunk with content."""
        chunk = {
            "id": "chatcmpl-123",
            "object": "chat.completion.chunk",
            "created": 1234567890,
            "model": "gpt-3.5-turbo",
            "choices": [{
                "index": 0,
                "delta": {"content": "Hello"},
                "finish_reason": None
            }]
        }
        
        result = chat_translator.translate_streaming_response(
            chunk, ollama_generate_request
        )
        
        assert result is not None
        assert result["model"] == "llama2"
        assert result["response"] == "Hello"
        assert result["done"] is False
    
    def test_translate_streaming_chunk_done(
        self, chat_translator, ollama_generate_request
    ):
        """Test translating the [DONE] streaming chunk."""
        result = chat_translator.translate_streaming_response(
            "[DONE]", ollama_generate_request
        )
        
        assert result is not None
        assert result["response"] == ""
        assert result["done"] is True
        assert result["done_reason"] == "stop"
    
    def test_translate_streaming_chunk_empty(
        self, chat_translator, ollama_generate_request
    ):
        """Test translating empty streaming chunk."""
        result = chat_translator.translate_streaming_response(
            "", ollama_generate_request
        )
        
        assert result is None
    
    def test_translate_streaming_chunk_invalid_json(
        self, chat_translator, ollama_generate_request
    ):
        """Test handling invalid JSON in streaming chunk."""
        with patch.object(chat_translator.logger, 'warning') as mock_warning:
            result = chat_translator.translate_streaming_response(
                "invalid json", ollama_generate_request
            )
            
            assert result is None
            mock_warning.assert_called_once()
    
    def test_translate_streaming_chunk_with_finish(
        self, chat_translator, ollama_generate_request
    ):
        """Test translating chunk with finish reason."""
        chunk = {
            "choices": [{
                "delta": {},
                "finish_reason": "stop"
            }]
        }
        
        result = chat_translator.translate_streaming_response(
            chunk, ollama_generate_request
        )
        
        assert result["done"] is True
        assert result["done_reason"] == "stop"
    
    def test_translate_streaming_chunk_json_string(
        self, chat_translator, ollama_generate_request
    ):
        """Test translating JSON string chunk."""
        chunk_data = {
            "model": "gpt-3.5-turbo",
            "choices": [{
                "delta": {"content": "Test"},
                "finish_reason": None
            }]
        }
        chunk_str = json.dumps(chunk_data)
        
        result = chat_translator.translate_streaming_response(
            chunk_str, ollama_generate_request
        )
        
        assert result is not None
        assert result["response"] == "Test"
        assert result["model"] == "llama2"


class TestChatTranslatorErrorHandling:
    """Test error handling in the translator."""
    
    def test_translate_request_generic_error(self, chat_translator):
        """Test generic error handling in request translation."""
        request = Mock()
        request.model = "test"
        request.side_effect = ValueError("Test error")
        
        with pytest.raises(TranslationError) as exc_info:
            chat_translator.translate_request(request)
        
        assert "Failed to translate in translate_request" in str(exc_info.value)
    
    def test_translate_response_generic_error(self, chat_translator):
        """Test generic error handling in response translation."""
        response = Mock()
        response.side_effect = ValueError("Test error")
        request = Mock()
        
        with pytest.raises(TranslationError) as exc_info:
            chat_translator.translate_response(response, request)
        
        assert "Failed to translate in translate_response" in str(exc_info.value)
    
    def test_translate_streaming_chunk_error(self, chat_translator):
        """Test error handling in streaming chunk translation."""
        chunk = Mock()
        chunk.side_effect = ValueError("Test error")
        request = Mock()
        
        with pytest.raises(TranslationError) as exc_info:
            chat_translator.translate_streaming_response(chunk, request)
        
        assert "Failed to translate in translate_streaming_response" in str(exc_info.value)


class TestChatTranslatorIntegration:
    """Integration tests for the chat translator."""
    
    def test_full_generate_flow(self, chat_translator):
        """Test complete generate request/response flow."""
        # Create generate request
        request = OllamaGenerateRequest(
            model="llama2",
            prompt="Explain quantum computing",
            system="You are a physics teacher.",
            options=OllamaOptions(
                temperature=0.8,
                num_predict=200
            )
        )
        
        # Translate to OpenAI format
        openai_request = chat_translator.translate_request(request)
        
        assert openai_request.model == "gpt-3.5-turbo"
        assert len(openai_request.messages) == 2
        assert openai_request.temperature == 0.8
        assert openai_request.max_tokens == 200
        
        # Simulate OpenAI response
        openai_response = OpenAIChatResponse(
            id="chatcmpl-123",
            object="chat.completion",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(
                        role="assistant",
                        content="Quantum computing uses quantum mechanics..."
                    ),
                    finish_reason="stop"
                )
            ],
            usage=OpenAIUsage(
                prompt_tokens=15,
                completion_tokens=25,
                total_tokens=40
            )
        )
        
        # Translate back to Ollama format
        ollama_response = chat_translator.translate_response(openai_response, request)
        
        assert ollama_response.model == "llama2"
        assert ollama_response.response == "Quantum computing uses quantum mechanics..."
        assert ollama_response.done is True
        assert ollama_response.prompt_eval_count == 15
        assert ollama_response.eval_count == 25
    
    def test_full_chat_streaming_flow(self, chat_translator):
        """Test complete chat streaming request/response flow."""
        # Create chat request
        request = OllamaChatRequest(
            model="mistral",
            messages=[
                OllamaChatMessage(role="user", content="Hello AI")
            ],
            stream=True
        )
        
        # Translate to OpenAI format
        openai_request = chat_translator.translate_request(request)
        
        assert openai_request.model == "gpt-4"
        assert openai_request.stream is True
        
        # Simulate streaming chunks
        chunks = [
            {"choices": [{"delta": {"content": "Hello"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": " there"}, "finish_reason": None}]},
            {"choices": [{"delta": {"content": "!"}, "finish_reason": None}]},
            {"choices": [{"delta": {}, "finish_reason": "stop"}]}
        ]
        
        responses = []
        for i, chunk in enumerate(chunks):
            chunk["model"] = "gpt-4"
            result = chat_translator.translate_streaming_response(
                chunk, 
                request,
                is_first_chunk=(i == 0),
                is_last_chunk=(i == len(chunks) - 1)
            )
            if result:
                responses.append(result)
        
        # Check responses
        assert len(responses) == 4
        assert responses[0]["response"] == "Hello"
        assert responses[1]["response"] == " there"
        assert responses[2]["response"] == "!"
        assert responses[3]["done"] is True
        assert all(r["model"] == "mistral" for r in responses)