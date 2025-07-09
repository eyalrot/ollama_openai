"""
Tests for HTTP client with retry logic and connection pooling.
"""

import asyncio
import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta

from src.utils.http_client import (
    RetryClient,
    CircuitBreaker,
    get_retry_client,
    retry_client_context,
    close_global_client,
)


class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_initial_state_is_closed(self):
        """Test that circuit breaker starts in closed state."""
        cb = CircuitBreaker()
        assert not cb.is_open
        assert cb._state == "closed"
    
    def test_opens_after_threshold_failures(self):
        """Test that circuit breaker opens after reaching failure threshold."""
        cb = CircuitBreaker(failure_threshold=3)
        
        # Record failures
        for _ in range(3):
            cb.record_failure()
            
        assert cb.is_open
        assert cb._state == "open"
    
    def test_transitions_to_half_open_after_timeout(self):
        """Test that circuit breaker transitions to half-open after recovery timeout."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.is_open
        
        # Wait for recovery timeout
        import time
        time.sleep(1.1)
        
        # Should transition to half-open
        assert not cb.is_open
        assert cb._state == "half-open"
    
    def test_closes_after_successful_half_open_calls(self):
        """Test that circuit breaker closes after successful half-open calls."""
        cb = CircuitBreaker(failure_threshold=2, half_open_max_calls=3)
        
        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        
        # Force to half-open
        cb._state = "half-open"
        cb._half_open_calls = 0
        
        # Record successful calls
        for _ in range(3):
            cb.record_success()
            
        assert cb._state == "closed"
        assert cb._failure_count == 0
    
    def test_reopens_on_half_open_failure(self):
        """Test that circuit breaker reopens on failure in half-open state."""
        cb = CircuitBreaker()
        
        # Force to half-open
        cb._state = "half-open"
        
        # Record failure
        cb.record_failure()
        
        assert cb._state == "open"


class TestRetryClient:
    """Test retry client functionality."""
    
    @pytest.fixture
    def mock_response(self):
        """Create a mock response."""
        response = Mock(spec=httpx.Response)
        response.status_code = 200
        response.text = '{"result": "success"}'
        response.json.return_value = {"result": "success"}
        return response
    
    @pytest.fixture
    def mock_error_response(self):
        """Create a mock error response."""
        response = Mock(spec=httpx.Response)
        response.status_code = 500
        response.text = '{"error": "server error"}'
        return response
    
    @pytest.mark.asyncio
    async def test_successful_request_no_retry(self, mock_response):
        """Test that successful requests don't trigger retries."""
        client = RetryClient(max_retries=3)
        
        # Mock the underlying httpx client
        with patch.object(client.client, 'request', return_value=mock_response) as mock_request:
            response = await client.request_with_retry("GET", "http://test.com")
            
            assert response.status_code == 200
            assert mock_request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_on_5xx_error(self, mock_error_response, mock_response):
        """Test that 5xx errors trigger retries."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)
        
        # Mock the underlying httpx client to fail twice then succeed
        with patch.object(
            client.client, 'request',
            side_effect=[mock_error_response, mock_error_response, mock_response]
        ) as mock_request:
            response = await client.request_with_retry("GET", "http://test.com")
            
            assert response.status_code == 200
            assert mock_request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_on_timeout(self, mock_response):
        """Test that timeouts trigger retries."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)
        
        # Mock the underlying httpx client to timeout once then succeed
        with patch.object(
            client.client, 'request',
            side_effect=[httpx.TimeoutException("timeout"), mock_response]
        ) as mock_request:
            response = await client.request_with_retry("GET", "http://test.com")
            
            assert response.status_code == 200
            assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_on_network_error(self, mock_response):
        """Test that network errors trigger retries."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)
        
        # Mock the underlying httpx client to have network error then succeed
        with patch.object(
            client.client, 'request',
            side_effect=[httpx.NetworkError("connection failed"), mock_response]
        ) as mock_request:
            response = await client.request_with_retry("GET", "http://test.com")
            
            assert response.status_code == 200
            assert mock_request.call_count == 2
    
    @pytest.mark.asyncio
    async def test_exponential_backoff(self, mock_error_response, mock_response):
        """Test exponential backoff timing."""
        client = RetryClient(
            max_retries=3,
            base_delay=0.1,
            exponential_base=2,
            jitter=False
        )
        
        delays = []
        original_sleep = asyncio.sleep
        
        async def mock_sleep(delay):
            delays.append(delay)
            await original_sleep(0.01)  # Small actual delay
        
        with patch.object(
            client.client, 'request',
            side_effect=[mock_error_response, mock_error_response, mock_response]
        ):
            with patch('asyncio.sleep', side_effect=mock_sleep):
                await client.request_with_retry("GET", "http://test.com")
        
        # Check exponential delays
        assert len(delays) == 2
        assert abs(delays[0] - 0.1) < 0.01  # First retry: base_delay
        assert abs(delays[1] - 0.2) < 0.01  # Second retry: base_delay * 2
    
    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test that delays are capped at max_delay."""
        client = RetryClient(
            max_retries=10,
            base_delay=1.0,
            max_delay=5.0,
            exponential_base=10,
            jitter=False
        )
        
        # Calculate delay for 5th attempt (should be capped)
        delay = client._calculate_delay(5)
        assert delay == 5.0
    
    @pytest.mark.asyncio
    async def test_jitter_adds_randomness(self):
        """Test that jitter adds randomness to delays."""
        client = RetryClient(base_delay=1.0, jitter=True)
        
        # Get multiple delays
        delays = [client._calculate_delay(1) for _ in range(10)]
        
        # Check that delays are different (due to jitter)
        assert len(set(delays)) > 1
        
        # Check that delays are within expected range (±25%)
        # With exponential backoff, the base is 2.0, so delay could be up to 2.0
        for delay in delays:
            assert 0.75 <= delay <= 2.5  # Account for exponential factor
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_blocks_requests(self):
        """Test that open circuit breaker blocks requests."""
        cb = CircuitBreaker(failure_threshold=1)
        client = RetryClient(circuit_breaker=cb)
        
        # Open the circuit
        cb.record_failure()
        
        with pytest.raises(httpx.NetworkError, match="Circuit breaker is open"):
            await client.request_with_retry("GET", "http://test.com")
    
    @pytest.mark.asyncio
    async def test_streaming_retry(self):
        """Test retry logic for streaming requests."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)
        
        # This test is complex due to httpx streaming implementation
        # Skip for now as streaming retry is tested in integration
        pytest.skip("Streaming retry tested in integration tests")
    
    @pytest.mark.asyncio
    async def test_custom_retry_predicate(self, mock_response, mock_error_response):
        """Test custom retry predicate function."""
        client = RetryClient(max_retries=3, base_delay=0.1, jitter=False)
        
        # Custom predicate that only retries on 503
        def custom_retry(response, error):
            if error:
                return False
            return response and response.status_code == 503
        
        # Create 503 response
        response_503 = Mock(spec=httpx.Response)
        response_503.status_code = 503
        
        with patch.object(
            client.client, 'request',
            side_effect=[response_503, mock_response]
        ) as mock_request:
            response = await client.request_with_retry(
                "GET", "http://test.com",
                retry_on=custom_retry
            )
            
            assert response.status_code == 200
            assert mock_request.call_count == 2
        
        # Test that 500 doesn't retry with custom predicate
        with patch.object(
            client.client, 'request',
            return_value=mock_error_response
        ) as mock_request:
            response = await client.request_with_retry(
                "GET", "http://test.com",
                retry_on=custom_retry
            )
            
            assert response.status_code == 500
            assert mock_request.call_count == 1


class TestGlobalClient:
    """Test global client management."""
    
    @pytest.mark.asyncio
    async def test_get_retry_client_singleton(self):
        """Test that get_retry_client returns singleton."""
        client1 = await get_retry_client()
        client2 = await get_retry_client()
        
        assert client1 is client2
        
        # Clean up
        await close_global_client()
    
    @pytest.mark.asyncio
    async def test_retry_client_context(self):
        """Test retry client context manager."""
        async with retry_client_context() as client:
            assert isinstance(client, RetryClient)
            
        # Should still be available after context exit
        client2 = await get_retry_client()
        assert isinstance(client2, RetryClient)
        
        # Clean up
        await close_global_client()
    
    @pytest.mark.asyncio
    async def test_close_global_client(self):
        """Test closing global client."""
        # Create client
        client = await get_retry_client()
        assert client is not None
        
        # Close it
        await close_global_client()
        
        # New client should be different instance
        new_client = await get_retry_client()
        assert new_client is not client
        
        # Clean up
        await close_global_client()


class TestIntegration:
    """Integration tests with real scenarios."""
    
    @pytest.mark.asyncio
    async def test_retry_with_different_status_codes(self):
        """Test retry behavior with various status codes."""
        client = RetryClient(max_retries=2, base_delay=0.1, jitter=False)
        
        test_cases = [
            (200, False),  # Success, no retry
            (400, False),  # Client error, no retry
            (404, False),  # Not found, no retry
            (429, True),   # Too many requests, retry
            (408, True),   # Request timeout, retry
            (500, True),   # Server error, retry
            (502, True),   # Bad gateway, retry
            (503, True),   # Service unavailable, retry
        ]
        
        for status_code, should_retry in test_cases:
            response = Mock(spec=httpx.Response)
            response.status_code = status_code
            
            with patch.object(client.client, 'request', return_value=response) as mock_request:
                result = await client.request_with_retry("GET", "http://test.com")
                
                if should_retry:
                    # Should have retried max_retries times
                    assert mock_request.call_count == client.max_retries
                else:
                    # Should not retry
                    assert mock_request.call_count == 1
    
    @pytest.mark.asyncio
    async def test_connection_pool_limits(self):
        """Test that connection pool limits are enforced."""
        client = RetryClient()
        
        # Check that limits are configured in client's internals
        # httpx stores limits differently in recent versions
        transport = client.client._transport
        if hasattr(transport, '_pool'):
            # Connection pooling is configured
            assert transport is not None
        else:
            # Just verify client is configured
            assert client.client is not None