"""
API router for embedding operations.
Provides endpoints for creating embeddings, indexing data packages, and semantic search.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.auth import get_current_active_user
from app.schemas import (
    UserDisplay, EmbeddingRequest, EmbeddingResponse, 
    VectorSearchRequest, VectorSearchResponse, 
    IndexPackageRequest, IndexPackageResponse, 
    RAGRequest, RAGResponse,
    HybridSearchRequest, HybridSearchResponse,
    CrossPackageContextRequest, CrossPackageContextResponse,
    QueryExpansionRequest, QueryExpansionResponse,
    FacetedSearchRequest, FacetedSearchResponse
)

# Set up logging
log = logging.getLogger("app")

# Create router
embedding_router = APIRouter(
    prefix="/api/embeddings",
    tags=["embeddings"]
)

@embedding_router.post("/create", response_model=Dict[str, Any])
async def create_embedding(
    request: EmbeddingRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Create an embedding for text or a data package.
    
    This endpoint creates vector embeddings that can be used for 
    semantic search and retrieval operations.
    
    Returns the embedding record information.
    """
    try:
        log.info(f"Creating embedding for {'package ' + request.package_id if request.package_id else 'text input'}")
        
        if not request.text and not request.package_id:
            raise HTTPException(status_code=400, detail="Either text or package_id must be provided")
        
        # Create the embedding
        embedding_result = await embedding_service.create_embedding(
            text_content=request.text,
            package_id=request.package_id,
            embedding_type=request.embedding_type or "content",
            model_name=request.model_name,
            use_nvidia_api=request.use_nvidia_api,
            metadata=request.metadata
        )
        
        log.info(f"Successfully created embedding, ID: {embedding_result['id']}")
        return embedding_result
        
    except Exception as e:
        log.error(f"Error creating embedding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating embedding: {str(e)}")

@embedding_router.post("/index-package", response_model=IndexPackageResponse)
async def index_data_package(
    request: IndexPackageRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Index a data package for semantic search.
    
    This endpoint creates embeddings for a data package's content
    and metadata to enable efficient semantic search.
    
    Returns information about the created embeddings.
    """
    try:
        log.info(f"Indexing data package {request.package_id}")
        
        # Create embeddings for the package
        index_result = await embedding_service.index_data_package(
            package_id=request.package_id,
            use_nvidia_api=request.use_nvidia_api
        )
        
        log.info(f"Successfully indexed package {request.package_id}")
        return index_result
        
    except Exception as e:
        log.error(f"Error indexing data package: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error indexing data package: {str(e)}")

@embedding_router.post("/search", response_model=VectorSearchResponse)
async def vector_search(
    request: VectorSearchRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Perform semantic vector search.
    
    This endpoint searches for semantically similar content
    based on vector similarity.
    
    Returns a list of results with similarity scores.
    """
    try:
        log.info(f"Performing vector search for query: {request.query_text[:50]}...")
        
        # Perform the search
        search_results = await embedding_service.vector_search(
            query_text=request.query_text,
            embedding_type=request.embedding_type,
            top_k=request.top_k,
            use_nvidia_api=request.use_nvidia_api,
            filter_metadata=request.filter_metadata
        )
        
        log.info(f"Vector search found {len(search_results)} results")
        return {
            "query": request.query_text,
            "results": search_results,
            "count": len(search_results)
        }
        
    except Exception as e:
        log.error(f"Error performing vector search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing vector search: {str(e)}")

@embedding_router.post("/retrieve-context", response_model=RAGResponse)
async def retrieve_context(
    request: RAGRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Retrieve context for retrieval augmented generation (RAG).
    
    This endpoint retrieves relevant context based on a query,
    formatted for use in RAG with LLMs.
    
    Returns the formatted context with metadata.
    """
    try:
        log.info(f"Retrieving context for RAG: {request.query_text[:50]}...")
        
        # Retrieve context
        context_result = await embedding_service.retrieve_context(
            query_text=request.query_text,
            top_k=request.top_k,
            max_tokens=request.max_tokens
        )
        
        log.info(f"Retrieved context with {context_result['result_count']} items")
        return context_result
        
    except Exception as e:
        log.error(f"Error retrieving context: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving context: {str(e)}")

@embedding_router.get("/{embedding_id}", response_model=Dict[str, Any])
async def get_embedding(
    embedding_id: int = Path(..., description="The ID of the embedding to retrieve"),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Get an embedding by ID.
    
    This endpoint retrieves an embedding record by its ID.
    
    Returns the embedding information and vector.
    """
    try:
        log.info(f"Retrieving embedding {embedding_id}")
        
        # Get the embedding
        embedding = await embedding_service.get_embedding(embedding_id=embedding_id)
        
        if not embedding:
            raise HTTPException(status_code=404, detail=f"Embedding {embedding_id} not found")
        
        log.info(f"Successfully retrieved embedding {embedding_id}")
        return embedding
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving embedding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving embedding: {str(e)}")

@embedding_router.get("/package/{package_id}/{embedding_type}", response_model=Dict[str, Any])
async def get_package_embedding(
    package_id: str = Path(..., description="The ID of the package"),
    embedding_type: str = Path(..., description="The type of embedding to retrieve"),
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Get an embedding for a package by type.
    
    This endpoint retrieves an embedding for a specific package and type.
    
    Returns the embedding information and vector.
    """
    try:
        log.info(f"Retrieving {embedding_type} embedding for package {package_id}")
        
        # Get the embedding
        embedding = await embedding_service.get_embedding(
            package_id=package_id,
            embedding_type=embedding_type
        )
        
        if not embedding:
            raise HTTPException(
                status_code=404,
                detail=f"Embedding of type {embedding_type} for package {package_id} not found"
            )
        
        log.info(f"Successfully retrieved embedding for package {package_id}")
        return embedding
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving package embedding: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving package embedding: {str(e)}")

@embedding_router.post("/hybrid-search", response_model=HybridSearchResponse)
async def hybrid_search(
    request: HybridSearchRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Perform hybrid search combining semantic and keyword matching.
    
    This endpoint performs a combined search that balances semantic understanding
    with keyword precision for better results.
    
    Returns weighted results from both search approaches.
    """
    try:
        log.info(f"Performing hybrid search for query: {request.query_text[:50]}...")
        
        # Perform the hybrid search
        search_results = await embedding_service.hybrid_search(
            query_text=request.query_text,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight,
            embedding_type=request.embedding_type,
            top_k=request.top_k,
            use_nvidia_api=request.use_nvidia_api,
            filter_metadata=request.filter_metadata
        )
        
        log.info(f"Hybrid search found {len(search_results)} results")
        return {
            "query": request.query_text,
            "results": search_results,
            "count": len(search_results),
            "semantic_weight": request.semantic_weight,
            "keyword_weight": request.keyword_weight,
            "search_type": "hybrid"
        }
        
    except Exception as e:
        log.error(f"Error performing hybrid search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing hybrid search: {str(e)}")

@embedding_router.post("/cross-package-context", response_model=CrossPackageContextResponse)
async def cross_package_context(
    request: CrossPackageContextRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Assemble context from multiple data packages for complex queries.
    
    This endpoint provides richer context by retrieving information
    from different data packages and combining them based on relevance.
    
    Returns assembled context with package organization.
    """
    try:
        log.info(f"Assembling cross-package context for query: {request.query_text[:50]}...")
        
        # Assemble cross-package context
        context_result = await embedding_service.assemble_cross_package_context(
            query_text=request.query_text,
            max_packages=request.max_packages,
            max_items_per_package=request.max_items_per_package,
            max_tokens=request.max_tokens,
            use_hybrid_search=request.use_hybrid_search,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight
        )
        
        log.info(f"Cross-package context assembled with {context_result['package_count']} packages")
        return context_result
        
    except Exception as e:
        log.error(f"Error assembling cross-package context: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error assembling cross-package context: {str(e)}")

@embedding_router.post("/query-expansion", response_model=QueryExpansionResponse)
async def query_expansion_search(
    request: QueryExpansionRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Enhance search by automatically expanding the query with related terms.
    
    This endpoint improves recall for queries by generating alternative
    phrasings and combining the results.
    
    Returns results from the expanded search with query information.
    """
    try:
        log.info(f"Performing query expansion search for: {request.query_text[:50]}...")
        
        # Perform query expansion search
        search_results = await embedding_service.query_expansion_search(
            query_text=request.query_text,
            top_k=request.top_k,
            use_hybrid_search=request.use_hybrid_search,
            max_expansions=request.max_expansions,
            expansion_model=request.expansion_model
        )
        
        log.info(f"Query expansion search found {search_results['result_count']} results with {len(search_results['expanded_queries'])} query variations")
        return search_results
        
    except Exception as e:
        log.error(f"Error performing query expansion search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing query expansion search: {str(e)}")

@embedding_router.post("/faceted-search", response_model=FacetedSearchResponse)
async def faceted_search(
    request: FacetedSearchRequest,
    db: AsyncSession = Depends(get_db),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Perform faceted search that combines semantic search with metadata filtering.
    
    This endpoint allows structured information retrieval by filtering
    and grouping results based on metadata facets while maintaining
    semantic relevance.
    
    Returns results organized by facets with relevance scores.
    """
    try:
        log.info(f"Performing faceted search for query: {request.query_text[:50]}...")
        
        # Perform faceted search
        search_results = await embedding_service.faceted_search(
            query_text=request.query_text,
            facets=request.facets,
            facet_weights=request.facet_weights,
            use_hybrid_search=request.use_hybrid_search,
            top_k=request.top_k
        )
        
        log.info(f"Faceted search found {search_results['result_count']} results across {len(request.facets)} facet categories")
        return search_results
        
    except Exception as e:
        log.error(f"Error performing faceted search: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing faceted search: {str(e)}") 