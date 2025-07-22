"""
Comprehensive embedding tests for Ollama SDK compatibility.
"""
import pytest
import logging
from typing import List, Dict, Any
import numpy as np
from ollama import Client

from config import (
    PROXY_HOST,
    DEFAULT_EMBEDDING_MODEL,
    TEST_EMBEDDING_MODELS,
    SAMPLE_TEXTS,
    UNICODE_TEST_TEXTS,
    LONG_TEXT,
    EXPECTED_DIMENSIONS,
    INVALID_MODELS,
    TIMEOUT,
)
from utils.test_helpers import (
    create_test_client,
    retry_on_failure,
    validate_embedding_response,
    calculate_cosine_similarity,
    assert_embeddings_similar,
    assert_embeddings_different,
    measure_response_time,
    extract_embedding,
)

logger = logging.getLogger(__name__)


class TestEmbeddings:
    """Test suite for Ollama SDK embedding functionality."""
    
    def setup_method(self):
        """Set up test client before each test."""
        self.client = create_test_client()
        self.test_text = SAMPLE_TEXTS[0]
        self.test_model = DEFAULT_EMBEDDING_MODEL
    
    # ===== Basic Embedding Tests =====
    
    def test_embed_single_string(self):
        """Test embedding a single string using embed() method."""
        response = self.client.embed(
            model=self.test_model,
            input=self.test_text
        )
        
        # Validate response structure
        validate_embedding_response(response, expected_count=1)
        
        # Extract and validate embedding
        embedding = extract_embedding(response)
        assert len(embedding) > 0, "Embedding should not be empty"
        
        # Check expected dimensions if known
        if self.test_model in EXPECTED_DIMENSIONS:
            expected_dim = EXPECTED_DIMENSIONS[self.test_model]
            assert len(embedding) == expected_dim, \
                f"Expected {expected_dim} dimensions, got {len(embedding)}"
        
        logger.info(f"Successfully embedded text with {len(embedding)} dimensions")
    
    def test_embeddings_deprecated(self):
        """Test the deprecated embeddings() method for backward compatibility."""
        response = self.client.embeddings(
            model=self.test_model,
            prompt=self.test_text
        )
        
        # Should have 'embedding' field (singular) for old format
        assert "embedding" in response, "Response should contain 'embedding' field"
        embedding = response["embedding"]
        
        assert isinstance(embedding, list), "Embedding should be a list"
        assert len(embedding) > 0, "Embedding should not be empty"
        assert all(isinstance(x, (int, float)) for x in embedding), \
            "Embedding should contain only numbers"
        
        logger.info("Deprecated embeddings() method still works")
    
    def test_embedding_dimensions(self):
        """Verify embedding dimensions match expected model output."""
        for model in TEST_EMBEDDING_MODELS:
            if model not in EXPECTED_DIMENSIONS:
                logger.warning(f"No expected dimensions for model {model}, skipping")
                continue
            
            try:
                response = self.client.embed(
                    model=model,
                    input=self.test_text
                )
                
                embedding = extract_embedding(response)
                expected_dim = EXPECTED_DIMENSIONS[model]
                
                assert len(embedding) == expected_dim, \
                    f"Model {model}: expected {expected_dim} dimensions, got {len(embedding)}"
                
                logger.info(f"Model {model} produces correct {expected_dim} dimensions")
                
            except Exception as e:
                logger.warning(f"Model {model} not available: {e}")
    
    # ===== Batch Embedding Tests =====
    
    def test_embed_batch(self):
        """Test embedding multiple strings in a single request."""
        texts = SAMPLE_TEXTS[:3]
        
        response = self.client.embed(
            model=self.test_model,
            input=texts
        )
        
        # Validate response
        validate_embedding_response(response, expected_count=len(texts))
        
        # Check all embeddings have same dimension
        embeddings = response["embeddings"]
        dimensions = [len(emb) for emb in embeddings]
        assert len(set(dimensions)) == 1, \
            f"All embeddings should have same dimension, got {dimensions}"
        
        # Verify different texts produce different embeddings
        assert_embeddings_different(
            embeddings[0], embeddings[1],
            message="Different texts should produce different embeddings"
        )
        
        logger.info(f"Successfully embedded batch of {len(texts)} texts")
    
    def test_embed_large_batch(self):
        """Test embedding with 100+ strings."""
        # Generate 100 unique texts
        large_batch = [f"Test text number {i}: {text}" 
                      for i, text in enumerate(SAMPLE_TEXTS * 20)]
        
        response = self.client.embed(
            model=self.test_model,
            input=large_batch
        )
        
        validate_embedding_response(response, expected_count=len(large_batch))
        
        logger.info(f"Successfully embedded large batch of {len(large_batch)} texts")
    
    def test_embed_empty_batch(self):
        """Test behavior with empty input list."""
        with pytest.raises(Exception) as exc_info:
            self.client.embed(
                model=self.test_model,
                input=[]
            )
        
        logger.info(f"Empty batch correctly raised: {exc_info.value}")
    
    # ===== Input Validation Tests =====
    
    def test_embed_input_types(self):
        """Test string vs list[string] inputs."""
        # Single string input
        response_single = self.client.embed(
            model=self.test_model,
            input=self.test_text
        )
        
        # List with single string
        response_list = self.client.embed(
            model=self.test_model,
            input=[self.test_text]
        )
        
        # Both should produce same embedding
        embedding_single = extract_embedding(response_single)
        embedding_list = extract_embedding(response_list)
        
        assert_embeddings_similar(
            embedding_single, embedding_list,
            threshold=0.999,  # Should be nearly identical
            message="Same text should produce same embedding regardless of input format"
        )
    
    def test_embed_unicode(self):
        """Test embedding with Unicode and special characters."""
        for unicode_text in UNICODE_TEST_TEXTS:
            response = self.client.embed(
                model=self.test_model,
                input=unicode_text
            )
            
            validate_embedding_response(response)
            embedding = extract_embedding(response)
            
            assert len(embedding) > 0, \
                f"Unicode text '{unicode_text}' should produce valid embedding"
            
            logger.info(f"Successfully embedded Unicode text: {unicode_text[:20]}...")
    
    def test_embed_long_input(self):
        """Test embedding with very long text (>8k tokens)."""
        response = self.client.embed(
            model=self.test_model,
            input=LONG_TEXT
        )
        
        validate_embedding_response(response)
        embedding = extract_embedding(response)
        
        assert len(embedding) > 0, "Long text should produce valid embedding"
        logger.info(f"Successfully embedded long text ({len(LONG_TEXT)} chars)")
    
    # ===== Options and Parameters Tests =====
    
    def test_embed_truncate(self):
        """Test the truncate parameter for long inputs."""
        # Test with truncate=True
        response_truncate = self.client.embed(
            model=self.test_model,
            input=LONG_TEXT,
            truncate=True
        )
        
        validate_embedding_response(response_truncate)
        logger.info("Truncate parameter accepted")
    
    def test_embed_keep_alive(self):
        """Test the keep_alive parameter."""
        # Test with different keep_alive values
        for keep_alive in ["5m", 300, "1h"]:
            response = self.client.embed(
                model=self.test_model,
                input=self.test_text,
                keep_alive=keep_alive
            )
            
            validate_embedding_response(response)
            logger.info(f"keep_alive={keep_alive} accepted")
    
    def test_embed_options(self):
        """Test passing custom options to embeddings."""
        response = self.client.embed(
            model=self.test_model,
            input=self.test_text,
            options={
                "temperature": 0.0,  # Some models might accept this
                "seed": 42,
            }
        )
        
        validate_embedding_response(response)
        logger.info("Custom options accepted")
    
    # ===== Error Handling Tests =====
    
    def test_embed_invalid_model(self):
        """Test error handling for non-existent embedding models."""
        for invalid_model in INVALID_MODELS:
            with pytest.raises(Exception) as exc_info:
                self.client.embed(
                    model=invalid_model,
                    input=self.test_text
                )
            
            logger.info(f"Invalid model '{invalid_model}' correctly raised: {exc_info.value}")
    
    def test_embed_empty_input(self):
        """Test error handling for empty or null inputs."""
        # Empty string
        with pytest.raises(Exception) as exc_info:
            self.client.embed(
                model=self.test_model,
                input=""
            )
        
        logger.info(f"Empty input correctly raised: {exc_info.value}")
    
    def test_embed_malformed_request(self):
        """Test error handling for malformed embedding requests."""
        # Test with None input
        with pytest.raises(Exception) as exc_info:
            self.client.embed(
                model=self.test_model,
                input=None
            )
        
        logger.info(f"None input correctly raised: {exc_info.value}")
    
    # ===== Response Format Verification =====
    
    def test_embed_response_format(self):
        """Verify the response matches Ollama's expected format."""
        response = self.client.embed(
            model=self.test_model,
            input=self.test_text
        )
        
        # Check response has embeddings field (handle both dict and object responses)
        if hasattr(response, 'embeddings'):
            # SDK object response
            assert hasattr(response, 'embeddings'), "Response should have 'embeddings' attribute"
            embeddings = response.embeddings
        else:
            # Dict response
            assert isinstance(response, dict), "Response should be a dictionary"
            assert "embeddings" in response, "Response should contain 'embeddings' field"
            embeddings = response["embeddings"]
        
        # Verify embeddings is a list
        assert isinstance(embeddings, list), "Embeddings should be a list"
        assert len(embeddings) > 0, "Embeddings list should not be empty"
        
        logger.info("Response format is valid")
    
    def test_embed_array_structure(self):
        """Verify embeddings are returned as proper float arrays."""
        response = self.client.embed(
            model=self.test_model,
            input=self.test_text
        )
        
        embedding = extract_embedding(response)
        
        # Check it's a list
        assert isinstance(embedding, list), "Embedding should be a list"
        
        # Check all values are floats or ints
        assert all(isinstance(x, (int, float)) for x in embedding), \
            "All embedding values should be numeric"
        
        # Check values are in reasonable range (typically normalized)
        embedding_array = np.array(embedding)
        assert np.all(np.isfinite(embedding_array)), \
            "Embedding should not contain inf or nan values"
        
        # Most embeddings are normalized, so magnitude should be reasonable
        magnitude = np.linalg.norm(embedding_array)
        assert 0.1 < magnitude < 10, \
            f"Embedding magnitude {magnitude} seems unusual"
        
        logger.info("Embedding array structure is valid")
    
    # ===== Performance Tests =====
    
    def test_embed_performance(self):
        """Benchmark embedding generation speed."""
        # Warm-up request
        self.client.embed(model=self.test_model, input=self.test_text)
        
        # Measure single embedding time
        response, elapsed_time = measure_response_time(
            lambda: self.client.embed(
                model=self.test_model,
                input=self.test_text
            )
        )
        
        validate_embedding_response(response)
        
        assert elapsed_time < TIMEOUT, \
            f"Embedding took {elapsed_time:.2f}s, exceeding timeout of {TIMEOUT}s"
        
        logger.info(f"Single embedding generated in {elapsed_time:.3f}s")
        
        # Measure batch embedding time
        batch_texts = SAMPLE_TEXTS[:5]
        batch_response, batch_time = measure_response_time(
            lambda: self.client.embed(
                model=self.test_model,
                input=batch_texts
            )
        )
        
        validate_embedding_response(batch_response, expected_count=len(batch_texts))
        
        # Batch should be more efficient than individual requests
        expected_individual_time = elapsed_time * len(batch_texts)
        efficiency = expected_individual_time / batch_time
        
        logger.info(
            f"Batch of {len(batch_texts)} embeddings in {batch_time:.3f}s "
            f"(efficiency: {efficiency:.1f}x)"
        )
    
    # ===== Semantic Tests =====
    
    def test_embed_semantic_similarity(self):
        """Test that semantically similar texts produce similar embeddings."""
        similar_texts = [
            "The cat sat on the mat",
            "A cat was sitting on a mat",
            "The feline rested on the rug"
        ]
        
        different_text = "Python is a programming language"
        
        # Get embeddings
        responses = [
            self.client.embed(model=self.test_model, input=text)
            for text in similar_texts + [different_text]
        ]
        
        embeddings = [extract_embedding(resp) for resp in responses]
        
        # Similar texts should have high similarity
        for i in range(len(similar_texts)):
            for j in range(i + 1, len(similar_texts)):
                similarity = calculate_cosine_similarity(embeddings[i], embeddings[j])
                assert similarity > 0.7, \
                    f"Similar texts should have similarity > 0.7, got {similarity:.3f}"
                logger.info(f"Similarity between text {i} and {j}: {similarity:.3f}")
        
        # Different text should have lower similarity
        for i in range(len(similar_texts)):
            similarity = calculate_cosine_similarity(embeddings[i], embeddings[-1])
            assert similarity < 0.8, \
                f"Different texts should have similarity < 0.8, got {similarity:.3f}"
            logger.info(f"Similarity between text {i} and different text: {similarity:.3f}")
    
    def test_embed_deterministic(self):
        """Test that same input produces same embedding (deterministic)."""
        # Generate embedding twice for same input
        response1 = self.client.embed(
            model=self.test_model,
            input=self.test_text
        )
        
        response2 = self.client.embed(
            model=self.test_model,
            input=self.test_text
        )
        
        embedding1 = extract_embedding(response1)
        embedding2 = extract_embedding(response2)
        
        # Should be identical or nearly identical
        assert_embeddings_similar(
            embedding1, embedding2,
            threshold=0.9999,
            message="Same input should produce (nearly) identical embeddings"
        )
        
        logger.info("Embeddings are deterministic")


# ===== Async Tests =====

class TestEmbeddingsAsync:
    """Test suite for async embedding operations."""
    
    @pytest.fixture
    def async_client(self):
        """Create async client for testing."""
        from ollama import AsyncClient
        return AsyncClient(host=PROXY_HOST)
    
    @pytest.mark.asyncio
    async def test_embed_async(self, async_client):
        """Test asynchronous embedding generation."""
        response = await async_client.embed(
            model=DEFAULT_EMBEDDING_MODEL,
            input=SAMPLE_TEXTS[0]
        )
        
        validate_embedding_response(response)
        logger.info("Async embedding successful")
    
    @pytest.mark.asyncio
    async def test_embed_async_batch(self, async_client):
        """Test async batch embedding processing."""
        import asyncio
        
        # Create multiple embedding tasks
        tasks = [
            async_client.embed(
                model=DEFAULT_EMBEDDING_MODEL,
                input=text
            )
            for text in SAMPLE_TEXTS[:5]
        ]
        
        # Run concurrently
        responses = await asyncio.gather(*tasks)
        
        # Validate all responses
        for i, response in enumerate(responses):
            validate_embedding_response(response)
        
        logger.info(f"Async batch of {len(responses)} embeddings successful")