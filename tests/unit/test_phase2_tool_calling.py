"""
Tests for Phase 2 tool calling functionality.

This module tests the translation of tool calling requests and responses
between Ollama and OpenAI formats.
"""

import pytest
from unittest.mock import Mock

from src.models import (
    OllamaChatRequest,
    OllamaChatMessage,
    OllamaChatResponse,
    OpenAIChatRequest,
    OpenAIChatResponse,
    OpenAIMessage,
    OpenAIChoice,
)
from src.translators.chat import ChatTranslator
from src.utils.exceptions import TranslationError


class TestToolCalling:
    """Test tool calling translation functionality."""

    @pytest.fixture
    def chat_translator(self):
        """Create a chat translator instance."""
        return ChatTranslator()

    def test_translate_tools_to_openai_format(self, chat_translator):
        """Test translation of Ollama tools to OpenAI format."""
        ollama_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        }
                    }
                }
            }
        ]

        openai_tools = chat_translator._translate_tools(ollama_tools)
        
        assert len(openai_tools) == 1
        assert openai_tools[0].type == "function"
        assert openai_tools[0].function.name == "get_weather"
        assert openai_tools[0].function.description == "Get weather information"
        assert "location" in openai_tools[0].function.parameters["properties"]

    def test_translate_direct_function_to_openai_format(self, chat_translator):
        """Test translation of direct function definition to OpenAI format."""
        ollama_tools = [
            {
                "name": "calculate",
                "description": "Perform calculation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"}
                    }
                }
            }
        ]

        openai_tools = chat_translator._translate_tools(ollama_tools)
        
        assert len(openai_tools) == 1
        assert openai_tools[0].type == "function"
        assert openai_tools[0].function.name == "calculate"
        assert openai_tools[0].function.description == "Perform calculation"

    def test_translate_request_with_tools(self, chat_translator):
        """Test translation of Ollama request with tools to OpenAI format."""
        request = OllamaChatRequest(
            model="llama2",
            messages=[OllamaChatMessage(role="user", content="What's the weather?")],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Get weather",
                        "parameters": {"type": "object"}
                    }
                }
            ]
        )

        result = chat_translator.translate_request(request)
        
        assert isinstance(result, OpenAIChatRequest)
        assert result.tools is not None
        assert len(result.tools) == 1
        assert result.tools[0].function.name == "get_weather"

    def test_translate_tool_calls_response(self, chat_translator):
        """Test translation of OpenAI tool calls response to Ollama format."""
        openai_tool_calls = [
            {
                "id": "call_123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "New York"}'
                }
            }
        ]

        ollama_tool_calls = chat_translator._translate_tool_calls(openai_tool_calls)
        
        assert len(ollama_tool_calls) == 1
        assert ollama_tool_calls[0]["id"] == "call_123"
        assert ollama_tool_calls[0]["type"] == "function"
        assert ollama_tool_calls[0]["function"]["name"] == "get_weather"
        assert ollama_tool_calls[0]["function"]["arguments"] == '{"location": "New York"}'

    def test_translate_function_call_legacy(self, chat_translator):
        """Test translation of legacy function call to Ollama format."""
        openai_function_call = {
            "name": "get_weather",
            "arguments": '{"location": "Boston"}'
        }

        ollama_tool_calls = chat_translator._translate_function_call(openai_function_call)
        
        assert len(ollama_tool_calls) == 1
        assert ollama_tool_calls[0]["id"] == "call_legacy"
        assert ollama_tool_calls[0]["type"] == "function"
        assert ollama_tool_calls[0]["function"]["name"] == "get_weather"
        assert ollama_tool_calls[0]["function"]["arguments"] == '{"location": "Boston"}'

    def test_translate_response_with_tool_calls(self, chat_translator):
        """Test full response translation with tool calls."""
        # Mock OpenAI response with tool calls
        openai_message = Mock()
        openai_message.content = "I'll get the weather for you."
        openai_message.tool_calls = [
            {
                "id": "call_456",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": '{"location": "Seattle"}'
                }
            }
        ]
        
        openai_choice = Mock()
        openai_choice.message = openai_message
        openai_choice.finish_reason = "tool_calls"
        
        openai_response = Mock()
        openai_response.model = "gpt-4"
        openai_response.choices = [openai_choice]
        openai_response.usage = None

        original_request = OllamaChatRequest(
            model="llama2",
            messages=[OllamaChatMessage(role="user", content="What's the weather?")]
        )

        result = chat_translator._translate_non_streaming_response(openai_response, original_request)
        
        assert isinstance(result, OllamaChatResponse)
        assert result.message.role == "assistant"
        assert result.message.content == "I'll get the weather for you."
        assert result.message.tool_calls is not None
        assert len(result.message.tool_calls) == 1
        assert result.message.tool_calls[0]["function"]["name"] == "get_weather"

    def test_translate_empty_tools_list(self, chat_translator):
        """Test translation with empty tools list."""
        result = chat_translator._translate_tools([])
        assert result == []

    def test_translate_malformed_tool(self, chat_translator):
        """Test handling of malformed tool definition."""
        malformed_tools = [
            "not_a_dict",
            {"missing_function_data": True}
        ]

        result = chat_translator._translate_tools(malformed_tools)
        
        # Should handle malformed tools gracefully
        assert len(result) == 1  # Only the second one creates a tool (with empty function)
        assert result[0].function.name == ""