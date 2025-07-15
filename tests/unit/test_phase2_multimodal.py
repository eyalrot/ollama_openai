"""
Tests for Phase 2 multimodal (image) functionality.

This module tests the translation of image inputs and multimodal messages
between Ollama and OpenAI formats.
"""

import pytest

from src.models import (
    OllamaChatMessage,
    OllamaChatRequest,
    OpenAIChatRequest,
)
from src.translators.chat import ChatTranslator


class TestMultimodalImages:
    """Test multimodal image handling functionality."""

    @pytest.fixture
    def chat_translator(self):
        """Create a chat translator instance."""
        return ChatTranslator()

    @pytest.fixture
    def sample_image_base64(self):
        """Create a sample base64 encoded image for testing."""
        # Create a minimal 1x1 pixel JPEG (simplified for testing)
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAFyBAgHCAAAAAElFTkSuQmCC"

    def test_convert_text_only_message(self, chat_translator):
        """Test conversion of text-only message (no images)."""
        message = OllamaChatMessage(role="user", content="Hello world")

        content = chat_translator._convert_message_content(message)

        assert isinstance(content, str)
        assert content == "Hello world"

    def test_convert_single_image_message(self, chat_translator, sample_image_base64):
        """Test conversion of message with single image."""
        message = OllamaChatMessage(role="user", content="Look at this image")
        message.images = [sample_image_base64]

        content = chat_translator._convert_message_content(message)

        assert isinstance(content, list)
        assert len(content) == 2

        # Check text part
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "Look at this image"

        # Check image part
        assert content[1]["type"] == "image_url"
        assert "url" in content[1]["image_url"]
        assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_convert_multiple_images_message(
        self, chat_translator, sample_image_base64
    ):
        """Test conversion of message with multiple images."""
        message = OllamaChatMessage(role="user", content="Compare these images")
        message.images = [sample_image_base64, sample_image_base64]

        content = chat_translator._convert_message_content(message)

        assert isinstance(content, list)
        assert len(content) == 3  # 1 text + 2 images

        # Check text part
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "Compare these images"

        # Check image parts
        for i in [1, 2]:
            assert content[i]["type"] == "image_url"
            assert "url" in content[i]["image_url"]
            assert content[i]["image_url"]["url"].startswith("data:image/jpeg;base64,")

    def test_convert_image_only_message(self, chat_translator, sample_image_base64):
        """Test conversion of message with only images (no text)."""
        message = OllamaChatMessage(role="user", content="")
        message.images = [sample_image_base64]

        content = chat_translator._convert_message_content(message)

        assert isinstance(content, list)
        assert len(content) == 1  # Only image, no text part

        # Check image part
        assert content[0]["type"] == "image_url"
        assert "url" in content[0]["image_url"]

    def test_format_image_url_plain_base64(self, chat_translator):
        """Test formatting of plain base64 data to data URL."""
        base64_data = "abc123"

        url = chat_translator._format_image_url(base64_data)

        assert url == "data:image/jpeg;base64,abc123"

    def test_format_image_url_existing_data_url(self, chat_translator):
        """Test that existing data URLs are preserved."""
        data_url = "data:image/png;base64,abc123"

        url = chat_translator._format_image_url(data_url)

        assert url == data_url  # Should remain unchanged

    def test_translate_request_with_images(self, chat_translator, sample_image_base64):
        """Test full request translation with images."""
        message = OllamaChatMessage(role="user", content="Describe this image")
        message.images = [sample_image_base64]

        request = OllamaChatRequest(model="llama2", messages=[message])

        result = chat_translator.translate_request(request)

        assert isinstance(result, OpenAIChatRequest)
        assert len(result.messages) == 1

        # Check that the message content is now multimodal
        msg = result.messages[0]
        assert isinstance(msg.content, list)
        assert len(msg.content) == 2  # text + image
        assert msg.content[0]["type"] == "text"
        assert msg.content[1]["type"] == "image_url"

    def test_translate_mixed_messages(self, chat_translator, sample_image_base64):
        """Test translation of mixed text-only and multimodal messages."""
        messages = [
            OllamaChatMessage(role="user", content="Hello"),
            OllamaChatMessage(role="assistant", content="Hi there!"),
        ]

        # Add image to the second message
        messages.append(OllamaChatMessage(role="user", content="Look at this"))
        messages[-1].images = [sample_image_base64]

        request = OllamaChatRequest(model="llama2", messages=messages)

        result = chat_translator.translate_request(request)

        assert len(result.messages) == 3

        # First message: text only
        assert isinstance(result.messages[0].content, str)
        assert result.messages[0].content == "Hello"

        # Second message: text only
        assert isinstance(result.messages[1].content, str)
        assert result.messages[1].content == "Hi there!"

        # Third message: multimodal
        assert isinstance(result.messages[2].content, list)
        assert len(result.messages[2].content) == 2

    def test_invalid_image_data_handling(self, chat_translator):
        """Test handling of invalid image data."""
        message = OllamaChatMessage(role="user", content="Text with invalid image")
        message.images = [123, None, "valid_base64"]  # Mix of invalid and valid

        # Should not raise exception, but filter out invalid images
        content = chat_translator._convert_message_content(message)

        assert isinstance(content, list)
        # Should have text + only 1 valid image
        assert len(content) == 2
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"

    def test_empty_images_list(self, chat_translator):
        """Test handling of empty images list."""
        message = OllamaChatMessage(role="user", content="Just text")
        message.images = []

        content = chat_translator._convert_message_content(message)

        # Should return simple string, not multimodal array
        assert isinstance(content, str)
        assert content == "Just text"

    def test_convert_message_content_error_handling(self, chat_translator):
        """Test error handling in message content conversion."""
        # Create a malformed message that might cause issues
        message = OllamaChatMessage(role="user", content="Test")

        # This should work fine
        content = chat_translator._convert_message_content(message)
        assert content == "Test"
