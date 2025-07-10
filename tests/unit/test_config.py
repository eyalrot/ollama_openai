"""
Unit tests for configuration management.
"""

import json
import os
import tempfile
import warnings
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings, reset_settings


class TestSettings:
    """Test the Settings class and its validators."""

    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()
        # Store original env vars
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Restore environment after each test."""
        # Restore original env vars
        os.environ.clear()
        os.environ.update(self.original_env)
        reset_settings()

    def test_valid_configuration(self):
        """Test loading valid configuration."""
        env_vars = {
            "OPENAI_API_BASE_URL": "https://api.openai.com/v1",
            "OPENAI_API_KEY": "sk-test123",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()
            assert str(settings.OPENAI_API_BASE_URL) == "https://api.openai.com/v1"
            assert settings.OPENAI_API_KEY == "sk-test123"
            assert settings.PROXY_PORT == 11434
            assert settings.LOG_LEVEL == "INFO"
            assert settings.REQUEST_TIMEOUT == 60
            assert settings.MAX_RETRIES == 3
            assert settings.DEBUG is False

    def test_missing_required_fields(self):
        """Test that missing required fields raise validation errors."""
        # Create a Settings class that doesn't use .env file
        with patch(
            "src.config.Settings.model_config",
            {"env_file": None, "case_sensitive": True, "extra": "ignore"},
        ):
            # Missing OPENAI_API_BASE_URL
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True):
                with pytest.raises(ValidationError) as exc_info:
                    Settings()
                assert "OPENAI_API_BASE_URL" in str(exc_info.value)

            # Missing OPENAI_API_KEY
            with patch.dict(
                os.environ, {"OPENAI_API_BASE_URL": "https://api.test.com"}, clear=True
            ):
                with pytest.raises(ValidationError) as exc_info:
                    Settings()
                assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_url_validation(self):
        """Test URL validation and normalization."""
        base_env = {"OPENAI_API_KEY": "test-key"}

        # Test URL without /v1 gets it appended
        env = {**base_env, "OPENAI_API_BASE_URL": "https://api.test.com"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert str(settings.OPENAI_API_BASE_URL) == "https://api.test.com/v1"

        # Test URL with /v1 remains unchanged
        env = {**base_env, "OPENAI_API_BASE_URL": "https://api.test.com/v1"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert str(settings.OPENAI_API_BASE_URL) == "https://api.test.com/v1"

        # Test URL with trailing slash and /v1
        env = {**base_env, "OPENAI_API_BASE_URL": "https://api.test.com/v1/"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert str(settings.OPENAI_API_BASE_URL) == "https://api.test.com/v1"

    def test_api_key_validation(self):
        """Test API key validation."""
        base_env = {"OPENAI_API_BASE_URL": "https://api.test.com"}

        # Test empty API key
        env = {**base_env, "OPENAI_API_KEY": ""}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "OPENAI_API_KEY cannot be empty" in str(exc_info.value)

        # Test whitespace-only API key
        env = {**base_env, "OPENAI_API_KEY": "   "}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "OPENAI_API_KEY cannot be empty" in str(exc_info.value)

        # Test API key with whitespace gets trimmed
        env = {**base_env, "OPENAI_API_KEY": "  test-key  "}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.OPENAI_API_KEY == "test-key"

    def test_log_level_validation(self):
        """Test log level validation."""
        base_env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
        }

        # Test valid log levels
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            env = {**base_env, "LOG_LEVEL": level}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                assert level == settings.LOG_LEVEL

        # Test lowercase gets converted to uppercase
        env = {**base_env, "LOG_LEVEL": "debug"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.LOG_LEVEL == "DEBUG"

        # Test invalid log level
        env = {**base_env, "LOG_LEVEL": "INVALID"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Invalid log level" in str(exc_info.value)

    def test_numeric_field_validation(self):
        """Test validation of numeric fields with bounds."""
        base_env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
        }

        # Test port validation
        env = {**base_env, "PROXY_PORT": "0"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

        env = {**base_env, "PROXY_PORT": "65536"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

        env = {**base_env, "PROXY_PORT": "8080"}
        with patch.dict(os.environ, env, clear=True):
            settings = Settings()
            assert settings.PROXY_PORT == 8080

        # Test timeout validation
        env = {**base_env, "REQUEST_TIMEOUT": "0"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

        env = {**base_env, "REQUEST_TIMEOUT": "601"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

        # Test retries validation
        env = {**base_env, "MAX_RETRIES": "-1"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

        env = {**base_env, "MAX_RETRIES": "11"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError):
                Settings()

    def test_timeout_retry_warning(self):
        """Test warning when timeout * retries exceeds threshold."""
        env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
            "REQUEST_TIMEOUT": "300",  # 5 minutes
            "MAX_RETRIES": "3",  # Total: 1200s (20 minutes)
        }

        with patch.dict(os.environ, env, clear=True):
            with warnings.catch_warnings(record=True) as w:
                Settings()  # This triggers the warning
                assert len(w) == 1
                assert "Total timeout with retries could exceed" in str(w[0].message)

    def test_model_mapping_file_validation(self):
        """Test model mapping file validation."""
        base_env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
        }

        # Test non-existent file
        env = {**base_env, "MODEL_MAPPING_FILE": "/non/existent/file.json"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            assert "Model mapping file not found" in str(exc_info.value)

        # Test non-JSON file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not json")
            temp_file = f.name

        try:
            env = {**base_env, "MODEL_MAPPING_FILE": temp_file}
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(ValidationError) as exc_info:
                    Settings()
                assert "Model mapping file must be JSON" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_load_model_mappings(self):
        """Test loading model mappings from file."""
        base_env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
        }

        # Test with no mapping file - should use defaults
        with patch.dict(os.environ, base_env, clear=True):
            settings = Settings()
            mappings = settings.load_model_mappings()
            assert "llama2" in mappings
            assert mappings["llama2"] == "meta-llama/Llama-2-7b-chat-hf"

        # Test with custom mapping file
        custom_mappings = {
            "custom-model": "provider/custom-model-v1",
            "llama2": "my-custom-llama2",  # Override default
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(custom_mappings, f)
            temp_file = f.name

        try:
            env = {**base_env, "MODEL_MAPPING_FILE": temp_file}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                mappings = settings.load_model_mappings()
                assert mappings["custom-model"] == "provider/custom-model-v1"
                assert (
                    mappings["llama2"] == "my-custom-llama2"
                )  # Custom overrides default
                assert (
                    mappings["mistral"] == "mistralai/Mistral-7B-Instruct-v0.1"
                )  # Default still present
        finally:
            os.unlink(temp_file)

        # Test with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json{")
            temp_file = f.name

        try:
            env = {**base_env, "MODEL_MAPPING_FILE": temp_file}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                with pytest.raises(ValueError) as exc_info:
                    settings.load_model_mappings()
                assert "Invalid JSON" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

        # Test with non-dict JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["not", "a", "dict"], f)
            temp_file = f.name

        try:
            env = {**base_env, "MODEL_MAPPING_FILE": temp_file}
            with patch.dict(os.environ, env, clear=True):
                settings = Settings()
                with pytest.raises(ValueError) as exc_info:
                    settings.load_model_mappings()
                assert "Model mappings must be a JSON object" in str(exc_info.value)
        finally:
            os.unlink(temp_file)

    def test_get_mapped_model_name(self):
        """Test model name mapping functionality."""
        base_env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, base_env, clear=True):
            settings = Settings()

            # Test default mapping
            assert (
                settings.get_mapped_model_name("llama2")
                == "meta-llama/Llama-2-7b-chat-hf"
            )

            # Test unmapped model returns as-is
            assert settings.get_mapped_model_name("unknown-model") == "unknown-model"

            # Test model variants
            assert (
                settings.get_mapped_model_name("llama2:13b")
                == "meta-llama/Llama-2-13b-chat-hf"
            )


class TestSingletonPattern:
    """Test the singleton pattern implementation."""

    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Restore environment after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)
        reset_settings()

    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env, clear=True):
            settings1 = get_settings()
            settings2 = get_settings()
            assert settings1 is settings2

    def test_reset_settings(self):
        """Test that reset_settings creates a new instance."""
        env = {
            "OPENAI_API_BASE_URL": "https://api.test.com",
            "OPENAI_API_KEY": "test-key",
        }

        with patch.dict(os.environ, env, clear=True):
            settings1 = get_settings()
            reset_settings()
            settings2 = get_settings()
            assert settings1 is not settings2

    def test_settings_immutable_after_creation(self):
        """Test that settings values don't change after creation."""
        env1 = {
            "OPENAI_API_BASE_URL": "https://api1.test.com",
            "OPENAI_API_KEY": "test-key-1",
        }

        with patch.dict(os.environ, env1, clear=True):
            settings = get_settings()
            assert settings.OPENAI_API_KEY == "test-key-1"

            # Change environment
            os.environ["OPENAI_API_KEY"] = "test-key-2"

            # Settings should not change
            assert settings.OPENAI_API_KEY == "test-key-1"

            # New instance after reset should have new value
            reset_settings()
            new_settings = get_settings()
            assert new_settings.OPENAI_API_KEY == "test-key-2"


class TestIntegration:
    """Integration tests for configuration loading."""

    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Restore environment after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)
        reset_settings()

    def test_env_file_loading(self):
        """Test loading configuration from .env file."""
        # Create a temporary .env file
        env_content = """
OPENAI_API_BASE_URL=https://env-file-test.com
OPENAI_API_KEY=env-file-key
PROXY_PORT=8888
LOG_LEVEL=DEBUG
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(env_content.strip())

            # Clear environment to ensure we're loading from file
            with patch.dict(os.environ, {}, clear=True):
                # Create a custom Settings class with the temp env file
                class TestSettings(Settings):
                    model_config = {
                        "env_file": str(env_file),
                        "case_sensitive": True,
                        "extra": "ignore",
                        "arbitrary_types_allowed": True,
                    }

                settings = TestSettings()
                assert (
                    str(settings.OPENAI_API_BASE_URL) == "https://env-file-test.com/v1"
                )
                assert settings.OPENAI_API_KEY == "env-file-key"
                assert settings.PROXY_PORT == 8888
                assert settings.LOG_LEVEL == "DEBUG"

    def test_env_var_overrides_env_file(self):
        """Test that environment variables override .env file values."""
        env_content = """
OPENAI_API_BASE_URL=https://env-file.com
OPENAI_API_KEY=file-key
LOG_LEVEL=INFO
"""

        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            env_file.write_text(env_content.strip())

            # Set environment variable to override
            env = {
                "LOG_LEVEL": "DEBUG",
                "OPENAI_API_BASE_URL": "https://env-file.com",  # Required field
                "OPENAI_API_KEY": "file-key",  # Required field
            }
            with patch.dict(os.environ, env, clear=True):
                # Create a custom Settings class with the temp env file
                class TestSettings(Settings):
                    model_config = {
                        "env_file": str(env_file),
                        "case_sensitive": True,
                        "extra": "ignore",
                        "arbitrary_types_allowed": True,
                    }

                settings = TestSettings()
                assert settings.LOG_LEVEL == "DEBUG"  # From env var
                assert settings.OPENAI_API_KEY == "file-key"  # From file/env
