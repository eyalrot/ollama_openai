"""
Configuration management for the Ollama to OpenAI proxy service.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Required settings
    OPENAI_API_BASE_URL: HttpUrl = Field(
        ...,
        description=(
            "Base URL for OpenAI-compatible API (e.g., http://vllm-server:8000/v1)"
        ),
    )
    OPENAI_API_KEY: str = Field(
        ..., description="API key for authentication with OpenAI-compatible server"
    )

    # Optional settings
    PROXY_PORT: int = Field(
        default=11434,
        description="Port for the proxy server to listen on",
        ge=1,
        le=65535,
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    REQUEST_TIMEOUT: int = Field(
        default=60, description="Request timeout in seconds", ge=1, le=600
    )
    MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests",
        ge=0,
        le=10,
    )
    MODEL_MAPPING_FILE: Optional[str] = Field(
        default=None, description="Path to optional model name mapping JSON file"
    )
    DEBUG: bool = Field(default=False, description="Enable debug mode")
    DISABLE_SSL_VERIFICATION: bool = Field(
        default=False,
        description=(
            "Disable SSL certificate verification (NOT recommended for production)"
        ),
    )

    # Runtime properties (not from env)
    _model_mappings: Optional[Dict[str, str]] = None

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(
                f"Invalid log level. Must be one of: {', '.join(valid_levels)}"
            )
        return v.upper()

    @field_validator("OPENAI_API_BASE_URL", mode="before")
    @classmethod
    def validate_base_url(cls, v: Any) -> Any:
        """Ensure base URL ends with /v1 if not already present."""
        if isinstance(v, str):
            # Remove any trailing slashes first
            v = v.rstrip("/")
            # Add /v1 if not present
            if not v.endswith("/v1"):
                v = f"{v}/v1"
        return v

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError("OPENAI_API_KEY cannot be empty")
        return v.strip()

    @field_validator("MODEL_MAPPING_FILE")
    @classmethod
    def validate_mapping_file(cls, v: Optional[str]) -> Optional[str]:
        """Validate model mapping file exists if specified."""
        if v is not None and v.strip() != "":
            path = Path(v)
            if not path.exists():
                raise ValueError(f"Model mapping file not found: {v}")
            if not path.is_file():
                raise ValueError(f"Model mapping path is not a file: {v}")
            if path.suffix not in [".json", ".JSON"]:
                raise ValueError(f"Model mapping file must be JSON: {v}")
            return v
        return None

    @model_validator(mode="after")
    def validate_timeout_vs_retries(self) -> "Settings":
        """Ensure timeout is reasonable given retry settings."""
        # Warn if total timeout could exceed 10 minutes
        total_possible_time = self.REQUEST_TIMEOUT * (self.MAX_RETRIES + 1)
        if total_possible_time > 600:  # 10 minutes
            import warnings

            warnings.warn(
                f"Total timeout with retries could exceed {total_possible_time}s. "
                f"Consider reducing REQUEST_TIMEOUT or MAX_RETRIES.",
                stacklevel=2,
            )

        return self

    def load_model_mappings(self) -> Dict[str, str]:
        """Load model mappings from file if specified."""
        if self._model_mappings is not None:
            return self._model_mappings

        self._model_mappings = {}

        if self.MODEL_MAPPING_FILE:
            try:
                with open(self.MODEL_MAPPING_FILE) as f:
                    mappings = json.load(f)

                if not isinstance(mappings, dict):
                    raise ValueError("Model mappings must be a JSON object")

                # Validate all mappings are string to string
                for key, value in mappings.items():
                    if not isinstance(key, str) or not isinstance(value, str):
                        raise ValueError(
                            f"Invalid mapping: {key} -> {value}. Both must be strings."
                        )

                self._model_mappings = mappings

            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in model mapping file: {e}")
            except Exception as e:
                raise ValueError(f"Error loading model mappings: {e}")

        # Add default mappings only if a mapping file is explicitly provided
        # This allows bypassing model mapping entirely when MODEL_MAPPING_FILE is not set
        if self.MODEL_MAPPING_FILE:
            default_mappings = {
                "llama2": "meta-llama/Llama-2-7b-chat-hf",
                "llama2:13b": "meta-llama/Llama-2-13b-chat-hf",
                "llama2:70b": "meta-llama/Llama-2-70b-chat-hf",
                "codellama": "codellama/CodeLlama-7b-Instruct-hf",
                "mistral": "mistralai/Mistral-7B-Instruct-v0.1",
                "mixtral": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "gemma": "google/gemma-7b-it",
                "phi": "microsoft/phi-2",
            }

            for key, value in default_mappings.items():
                if key not in self._model_mappings:
                    self._model_mappings[key] = value

        return self._model_mappings

    def get_mapped_model_name(self, ollama_model: str) -> str:
        """Get the mapped model name for an Ollama model."""
        mappings = self.load_model_mappings()
        return mappings.get(ollama_model, ollama_model)

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
        "arbitrary_types_allowed": True,
    }


# Global settings instance (singleton)
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance (singleton pattern).

    Returns:
        Settings: The global settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()  # type: ignore[call-arg]
        # Log SSL verification setting on startup
        import logging

        logger = logging.getLogger(__name__)
        logger.info(
            f"SSL verification disabled: {_settings.DISABLE_SSL_VERIFICATION}",
            extra={
                "extra_data": {
                    "disable_ssl_verification": _settings.DISABLE_SSL_VERIFICATION
                }
            },
        )
    return _settings


def reset_settings() -> None:
    """
    Reset the global settings instance.
    Useful for testing or reloading configuration.
    """
    global _settings
    _settings = None
