"""
HTTP client with retry logic and connection pooling.
"""

import asyncio
import logging
import random
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Callable, Optional, TypeVar

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreaker:
    """Circuit breaker pattern implementation to prevent retry storms."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls

        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = "closed"  # closed, open, half-open
        self._half_open_calls = 0

    @property
    def is_open(self) -> bool:
        """Check if circuit breaker is open (blocking requests)."""
        if self._state == "closed":
            return False

        if self._state == "open":
            # Check if we should transition to half-open
            if self._last_failure_time:
                time_since_failure = (
                    datetime.now() - self._last_failure_time
                ).total_seconds()
                if time_since_failure > self.recovery_timeout:
                    self._state = "half-open"
                    self._half_open_calls = 0
                    return False
            return True

        # Half-open state
        return self._half_open_calls >= self.half_open_max_calls

    def record_success(self):
        """Record a successful request."""
        if self._state == "half-open":
            self._half_open_calls += 1
            # If we've had enough successful calls, close the circuit
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = "closed"
                self._failure_count = 0
                self._last_failure_time = None
        elif self._state == "closed":
            self._failure_count = 0

    def record_failure(self):
        """Record a failed request."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._state == "half-open":
            # Any failure in half-open state reopens the circuit
            self._state = "open"
        elif self._failure_count >= self.failure_threshold:
            self._state = "open"
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )


class RetryClient:
    """HTTP client with retry logic, connection pooling, and circuit breaker."""

    def __init__(
        self,
        max_retries: Optional[int] = None,
        timeout: Optional[int] = None,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        circuit_breaker: Optional[CircuitBreaker] = None,
    ):
        settings = get_settings()
        self.max_retries = max_retries or settings.MAX_RETRIES
        self.timeout = timeout or settings.REQUEST_TIMEOUT
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

        # Configure connection pooling
        limits = httpx.Limits(
            max_keepalive_connections=20, max_connections=100, keepalive_expiry=30.0
        )

        # Configure timeouts
        timeout_config = httpx.Timeout(
            timeout=self.timeout, connect=5.0, read=self.timeout, write=10.0, pool=5.0
        )

        verify_ssl = not settings.DISABLE_SSL_VERIFICATION
        logger.info(
            f"HTTP client SSL verification: {verify_ssl}",
            extra={
                "extra_data": {
                    "ssl_verification": verify_ssl,
                    "disable_ssl_verification": settings.DISABLE_SSL_VERIFICATION,
                }
            },
        )

        self.client = httpx.AsyncClient(
            timeout=timeout_config,
            limits=limits,
            follow_redirects=True,
            http2=False,  # HTTP/2 requires additional dependencies
            verify=verify_ssl,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and optional jitter."""
        delay = min(self.base_delay * (self.exponential_base**attempt), self.max_delay)

        if self.jitter:
            # Add random jitter (±25% of the delay)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)  # Ensure non-negative

    def _should_retry(
        self, response: Optional[httpx.Response], error: Optional[Exception]
    ) -> bool:
        """Determine if request should be retried based on response or error."""
        if error:
            # Retry on network errors and timeouts
            return isinstance(error, (httpx.NetworkError, httpx.TimeoutException))

        if response:
            # Retry on 5xx errors and specific 4xx errors
            return response.status_code >= 500 or response.status_code in [
                429,
                408,
                425,
            ]

        return False

    async def request_with_retry(
        self,
        method: str,
        url: str,
        retry_on: Optional[
            Callable[[Optional[httpx.Response], Optional[Exception]], bool]
        ] = None,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry."""
        retry_on = retry_on or self._should_retry
        last_exception: Optional[Exception] = None

        # Check circuit breaker
        if self.circuit_breaker.is_open:
            raise httpx.NetworkError("Circuit breaker is open - too many failures")

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, url, **kwargs)

                if not retry_on(response, None):
                    self.circuit_breaker.record_success()
                    return response

                # Response indicates we should retry
                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Request failed with status {response.status_code}, "
                        f"retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Last attempt failed
                    self.circuit_breaker.record_failure()
                    return response

            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_exception = e

                if retry_on(None, e) and attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"{type(e).__name__}: {e}, retrying in {delay:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    # Last attempt failed or error is not retryable
                    self.circuit_breaker.record_failure()
                    raise

        # If we get here, all retries have been exhausted
        self.circuit_breaker.record_failure()
        if last_exception:
            raise last_exception
        return response  # Return the last response if no exception

    async def stream_with_retry(
        self,
        method: str,
        url: str,
        retry_on: Optional[
            Callable[[Optional[httpx.Response], Optional[Exception]], bool]
        ] = None,
        **kwargs,
    ):
        """Make streaming HTTP request with retry logic."""
        retry_on = retry_on or self._should_retry

        # Check circuit breaker
        if self.circuit_breaker.is_open:
            raise httpx.NetworkError("Circuit breaker is open - too many failures")

        for attempt in range(self.max_retries):
            try:
                async with self.client.stream(method, url, **kwargs) as response:
                    # Check if we should retry based on status code
                    if retry_on(response, None) and attempt < self.max_retries - 1:
                        delay = self._calculate_delay(attempt)
                        logger.warning(
                            f"Stream request failed with status {response.status_code}, "
                            f"retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                        await asyncio.sleep(delay)
                        continue

                    # Success or final attempt
                    response.raise_for_status()
                    self.circuit_breaker.record_success()

                    # Yield the response for streaming
                    async for chunk in response.aiter_raw():
                        yield chunk
                    return

            except (httpx.NetworkError, httpx.TimeoutException) as e:
                if retry_on(None, e) and attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"Stream {type(e).__name__}: {e}, retrying in {delay:.2f}s "
                        f"(attempt {attempt + 1}/{self.max_retries})"
                    )
                    await asyncio.sleep(delay)
                else:
                    self.circuit_breaker.record_failure()
                    raise

        # If we get here, all retries have been exhausted
        self.circuit_breaker.record_failure()


# Global client instance management
_retry_client: Optional[RetryClient] = None
_client_lock = asyncio.Lock()


async def get_retry_client() -> RetryClient:
    """Get or create global retry client."""
    global _retry_client

    if _retry_client is None:
        async with _client_lock:
            if _retry_client is None:
                _retry_client = RetryClient()

    return _retry_client


@asynccontextmanager
async def retry_client_context():
    """Context manager for using the global retry client."""
    client = await get_retry_client()
    try:
        yield client
    finally:
        # Don't close the global client
        pass


async def close_global_client():
    """Close the global retry client (call during app shutdown)."""
    global _retry_client

    if _retry_client:
        await _retry_client.close()
        _retry_client = None
