"""
Pydantic models for request/response validation.

This module contains all data models for both Ollama and OpenAI APIs,
including request/response models, streaming models, and validation rules.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ===========================
# Ollama API Models
# ===========================


class OllamaOptions(BaseModel):
    """Options for Ollama model inference."""

    # Generation parameters
    seed: Optional[int] = Field(None, description="Random seed for generation")
    num_predict: Optional[int] = Field(
        None, description="Maximum number of tokens to predict"
    )
    top_k: Optional[int] = Field(None, description="Top-k sampling parameter")
    top_p: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Top-p (nucleus) sampling"
    )
    tfs_z: Optional[float] = Field(None, description="Tail free sampling parameter")
    typical_p: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Typical sampling parameter"
    )
    repeat_last_n: Optional[int] = Field(
        None, description="Last n tokens to consider for repeat penalty"
    )
    temperature: Optional[float] = Field(
        None, ge=0.0, description="Sampling temperature"
    )
    repeat_penalty: Optional[float] = Field(
        None, description="Repeat penalty parameter"
    )
    presence_penalty: Optional[float] = Field(
        None, description="Presence penalty parameter"
    )
    frequency_penalty: Optional[float] = Field(
        None, description="Frequency penalty parameter"
    )
    mirostat: Optional[int] = Field(None, description="Mirostat sampling mode (0/1/2)")
    mirostat_tau: Optional[float] = Field(None, description="Mirostat target entropy")
    mirostat_eta: Optional[float] = Field(None, description="Mirostat learning rate")
    penalize_newline: Optional[bool] = Field(
        None, description="Whether to penalize newlines"
    )
    stop: Optional[List[str]] = Field(None, description="Stop sequences")

    # Model loading parameters
    numa: Optional[bool] = Field(None, description="Enable NUMA support")
    num_ctx: Optional[int] = Field(None, description="Context window size")
    num_batch: Optional[int] = Field(
        None, description="Batch size for prompt processing"
    )
    num_gqa: Optional[int] = Field(None, description="Number of GQA groups")
    num_gpu: Optional[int] = Field(
        None, description="Number of layers to offload to GPU"
    )
    main_gpu: Optional[int] = Field(None, description="Main GPU to use")
    low_vram: Optional[bool] = Field(None, description="Enable low VRAM mode")
    f16_kv: Optional[bool] = Field(None, description="Use 16-bit floats for KV cache")
    vocab_only: Optional[bool] = Field(None, description="Load vocabulary only")
    use_mmap: Optional[bool] = Field(None, description="Use memory mapping for model")
    use_mlock: Optional[bool] = Field(None, description="Lock model in memory")
    num_thread: Optional[int] = Field(None, description="Number of threads to use")


class OllamaGenerateRequest(BaseModel):
    """Request model for Ollama generate endpoint."""

    model: str = Field(..., description="Model name to use for generation")
    prompt: str = Field(..., description="Input prompt for generation")
    images: Optional[List[str]] = Field(None, description="Base64 encoded images")
    format: Optional[Literal["json"]] = Field(None, description="Response format")
    options: Optional[OllamaOptions] = Field(None, description="Model options")
    system: Optional[str] = Field(None, description="System prompt")
    template: Optional[str] = Field(None, description="Prompt template")
    context: Optional[List[int]] = Field(None, description="Conversation context")
    stream: bool = Field(True, description="Stream response")
    raw: bool = Field(False, description="Bypass prompt template")
    keep_alive: Optional[Union[str, int]] = Field(
        "5m", description="Model keep-alive duration"
    )


class OllamaChatMessage(BaseModel):
    """Chat message model for Ollama."""

    role: Literal["system", "user", "assistant", "tool"] = Field(
        ..., description="Message role"
    )
    content: str = Field(..., description="Message content")
    images: Optional[List[str]] = Field(None, description="Base64 encoded images")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None, description="Tool calls made by assistant"
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate message role."""
        valid_roles = {"system", "user", "assistant", "tool"}
        if v not in valid_roles:
            raise ValueError(f"Invalid role: {v}. Must be one of {valid_roles}")
        return v


class OllamaChatRequest(BaseModel):
    """Request model for Ollama chat endpoint."""

    model: str = Field(..., description="Model name to use")
    messages: List[OllamaChatMessage] = Field(
        ..., min_length=1, description="Chat messages"
    )
    format: Optional[Literal["json"]] = Field(None, description="Response format")
    options: Optional[OllamaOptions] = Field(None, description="Model options")
    template: Optional[str] = Field(None, description="Prompt template")
    stream: bool = Field(True, description="Stream response")
    keep_alive: Optional[Union[str, int]] = Field(
        "5m", description="Model keep-alive duration"
    )
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Available tools")


class OllamaEmbeddingRequest(BaseModel):
    """Request model for Ollama embeddings endpoint."""

    model: str = Field(..., description="Model name to use")
    prompt: Union[str, List[str]] = Field(
        ..., description="Text to embed (single string or list of strings)"
    )
    options: Optional[OllamaOptions] = Field(None, description="Model options")
    keep_alive: Optional[Union[str, int]] = Field(
        "5m", description="Model keep-alive duration"
    )


class OllamaPullRequest(BaseModel):
    """Request model for pulling models."""

    name: str = Field(..., description="Model name to pull")
    insecure: bool = Field(False, description="Allow insecure connections")
    stream: bool = Field(True, description="Stream pull progress")


class OllamaPushRequest(BaseModel):
    """Request model for pushing models."""

    name: str = Field(..., description="Model name to push")
    insecure: bool = Field(False, description="Allow insecure connections")
    stream: bool = Field(True, description="Stream push progress")


class OllamaCreateRequest(BaseModel):
    """Request model for creating models."""

    name: str = Field(..., description="Name for the new model")
    modelfile: str = Field(..., description="Modelfile content")
    stream: bool = Field(True, description="Stream creation progress")
    path: Optional[str] = Field(None, description="Path to modelfile")


class OllamaCopyRequest(BaseModel):
    """Request model for copying models."""

    source: str = Field(..., description="Source model name")
    destination: str = Field(..., description="Destination model name")


class OllamaDeleteRequest(BaseModel):
    """Request model for deleting models."""

    name: str = Field(..., description="Model name to delete")


class OllamaShowRequest(BaseModel):
    """Request model for showing model information."""

    name: str = Field(..., description="Model name to show")
    verbose: bool = Field(False, description="Show verbose information")


# Ollama Response Models


class OllamaGenerateResponse(BaseModel):
    """Response model for Ollama generate endpoint."""

    model: str = Field(..., description="Model used for generation")
    created_at: str = Field(..., description="Creation timestamp")
    response: str = Field(..., description="Generated text")
    done: bool = Field(..., description="Whether generation is complete")
    done_reason: Optional[str] = Field(None, description="Reason for completion")
    context: Optional[List[int]] = Field(None, description="Updated context")
    total_duration: Optional[int] = Field(
        None, description="Total duration in nanoseconds"
    )
    load_duration: Optional[int] = Field(None, description="Model load duration")
    prompt_eval_count: Optional[int] = Field(None, description="Tokens in prompt")
    prompt_eval_duration: Optional[int] = Field(
        None, description="Prompt evaluation duration"
    )
    eval_count: Optional[int] = Field(None, description="Tokens generated")
    eval_duration: Optional[int] = Field(None, description="Generation duration")


class OllamaChatResponse(BaseModel):
    """Response model for Ollama chat endpoint."""

    model: str = Field(..., description="Model used")
    created_at: str = Field(..., description="Creation timestamp")
    message: OllamaChatMessage = Field(..., description="Assistant's response message")
    done: bool = Field(..., description="Whether response is complete")
    done_reason: Optional[str] = Field(None, description="Reason for completion")
    total_duration: Optional[int] = Field(
        None, description="Total duration in nanoseconds"
    )
    load_duration: Optional[int] = Field(None, description="Model load duration")
    prompt_eval_count: Optional[int] = Field(None, description="Tokens in prompt")
    prompt_eval_duration: Optional[int] = Field(
        None, description="Prompt evaluation duration"
    )
    eval_count: Optional[int] = Field(None, description="Tokens generated")
    eval_duration: Optional[int] = Field(None, description="Generation duration")


class OllamaEmbeddingResponse(BaseModel):
    """Response model for Ollama embeddings endpoint."""

    embedding: List[float] = Field(..., description="Embedding vector")


class OllamaModelInfo(BaseModel):
    """Model information for Ollama."""

    name: str = Field(..., description="Model name")
    model: str = Field(..., description="Model identifier")
    modified_at: str = Field(..., description="Last modified timestamp")
    size: int = Field(..., description="Model size in bytes")
    digest: str = Field(..., description="Model digest")
    details: Optional[Dict[str, Any]] = Field(None, description="Model details")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")


class OllamaModelsResponse(BaseModel):
    """Response for model listing."""

    models: List[OllamaModelInfo] = Field(..., description="List of available models")


class OllamaShowResponse(BaseModel):
    """Response for showing model information."""

    model_config = ConfigDict(protected_namespaces=())

    modelfile: str = Field(..., description="Modelfile content")
    parameters: str = Field(..., description="Model parameters")
    template: str = Field(..., description="Model template")
    details: Dict[str, Any] = Field(..., description="Model details")
    model_info: Dict[str, Any] = Field(
        default_factory=dict, description="Additional model info"
    )


class OllamaPullResponse(BaseModel):
    """Response for model pull progress."""

    status: str = Field(..., description="Pull status")
    digest: Optional[str] = Field(None, description="Layer digest")
    total: Optional[int] = Field(None, description="Total size")
    completed: Optional[int] = Field(None, description="Downloaded size")


class OllamaVersionResponse(BaseModel):
    """Response for version endpoint."""

    version: str = Field(..., description="Ollama version")


# ===========================
# OpenAI API Models
# ===========================


class OpenAIMessage(BaseModel):
    """OpenAI chat message model."""

    role: Literal["system", "user", "assistant", "function", "tool"] = Field(
        ..., description="Message role"
    )
    content: Optional[Union[str, List[Dict[str, Any]]]] = Field(
        None, description="Message content"
    )
    name: Optional[str] = Field(None, description="Name of function/tool")
    function_call: Optional[Dict[str, Any]] = Field(None, description="Function call")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls")
    tool_call_id: Optional[str] = Field(None, description="Tool call ID")

    @model_validator(mode="after")
    def validate_content_or_function(self):
        """Ensure message has either content or function_call/tool_calls."""
        if (
            self.content is None
            and self.function_call is None
            and self.tool_calls is None
        ):
            raise ValueError(
                "Message must have either content, function_call, or tool_calls"
            )
        return self


class OpenAIFunction(BaseModel):
    """OpenAI function definition."""

    name: str = Field(..., description="Function name")
    description: Optional[str] = Field(None, description="Function description")
    parameters: Dict[str, Any] = Field(
        ..., description="Function parameters as JSON Schema"
    )


class OpenAITool(BaseModel):
    """OpenAI tool definition."""

    type: Literal["function"] = Field("function", description="Tool type")
    function: OpenAIFunction = Field(..., description="Function definition")


class OpenAIChatRequest(BaseModel):
    """OpenAI chat completion request model."""

    model: str = Field(..., description="Model to use")
    messages: List[OpenAIMessage] = Field(
        ..., min_length=1, description="Input messages"
    )

    # Sampling parameters
    temperature: Optional[float] = Field(
        1.0, ge=0.0, le=2.0, description="Sampling temperature"
    )
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Top-p sampling")
    n: Optional[int] = Field(1, ge=1, description="Number of completions")
    stream: Optional[bool] = Field(False, description="Stream response")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    max_tokens: Optional[int] = Field(
        None, ge=1, description="Maximum tokens to generate"
    )
    presence_penalty: Optional[float] = Field(
        0.0, ge=-2.0, le=2.0, description="Presence penalty"
    )
    frequency_penalty: Optional[float] = Field(
        0.0, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    logit_bias: Optional[Dict[str, float]] = Field(None, description="Token logit bias")
    user: Optional[str] = Field(None, description="User identifier")

    # Function calling
    functions: Optional[List[OpenAIFunction]] = Field(
        None, description="Available functions (deprecated)"
    )
    function_call: Optional[Union[str, Dict[str, str]]] = Field(
        None, description="Function call mode (deprecated)"
    )
    tools: Optional[List[OpenAITool]] = Field(None, description="Available tools")
    tool_choice: Optional[Union[str, Dict[str, Any]]] = Field(
        None, description="Tool choice mode"
    )

    # Additional parameters
    seed: Optional[int] = Field(None, description="Random seed")
    response_format: Optional[Dict[str, str]] = Field(
        None, description="Response format"
    )
    logprobs: Optional[bool] = Field(None, description="Return log probabilities")
    top_logprobs: Optional[int] = Field(
        None, ge=0, le=20, description="Number of top log probabilities"
    )


class OpenAIChoice(BaseModel):
    """OpenAI response choice model."""

    index: int = Field(..., description="Choice index")
    message: OpenAIMessage = Field(..., description="Generated message")
    finish_reason: Optional[str] = Field(None, description="Reason for completion")
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probabilities")


class OpenAIUsage(BaseModel):
    """OpenAI token usage model."""

    prompt_tokens: int = Field(..., description="Tokens in prompt")
    completion_tokens: Optional[int] = Field(
        None, description="Tokens in completion (not used for embeddings)"
    )
    total_tokens: int = Field(..., description="Total tokens used")


class OpenAIChatResponse(BaseModel):
    """OpenAI chat completion response model."""

    id: str = Field(
        default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:8]}",
        description="Unique ID",
    )
    object: Literal["chat.completion"] = Field(
        "chat.completion", description="Object type"
    )
    created: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Creation timestamp",
    )
    model: str = Field(..., description="Model used")
    choices: List[OpenAIChoice] = Field(..., description="Response choices")
    usage: Optional[OpenAIUsage] = Field(None, description="Token usage")
    system_fingerprint: Optional[str] = Field(None, description="System fingerprint")


class OpenAIEmbeddingRequest(BaseModel):
    """OpenAI embedding request model."""

    model: str = Field(..., description="ID of the model to use")
    input: Union[str, List[str], List[int], List[List[int]]] = Field(
        ..., description="Input text to embed, encoded as a string or array of tokens"
    )
    encoding_format: Optional[Literal["float", "base64"]] = Field(
        "float", description="Format to return embeddings in"
    )
    dimensions: Optional[int] = Field(
        None,
        description="Number of dimensions the resulting output embeddings should have",
    )
    user: Optional[str] = Field(
        None, description="Unique identifier representing end user"
    )


class OpenAIEmbeddingData(BaseModel):
    """Individual embedding data in OpenAI response."""

    object: Literal["embedding"] = Field("embedding", description="Object type")
    index: int = Field(..., description="Index of the embedding in the list")
    embedding: List[float] = Field(..., description="Embedding vector")


class OpenAIEmbeddingResponse(BaseModel):
    """OpenAI embedding response model."""

    object: Literal["list"] = Field("list", description="Object type")
    data: List[OpenAIEmbeddingData] = Field(
        ..., description="List of embedding objects"
    )
    model: str = Field(..., description="ID of the model used")
    usage: OpenAIUsage = Field(..., description="Usage statistics")


# OpenAI Streaming Models


class OpenAIDelta(BaseModel):
    """Delta content for streaming responses."""

    role: Optional[str] = Field(None, description="Role in first chunk")
    content: Optional[str] = Field(None, description="Content delta")
    function_call: Optional[Dict[str, Any]] = Field(
        None, description="Function call delta"
    )
    tool_calls: Optional[List[Dict[str, Any]]] = Field(
        None, description="Tool calls delta"
    )


class OpenAIStreamChoice(BaseModel):
    """Choice for streaming response."""

    index: int = Field(..., description="Choice index")
    delta: OpenAIDelta = Field(..., description="Content delta")
    finish_reason: Optional[str] = Field(
        None, description="Finish reason when complete"
    )
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probabilities")


class OpenAIStreamResponse(BaseModel):
    """OpenAI streaming chat completion response."""

    id: str = Field(..., description="Unique ID")
    object: Literal["chat.completion.chunk"] = Field(
        "chat.completion.chunk", description="Object type"
    )
    created: int = Field(..., description="Creation timestamp")
    model: str = Field(..., description="Model used")
    choices: List[OpenAIStreamChoice] = Field(..., description="Response choices")
    system_fingerprint: Optional[str] = Field(None, description="System fingerprint")


# OpenAI Model Models


class OpenAIModel(BaseModel):
    """OpenAI model information."""

    id: str = Field(..., description="Model ID")
    object: Literal["model"] = Field("model", description="Object type")
    created: int = Field(..., description="Creation timestamp")
    owned_by: Optional[str] = Field(None, description="Model owner")
    permission: Optional[List[Dict[str, Any]]] = Field(
        None, description="Model permissions"
    )
    root: Optional[str] = Field(None, description="Root model")
    parent: Optional[str] = Field(None, description="Parent model")


class OpenAIModelsResponse(BaseModel):
    """Response for OpenAI model listing."""

    object: Literal["list"] = Field("list", description="Object type")
    data: List[OpenAIModel] = Field(..., description="List of models")


# ===========================
# Error Models
# ===========================


class ErrorDetail(BaseModel):
    """Error detail model."""

    message: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")
    param: Optional[str] = Field(None, description="Parameter that caused error")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail = Field(..., description="Error details")


# ===========================
# Streaming Event Models
# ===========================


class StreamEvent(BaseModel):
    """Base class for streaming events."""

    event: str = Field(..., description="Event type")
    data: Any = Field(..., description="Event data")


class StreamDoneEvent(BaseModel):
    """Event indicating stream completion."""

    event: Literal["done"] = Field("done", description="Event type")
    data: Literal["[DONE]"] = Field("[DONE]", description="Completion marker")
