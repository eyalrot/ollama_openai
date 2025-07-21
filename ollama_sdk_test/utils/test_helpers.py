"""
Common test utilities and helper functions.
"""
import time
import logging
from typing import Any, Dict, List, Optional, Callable
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from ollama import Client

logger = logging.getLogger(__name__)


def create_test_client(host: Optional[str] = None) -> Client:
    """
    Create an Ollama client for testing.
    
    Args:
        host: Optional host URL. If not provided, uses config.PROXY_HOST
        
    Returns:
        Configured Ollama client
    """
    from config import PROXY_HOST
    return Client(host=host or PROXY_HOST)


def retry_on_failure(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry a function call on failure.
    
    Args:
        func: Function to call
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} attempts failed")
    
    raise last_exception


def validate_embedding_response(response: Dict[str, Any], expected_count: int = 1) -> None:
    """
    Validate an embedding response structure.
    
    Args:
        response: Response from embed() or embeddings() call
        expected_count: Expected number of embeddings
        
    Raises:
        AssertionError if validation fails
    """
    # Check for either new format (embed) or old format (embeddings)
    if "embeddings" in response:
        # New format from embed()
        assert isinstance(response["embeddings"], list), "Embeddings should be a list"
        assert len(response["embeddings"]) == expected_count, \
            f"Expected {expected_count} embeddings, got {len(response['embeddings'])}"
        
        for i, embedding in enumerate(response["embeddings"]):
            assert isinstance(embedding, list), f"Embedding {i} should be a list"
            assert len(embedding) > 0, f"Embedding {i} should not be empty"
            assert all(isinstance(x, (int, float)) for x in embedding), \
                f"Embedding {i} should contain only numbers"
    
    elif "embedding" in response:
        # Old format from embeddings()
        assert expected_count == 1, "Old format only supports single embeddings"
        embedding = response["embedding"]
        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) > 0, "Embedding should not be empty"
        assert all(isinstance(x, (int, float)) for x in embedding), \
            "Embedding should contain only numbers"
    
    else:
        raise AssertionError("Response missing both 'embeddings' and 'embedding' fields")


def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score between -1 and 1
    """
    # Convert to numpy arrays and reshape for sklearn
    emb1 = np.array(embedding1).reshape(1, -1)
    emb2 = np.array(embedding2).reshape(1, -1)
    
    return cosine_similarity(emb1, emb2)[0][0]


def assert_embeddings_similar(
    embedding1: List[float],
    embedding2: List[float],
    threshold: float = 0.95,
    message: str = ""
) -> None:
    """
    Assert that two embeddings are similar enough.
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        threshold: Minimum cosine similarity (default 0.95)
        message: Optional assertion message
    """
    similarity = calculate_cosine_similarity(embedding1, embedding2)
    assert similarity >= threshold, \
        f"Embeddings not similar enough: {similarity:.4f} < {threshold}. {message}"


def assert_embeddings_different(
    embedding1: List[float],
    embedding2: List[float],
    threshold: float = 0.8,
    message: str = ""
) -> None:
    """
    Assert that two embeddings are different enough.
    
    Args:
        embedding1: First embedding
        embedding2: Second embedding
        threshold: Maximum cosine similarity (default 0.8)
        message: Optional assertion message
    """
    similarity = calculate_cosine_similarity(embedding1, embedding2)
    assert similarity <= threshold, \
        f"Embeddings too similar: {similarity:.4f} > {threshold}. {message}"


def measure_response_time(func: Callable) -> tuple[Any, float]:
    """
    Measure the response time of a function call.
    
    Args:
        func: Function to time
        
    Returns:
        Tuple of (result, elapsed_time_in_seconds)
    """
    start_time = time.time()
    result = func()
    elapsed_time = time.time() - start_time
    return result, elapsed_time


def is_valid_model_list_response(response: Dict[str, Any]) -> bool:
    """
    Validate a model list response structure.
    
    Args:
        response: Response from list() call
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(response, dict):
        return False
    
    if "models" not in response:
        return False
    
    models = response["models"]
    if not isinstance(models, list):
        return False
    
    # Check each model entry
    for model in models:
        if not isinstance(model, dict):
            return False
        if "name" not in model:
            return False
    
    return True


def extract_embedding(response: Dict[str, Any], index: int = 0) -> List[float]:
    """
    Extract an embedding from a response, handling both formats.
    
    Args:
        response: Embedding response
        index: Index for batch responses (only for new format)
        
    Returns:
        Embedding vector as list of floats
    """
    if "embeddings" in response:
        return response["embeddings"][index]
    elif "embedding" in response:
        if index != 0:
            raise ValueError("Old format only supports single embeddings")
        return response["embedding"]
    else:
        raise ValueError("No embedding found in response")


def generate_test_image_base64() -> str:
    """
    Generate a simple test image as base64 string.
    
    Returns:
        Base64 encoded PNG image
    """
    import base64
    from io import BytesIO
    from PIL import Image
    
    # Create a simple 100x100 red square
    img = Image.new('RGB', (100, 100), color='red')
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_bytes = buffer.getvalue()
    
    return base64.b64encode(img_bytes).decode('utf-8')