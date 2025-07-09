"""
Tests for model name mapping functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings, reset_settings
from src.translators.chat import ChatTranslator
from src.models import OllamaGenerateRequest, OllamaChatRequest


class TestModelMappingConfig:
    """Test model mapping configuration functionality."""
    
    def test_default_model_mappings(self):
        """Test that default model mappings are loaded."""
        settings = Settings(
            OPENAI_API_BASE_URL="http://test:8000/v1",
            OPENAI_API_KEY="test-key"
        )
        
        mappings = settings.load_model_mappings()
        
        # Check some default mappings
        assert mappings["llama2"] == "meta-llama/Llama-2-7b-chat-hf"
        assert mappings["mistral"] == "mistralai/Mistral-7B-Instruct-v0.1"
        assert mappings["codellama"] == "codellama/CodeLlama-7b-Instruct-hf"
    
    def test_custom_mapping_file_loads(self):
        """Test loading custom mappings from file."""
        # Create a temporary mapping file
        custom_mappings = {
            "custom-model": "org/custom-model-v1",
            "llama2": "custom/llama2-override",  # Override default
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_mappings, f)
            mapping_file = f.name
        
        try:
            settings = Settings(
                OPENAI_API_BASE_URL="http://test:8000/v1",
                OPENAI_API_KEY="test-key",
                MODEL_MAPPING_FILE=mapping_file
            )
            
            mappings = settings.load_model_mappings()
            
            # Custom mapping should be present
            assert mappings["custom-model"] == "org/custom-model-v1"
            
            # Custom mapping should override default
            assert mappings["llama2"] == "custom/llama2-override"
            
            # Other defaults should still be present
            assert mappings["mistral"] == "mistralai/Mistral-7B-Instruct-v0.1"
            
        finally:
            Path(mapping_file).unlink()
    
    def test_invalid_mapping_file_path(self):
        """Test error handling for invalid mapping file path."""
        with pytest.raises(ValidationError, match="Model mapping file not found"):
            Settings(
                OPENAI_API_BASE_URL="http://test:8000/v1",
                OPENAI_API_KEY="test-key",
                MODEL_MAPPING_FILE="/nonexistent/file.json"
            )
    
    def test_invalid_json_in_mapping_file(self):
        """Test error handling for invalid JSON in mapping file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json {")
            mapping_file = f.name
        
        try:
            settings = Settings(
                OPENAI_API_BASE_URL="http://test:8000/v1",
                OPENAI_API_KEY="test-key",
                MODEL_MAPPING_FILE=mapping_file
            )
            
            with pytest.raises(ValueError, match="Invalid JSON"):
                settings.load_model_mappings()
                
        finally:
            Path(mapping_file).unlink()
    
    def test_non_dict_mapping_file(self):
        """Test error handling for non-dict JSON in mapping file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(["not", "a", "dict"], f)
            mapping_file = f.name
        
        try:
            settings = Settings(
                OPENAI_API_BASE_URL="http://test:8000/v1",
                OPENAI_API_KEY="test-key",
                MODEL_MAPPING_FILE=mapping_file
            )
            
            with pytest.raises(ValueError, match="must be a JSON object"):
                settings.load_model_mappings()
                
        finally:
            Path(mapping_file).unlink()
    
    def test_invalid_mapping_types(self):
        """Test error handling for invalid mapping types."""
        invalid_mappings = {
            "model1": "valid",
            "model2": 123,  # Invalid: not a string
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(invalid_mappings, f)
            mapping_file = f.name
        
        try:
            settings = Settings(
                OPENAI_API_BASE_URL="http://test:8000/v1",
                OPENAI_API_KEY="test-key",
                MODEL_MAPPING_FILE=mapping_file
            )
            
            with pytest.raises(ValueError, match="Both must be strings"):
                settings.load_model_mappings()
                
        finally:
            Path(mapping_file).unlink()
    
    def test_get_mapped_model_name(self):
        """Test get_mapped_model_name method."""
        settings = Settings(
            OPENAI_API_BASE_URL="http://test:8000/v1",
            OPENAI_API_KEY="test-key"
        )
        
        # Test existing mapping
        assert settings.get_mapped_model_name("llama2") == "meta-llama/Llama-2-7b-chat-hf"
        
        # Test non-existent mapping (should return original)
        assert settings.get_mapped_model_name("unknown-model") == "unknown-model"
    
    def test_mapping_file_with_comments(self):
        """Test that mapping files with comment fields work correctly."""
        mappings_with_comments = {
            "_comment": "This is a comment",
            "_description": "This is a description",
            "model1": "mapped/model1",
            "model2": "mapped/model2"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mappings_with_comments, f)
            mapping_file = f.name
        
        try:
            settings = Settings(
                OPENAI_API_BASE_URL="http://test:8000/v1",
                OPENAI_API_KEY="test-key",
                MODEL_MAPPING_FILE=mapping_file
            )
            
            mappings = settings.load_model_mappings()
            
            # Comments should be included (they're valid JSON keys)
            assert "_comment" in mappings
            assert mappings["model1"] == "mapped/model1"
            assert mappings["model2"] == "mapped/model2"
            
        finally:
            Path(mapping_file).unlink()


class TestModelMappingInTranslator:
    """Test model mapping integration with translators."""
    
    def test_chat_translator_uses_model_mapping(self):
        """Test that ChatTranslator uses model mappings."""
        # Create custom settings with mappings
        custom_mappings = {
            "test-ollama-model": "test-openai-model"
        }
        
        translator = ChatTranslator(model_mappings=custom_mappings)
        
        # Create a generate request
        ollama_request = OllamaGenerateRequest(
            model="test-ollama-model",
            prompt="Test prompt",
            stream=False
        )
        
        # Translate the request
        openai_request = translator.translate_request(ollama_request)
        
        # Verify the model was mapped
        assert openai_request.model == "test-openai-model"
    
    def test_chat_translator_passthrough_unmapped_models(self):
        """Test that unmapped models pass through unchanged."""
        translator = ChatTranslator(model_mappings={})
        
        # Create a request with unmapped model
        ollama_request = OllamaGenerateRequest(
            model="unmapped-model",
            prompt="Test prompt",
            stream=False
        )
        
        # Translate the request
        openai_request = translator.translate_request(ollama_request)
        
        # Verify the model passed through unchanged
        assert openai_request.model == "unmapped-model"
    
    def test_reverse_model_mapping(self):
        """Test reverse model mapping for responses."""
        custom_mappings = {
            "ollama-model": "openai-model"
        }
        
        translator = ChatTranslator(model_mappings=custom_mappings)
        
        # Test reverse mapping
        assert translator.reverse_map_model_name("openai-model") == "ollama-model"
        assert translator.reverse_map_model_name("unknown-model") == "unknown-model"
    
    def test_model_mapping_logging(self):
        """Test that model mapping is logged."""
        custom_mappings = {
            "ollama-model": "openai-model"
        }
        
        translator = ChatTranslator(model_mappings=custom_mappings)
        
        # Mock the logger directly on the translator instance
        mock_logger = MagicMock()
        translator.logger = mock_logger
        
        # Trigger mapping
        translator.map_model_name("ollama-model")
        
        # Verify debug log was called
        mock_logger.debug.assert_called_with("Mapped model 'ollama-model' to 'openai-model'")


class TestModelMappingIntegration:
    """Test end-to-end model mapping integration."""
    
    def test_settings_singleton_with_mapping_file(self):
        """Test that settings singleton works with mapping file."""
        reset_settings()
        
        # Create a mapping file
        custom_mappings = {
            "singleton-test": "singleton-mapped"
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_mappings, f)
            mapping_file = f.name
        
        try:
            with patch.dict('os.environ', {
                'OPENAI_API_BASE_URL': 'http://test:8000/v1',
                'OPENAI_API_KEY': 'test-key',
                'MODEL_MAPPING_FILE': mapping_file
            }):
                settings = get_settings()
                
                # Verify custom mapping is loaded
                assert settings.get_mapped_model_name("singleton-test") == "singleton-mapped"
                
                # Verify singleton behavior
                settings2 = get_settings()
                assert settings is settings2
                
        finally:
            Path(mapping_file).unlink()
            reset_settings()
    
    def test_large_mapping_file_performance(self):
        """Test performance with large mapping file."""
        # Create a large mapping file
        large_mappings = {f"model-{i}": f"mapped-model-{i}" for i in range(1000)}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_mappings, f)
            mapping_file = f.name
        
        try:
            settings = Settings(
                OPENAI_API_BASE_URL="http://test:8000/v1",
                OPENAI_API_KEY="test-key",
                MODEL_MAPPING_FILE=mapping_file
            )
            
            # Load mappings (should be cached after first call)
            mappings1 = settings.load_model_mappings()
            assert len(mappings1) >= 1000
            
            # Second call should use cache
            mappings2 = settings.load_model_mappings()
            assert mappings1 is mappings2  # Same object reference
            
            # Test lookup performance
            assert settings.get_mapped_model_name("model-500") == "mapped-model-500"
            
        finally:
            Path(mapping_file).unlink()