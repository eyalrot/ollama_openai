"""
Additional tests for HTTP client streaming functionality.
"""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from src.utils.http_client import CircuitBreaker, RetryClient


class TestStreamingRetry:
    """Test streaming functionality with retry logic."""

    @pytest.mark.asyncio
    async def test_streaming_success(self):
        """Test successful streaming without retries."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)

        # Mock successful streaming response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()

        chunks = [b"chunk1", b"chunk2", b"chunk3"]

        async def mock_aiter_raw():
            for chunk in chunks:
                yield chunk

        mock_response.aiter_raw = mock_aiter_raw

        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            yield mock_response

        with patch.object(client.client, "stream", mock_stream):
            received_chunks = []
            async for chunk in client.stream_with_retry("GET", "http://test.com"):
                received_chunks.append(chunk)

            assert received_chunks == chunks

    @pytest.mark.asyncio
    async def test_streaming_retry_on_error(self):
        """Test streaming retry on initial connection error."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)

        # Track attempts
        attempt_count = 0

        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count == 1:
                # First attempt fails
                raise httpx.NetworkError("Connection failed")
            else:
                # Second attempt succeeds
                mock_response = AsyncMock()
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()

                async def mock_aiter_raw():
                    yield b"success after retry"

                mock_response.aiter_raw = mock_aiter_raw
                yield mock_response

        with patch.object(client.client, "stream", mock_stream):
            chunks = []
            async for chunk in client.stream_with_retry("GET", "http://test.com"):
                chunks.append(chunk)

            assert attempt_count == 2
            assert chunks == [b"success after retry"]

    @pytest.mark.asyncio
    async def test_streaming_retry_on_status_error(self):
        """Test streaming retry on error status code."""
        client = RetryClient(max_retries=2, base_delay=0.1, jitter=False)

        attempt_count = 0

        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            mock_response = AsyncMock()

            if attempt_count == 1:
                # First attempt returns 503
                mock_response.status_code = 503
                mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                    "Service unavailable", request=Mock(), response=mock_response
                )
            else:
                # Second attempt succeeds
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()

                async def mock_aiter_raw():
                    yield b"success"

                mock_response.aiter_raw = mock_aiter_raw

            yield mock_response

        with patch.object(client.client, "stream", mock_stream):
            chunks = []
            async for chunk in client.stream_with_retry("GET", "http://test.com"):
                chunks.append(chunk)

            assert attempt_count == 2
            assert chunks == [b"success"]

    @pytest.mark.asyncio
    async def test_streaming_max_retries_exceeded(self):
        """Test streaming fails after max retries."""
        client = RetryClient(max_retries=2, base_delay=0.1, jitter=False)

        # Create a mock that always raises timeout
        mock_stream = Mock(side_effect=httpx.TimeoutException("Stream timeout"))

        with patch.object(client.client, "stream", mock_stream):
            with pytest.raises(httpx.TimeoutException):
                async for chunk in client.stream_with_retry("GET", "http://test.com"):
                    pass  # Should not reach here

    @pytest.mark.asyncio
    async def test_streaming_with_circuit_breaker_open(self):
        """Test streaming blocked by open circuit breaker."""
        cb = CircuitBreaker(failure_threshold=1)
        client = RetryClient(circuit_breaker=cb)

        # Open the circuit breaker
        cb.record_failure()

        with pytest.raises(httpx.NetworkError, match="Circuit breaker is open"):
            async for chunk in client.stream_with_retry("GET", "http://test.com"):
                pass  # Should not reach here

    @pytest.mark.asyncio
    async def test_streaming_custom_retry_predicate(self):
        """Test streaming with custom retry predicate."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)

        attempt_count = 0

        # Custom predicate that only retries on 429 (rate limit)
        def custom_retry(response, error):
            if error:
                return False  # Don't retry on errors
            return response and response.status_code == 429

        @asynccontextmanager
        async def mock_stream(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1

            mock_response = AsyncMock()

            if attempt_count == 1:
                # First attempt returns 429
                mock_response.status_code = 429
            elif attempt_count == 2:
                # Second attempt returns 500 (should not retry)
                mock_response.status_code = 500
            else:
                # Should not reach here
                mock_response.status_code = 200

            mock_response.raise_for_status = Mock()

            async def mock_aiter_raw():
                yield f"attempt {attempt_count}".encode()

            mock_response.aiter_raw = mock_aiter_raw
            yield mock_response

        with patch.object(client.client, "stream", mock_stream):
            chunks = []
            async for chunk in client.stream_with_retry(
                "GET", "http://test.com", retry_on=custom_retry
            ):
                chunks.append(chunk.decode())

            # Should have made 2 attempts (retry on 429, not on 500)
            assert attempt_count == 2
            assert chunks == ["attempt 2"]
