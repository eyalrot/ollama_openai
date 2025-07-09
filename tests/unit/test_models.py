"""
Unit tests for data models.
"""

import json
import pytest
from pydantic import ValidationError

from src.models import (
    OllamaGenerateRequest,
    OllamaChatMessage,
    OllamaChatRequest,
    OllamaGenerateResponse,
    OpenAIMessage,
    OpenAIChatRequest,
    OpenAIChoice,
    OpenAIUsage,
    OpenAIChatResponse,
    ModelInfo,
    ModelsResponse
)


class TestOllamaModels:
    """Test Ollama API models."""
    
    def test_ollama_chat_message(self):
        """Test OllamaChatMessage model."""
        msg = OllamaChatMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.images is None
        
        # With images
        msg_with_images = OllamaChatMessage(
            role="user",
            content="What's in this image?",
            images=["base64encodedimage"]
        )
        assert len(msg_with_images.images) == 1
    
    def test_ollama_chat_request(self):
        """Test OllamaChatRequest model."""
        req = OllamaChatRequest(
            model="llama2",
            messages=[
                OllamaChatMessage(role="system", content="You are helpful"),
                OllamaChatMessage(role="user", content="Hello")
            ]
        )
        assert req.model == "llama2"
        assert len(req.messages) == 2
        assert req.stream is True  # Default
        assert req.options is None
    
    def test_ollama_chat_request_with_options(self):
        """Test OllamaChatRequest with options."""
        req = OllamaChatRequest(
            model="mistral",
            messages=[OllamaChatMessage(role="user", content="Hi")],
            stream=False,
            options={"temperature": 0.7, "top_k": 40}
        )
        assert req.stream is False
        assert req.options["temperature"] == 0.7
    
    def test_ollama_generate_request(self):
        """Test OllamaGenerateRequest model."""
        req = OllamaGenerateRequest(
            model="llama2",
            prompt="Tell me a story"
        )
        assert req.model == "llama2"
        assert req.prompt == "Tell me a story"
        assert req.stream is True  # Default
        assert req.raw is False  # Default
    
    def test_ollama_generate_request_full(self):
        """Test OllamaGenerateRequest with all fields."""
        req = OllamaGenerateRequest(
            model="codellama",
            prompt="Write a function",
            images=["image1"],
            stream=False,
            options={"temperature": 0.5},
            system="You are a coder",
            template="### Instruction: {prompt}",
            context=[1, 2, 3],
            raw=True
        )
        assert req.model == "codellama"
        assert req.system == "You are a coder"
        assert req.raw is True
        assert len(req.context) == 3
    
    def test_ollama_generate_response(self):
        """Test OllamaGenerateResponse model."""
        resp = OllamaGenerateResponse(
            model="llama2",
            created_at="2024-01-01T00:00:00Z",
            response="Once upon a time...",
            done=True
        )
        assert resp.model == "llama2"
        assert resp.response == "Once upon a time..."
        assert resp.done is True
        assert resp.context is None
    
    def test_ollama_generate_response_with_metrics(self):
        """Test OllamaGenerateResponse with performance metrics."""
        resp = OllamaGenerateResponse(
            model="llama2",
            created_at="2024-01-01T00:00:00Z",
            response="Generated text",
            done=True,
            context=[1, 2, 3],
            total_duration=1000000000,  # 1 second in nanoseconds
            load_duration=100000000,
            prompt_eval_count=10,
            prompt_eval_duration=50000000,
            eval_count=20,
            eval_duration=850000000
        )
        assert resp.total_duration == 1000000000
        assert resp.eval_count == 20


class TestOpenAIModels:
    """Test OpenAI API models."""
    
    def test_openai_message(self):
        """Test OpenAIMessage model."""
        msg = OpenAIMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.name is None
        
        # With name
        msg_with_name = OpenAIMessage(
            role="user",
            content="Hi",
            name="john"
        )
        assert msg_with_name.name == "john"
    
    def test_openai_message_with_content_parts(self):
        """Test OpenAIMessage with content parts (for vision)."""
        msg = OpenAIMessage(
            role="user",
            content=[
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
            ]
        )
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2
    
    def test_openai_chat_request(self):
        """Test OpenAIChatRequest model."""
        req = OpenAIChatRequest(
            model="gpt-3.5-turbo",
            messages=[
                OpenAIMessage(role="system", content="You are helpful"),
                OpenAIMessage(role="user", content="Hello")
            ]
        )
        assert req.model == "gpt-3.5-turbo"
        assert len(req.messages) == 2
        assert req.temperature == 1.0  # Default
        assert req.stream is False  # Default
    
    def test_openai_chat_request_with_params(self):
        """Test OpenAIChatRequest with parameters."""
        req = OpenAIChatRequest(
            model="gpt-4",
            messages=[OpenAIMessage(role="user", content="Hi")],
            temperature=0.7,
            top_p=0.9,
            n=2,
            stream=True,
            stop=["END", "STOP"],
            max_tokens=150,
            presence_penalty=0.1,
            frequency_penalty=0.2,
            user="test-user"
        )
        assert req.temperature == 0.7
        assert req.n == 2
        assert req.stream is True
        assert req.max_tokens == 150
        assert req.stop == ["END", "STOP"]
    
    def test_openai_usage(self):
        """Test OpenAIUsage model."""
        usage = OpenAIUsage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30
    
    def test_openai_choice(self):
        """Test OpenAIChoice model."""
        choice = OpenAIChoice(
            index=0,
            message=OpenAIMessage(role="assistant", content="Hello there!"),
            finish_reason="stop"
        )
        assert choice.index == 0
        assert choice.message.role == "assistant"
        assert choice.message.content == "Hello there!"
        assert choice.finish_reason == "stop"
    
    def test_openai_chat_response(self):
        """Test OpenAIChatResponse model."""
        resp = OpenAIChatResponse(
            id="chatcmpl-123",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content="Hi!"),
                    finish_reason="stop"
                )
            ]
        )
        assert resp.id == "chatcmpl-123"
        assert resp.object == "chat.completion"
        assert resp.model == "gpt-3.5-turbo"
        assert len(resp.choices) == 1
        assert resp.usage is None
    
    def test_openai_chat_response_with_usage(self):
        """Test OpenAIChatResponse with usage info."""
        resp = OpenAIChatResponse(
            id="chatcmpl-456",
            created=1234567890,
            model="gpt-4",
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content="Response"),
                    finish_reason="stop"
                )
            ],
            usage=OpenAIUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            system_fingerprint="fp_123"
        )
        assert resp.usage.total_tokens == 15
        assert resp.system_fingerprint == "fp_123"


class TestModelListingModels:
    """Test model listing models."""
    
    def test_model_info(self):
        """Test ModelInfo model."""
        info = ModelInfo(
            name="llama2:latest",
            modified_at="2024-01-01T00:00:00Z",
            size=3826793216,
            digest="sha256:abc123..."
        )
        assert info.name == "llama2:latest"
        assert info.size == 3826793216
        assert info.details is None
    
    def test_model_info_with_details(self):
        """Test ModelInfo with details."""
        info = ModelInfo(
            name="mistral:7b",
            modified_at="2024-01-01T00:00:00Z",
            size=4109000000,
            digest="sha256:def456...",
            details={
                "format": "gguf",
                "family": "mistral",
                "parameter_size": "7B"
            }
        )
        assert info.details["family"] == "mistral"
        assert info.details["parameter_size"] == "7B"
    
    def test_models_response(self):
        """Test ModelsResponse model."""
        resp = ModelsResponse(
            models=[
                ModelInfo(
                    name="llama2:latest",
                    modified_at="2024-01-01T00:00:00Z",
                    size=3826793216,
                    digest="sha256:abc123..."
                ),
                ModelInfo(
                    name="mistral:latest",
                    modified_at="2024-01-02T00:00:00Z",
                    size=4109000000,
                    digest="sha256:def456..."
                )
            ]
        )
        assert len(resp.models) == 2
        assert resp.models[0].name == "llama2:latest"
        assert resp.models[1].name == "mistral:latest"


class TestModelSerialization:
    """Test model serialization/deserialization."""
    
    def test_ollama_chat_request_json(self):
        """Test OllamaChatRequest JSON serialization."""
        req = OllamaChatRequest(
            model="llama2",
            messages=[
                OllamaChatMessage(role="user", content="Hello")
            ],
            stream=False
        )
        
        # Serialize to JSON
        json_str = req.model_dump_json()
        data = json.loads(json_str)
        
        assert data["model"] == "llama2"
        assert data["stream"] is False
        assert len(data["messages"]) == 1
        
        # Deserialize back
        req2 = OllamaChatRequest.model_validate_json(json_str)
        assert req2.model == req.model
        assert req2.messages[0].content == req.messages[0].content
    
    def test_openai_chat_response_json(self):
        """Test OpenAIChatResponse JSON serialization."""
        resp = OpenAIChatResponse(
            id="test-123",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content="Hello!"),
                    finish_reason="stop"
                )
            ],
            usage=OpenAIUsage(prompt_tokens=5, completion_tokens=2, total_tokens=7)
        )
        
        # Serialize to JSON
        json_str = resp.model_dump_json()
        data = json.loads(json_str)
        
        # Verify OpenAI format
        assert data["id"] == "test-123"
        assert data["object"] == "chat.completion"
        assert data["choices"][0]["message"]["role"] == "assistant"
        assert data["usage"]["total_tokens"] == 7
        
        # Deserialize back
        resp2 = OpenAIChatResponse.model_validate_json(json_str)
        assert resp2.id == resp.id
        assert resp2.choices[0].message.content == resp.choices[0].message.content