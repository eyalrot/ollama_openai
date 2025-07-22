"""
Unit tests for Pydantic models.
"""

import json

import pytest
from pydantic import ValidationError

from src.models import (
    # Error Models
    ErrorDetail,
    ErrorResponse,
    OllamaChatMessage,
    OllamaChatRequest,
    OllamaChatResponse,
    OllamaCopyRequest,
    OllamaCreateRequest,
    OllamaDeleteRequest,
    OllamaEmbeddingRequest,
    OllamaEmbeddingResponse,
    OllamaEmbedRequest,
    OllamaGenerateRequest,
    # Ollama Response Models
    OllamaGenerateResponse,
    OllamaModelInfo,
    OllamaModelsResponse,
    # Ollama Request Models
    OllamaOptions,
    OllamaPullRequest,
    OllamaPullResponse,
    OllamaPushRequest,
    OllamaShowRequest,
    OllamaShowResponse,
    OllamaVersionResponse,
    OpenAIChatRequest,
    OpenAIChatResponse,
    # OpenAI Response Models
    OpenAIChoice,
    # OpenAI Streaming Models
    OpenAIDelta,
    OpenAIFunction,
    # OpenAI Request Models
    OpenAIMessage,
    # OpenAI Model Models
    OpenAIModel,
    OpenAIModelsResponse,
    OpenAIStreamChoice,
    OpenAIStreamResponse,
    OpenAITool,
    OpenAIUsage,
    StreamDoneEvent,
    # Streaming Event Models
    StreamEvent,
)


class TestOllamaOptions:
    """Test OllamaOptions model."""

    def test_valid_options(self):
        """Test creating options with valid values."""
        options = OllamaOptions(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            num_predict=100,
            seed=42,
            stop=["\\n", "###"],
        )
        assert options.temperature == 0.7
        assert options.top_p == 0.9
        assert options.top_k == 40
        assert options.num_predict == 100
        assert options.seed == 42
        assert options.stop == ["\\n", "###"]

    def test_all_options(self):
        """Test creating options with all fields."""
        options = OllamaOptions(
            # Generation parameters
            seed=42,
            num_predict=100,
            top_k=40,
            top_p=0.9,
            tfs_z=1.0,
            typical_p=1.0,
            repeat_last_n=64,
            temperature=0.7,
            repeat_penalty=1.1,
            presence_penalty=0.0,
            frequency_penalty=0.0,
            mirostat=0,
            mirostat_tau=5.0,
            mirostat_eta=0.1,
            penalize_newline=True,
            stop=["\\n"],
            # Model loading parameters
            numa=False,
            num_ctx=2048,
            num_batch=512,
            num_gqa=1,
            num_gpu=1,
            main_gpu=0,
            low_vram=False,
            f16_kv=True,
            vocab_only=False,
            use_mmap=True,
            use_mlock=False,
            num_thread=4,
        )
        assert options.seed == 42
        assert options.num_ctx == 2048
        assert options.num_gpu == 1

    def test_optional_fields(self):
        """Test that all fields are optional."""
        options = OllamaOptions()
        assert options.temperature is None
        assert options.top_p is None
        assert options.seed is None

    def test_validation_ranges(self):
        """Test field validation ranges."""
        # Valid ranges
        options = OllamaOptions(top_p=0.0, temperature=0.0)
        assert options.top_p == 0.0
        assert options.temperature == 0.0

        options = OllamaOptions(top_p=1.0)
        assert options.top_p == 1.0

        # Invalid ranges
        with pytest.raises(ValidationError):
            OllamaOptions(top_p=-0.1)

        with pytest.raises(ValidationError):
            OllamaOptions(top_p=1.1)

        with pytest.raises(ValidationError):
            OllamaOptions(temperature=-0.1)


class TestOllamaGenerateRequest:
    """Test OllamaGenerateRequest model."""

    def test_minimal_request(self):
        """Test creating request with minimal fields."""
        req = OllamaGenerateRequest(
            model="llama2",
            prompt="Hello, world!",
        )
        assert req.model == "llama2"
        assert req.prompt == "Hello, world!"
        assert req.stream is True  # Default
        assert req.raw is False  # Default
        assert req.keep_alive == "5m"  # Default

    def test_full_request(self):
        """Test creating request with all fields."""
        options = OllamaOptions(temperature=0.7)
        req = OllamaGenerateRequest(
            model="llama2",
            prompt="Hello, world!",
            images=["base64encodedimage"],
            format="json",
            options=options,
            system="You are a helpful assistant",
            template="{{.System}} {{.Prompt}}",
            context=[1, 2, 3],
            stream=False,
            raw=True,
            keep_alive=300,
        )
        assert req.model == "llama2"
        assert req.images == ["base64encodedimage"]
        assert req.format == "json"
        assert req.options.temperature == 0.7
        assert req.stream is False
        assert req.keep_alive == 300

    def test_format_validation(self):
        """Test format field validation."""
        # Valid format
        req = OllamaGenerateRequest(model="llama2", prompt="test", format="json")
        assert req.format == "json"

        # None is valid (optional)
        req = OllamaGenerateRequest(model="llama2", prompt="test")
        assert req.format is None

        # Invalid format
        with pytest.raises(ValidationError):
            OllamaGenerateRequest(model="llama2", prompt="test", format="xml")


class TestOllamaChatMessage:
    """Test OllamaChatMessage model."""

    def test_valid_message(self):
        """Test creating valid chat message."""
        msg = OllamaChatMessage(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"
        assert msg.images is None

    def test_message_with_images(self):
        """Test message with images."""
        msg = OllamaChatMessage(
            role="user",
            content="What's in this image?",
            images=["base64image1", "base64image2"],
        )
        assert len(msg.images) == 2

    def test_message_with_tool_calls(self):
        """Test assistant message with tool calls."""
        msg = OllamaChatMessage(
            role="assistant",
            content="I'll help you with that.",
            tool_calls=[{"name": "search", "arguments": {"query": "test"}}],
        )
        assert msg.tool_calls[0]["name"] == "search"

    def test_role_validation(self):
        """Test role field validation."""
        # Valid roles
        for role in ["system", "user", "assistant", "tool"]:
            msg = OllamaChatMessage(role=role, content="test")
            assert msg.role == role

        # Invalid role
        with pytest.raises(ValidationError):
            OllamaChatMessage(role="invalid", content="test")


class TestOllamaChatRequest:
    """Test OllamaChatRequest model."""

    def test_minimal_request(self):
        """Test creating request with minimal fields."""
        req = OllamaChatRequest(
            model="llama2",
            messages=[OllamaChatMessage(role="user", content="Hello!")],
        )
        assert req.model == "llama2"
        assert len(req.messages) == 1
        assert req.stream is True  # Default

    def test_full_request(self):
        """Test creating request with all fields."""
        options = OllamaOptions(temperature=0.7)
        req = OllamaChatRequest(
            model="llama2",
            messages=[
                OllamaChatMessage(role="system", content="You are helpful"),
                OllamaChatMessage(role="user", content="Hello!"),
            ],
            format="json",
            options=options,
            template="{{.System}} {{.Prompt}}",
            stream=False,
            keep_alive=600,
            tools=[{"type": "function", "function": {"name": "search"}}],
        )
        assert len(req.messages) == 2
        assert req.format == "json"
        assert req.options.temperature == 0.7
        assert req.stream is False
        assert req.keep_alive == 600
        assert len(req.tools) == 1

    def test_messages_validation(self):
        """Test messages field validation."""
        # Empty messages list
        with pytest.raises(ValidationError):
            OllamaChatRequest(model="llama2", messages=[])


class TestOllamaEmbeddingRequest:
    """Test OllamaEmbeddingRequest model."""

    def test_minimal_request(self):
        """Test creating embedding request."""
        req = OllamaEmbeddingRequest(
            model="llama2",
            prompt="Hello, world!",
        )
        assert req.model == "llama2"
        assert req.prompt == "Hello, world!"
        assert req.keep_alive == "5m"

    def test_with_options(self):
        """Test embedding request with options."""
        options = OllamaOptions(num_thread=8)
        req = OllamaEmbeddingRequest(
            model="llama2",
            prompt="Hello, world!",
            options=options,
            keep_alive=300,
        )
        assert req.options.num_thread == 8
        assert req.keep_alive == 300


class TestOllamaEmbedRequest:
    """Test OllamaEmbedRequest model (new /embed endpoint)."""

    def test_minimal_request_single_input(self):
        """Test minimal embed request with single string input."""
        req = OllamaEmbedRequest(
            model="text-embedding-ada-002", input="Test embedding text"
        )
        assert req.model == "text-embedding-ada-002"
        assert req.input == "Test embedding text"
        assert req.truncate is None
        assert req.keep_alive == "5m"

    def test_minimal_request_list_input(self):
        """Test minimal embed request with list input."""
        req = OllamaEmbedRequest(
            model="text-embedding-ada-002", input=["Text one", "Text two", "Text three"]
        )
        assert req.model == "text-embedding-ada-002"
        assert isinstance(req.input, list)
        assert len(req.input) == 3
        assert req.input[0] == "Text one"

    def test_with_all_options(self):
        """Test embed request with all optional fields."""
        req = OllamaEmbedRequest(
            model="text-embedding-ada-002",
            input="Test text",
            truncate=True,
            options=OllamaOptions(temperature=0.5, top_p=0.9),
            keep_alive="10m",
        )
        assert req.model == "text-embedding-ada-002"
        assert req.input == "Test text"
        assert req.truncate is True
        assert req.options.temperature == 0.5
        assert req.options.top_p == 0.9
        assert req.keep_alive == "10m"

    def test_validation_missing_required_fields(self):
        """Test validation errors for missing required fields."""
        # Missing model
        with pytest.raises(ValidationError) as exc_info:
            OllamaEmbedRequest(input="Test text")
        assert "model" in str(exc_info.value).lower()

        # Missing input
        with pytest.raises(ValidationError) as exc_info:
            OllamaEmbedRequest(model="text-embedding-ada-002")
        assert "input" in str(exc_info.value).lower()

    def test_empty_input_validation(self):
        """Test validation for empty input."""
        # Empty string should be allowed
        req = OllamaEmbedRequest(model="text-embedding-ada-002", input="")
        assert req.input == ""

        # Empty list should be allowed
        req = OllamaEmbedRequest(model="text-embedding-ada-002", input=[])
        assert req.input == []


class TestOllamaModelManagementRequests:
    """Test model management request models."""

    def test_pull_request(self):
        """Test pull request model."""
        req = OllamaPullRequest(name="llama2:latest")
        assert req.name == "llama2:latest"
        assert req.insecure is False
        assert req.stream is True

        req = OllamaPullRequest(name="llama2", insecure=True, stream=False)
        assert req.insecure is True
        assert req.stream is False

    def test_push_request(self):
        """Test push request model."""
        req = OllamaPushRequest(name="mymodel:latest")
        assert req.name == "mymodel:latest"
        assert req.insecure is False
        assert req.stream is True

    def test_create_request(self):
        """Test create request model."""
        req = OllamaCreateRequest(
            name="mymodel",
            modelfile="FROM llama2\\nSYSTEM You are helpful",
        )
        assert req.name == "mymodel"
        assert req.modelfile.startswith("FROM llama2")
        assert req.stream is True
        assert req.path is None

    def test_copy_request(self):
        """Test copy request model."""
        req = OllamaCopyRequest(source="llama2", destination="mymodel")
        assert req.source == "llama2"
        assert req.destination == "mymodel"

    def test_delete_request(self):
        """Test delete request model."""
        req = OllamaDeleteRequest(name="mymodel")
        assert req.name == "mymodel"

    def test_show_request(self):
        """Test show request model."""
        req = OllamaShowRequest(name="llama2")
        assert req.name == "llama2"
        assert req.verbose is False

        req = OllamaShowRequest(name="llama2", verbose=True)
        assert req.verbose is True

    def test_show_request_with_model_field(self):
        """Test show request with new 'model' field support."""
        # Test with 'model' field only
        req = OllamaShowRequest(model="llama2")
        assert req.model == "llama2"
        assert req.name == "llama2"  # Should be copied from model
        assert req.verbose is False

        # Test with both 'name' and 'model' fields
        req = OllamaShowRequest(name="llama2", model="llama3")
        assert req.name == "llama2"  # name takes precedence
        assert req.model == "llama3"

        # Test with neither field should raise error
        with pytest.raises(ValidationError) as exc_info:
            OllamaShowRequest(verbose=True)
        assert "Either 'name' or 'model' field is required" in str(exc_info.value)


class TestOllamaResponses:
    """Test Ollama response models."""

    def test_generate_response(self):
        """Test generate response model."""
        resp = OllamaGenerateResponse(
            model="llama2",
            created_at="2023-08-04T19:22:45.499127Z",
            response="Hello! How can I help you?",
            done=True,
            eval_count=25,
            eval_duration=1234567890,
        )
        assert resp.model == "llama2"
        assert resp.response == "Hello! How can I help you?"
        assert resp.done is True
        assert resp.eval_count == 25

    def test_generate_response_partial(self):
        """Test partial generate response."""
        resp = OllamaGenerateResponse(
            model="llama2",
            created_at="2023-08-04T19:22:45.499127Z",
            response="Hello",
            done=False,
        )
        assert resp.response == "Hello"
        assert resp.done is False
        assert resp.eval_count is None

    def test_chat_response(self):
        """Test chat response model."""
        msg = OllamaChatMessage(role="assistant", content="Hello!")
        resp = OllamaChatResponse(
            model="llama2",
            created_at="2023-08-04T19:22:45.499127Z",
            message=msg,
            done=True,
            total_duration=5000000000,
            eval_count=20,
        )
        assert resp.model == "llama2"
        assert resp.message.content == "Hello!"
        assert resp.done is True
        assert resp.total_duration == 5000000000

    def test_embedding_response(self):
        """Test embedding response model."""
        resp = OllamaEmbeddingResponse(
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
        )
        assert len(resp.embedding) == 5
        assert resp.embedding[0] == 0.1

    def test_model_info(self):
        """Test model info model."""
        info = OllamaModelInfo(
            name="llama2:latest",
            model="llama2:latest",
            modified_at="2023-08-04T19:22:45.499127Z",
            size=3826793152,
            digest="sha256:abc123",
            details={"format": "gguf", "family": "llama"},
        )
        assert info.name == "llama2:latest"
        assert info.size == 3826793152
        assert info.details["family"] == "llama"

    def test_models_response(self):
        """Test models listing response."""
        models = [
            OllamaModelInfo(
                name="llama2:latest",
                model="llama2:latest",
                modified_at="2023-08-04T19:22:45.499127Z",
                size=3826793152,
                digest="sha256:abc123",
            ),
            OllamaModelInfo(
                name="codellama:latest",
                model="codellama:latest",
                modified_at="2023-08-05T19:22:45.499127Z",
                size=4826793152,
                digest="sha256:def456",
            ),
        ]
        resp = OllamaModelsResponse(models=models)
        assert len(resp.models) == 2
        assert resp.models[0].name == "llama2:latest"
        assert resp.models[1].name == "codellama:latest"

    def test_show_response(self):
        """Test show response model."""
        resp = OllamaShowResponse(
            modelfile="FROM llama2",
            parameters="temperature 0.7",
            template="{{.System}} {{.Prompt}}",
            details={"format": "gguf", "family": "llama"},
        )
        assert resp.modelfile == "FROM llama2"
        assert resp.parameters == "temperature 0.7"
        assert resp.details["family"] == "llama"

    def test_pull_response(self):
        """Test pull progress response."""
        resp = OllamaPullResponse(
            status="pulling manifest",
            digest="sha256:abc123",
            total=1024,
            completed=512,
        )
        assert resp.status == "pulling manifest"
        assert resp.total == 1024
        assert resp.completed == 512

    def test_version_response(self):
        """Test version response."""
        resp = OllamaVersionResponse(version="0.1.29")
        assert resp.version == "0.1.29"


class TestOpenAIMessage:
    """Test OpenAIMessage model."""

    def test_text_message(self):
        """Test simple text message."""
        msg = OpenAIMessage(role="user", content="Hello!")
        assert msg.role == "user"
        assert msg.content == "Hello!"

    def test_multimodal_message(self):
        """Test message with content parts."""
        msg = OpenAIMessage(
            role="user",
            content=[
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": {"url": "data:image/png;base64,..."},
                },
            ],
        )
        assert msg.role == "user"
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2

    def test_function_message(self):
        """Test function message."""
        msg = OpenAIMessage(
            role="function",
            content="search results",
            name="search_function",
        )
        assert msg.role == "function"
        assert msg.name == "search_function"

    def test_assistant_with_function_call(self):
        """Test assistant message with function call."""
        msg = OpenAIMessage(
            role="assistant",
            content=None,
            function_call={"name": "search", "arguments": '{"query": "test"}'},
        )
        assert msg.function_call["name"] == "search"

    def test_assistant_with_tool_calls(self):
        """Test assistant message with tool calls."""
        msg = OpenAIMessage(
            role="assistant",
            content=None,
            tool_calls=[
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "search", "arguments": '{"query": "test"}'},
                }
            ],
        )
        assert msg.tool_calls[0]["id"] == "call_123"

    def test_tool_message(self):
        """Test tool message."""
        msg = OpenAIMessage(
            role="tool",
            content="search results",
            tool_call_id="call_123",
        )
        assert msg.role == "tool"
        assert msg.tool_call_id == "call_123"

    def test_validation_content_or_function(self):
        """Test validation that message must have content or function."""
        # Valid: has content
        msg = OpenAIMessage(role="user", content="test")
        assert msg.content == "test"

        # Valid: has function_call
        msg = OpenAIMessage(
            role="assistant",
            content=None,
            function_call={"name": "test"},
        )
        assert msg.function_call["name"] == "test"

        # Invalid: neither content nor function
        with pytest.raises(ValidationError) as exc_info:
            OpenAIMessage(role="assistant")
        assert "must have either content" in str(exc_info.value)


class TestOpenAIFunction:
    """Test OpenAIFunction model."""

    def test_function_definition(self):
        """Test function definition."""
        func = OpenAIFunction(
            name="search",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                },
                "required": ["query"],
            },
        )
        assert func.name == "search"
        assert func.description == "Search the web"
        assert func.parameters["properties"]["query"]["type"] == "string"

    def test_minimal_function(self):
        """Test minimal function definition."""
        func = OpenAIFunction(
            name="get_time",
            parameters={"type": "object", "properties": {}},
        )
        assert func.name == "get_time"
        assert func.description is None


class TestOpenAITool:
    """Test OpenAITool model."""

    def test_tool_definition(self):
        """Test tool definition."""
        func = OpenAIFunction(
            name="search",
            parameters={"type": "object", "properties": {}},
        )
        tool = OpenAITool(type="function", function=func)
        assert tool.type == "function"
        assert tool.function.name == "search"


class TestOpenAIChatRequest:
    """Test OpenAIChatRequest model."""

    def test_minimal_request(self):
        """Test minimal chat request."""
        req = OpenAIChatRequest(
            model="gpt-3.5-turbo",
            messages=[OpenAIMessage(role="user", content="Hello!")],
        )
        assert req.model == "gpt-3.5-turbo"
        assert len(req.messages) == 1
        assert req.temperature == 1.0  # Default
        assert req.stream is False  # Default

    def test_full_request(self):
        """Test request with all parameters."""
        func = OpenAIFunction(
            name="search",
            parameters={"type": "object", "properties": {}},
        )
        tool = OpenAITool(function=func)

        req = OpenAIChatRequest(
            model="gpt-4",
            messages=[
                OpenAIMessage(role="system", content="You are helpful"),
                OpenAIMessage(role="user", content="Hello!"),
            ],
            temperature=0.7,
            top_p=0.9,
            n=2,
            stream=True,
            stop=["\\n", "###"],
            max_tokens=100,
            presence_penalty=0.1,
            frequency_penalty=0.1,
            logit_bias={"50256": -100},
            user="user123",
            tools=[tool],
            tool_choice="auto",
            seed=42,
            response_format={"type": "json_object"},
            logprobs=True,
            top_logprobs=5,
        )
        assert req.model == "gpt-4"
        assert req.temperature == 0.7
        assert req.n == 2
        assert req.stream is True
        assert req.max_tokens == 100
        assert req.seed == 42
        assert len(req.tools) == 1

    def test_deprecated_function_calling(self):
        """Test deprecated function calling parameters."""
        func = OpenAIFunction(
            name="search",
            parameters={"type": "object", "properties": {}},
        )
        req = OpenAIChatRequest(
            model="gpt-3.5-turbo",
            messages=[OpenAIMessage(role="user", content="Hello!")],
            functions=[func],
            function_call="auto",
        )
        assert len(req.functions) == 1
        assert req.function_call == "auto"

    def test_parameter_validation(self):
        """Test parameter validation."""
        messages = [OpenAIMessage(role="user", content="test")]

        # Temperature range
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, temperature=-0.1)
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, temperature=2.1)

        # Top-p range
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, top_p=-0.1)
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, top_p=1.1)

        # Penalty ranges
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, presence_penalty=-2.1)
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, frequency_penalty=2.1)

        # N must be positive
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, n=0)

        # Max tokens must be positive
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, max_tokens=0)

        # Top logprobs range
        with pytest.raises(ValidationError):
            OpenAIChatRequest(model="gpt-4", messages=messages, top_logprobs=21)


class TestOpenAIResponses:
    """Test OpenAI response models."""

    def test_chat_response(self):
        """Test chat completion response."""
        choice = OpenAIChoice(
            index=0,
            message=OpenAIMessage(role="assistant", content="Hello!"),
            finish_reason="stop",
        )
        usage = OpenAIUsage(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )
        resp = OpenAIChatResponse(
            model="gpt-3.5-turbo",
            choices=[choice],
            usage=usage,
        )
        assert resp.model == "gpt-3.5-turbo"
        assert resp.object == "chat.completion"
        assert len(resp.choices) == 1
        assert resp.choices[0].message.content == "Hello!"
        assert resp.usage.total_tokens == 15
        assert resp.id.startswith("chatcmpl-")
        assert isinstance(resp.created, int)

    def test_chat_response_defaults(self):
        """Test chat response with defaults."""
        choice = OpenAIChoice(
            index=0,
            message=OpenAIMessage(role="assistant", content="Hi!"),
        )
        resp = OpenAIChatResponse(
            model="gpt-3.5-turbo",
            choices=[choice],
        )
        assert resp.id.startswith("chatcmpl-")
        assert resp.created > 0
        assert resp.usage is None
        assert resp.system_fingerprint is None

    def test_streaming_response(self):
        """Test streaming response."""
        delta = OpenAIDelta(content="Hello")
        choice = OpenAIStreamChoice(index=0, delta=delta)
        resp = OpenAIStreamResponse(
            id="chatcmpl-123",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[choice],
        )
        assert resp.object == "chat.completion.chunk"
        assert resp.choices[0].delta.content == "Hello"

    def test_streaming_first_chunk(self):
        """Test first streaming chunk with role."""
        delta = OpenAIDelta(role="assistant", content="")
        choice = OpenAIStreamChoice(index=0, delta=delta)
        resp = OpenAIStreamResponse(
            id="chatcmpl-123",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[choice],
        )
        assert resp.choices[0].delta.role == "assistant"
        assert resp.choices[0].delta.content == ""

    def test_streaming_final_chunk(self):
        """Test final streaming chunk."""
        delta = OpenAIDelta()
        choice = OpenAIStreamChoice(
            index=0,
            delta=delta,
            finish_reason="stop",
        )
        resp = OpenAIStreamResponse(
            id="chatcmpl-123",
            created=1234567890,
            model="gpt-3.5-turbo",
            choices=[choice],
        )
        assert resp.choices[0].finish_reason == "stop"
        assert resp.choices[0].delta.content is None


class TestOpenAIModels:
    """Test OpenAI model listing models."""

    def test_model_info(self):
        """Test model information."""
        model = OpenAIModel(
            id="gpt-3.5-turbo",
            created=1234567890,
            owned_by="openai",
        )
        assert model.id == "gpt-3.5-turbo"
        assert model.object == "model"
        assert model.owned_by == "openai"

    def test_model_info_without_owned_by(self):
        """Test model information without owned_by field (for OpenRouter compatibility)."""
        model = OpenAIModel(
            id="anthropic/claude-3-sonnet",
            created=1234567890,
        )
        assert model.id == "anthropic/claude-3-sonnet"
        assert model.object == "model"
        assert model.owned_by is None

    def test_models_response(self):
        """Test models listing response."""
        models = [
            OpenAIModel(id="gpt-3.5-turbo", created=1234567890, owned_by="openai"),
            OpenAIModel(id="gpt-4", created=1234567891, owned_by="openai"),
        ]
        resp = OpenAIModelsResponse(data=models)
        assert resp.object == "list"
        assert len(resp.data) == 2
        assert resp.data[0].id == "gpt-3.5-turbo"


class TestErrorModels:
    """Test error models."""

    def test_error_detail(self):
        """Test error detail model."""
        error = ErrorDetail(
            message="Invalid request",
            type="invalid_request_error",
            param="messages",
            code="invalid_messages",
        )
        assert error.message == "Invalid request"
        assert error.type == "invalid_request_error"
        assert error.param == "messages"
        assert error.code == "invalid_messages"

    def test_minimal_error(self):
        """Test minimal error."""
        error = ErrorDetail(
            message="Server error",
            type="server_error",
        )
        assert error.message == "Server error"
        assert error.param is None
        assert error.code is None

    def test_error_response(self):
        """Test error response."""
        detail = ErrorDetail(message="Bad request", type="invalid_request_error")
        resp = ErrorResponse(error=detail)
        assert resp.error.message == "Bad request"


class TestStreamingEvents:
    """Test streaming event models."""

    def test_stream_event(self):
        """Test generic stream event."""
        event = StreamEvent(event="message", data={"text": "Hello"})
        assert event.event == "message"
        assert event.data["text"] == "Hello"

    def test_stream_done_event(self):
        """Test stream done event."""
        event = StreamDoneEvent()
        assert event.event == "done"
        assert event.data == "[DONE]"


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_ollama_request_json(self):
        """Test Ollama request JSON serialization."""
        req = OllamaChatRequest(
            model="llama2",
            messages=[
                OllamaChatMessage(role="user", content="Hello!"),
            ],
            stream=False,
        )
        json_str = req.model_dump_json()
        data = json.loads(json_str)
        assert data["model"] == "llama2"
        assert data["messages"][0]["content"] == "Hello!"
        assert data["stream"] is False

        # Deserialize back
        req2 = OllamaChatRequest.model_validate(data)
        assert req2.model == req.model
        assert req2.messages[0].content == req.messages[0].content

    def test_openai_response_json(self):
        """Test OpenAI response JSON serialization."""
        resp = OpenAIChatResponse(
            model="gpt-3.5-turbo",
            choices=[
                OpenAIChoice(
                    index=0,
                    message=OpenAIMessage(role="assistant", content="Hello!"),
                    finish_reason="stop",
                )
            ],
        )
        json_str = resp.model_dump_json()
        data = json.loads(json_str)
        assert data["model"] == "gpt-3.5-turbo"
        assert data["choices"][0]["message"]["content"] == "Hello!"

        # Deserialize back
        resp2 = OpenAIChatResponse.model_validate(data)
        assert resp2.model == resp.model
        assert resp2.choices[0].message.content == resp.choices[0].message.content

    def test_exclude_none_serialization(self):
        """Test that None values are excluded from serialization."""
        req = OllamaGenerateRequest(
            model="llama2",
            prompt="Hello",
        )
        data = req.model_dump(exclude_none=True)
        assert "images" not in data
        assert "system" not in data
        assert "options" not in data

    def test_field_aliases(self):
        """Test that field descriptions are preserved."""
        # The Field descriptions are for documentation, not aliases
        msg = OllamaChatMessage(role="user", content="test")
        assert hasattr(msg.__class__.model_fields["role"], "description")
        assert msg.__class__.model_fields["role"].description == "Message role"
