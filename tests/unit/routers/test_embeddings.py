"""
Unit tests for the embeddings router.
"""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from src.routers.embeddings import create_embeddings, router


class TestEmbeddingsEndpoint:
    """Test the embeddings endpoint."""

    @pytest.mark.asyncio
    async def test_embeddings_not_implemented(self):
        """Test that embeddings endpoint raises not implemented error."""
        # Create a mock request
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.request_id = "test-embeddings-123"

        # Create a mock embeddings request
        mock_embeddings_request = {
            "model": "text-embedding-ada-002",
            "input": "Test embedding text",
        }

        # Test that the endpoint raises HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await create_embeddings(mock_embeddings_request)

        # Verify the exception details
        assert exc_info.value.status_code == 501
        assert "not implemented" in exc_info.value.detail.lower()

    def test_router_configured(self):
        """Test that the router is properly configured."""
        # Check that router has the endpoint
        routes = [route.path for route in router.routes]
        assert "/api/embeddings" in routes

        # Check the endpoint accepts POST
        for route in router.routes:
            if route.path == "/api/embeddings":
                assert "POST" in route.methods
