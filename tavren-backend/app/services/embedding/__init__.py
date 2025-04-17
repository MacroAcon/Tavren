"""
Embedding Service Package

This package contains modularized components of the embedding service,
which has been split from a monolithic implementation into focused modules.
"""

from typing import Dict, Any, Optional, List, Tuple, Union, TYPE_CHECKING

# Import key components to expose at package level
from .index import EmbeddingIndexer, create_index, delete_index
from .search import VectorSearch, hybrid_search, faceted_search, query_expansion
from .vector_ops import VectorOperations, similarity_score, normalize_vector
from .models import EmbeddingConfig, SearchParams, IndexStats, SearchResult

# Optional: Factory function to create appropriate service components
def create_embedding_service(
    config: Optional[Dict[str, Any]] = None
) -> Tuple[EmbeddingIndexer, VectorSearch, VectorOperations]:
    """
    Factory function to create embedding service components with consistent configuration.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Tuple of (indexer, search, vector_ops) components
    """
    cfg = EmbeddingConfig(**(config or {}))
    indexer = EmbeddingIndexer(cfg)
    search = VectorSearch(cfg)
    vector_ops = VectorOperations(cfg)
    return indexer, search, vector_ops

# Type aliases for better code readability
EmbeddingVector = List[float]
DocumentID = str
ScoreValue = float
SearchResults = List[Tuple[DocumentID, ScoreValue, Dict[str, Any]]]

__all__ = [
    # Core components
    'EmbeddingIndexer', 
    'VectorSearch', 
    'VectorOperations',
    
    # Helper functions
    'create_index',
    'delete_index',
    'hybrid_search',
    'faceted_search',
    'query_expansion',
    'similarity_score',
    'normalize_vector',
    
    # Factory
    'create_embedding_service',
    
    # Models
    'EmbeddingConfig',
    'SearchParams',
    'IndexStats',
    'SearchResult',
    
    # Type aliases
    'EmbeddingVector',
    'DocumentID',
    'ScoreValue',
    'SearchResults'
] 