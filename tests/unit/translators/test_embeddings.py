"""
Unit tests for the embeddings translator.
"""

from unittest.mock import Mock, patch

import pytest

from src.models import (
    OllamaEmbeddingRequest,
    OllamaEmbeddingResponse,
    OllamaOptions,
    OpenAIEmbeddingData,
    OpenAIEmbeddingRequest,
    OpenAIEmbeddingResponse,
    OpenAIUsage,
)
from src.translators.embeddings import EmbeddingsTranslator
from src.utils.exceptions import TranslationError


class TestEmbeddingsTranslator:
    """Test the embeddings translator."""

    @pytest.fixture
    def translator(self):
        """Create an embeddings translator instance."""
        return EmbeddingsTranslator()

    @pytest.fixture
    def translator_with_mappings(self):
        """Create an embeddings translator with model mappings."""
        mappings = {
            "test-model": "mapped-test-model",
            "embedding-model": "openai-embedding-model"
        }
        return EmbeddingsTranslator(model_mappings=mappings)

    @pytest.fixture
    def sample_ollama_request(self):
        """Create a sample Ollama embedding request."""
        return OllamaEmbeddingRequest(
            model="text-embedding-ada-002",
            prompt="Test embedding text"
        )

    @pytest.fixture
    def sample_ollama_batch_request(self):
        """Create a sample Ollama batch embedding request."""
        return OllamaEmbeddingRequest(
            model="text-embedding-ada-002",
            prompt=["Text one", "Text two", "Text three"]
        )

    @pytest.fixture
    def sample_ollama_request_with_options(self):
        """Create a sample Ollama embedding request with options."""
        options = OllamaOptions(
            temperature=0.5,
            top_p=0.9
        )
        return OllamaEmbeddingRequest(
            model="test-model",
            prompt="Test text with options",
            options=options
        )

    @pytest.fixture
    def sample_openai_response(self):
        """Create a sample OpenAI embedding response."""
        return OpenAIEmbeddingResponse(
            object="list",
            data=[
                OpenAIEmbeddingData(
                    object="embedding",
                    index=0,
                    embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
                )
            ],
            model="text-embedding-ada-002",
            usage=OpenAIUsage(
                prompt_tokens=10,
                completion_tokens=0,
                total_tokens=10
            )
        )

    @pytest.fixture
    def sample_openai_batch_response(self):
        """Create a sample OpenAI batch embedding response."""
        return OpenAIEmbeddingResponse(
            object="list",
            data=[
                OpenAIEmbeddingData(
                    object="embedding",
                    index=0,
                    embedding=[0.1, 0.2, 0.3]
                ),
                OpenAIEmbeddingData(
                    object="embedding",
                    index=1,
                    embedding=[0.4, 0.5, 0.6]
                ),
                OpenAIEmbeddingData(
                    object="embedding",
                    index=2,
                    embedding=[0.7, 0.8, 0.9]
                )
            ],
            model="text-embedding-ada-002",
            usage=OpenAIUsage(
                prompt_tokens=30,
                completion_tokens=0,
                total_tokens=30
            )
        )

    def test_translate_request_single_prompt(self, translator, sample_ollama_request):
        """Test translating a single prompt request."""
        result = translator.translate_request(sample_ollama_request)
        
        assert isinstance(result, OpenAIEmbeddingRequest)
        assert result.model == "text-embedding-ada-002"
        assert result.input == ["Test embedding text"]
        assert result.encoding_format == "float"
        assert result.dimensions is None
        assert result.user is None

    def test_translate_request_batch_prompt(self, translator, sample_ollama_batch_request):
        """Test translating a batch prompt request."""
        result = translator.translate_request(sample_ollama_batch_request)
        
        assert isinstance(result, OpenAIEmbeddingRequest)
        assert result.model == "text-embedding-ada-002"
        assert result.input == ["Text one", "Text two", "Text three"]
        assert result.encoding_format == "float"

    def test_translate_request_with_model_mapping(self, translator_with_mappings, sample_ollama_request_with_options):
        """Test translating request with model mapping."""
        result = translator_with_mappings.translate_request(sample_ollama_request_with_options)
        
        assert isinstance(result, OpenAIEmbeddingRequest)
        assert result.model == "mapped-test-model"  # Should be mapped
        assert result.input == ["Test text with options"]

    def test_translate_request_with_options_no_dimensions(self, translator):
        """Test translating request with options but no dimensions."""
        options = OllamaOptions(temperature=0.5)
        
        request = OllamaEmbeddingRequest(
            model="test-model",
            prompt="Test text",
            options=options
        )
        
        result = translator.translate_request(request)
        
        # Since OllamaOptions doesn't have dimensions, it should be None
        assert result.dimensions is None

    def test_translate_request_error_handling(self, translator):
        """Test error handling in request translation."""
        # Create an invalid request that will cause an error
        with patch.object(translator, 'map_model_name', side_effect=Exception("Mapping error")):
            request = OllamaEmbeddingRequest(model="test", prompt="test")
            
            with pytest.raises(TranslationError):
                translator.translate_request(request)

    def test_translate_response_single_embedding(self, translator, sample_ollama_request, sample_openai_response):
        """Test translating a single embedding response."""
        result = translator.translate_response(sample_openai_response, sample_ollama_request)
        
        assert isinstance(result, OllamaEmbeddingResponse)
        assert result.embedding == [0.1, 0.2, 0.3, 0.4, 0.5]

    def test_translate_response_batch_to_single(self, translator, sample_ollama_batch_request, sample_openai_batch_response):
        """Test translating a batch response to single (Ollama format limitation)."""
        result = translator.translate_response(sample_openai_batch_response, sample_ollama_batch_request)
        
        assert isinstance(result, OllamaEmbeddingResponse)
        # Should return the first embedding for batch requests
        assert result.embedding == [0.1, 0.2, 0.3]

    def test_translate_response_empty_data(self, translator, sample_ollama_request):
        """Test translating response with empty data."""
        empty_response = OpenAIEmbeddingResponse(
            object="list",
            data=[],
            model="test-model",
            usage=OpenAIUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        )
        
        with pytest.raises(TranslationError) as exc_info:
            translator.translate_response(empty_response, sample_ollama_request)
        
        assert "no embedding data" in str(exc_info.value).lower()

    def test_translate_response_error_handling(self, translator, sample_ollama_request):
        """Test error handling in response translation."""
        # Create a response that will cause an error
        with patch.object(translator, 'handle_translation_error') as mock_handler:
            mock_handler.side_effect = TranslationError("Response error")
            
            invalid_response = Mock()
            invalid_response.data = None  # This will cause an error
            
            with pytest.raises(TranslationError):
                translator.translate_response(invalid_response, sample_ollama_request)

    def test_translate_streaming_response_returns_none(self, translator, sample_ollama_request):
        """Test that streaming response always returns None (not supported)."""
        result = translator.translate_streaming_response(
            {"some": "chunk"}, 
            sample_ollama_request,
            is_first_chunk=True
        )
        
        assert result is None

    def test_translate_streaming_response_all_parameters(self, translator, sample_ollama_request):
        """Test streaming response with all parameters."""
        result = translator.translate_streaming_response(
            {"data": "chunk"},
            sample_ollama_request,
            is_first_chunk=False,
            is_last_chunk=True
        )
        
        assert result is None

    def test_translate_batch_request(self, translator, sample_ollama_request):
        """Test batch request translation."""
        result = translator.translate_batch_request(sample_ollama_request)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], OpenAIEmbeddingRequest)
        assert result[0].model == "text-embedding-ada-002"

    def test_translate_batch_request_with_batch_input(self, translator, sample_ollama_batch_request):
        """Test batch request translation with batch input."""
        result = translator.translate_batch_request(sample_ollama_batch_request)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], OpenAIEmbeddingRequest)
        assert result[0].input == ["Text one", "Text two", "Text three"]

    def test_calculate_embedding_tokens_single_text(self, translator):
        """Test token calculation for single text."""
        with patch.object(translator, 'calculate_tokens', return_value=10):
            result = translator.calculate_embedding_tokens("Test text")
            
            assert result == 10

    def test_calculate_embedding_tokens_list_text(self, translator):
        """Test token calculation for list of texts."""
        with patch.object(translator, 'calculate_tokens', return_value=5):
            result = translator.calculate_embedding_tokens(["Text one", "Text two"])
            
            assert result == 10  # 5 tokens per text * 2 texts

    def test_calculate_embedding_tokens_empty_list(self, translator):
        """Test token calculation for empty list."""
        result = translator.calculate_embedding_tokens([])
        
        assert result == 0

    def test_inheritance_and_type_annotations(self, translator):
        """Test that the translator properly inherits from BaseTranslator."""
        from src.translators.base import BaseTranslator
        
        assert isinstance(translator, BaseTranslator)
        
        # Check that it has the required methods
        assert hasattr(translator, 'translate_request')
        assert hasattr(translator, 'translate_response')
        assert hasattr(translator, 'translate_streaming_response')

    def test_model_validation_integration(self, translator):
        """Test integration with model validation."""
        with patch.object(translator, 'validate_model_name') as mock_validate:
            request = OllamaEmbeddingRequest(model="test-model", prompt="test")
            translator.translate_request(request)
            
            # validate_model_name should not be called in translate_request
            # It's called in the router
            mock_validate.assert_not_called()

    def test_error_handling_methods(self, translator):
        """Test that error handling methods are properly inherited."""
        assert hasattr(translator, 'handle_translation_error')
        
        # Test that it properly handles exceptions
        with pytest.raises(TranslationError):
            translator.handle_translation_error(ValueError("Test error"), "test_method")


class TestEmbeddingsTranslatorIntegration:
    """Integration tests for the embeddings translator."""

    @pytest.fixture
    def translator(self):
        """Create an embeddings translator instance."""
        return EmbeddingsTranslator()

    def test_full_translation_flow(self, translator):
        """Test the complete translation flow."""
        # Create request
        ollama_request = OllamaEmbeddingRequest(
            model="text-embedding-ada-002",
            prompt="Integration test text"
        )
        
        # Translate to OpenAI format
        openai_request = translator.translate_request(ollama_request)
        
        # Verify OpenAI request
        assert openai_request.model == "text-embedding-ada-002"
        assert openai_request.input == ["Integration test text"]
        
        # Create mock OpenAI response
        openai_response = OpenAIEmbeddingResponse(
            object="list",
            data=[
                OpenAIEmbeddingData(
                    object="embedding",
                    index=0,
                    embedding=[0.1, 0.2, 0.3, 0.4]
                )
            ],
            model="text-embedding-ada-002",
            usage=OpenAIUsage(prompt_tokens=5, completion_tokens=0, total_tokens=5)
        )
        
        # Translate back to Ollama format
        ollama_response = translator.translate_response(openai_response, ollama_request)
        
        # Verify final response
        assert isinstance(ollama_response, OllamaEmbeddingResponse)
        assert ollama_response.embedding == [0.1, 0.2, 0.3, 0.4]

    def test_batch_integration_flow(self, translator):
        """Test batch processing integration."""
        # Create batch request
        ollama_request = OllamaEmbeddingRequest(
            model="text-embedding-ada-002",
            prompt=["Text one", "Text two"]
        )
        
        # Translate to OpenAI
        openai_request = translator.translate_request(ollama_request)
        assert openai_request.input == ["Text one", "Text two"]
        
        # Create batch response
        openai_response = OpenAIEmbeddingResponse(
            object="list",
            data=[
                OpenAIEmbeddingData(object="embedding", index=0, embedding=[0.1, 0.2]),
                OpenAIEmbeddingData(object="embedding", index=1, embedding=[0.3, 0.4])
            ],
            model="text-embedding-ada-002",
            usage=OpenAIUsage(prompt_tokens=10, completion_tokens=0, total_tokens=10)
        )
        
        # Translate back (should return first embedding for Ollama compatibility)
        ollama_response = translator.translate_response(openai_response, ollama_request)
        assert ollama_response.embedding == [0.1, 0.2]

    def test_error_propagation(self, translator):
        """Test that errors propagate correctly through the translation flow."""
        # Test with invalid request
        with patch.object(translator, 'map_model_name', side_effect=ValueError("Invalid model")):
            request = OllamaEmbeddingRequest(model="invalid", prompt="test")
            
            with pytest.raises(TranslationError):
                translator.translate_request(request)