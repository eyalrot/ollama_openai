"""
Unit tests for request body utility functions.
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException, Request

from src.utils.request_body import get_body_bytes, get_body_json


class TestGetBodyBytes:
    """Test the get_body_bytes function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-request-123"
        return request

    @pytest.mark.asyncio
    async def test_get_body_bytes_from_cached_body(self, mock_request):
        """Test getting body bytes from cached _body attribute."""
        # Setup cached body
        test_body = b'{"test": "data"}'
        mock_request._body = test_body

        # Call function
        result = await get_body_bytes(mock_request)

        # Verify result
        assert result == test_body

    @pytest.mark.asyncio
    async def test_get_body_bytes_from_state_body(self, mock_request):
        """Test getting body bytes from request.state.body."""
        # Setup state body
        test_body = b'{"test": "data"}'
        mock_request.state.body = test_body

        # Call function
        result = await get_body_bytes(mock_request)

        # Verify result
        assert result == test_body

    @pytest.mark.asyncio
    async def test_get_body_bytes_from_state_body_string(self, mock_request):
        """Test getting body bytes from request.state.body when it's a string."""
        # Setup state body as string (should be ignored)
        mock_request.state.body = "string_body"

        # Mock the request.body() method
        test_body = b'{"test": "data"}'
        mock_request.body = AsyncMock(return_value=test_body)

        # Call function
        result = await get_body_bytes(mock_request)

        # Verify result
        assert result == test_body
        mock_request.body.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_body_bytes_direct_read(self, mock_request):
        """Test getting body bytes by reading directly from request."""
        # Setup request body method
        test_body = b'{"test": "data"}'
        mock_request.body = AsyncMock(return_value=test_body)

        # Call function
        result = await get_body_bytes(mock_request)

        # Verify result
        assert result == test_body
        mock_request.body.assert_called_once()

        # Verify body was cached
        assert mock_request._body == test_body

    @pytest.mark.asyncio
    async def test_get_body_bytes_read_failure(self, mock_request):
        """Test handling of body read failure."""
        # Setup request body method to raise exception
        mock_request.body = AsyncMock(side_effect=RuntimeError("Body already consumed"))

        # Call function and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_body_bytes(mock_request)

        # Verify exception
        assert exc_info.value.status_code == 400
        assert "already been consumed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_body_bytes_priority_order(self, mock_request):
        """Test that cached _body takes priority over state.body."""
        # Setup both cached and state body
        cached_body = b'{"cached": "data"}'
        state_body = b'{"state": "data"}'

        mock_request._body = cached_body
        mock_request.state.body = state_body

        # Call function
        result = await get_body_bytes(mock_request)

        # Verify cached body was used
        assert result == cached_body

    @pytest.mark.asyncio
    async def test_get_body_bytes_no_request_id(self):
        """Test function works when request_id is not available."""
        # Create request without request_id
        mock_request = Mock(spec=Request)
        mock_request.state = Mock()
        # No request_id attribute

        test_body = b'{"test": "data"}'
        mock_request.body = AsyncMock(return_value=test_body)

        # Call function (should not raise exception)
        result = await get_body_bytes(mock_request)

        # Verify result
        assert result == test_body


class TestGetBodyJson:
    """Test the get_body_json function."""

    @pytest.fixture
    def mock_request(self):
        """Create a mock FastAPI request."""
        request = Mock(spec=Request)
        request.state = Mock()
        request.state.request_id = "test-request-123"
        return request

    @pytest.mark.asyncio
    async def test_get_body_json_success(self, mock_request):
        """Test successful JSON parsing from body."""
        # Setup test data
        test_data = {"key": "value", "number": 42, "nested": {"inner": "data"}}
        test_body = json.dumps(test_data).encode()

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function
            result = await get_body_json(mock_request)

            # Verify result
            assert result == test_data
            mock_get_body_bytes.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_get_body_json_empty_dict(self, mock_request):
        """Test JSON parsing of empty dictionary."""
        # Setup test data
        test_data = {}
        test_body = json.dumps(test_data).encode()

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function
            result = await get_body_json(mock_request)

            # Verify result
            assert result == test_data

    @pytest.mark.asyncio
    async def test_get_body_json_array(self, mock_request):
        """Test JSON parsing of array data."""
        # Setup test data
        test_data = [{"item": 1}, {"item": 2}, {"item": 3}]
        test_body = json.dumps(test_data).encode()

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function
            result = await get_body_json(mock_request)

            # Verify result
            assert result == test_data

    @pytest.mark.asyncio
    async def test_get_body_json_invalid_json(self, mock_request):
        """Test handling of invalid JSON."""
        # Setup invalid JSON
        test_body = b'{"invalid": json}'

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function and expect HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await get_body_json(mock_request)

            # Verify exception
            assert exc_info.value.status_code == 400
            assert "Invalid JSON" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_body_json_empty_body(self, mock_request):
        """Test handling of empty body."""
        # Setup empty body
        test_body = b""

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function and expect HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await get_body_json(mock_request)

            # Verify exception
            assert exc_info.value.status_code == 400
            assert "Invalid JSON" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_body_json_malformed_json(self, mock_request):
        """Test handling of malformed JSON."""
        # Setup malformed JSON
        test_body = b'{"key": "value", "missing_quote: "value"}'

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function and expect HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await get_body_json(mock_request)

            # Verify exception
            assert exc_info.value.status_code == 400
            assert "Invalid JSON" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_body_json_get_body_bytes_exception(self, mock_request):
        """Test handling when get_body_bytes raises exception."""
        # Mock get_body_bytes to raise HTTPException
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.side_effect = HTTPException(
                status_code=400, detail="Body already consumed"
            )

            # Call function and expect same HTTPException
            with pytest.raises(HTTPException) as exc_info:
                await get_body_json(mock_request)

            # Verify exception
            assert exc_info.value.status_code == 400
            assert "Body already consumed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_body_json_unicode_content(self, mock_request):
        """Test JSON parsing with unicode content."""
        # Setup test data with unicode
        test_data = {"message": "Hello 世界", "emoji": "🌍", "special": "café"}
        test_body = json.dumps(test_data, ensure_ascii=False).encode("utf-8")

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function
            result = await get_body_json(mock_request)

            # Verify result
            assert result == test_data

    @pytest.mark.asyncio
    async def test_get_body_json_no_request_id(self):
        """Test function works when request_id is not available."""
        # Create request without request_id
        mock_request = Mock(spec=Request)
        mock_request.state = Mock()
        # No request_id attribute

        test_data = {"test": "data"}
        test_body = json.dumps(test_data).encode()

        # Mock get_body_bytes
        with patch("src.utils.request_body.get_body_bytes") as mock_get_body_bytes:
            mock_get_body_bytes.return_value = test_body

            # Call function (should not raise exception)
            result = await get_body_json(mock_request)

            # Verify result
            assert result == test_data
