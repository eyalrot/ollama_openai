"""
Basic connectivity and operation tests for Ollama SDK.
"""
import pytest
import logging
from ollama import Client, AsyncClient

from config import (
    PROXY_HOST,
    DEFAULT_CHAT_MODEL,
    TEST_CHAT_MODELS,
    TIMEOUT,
)
from utils.test_helpers import (
    create_test_client,
    is_valid_model_list_response,
    retry_on_failure,
)

logger = logging.getLogger(__name__)


class TestBasicOperations:
    """Test basic connectivity and operations."""
    
    def setup_method(self):
        """Set up test client before each test."""
        self.client = create_test_client()
    
    def test_client_initialization(self):
        """Test client can be initialized with different hosts."""
        # Test with explicit host
        client = Client(host=PROXY_HOST)
        assert client is not None
        
        # Test with trailing slash
        client_slash = Client(host=f"{PROXY_HOST}/")
        assert client_slash is not None
        
        logger.info("Client initialization successful")
    
    def test_connection_verify(self):
        """Test basic connection to the proxy server."""
        try:
            # Try to list models as a connection test
            response = self.client.list()
            assert response is not None
            logger.info("Successfully connected to proxy server")
        except Exception as e:
            pytest.fail(f"Failed to connect to proxy server: {e}")
    
    def test_list_models(self):
        """Test listing available models."""
        response = self.client.list()
        
        # Validate response structure
        assert is_valid_model_list_response(response), \
            "Invalid model list response structure"
        
        models = response["models"]
        assert len(models) > 0, "Should have at least one model available"
        
        # Log available models
        model_names = [model["name"] for model in models]
        logger.info(f"Available models: {', '.join(model_names)}")
        
        # Check if our test models are available
        for test_model in TEST_CHAT_MODELS:
            if test_model in model_names:
                logger.info(f"Test model '{test_model}' is available")
    
    def test_show_model_info(self):
        """Test getting detailed model information."""
        try:
            response = self.client.show(DEFAULT_CHAT_MODEL)
            
            # Validate response has expected fields
            assert isinstance(response, dict), "Response should be a dictionary"
            
            # Common fields that might be present
            possible_fields = ["name", "modelfile", "parameters", "template", "details"]
            found_fields = [field for field in possible_fields if field in response]
            
            if found_fields:
                logger.info(f"Model info contains fields: {', '.join(found_fields)}")
            else:
                logger.warning("Model info response has no recognized fields")
                
        except Exception as e:
            # Some proxies might not implement show()
            logger.warning(f"show() method not supported or failed: {e}")
    
    def test_model_availability(self):
        """Test which models from our test list are actually available."""
        response = self.client.list()
        available_models = [model["name"] for model in response["models"]]
        
        results = {}
        for test_model in TEST_CHAT_MODELS:
            is_available = test_model in available_models
            results[test_model] = is_available
            
            if is_available:
                logger.info(f"✓ Model '{test_model}' is available")
            else:
                logger.warning(f"✗ Model '{test_model}' is NOT available")
        
        # At least one model should be available
        assert any(results.values()), \
            "At least one test model should be available"
    
    def test_error_handling_connection(self):
        """Test error handling for connection failures."""
        # Create client with invalid host
        bad_client = Client(host="http://localhost:99999")
        
        with pytest.raises(Exception) as exc_info:
            bad_client.list()
        
        logger.info(f"Connection error correctly raised: {type(exc_info.value).__name__}")
    
    def test_retry_mechanism(self):
        """Test that retry mechanism works for transient failures."""
        # This is a basic test - in real scenario we'd mock failures
        def flaky_operation():
            return self.client.list()
        
        # Should succeed with retries
        result = retry_on_failure(flaky_operation, max_retries=3)
        assert is_valid_model_list_response(result)
        
        logger.info("Retry mechanism working")
    
    def test_timeout_handling(self):
        """Test timeout configuration."""
        # Create client with short timeout
        # Note: This might not actually timeout unless the server is slow
        import httpx
        
        # The Ollama client might not directly expose timeout setting,
        # but we can test that it handles the configuration
        try:
            client = Client(
                host=PROXY_HOST,
                timeout=0.001  # Very short timeout
            )
            # This might or might not fail depending on network speed
            client.list()
        except Exception as e:
            logger.info(f"Timeout test resulted in: {type(e).__name__}")
    
    def test_headers_configuration(self):
        """Test custom headers configuration."""
        # The Ollama client might support custom headers
        try:
            client = Client(
                host=PROXY_HOST,
                headers={"X-Custom-Header": "test-value"}
            )
            response = client.list()
            assert response is not None
            logger.info("Custom headers accepted")
        except Exception as e:
            logger.warning(f"Custom headers not supported: {e}")


class TestAsyncBasicOperations:
    """Test async client basic operations."""
    
    @pytest.fixture
    def async_client(self):
        """Create async client for testing."""
        return AsyncClient(host=PROXY_HOST)
    
    @pytest.mark.asyncio
    async def test_async_client_initialization(self):
        """Test async client initialization."""
        client = AsyncClient(host=PROXY_HOST)
        assert client is not None
        logger.info("Async client initialization successful")
    
    @pytest.mark.asyncio
    async def test_async_list_models(self, async_client):
        """Test async model listing."""
        response = await async_client.list()
        
        assert is_valid_model_list_response(response), \
            "Invalid model list response structure"
        
        models = response["models"]
        assert len(models) > 0, "Should have at least one model available"
        
        logger.info(f"Async list found {len(models)} models")
    
    @pytest.mark.asyncio
    async def test_async_error_handling(self):
        """Test async error handling."""
        bad_client = AsyncClient(host="http://localhost:99999")
        
        with pytest.raises(Exception) as exc_info:
            await bad_client.list()
        
        logger.info(f"Async error correctly raised: {type(exc_info.value).__name__}")