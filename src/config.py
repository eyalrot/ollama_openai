"""
Configuration management for the Ollama to OpenAI proxy service.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Required settings
    OPENAI_API_BASE_URL: HttpUrl = Field(
        ...,
        description="Base URL for the OpenAI-compatible API (e.g., http://vllm-server:8000/v1)"
    )
    OPENAI_API_KEY: str = Field(
        ...,
        description="API key for authentication with the OpenAI-compatible server"
    )
    
    # Optional settings
    PROXY_PORT: int = Field(
        default=11434,
        description="Port for the proxy server to listen on"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    REQUEST_TIMEOUT: int = Field(
        default=60,
        description="Request timeout in seconds"
    )
    MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed requests"
    )
    MODEL_MAPPING_FILE: Optional[str] = Field(
        default=None,
        description="Path to optional model name mapping JSON file"
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v):
        """Validate log level is valid."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v.upper()
    
    @validator("OPENAI_API_BASE_URL", pre=True)
    def validate_base_url(cls, v):
        """Ensure base URL ends with /v1 if not already present."""
        if isinstance(v, str) and not v.endswith("/v1"):
            return f"{v.rstrip('/')}/v1"
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()