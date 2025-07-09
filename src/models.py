"""
Pydantic models for request/response validation.
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel


# Ollama API Models
class OllamaGenerateRequest(BaseModel):
    """Request model for Ollama generate endpoint."""

    model: str
    prompt: str
    images: Optional[List[str]] = None
    stream: bool = True
    options: Optional[Dict[str, Any]] = None
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None
    raw: bool = False


class OllamaChatMessage(BaseModel):
    """Chat message model for Ollama."""

    role: str
    content: str
    images: Optional[List[str]] = None


class OllamaChatRequest(BaseModel):
    """Request model for Ollama chat endpoint."""

    model: str
    messages: List[OllamaChatMessage]
    stream: bool = True
    options: Optional[Dict[str, Any]] = None
    template: Optional[str] = None


class OllamaGenerateResponse(BaseModel):
    """Response model for Ollama generate endpoint."""

    model: str
    created_at: str
    response: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    prompt_eval_duration: Optional[int] = None
    eval_count: Optional[int] = None
    eval_duration: Optional[int] = None


# OpenAI API Models
class OpenAIMessage(BaseModel):
    """OpenAI chat message model."""

    role: str
    content: Union[str, List[Dict[str, Any]]]
    name: Optional[str] = None


class OpenAIChatRequest(BaseModel):
    """OpenAI chat completion request model."""

    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None


class OpenAIChoice(BaseModel):
    """OpenAI response choice model."""

    index: int
    message: OpenAIMessage
    finish_reason: Optional[str] = None


class OpenAIUsage(BaseModel):
    """OpenAI token usage model."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class OpenAIChatResponse(BaseModel):
    """OpenAI chat completion response model."""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChoice]
    usage: Optional[OpenAIUsage] = None
    system_fingerprint: Optional[str] = None


# Model listing models
class ModelInfo(BaseModel):
    """Model information."""

    name: str
    modified_at: str
    size: int
    digest: str
    details: Optional[Dict[str, Any]] = None


class ModelsResponse(BaseModel):
    """Response for model listing."""

    models: List[ModelInfo]
