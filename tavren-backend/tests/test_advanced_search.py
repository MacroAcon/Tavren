"""
Tests for the advanced search features in the embedding service.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from fastapi.testclient import TestClient

from app.main import app
from app.services.embedding_service import EmbeddingService

client = TestClient(app)

# Authentication mock
@pytest.fixture(autouse=True)
def mock_auth():
    """Mock authentication to bypass it in tests."""
    with patch("app.auth.get_current_active_user", return_value={"id": 1, "username": "testuser", "is_active": True}):
        yield

# Test data
@pytest.fixture
def sample_package_data():
    return {
        "package_id": "pkg_test123",
        "content": "This is test content for search functionality.",
        "metadata": {
            "data_type": "test",
            "record_count": 1,
            "schema_version": "1.0"
        }
    }

@pytest.fixture
def sample_embedding_result():
    return {
        "id": 123,
        "package_id": "pkg_test123",
        "embedding_type": "content_chunk_0",
        "text_content": "This is test content for search functionality.",
        "metadata": {"data_type": "test"},
        "semantic_score": 0.85,
        "keyword_score": 0.75,
        "combined_score": 0.82
    }

# Tests for hybrid search
@pytest.mark.asyncio
async def test_hybrid_search(sample_embedding_result):
    """Test the hybrid search endpoint."""
    # Mock the embedding service
    with patch("app.services.embedding_service.EmbeddingService.hybrid_search") as mock_hybrid_search:
        # Setup mock return value
        mock_hybrid_search.return_value = [sample_embedding_result]
        
        # Make request to the endpoint
        response = client.post(
            "/api/embeddings/hybrid-search",
            json={
                "query_text": "test search",
                "semantic_weight": 0.7,
                "keyword_weight": 0.3,
                "top_k": 5
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test search"
        assert data["count"] == 1
        assert data["search_type"] == "hybrid"
        assert data["semantic_weight"] == 0.7
        assert data["keyword_weight"] == 0.3
        assert len(data["results"]) == 1
        assert data["results"][0]["id"] == 123

# Tests for cross-package context assembly
@pytest.mark.asyncio
async def test_cross_package_context():
    """Test the cross-package context assembly endpoint."""
    # Mock the embedding service
    with patch("app.services.embedding_service.EmbeddingService.assemble_cross_package_context") as mock_cross_package:
        # Setup mock return value
        mock_cross_package.return_value = {
            "query": "test query",
            "context": "Assembled context from multiple packages",
            "package_count": 2,
            "item_count": 3,
            "token_count": 100,
            "latency_ms": 150.5,
            "packages": [
                {"id": "pkg_test1", "name": "Test Package 1", "item_count": 2},
                {"id": "pkg_test2", "name": "Test Package 2", "item_count": 1}
            ],
            "search_type": "hybrid",
            "timestamp": "2023-07-15T14:32:24.123Z"
        }
        
        # Make request to the endpoint
        response = client.post(
            "/api/embeddings/cross-package-context",
            json={
                "query_text": "test query",
                "max_packages": 3,
                "max_items_per_package": 2
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert data["package_count"] == 2
        assert data["item_count"] == 3
        assert data["search_type"] == "hybrid"
        assert len(data["packages"]) == 2

# Tests for query expansion search
@pytest.mark.asyncio
async def test_query_expansion_search(sample_embedding_result):
    """Test the query expansion search endpoint."""
    # Mock the embedding service
    with patch("app.services.embedding_service.EmbeddingService.query_expansion_search") as mock_expansion:
        # Setup mock return value
        mock_expansion.return_value = {
            "original_query": "test query",
            "expanded_queries": [
                "test query",
                "query for testing",
                "search test"
            ],
            "results": [sample_embedding_result],
            "result_count": 1,
            "latency_ms": 200.3,
            "search_type": "query_expansion",
            "timestamp": "2023-07-15T14:35:18.456Z"
        }
        
        # Make request to the endpoint
        response = client.post(
            "/api/embeddings/query-expansion",
            json={
                "query_text": "test query",
                "max_expansions": 3
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["original_query"] == "test query"
        assert len(data["expanded_queries"]) == 3
        assert data["result_count"] == 1
        assert data["search_type"] == "query_expansion"
        assert len(data["results"]) == 1

# Tests for faceted search
@pytest.mark.asyncio
async def test_faceted_search(sample_embedding_result):
    """Test the faceted search endpoint."""
    # Create a sample faceted result
    faceted_result = dict(sample_embedding_result)
    faceted_result["facet_match_score"] = 0.9
    faceted_result["matched_facets"] = 1
    faceted_result["original_score"] = 0.85
    faceted_result["faceted_score"] = 0.87
    
    # Mock the embedding service
    with patch("app.services.embedding_service.EmbeddingService.faceted_search") as mock_faceted:
        # Setup mock return value
        mock_faceted.return_value = {
            "query": "test query",
            "facets": {"data_type": ["test"]},
            "facet_weights": {"data_type": 1.0},
            "results": [faceted_result],
            "facet_groups": {
                "data_type": {
                    "test": [faceted_result]
                }
            },
            "result_count": 1,
            "latency_ms": 150.8,
            "search_type": "faceted",
            "use_hybrid_search": True,
            "timestamp": "2023-07-15T14:40:52.789Z"
        }
        
        # Make request to the endpoint
        response = client.post(
            "/api/embeddings/faceted-search",
            json={
                "query_text": "test query",
                "facets": {"data_type": ["test"]}
            }
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert data["facets"] == {"data_type": ["test"]}
        assert data["result_count"] == 1
        assert data["search_type"] == "faceted"
        assert "facet_groups" in data
        assert "data_type" in data["facet_groups"] 