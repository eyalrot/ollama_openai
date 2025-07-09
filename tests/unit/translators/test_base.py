"""
Unit tests for the base translator class.
"""

from typing import Dict, Any, Optional
from unittest.mock import patch
from datetime import datetime

import pytest

from src.translators.base import BaseTranslator
from src.utils.exceptions import TranslationError, ValidationError
from src.models import OllamaOptions


@pytest.fixture
def mock_settings():
    """Mock settings for tests."""
    with patch("src.translators.base.get_settings") as mock:
        mock.return_value.load_model_mappings.return_value = {}
        yield mock


# Concrete implementation for testing
class ConcreteTranslator(
    BaseTranslator[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]
):
    """Concrete translator for testing."""

    def translate_request(self, ollama_request: Dict[str, Any]) -> Dict[str, Any]:
        """Test implementation of translate_request."""
        return {
            "translated": True,
            "model": self.map_model_name(ollama_request.get("model", "")),
        }

    def translate_response(
        self, openai_response: Dict[str, Any], original_request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test implementation of translate_response."""
        return {"response": True, "original_model": original_request.get("model")}

    def translate_streaming_response(
        self,
        openai_chunk: Dict[str, Any],
        original_request: Dict[str, Any],
        is_first_chunk: bool = False,
        is_last_chunk: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """Test implementation of translate_streaming_response."""
        if openai_chunk.get("skip"):
            return None
        return {"chunk": True, "first": is_first_chunk, "last": is_last_chunk}


class TestBaseTranslator:
    """Test the BaseTranslator abstract class."""

    def test_initialization_with_mappings(self):
        """Test translator initialization with custom model mappings."""
        mappings = {"llama2": "gpt-3.5-turbo", "codellama": "gpt-4"}
        translator = ConcreteTranslator(model_mappings=mappings)

        assert translator.model_mappings == mappings
        assert hasattr(translator, "logger")
        assert hasattr(translator, "settings")

    def test_initialization_from_config(self):
        """Test translator initialization with mappings from config."""
        with patch("src.translators.base.get_settings") as mock_settings:
            mock_settings.return_value.load_model_mappings.return_value = {
                "mistral": "gpt-3.5-turbo"
            }
            translator = ConcreteTranslator()

            assert translator.model_mappings == {"mistral": "gpt-3.5-turbo"}

    def test_initialization_no_mappings(self):
        """Test translator initialization with no mappings."""
        with patch("src.translators.base.get_settings") as mock_settings:
            mock_settings.return_value.load_model_mappings.return_value = {}
            translator = ConcreteTranslator()

            assert translator.model_mappings == {}

    def test_map_model_name(self):
        """Test model name mapping."""
        mappings = {"llama2": "gpt-3.5-turbo", "codellama": "gpt-4"}
        translator = ConcreteTranslator(model_mappings=mappings)

        # Test existing mapping
        assert translator.map_model_name("llama2") == "gpt-3.5-turbo"
        assert translator.map_model_name("codellama") == "gpt-4"

        # Test no mapping (returns original)
        assert translator.map_model_name("unknown-model") == "unknown-model"

    def test_reverse_map_model_name(self):
        """Test reverse model name mapping."""
        mappings = {"llama2": "gpt-3.5-turbo", "codellama": "gpt-4"}
        translator = ConcreteTranslator(model_mappings=mappings)

        # Test reverse mapping
        assert translator.reverse_map_model_name("gpt-3.5-turbo") == "llama2"
        assert translator.reverse_map_model_name("gpt-4") == "codellama"

        # Test no mapping (returns original)
        assert translator.reverse_map_model_name("claude-2") == "claude-2"

    @patch("src.translators.base.get_settings")
    def test_extract_options_with_ollama_options(self, mock_settings):
        """Test extracting options from OllamaOptions object."""
        mock_settings.return_value.load_model_mappings.return_value = {}
        translator = ConcreteTranslator()

        options = OllamaOptions(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            num_predict=100,
            stop=["\\n", "###"],
            seed=42,
            presence_penalty=0.1,
            frequency_penalty=0.2,
        )

        result = translator.extract_options(options)

        assert result["temperature"] == 0.7
        assert result["top_p"] == 0.9
        assert "top_k" not in result  # Should be skipped
        assert result["max_tokens"] == 100
        assert result["stop"] == ["\\n", "###"]
        assert result["seed"] == 42
        assert result["presence_penalty"] == 0.1
        assert result["frequency_penalty"] == 0.2

    def test_extract_options_none(self):
        """Test extracting options with None input."""
        translator = ConcreteTranslator()
        result = translator.extract_options(None)
        assert result == {}

    def test_extract_options_empty(self):
        """Test extracting options with empty OllamaOptions."""
        translator = ConcreteTranslator()
        options = OllamaOptions()
        result = translator.extract_options(options)
        assert result == {}

    def test_extract_ollama_options(self):
        """Test extracting OpenAI params to Ollama options."""
        translator = ConcreteTranslator()

        openai_params = {
            "temperature": 0.8,
            "top_p": 0.95,
            "max_tokens": 200,
            "stop": ["END"],
            "seed": 123,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.3,
            "other_param": "ignored",
        }

        result = translator.extract_ollama_options(openai_params)

        assert result["temperature"] == 0.8
        assert result["top_p"] == 0.95
        assert result["num_predict"] == 200
        assert result["stop"] == ["END"]
        assert result["seed"] == 123
        assert result["presence_penalty"] == 0.5
        assert result["frequency_penalty"] == 0.3
        assert "other_param" not in result

    def test_generate_message_id(self):
        """Test message ID generation."""
        translator = ConcreteTranslator()

        msg_id = translator.generate_message_id()
        assert msg_id.startswith("msg-")
        assert len(msg_id) == 12  # "msg-" + 8 hex chars

        # Test uniqueness
        msg_id2 = translator.generate_message_id()
        assert msg_id != msg_id2

    def test_generate_request_id(self):
        """Test request ID generation."""
        translator = ConcreteTranslator()

        req_id = translator.generate_request_id()
        assert req_id.startswith("chatcmpl-")
        assert len(req_id) == 17  # "chatcmpl-" + 8 hex chars

        # Test uniqueness
        req_id2 = translator.generate_request_id()
        assert req_id != req_id2

    def test_get_timestamp(self):
        """Test Unix timestamp generation."""
        translator = ConcreteTranslator()

        before = int(datetime.now().timestamp())
        timestamp = translator.get_timestamp()
        after = int(datetime.now().timestamp())

        assert before <= timestamp <= after
        assert isinstance(timestamp, int)

    def test_get_iso_timestamp(self):
        """Test ISO timestamp generation."""
        translator = ConcreteTranslator()

        timestamp = translator.get_iso_timestamp()
        assert timestamp.endswith("Z")
        assert "T" in timestamp

        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(timestamp[:-1])  # Remove 'Z' for parsing

    def test_validate_model_name_valid(self):
        """Test model name validation with valid name."""
        translator = ConcreteTranslator()

        # Should not raise
        translator.validate_model_name("gpt-3.5-turbo")
        translator.validate_model_name("llama2")

    def test_validate_model_name_empty(self):
        """Test model name validation with empty name."""
        translator = ConcreteTranslator()

        with pytest.raises(ValidationError) as exc_info:
            translator.validate_model_name("")
        assert "Model name cannot be empty" in str(exc_info.value)

    def test_calculate_tokens(self):
        """Test token calculation estimation."""
        translator = ConcreteTranslator()

        # Test various text lengths
        assert translator.calculate_tokens("") == 0
        assert translator.calculate_tokens("test") == 1  # 4 chars / 4
        assert translator.calculate_tokens("Hello, world!") == 3  # 13 chars / 4
        assert translator.calculate_tokens("a" * 100) == 25  # 100 chars / 4

    def test_handle_translation_error_with_custom_errors(self):
        """Test error handling with custom exception types."""
        translator = ConcreteTranslator()

        # Test with TranslationError
        trans_error = TranslationError("Translation failed")
        with pytest.raises(TranslationError) as exc_info:
            translator.handle_translation_error(trans_error, "test_context")
        assert exc_info.value == trans_error

        # Test with ValidationError
        val_error = ValidationError("Validation failed")
        with pytest.raises(ValidationError) as exc_info:
            translator.handle_translation_error(val_error, "test_context")
        assert exc_info.value == val_error

    def test_handle_translation_error_with_generic_error(self):
        """Test error handling with generic exception."""
        translator = ConcreteTranslator()

        generic_error = ValueError("Something went wrong")
        with pytest.raises(TranslationError) as exc_info:
            translator.handle_translation_error(generic_error, "test_context")

        error = exc_info.value
        assert "Failed to translate in test_context" in str(error)
        assert error.details["original_error"] == "Something went wrong"
        assert error.details["error_type"] == "ValueError"

    def test_abstract_methods_not_implemented(self):
        """Test that abstract methods must be implemented."""
        # Can't instantiate abstract class directly
        with pytest.raises(TypeError):
            BaseTranslator()

    def test_concrete_implementation(self):
        """Test the concrete implementation works correctly."""
        translator = ConcreteTranslator(model_mappings={"llama2": "gpt-3.5-turbo"})

        # Test translate_request
        request = {"model": "llama2", "prompt": "Hello"}
        result = translator.translate_request(request)
        assert result["translated"] is True
        assert result["model"] == "gpt-3.5-turbo"

        # Test translate_response
        response = {"result": "data"}
        original = {"model": "llama2"}
        result = translator.translate_response(response, original)
        assert result["response"] is True
        assert result["original_model"] == "llama2"

        # Test translate_streaming_response
        chunk = {"data": "chunk"}
        result = translator.translate_streaming_response(chunk, original, True, False)
        assert result["chunk"] is True
        assert result["first"] is True
        assert result["last"] is False

        # Test skip chunk
        skip_chunk = {"skip": True}
        result = translator.translate_streaming_response(skip_chunk, original)
        assert result is None


class TestIntegration:
    """Integration tests for BaseTranslator."""

    def test_full_translation_flow(self):
        """Test a complete translation flow."""
        mappings = {"llama2:7b": "gpt-3.5-turbo-0613"}
        translator = ConcreteTranslator(model_mappings=mappings)

        # Create Ollama request with options
        ollama_options = OllamaOptions(
            temperature=0.7,
            num_predict=100,
            top_k=40,  # Should be skipped
            seed=42,
        )

        # Simulate request translation
        ollama_request = {"model": "llama2:7b", "options": ollama_options}
        openai_request = translator.translate_request(ollama_request)

        # Verify model mapping worked
        assert openai_request["model"] == "gpt-3.5-turbo-0613"

        # Extract options
        extracted_options = translator.extract_options(ollama_options)
        assert extracted_options["temperature"] == 0.7
        assert extracted_options["max_tokens"] == 100
        assert "top_k" not in extracted_options
        assert extracted_options["seed"] == 42

        # Simulate response translation
        openai_response = {"id": "test", "model": "gpt-3.5-turbo-0613"}
        ollama_response = translator.translate_response(openai_response, ollama_request)

        assert ollama_response["original_model"] == "llama2:7b"

    def test_streaming_translation_flow(self):
        """Test streaming translation flow."""
        translator = ConcreteTranslator()

        original_request = {"model": "llama2", "stream": True}

        # First chunk
        chunk1 = {"id": "1", "choices": [{"delta": {"content": "Hello"}}]}
        result1 = translator.translate_streaming_response(
            chunk1, original_request, is_first_chunk=True
        )
        assert result1 is not None
        assert result1["first"] is True
        assert result1["last"] is False

        # Middle chunk
        chunk2 = {"id": "1", "choices": [{"delta": {"content": " world"}}]}
        result2 = translator.translate_streaming_response(chunk2, original_request)
        assert result2 is not None
        assert result2["first"] is False
        assert result2["last"] is False

        # Last chunk
        chunk3 = {"id": "1", "choices": [{"finish_reason": "stop"}]}
        result3 = translator.translate_streaming_response(
            chunk3, original_request, is_last_chunk=True
        )
        assert result3 is not None
        assert result3["first"] is False
        assert result3["last"] is True
