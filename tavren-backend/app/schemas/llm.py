"""
Pydantic schemas for LLM, embedding, and vector search operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

# LLM Processing Schemas
class LLMProcessRequest(BaseModel):
    """Schema for LLM processing requests."""
    package_id: str
    instructions: str
    model_config: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None

class LLMProcessResponse(BaseModel):
    """Schema for LLM processing responses."""
    request_id: str
    model_used: str
    package_id: str
    result: str
    usage: Dict[str, Any]
    timestamp: float

# Embedding Schemas
class EmbeddingRequest(BaseModel):
    """Schema for embedding generation requests."""
    text: Optional[str] = None
    package_id: Optional[str] = None
    model_name: Optional[str] = None
    embedding_type: Optional[str] = "content"
    use_nvidia_api: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Sample text to create embeddings for",
                "model_name": "text-embedding-ada-002",
                "embedding_type": "content",
                "use_nvidia_api": True
            }
        }

class EmbeddingResponse(BaseModel):
    """Schema for embedding generation responses."""
    request_id: str
    model_used: str
    embedding: List[float]
    dimension: int
    usage: Dict[str, Any]
    timestamp: float
    package_id: Optional[str] = None

# Vector Search Schemas
class VectorSearchRequest(BaseModel):
    """Schema for vector search requests."""
    query_text: str
    embedding_type: Optional[str] = None
    top_k: Optional[int] = None
    use_nvidia_api: bool = True
    filter_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "Sample search query",
                "embedding_type": "content",
                "top_k": 5,
                "use_nvidia_api": True,
                "filter_metadata": {"category": "health"}
            }
        }

class VectorSearchResponse(BaseModel):
    """Schema for vector search responses."""
    query: str
    results: List[Dict[str, Any]]
    count: int

# Index Schemas
class IndexPackageRequest(BaseModel):
    """Schema for indexing package requests."""
    package_id: str
    use_nvidia_api: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "package_id": "package123",
                "use_nvidia_api": True
            }
        }

class IndexPackageResponse(BaseModel):
    """Schema for indexing package responses."""
    package_id: str
    embeddings_created: List[Dict[str, Any]]
    data_type: str
    record_count: int

# RAG Schemas
class RAGRequest(BaseModel):
    """Schema for RAG retrieval requests."""
    query_text: str
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "What medications are available for diabetes?",
                "top_k": 3,
                "max_tokens": 1000
            }
        }

class RAGResponse(BaseModel):
    """Schema for RAG retrieval responses."""
    query: str
    context: str
    package_ids: List[str]
    result_count: int
    timestamp: float

class RAGGenerationRequest(BaseModel):
    """Schema for RAG generation requests."""
    query: str
    instructions: Optional[str] = "Provide a concise and accurate response based on the retrieved context."
    model_name: Optional[str] = None
    top_k: Optional[int] = 3
    context_max_tokens: Optional[int] = 2000
    response_max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What medications are available for diabetes?",
                "instructions": "Provide a concise and accurate response based on the retrieved context.",
                "top_k": 3,
                "context_max_tokens": 2000,
                "response_max_tokens": 1000,
                "temperature": 0.7
            }
        }

class RAGGenerationResponse(BaseModel):
    """Schema for RAG generation responses."""
    request_id: str
    query: str
    response: str
    context_packages: List[str]
    context_count: int
    model_used: str
    usage: Dict[str, Any]
    timestamp: float

# Advanced Search Schemas
class HybridSearchRequest(BaseModel):
    """Schema for hybrid search requests."""
    query_text: str
    semantic_weight: Optional[float] = 0.7
    keyword_weight: Optional[float] = 0.3
    embedding_type: Optional[str] = None
    top_k: Optional[int] = None
    use_nvidia_api: bool = True
    filter_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "diabetes treatment options",
                "semantic_weight": 0.7,
                "keyword_weight": 0.3,
                "top_k": 5
            }
        }

class HybridSearchResponse(BaseModel):
    """Schema for hybrid search responses."""
    query: str
    results: List[Dict[str, Any]]
    count: int
    semantic_weight: float
    keyword_weight: float
    search_type: str = "hybrid"

class CrossPackageContextRequest(BaseModel):
    """Schema for cross-package context requests."""
    query_text: str
    max_packages: Optional[int] = 5
    max_items_per_package: Optional[int] = 3
    max_tokens: Optional[int] = 2000
    use_hybrid_search: bool = True
    semantic_weight: Optional[float] = 0.7
    keyword_weight: Optional[float] = 0.3
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "treatment options for chronic conditions",
                "max_packages": 5,
                "max_items_per_package": 3,
                "max_tokens": 2000,
                "use_hybrid_search": True
            }
        }

class CrossPackageContextResponse(BaseModel):
    """Schema for cross-package context responses."""
    query: str
    context: str
    package_count: int
    item_count: int
    token_count: int
    latency_ms: float
    packages: List[Dict[str, Any]]
    search_type: str
    timestamp: str

class QueryExpansionRequest(BaseModel):
    """Schema for query expansion requests."""
    query_text: str
    top_k: Optional[int] = None
    use_hybrid_search: bool = True
    max_expansions: Optional[int] = 3
    expansion_model: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "diabetes",
                "top_k": 10,
                "use_hybrid_search": True,
                "max_expansions": 3
            }
        }

class QueryExpansionResponse(BaseModel):
    """Schema for query expansion responses."""
    original_query: str
    expanded_queries: List[str]
    results: List[Dict[str, Any]]
    result_count: int
    latency_ms: float
    search_type: str = "query_expansion"
    timestamp: str

class FacetedSearchRequest(BaseModel):
    """Schema for faceted search requests."""
    query_text: str
    facets: Dict[str, List[str]]
    facet_weights: Optional[Dict[str, float]] = None
    use_hybrid_search: bool = True
    top_k: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "diabetes medication",
                "facets": {
                    "data_type": ["medical_records", "research_papers"],
                    "source": ["trusted_provider", "academic"]
                },
                "facet_weights": {
                    "data_type": 0.6,
                    "source": 0.4
                },
                "use_hybrid_search": True,
                "top_k": 10
            }
        }

class FacetedSearchResponse(BaseModel):
    """Schema for faceted search responses."""
    query: str
    facets: Dict[str, List[str]]
    facet_weights: Dict[str, float]
    results: List[Dict[str, Any]]
    facet_groups: Dict[str, Dict[str, List[Dict[str, Any]]]]
    result_count: int
    latency_ms: float
    search_type: str = "faceted"
    use_hybrid_search: bool
    timestamp: str 