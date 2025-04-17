"""
Embedding service data models.

This module contains data models used across embedding service components.
"""

from typing import Dict, Any, Optional, List, Union, TypedDict
from pydantic import BaseModel, Field
from enum import Enum, auto
from datetime import datetime

class EmbeddingModel(str, Enum):
    """Supported embedding models."""
    OPENAI = "openai"
    MPNET = "all-mpnet-base-v2"
    MINILM = "all-MiniLM-L6-v2"
    CUSTOM = "custom"

class DistanceMetric(str, Enum):
    """Vector distance metrics."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT = "dot"
    MANHATTAN = "manhattan"

class SearchType(str, Enum):
    """Search types supported by the service."""
    VECTOR = "vector"
    HYBRID = "hybrid"
    FACETED = "faceted"
    CROSS_PACKAGE = "cross_package"

class EmbeddingConfig(BaseModel):
    """Configuration for embedding operations."""
    
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    distance_metric: DistanceMetric = DistanceMetric.COSINE
    normalize: bool = True
    batch_size: int = 32
    cache_enabled: bool = True
    cache_ttl: int = 3600  # seconds
    default_top_k: int = 10
    
    # Optional API keys and credentials - never logged
    api_keys: Dict[str, str] = Field(default_factory=dict, exclude=True)
    
    class Config:
        use_enum_values = True

class SearchParams(BaseModel):
    """Search parameters for vector search."""
    
    query: str
    top_k: int = 10
    min_score: float = 0.0
    filter_metadata: Optional[Dict[str, Any]] = None
    search_type: SearchType = SearchType.VECTOR
    include_metadata: bool = True
    
    # Hybrid search options
    hybrid_alpha: float = 0.5  # weight between vector and text search
    
    # Faceted search options
    facets: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True

class SearchResult(TypedDict, total=False):
    """Type hint for search results."""
    
    id: str
    score: float
    metadata: Dict[str, Any]
    content: Optional[str]
    distance: float
    vector: Optional[List[float]]

class IndexStats(BaseModel):
    """Statistics about an embedding index."""
    
    index_name: str
    vector_count: int
    dimension: int
    created_at: datetime
    updated_at: datetime
    disk_size_bytes: int
    metadata_fields: List[str]
    model_name: str
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        } 