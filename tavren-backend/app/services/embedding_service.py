"""
Embedding service for processing, storing, and retrieving vector embeddings.
Provides functionality for semantic search and retrieval augmented generation.
"""

import logging
import json
import numpy as np
import time
import hashlib
import re
from typing import Dict, Any, List, Optional, Tuple, Union
from fastapi import Depends
from sqlalchemy import select, desc, func, or_, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime
import asyncio

from app.database import get_db
from app.models import DataPackageEmbedding, DataPackage
from app.config import settings
from app.services.llm_service import LLMService, get_llm_service
from app.services.data_packaging import DataPackagingService, get_data_packaging_service
from app.services.data_service import DataService, get_data_service
from app.utils.text_utils import count_tokens, truncate_text_to_token_limit, chunk_text
from app.utils.cache_utils import (
    cache_embedding, get_cached_embedding,
    cache_vector_search, get_cached_vector_search,
    cached
)

# Set up logging
log = logging.getLogger("app")

# Import pgvector specific functions if using PostgreSQL
if settings.DATABASE_URL.startswith('postgresql'):
    from pgvector.sqlalchemy import Vector
    from sqlalchemy.sql.expression import cast
    from sqlalchemy import Float as SqlFloat
    from sqlalchemy.dialects.postgresql import ARRAY, JSONB
    from sqlalchemy.dialects.postgresql.operators import custom_op

class EmbeddingService:
    """Service for managing vector embeddings and semantic search"""
    
    def __init__(
        self, 
        db: AsyncSession,
        llm_service: LLMService,
        data_packaging_service: DataPackagingService,
        data_service: DataService
    ):
        """Initialize the embedding service with database session and dependencies."""
        self.db = db
        self.llm_service = llm_service
        self.data_packaging_service = data_packaging_service
        self.data_service = data_service
        
        # Default model configuration
        self.default_model_name = settings.DEFAULT_EMBEDDING_MODEL
        self.vector_dimension = settings.EMBEDDING_DIMENSION
        self.vector_search_top_k = settings.VECTOR_SEARCH_TOP_K
        self.is_postgres = settings.DATABASE_URL.startswith('postgresql')
        
        # Local embedding model for smaller operations or fallback
        self._local_model = None
        
        # Hybrid search configuration
        self.hybrid_search_weight_semantic = 0.7  # Weight for semantic search (0-1)
        self.hybrid_search_weight_keyword = 0.3   # Weight for keyword search (0-1)
        self.hybrid_search_boost_exact_match = 1.2  # Boost factor for exact matches
        self.cross_package_max_items = 20  # Max items to include in cross-package context
        
        log.info(f"Embedding Service initialized with dimension {self.vector_dimension} and PostgreSQL support: {self.is_postgres}")
    
    def _get_local_model(self) -> SentenceTransformer:
        """Lazy load the local embedding model when needed."""
        if self._local_model is None:
            try:
                # Use a smaller local model for efficient processing
                # This can be replaced with a more powerful model if needed
                self._local_model = SentenceTransformer('all-MiniLM-L6-v2')
                log.info("Local embedding model loaded successfully")
            except Exception as e:
                log.error(f"Error loading local embedding model: {str(e)}", exc_info=True)
                raise Exception(f"Failed to load local embedding model: {str(e)}")
        
        return self._local_model
    
    async def create_embedding(
        self,
        text_content: str,
        package_id: Optional[str] = None,
        embedding_type: str = "content",
        model_name: Optional[str] = None,
        use_nvidia_api: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        audit_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create and store an embedding for text content or a data package.
        
        Args:
            text_content: Text to create embedding for
            package_id: Optional ID of associated data package
            embedding_type: Type of embedding (content, metadata, combined)
            model_name: Name of model to use for embedding
            use_nvidia_api: Whether to use Nvidia API (True) or local model (False)
            metadata: Additional metadata for the embedding
            audit_id: Optional ID of associated audit record
            
        Returns:
            Dict with embedding information
        """
        try:
            # Use specified model or default
            model_name = model_name or self.default_model_name
            
            # Generate the embedding
            if use_nvidia_api:
                # Use Nvidia's API for embedding generation
                embedding_result = await self.llm_service.generate_embedding(
                    text=text_content,
                    model_name=model_name
                )
                embedding_vector = embedding_result.get("embedding", [])
                dimension = embedding_result.get("dimension", len(embedding_vector))
            else:
                # Use local model for embedding generation
                local_model = self._get_local_model()
                embedding_vector = local_model.encode(text_content).tolist()
                dimension = len(embedding_vector)
            
            # Create the embedding record
            embedding_record = DataPackageEmbedding(
                package_id=package_id,
                embedding_type=embedding_type,
                model_name=model_name,
                dimension=dimension,
                embedding_json=json.dumps(embedding_vector),
                text_content=text_content[:10000],  # Limit to prevent huge text storage
                metadata=metadata,
                audit_id=audit_id
            )
            
            # If using PostgreSQL with pgvector, populate the embedding column
            if self.is_postgres:
                setattr(embedding_record, 'embedding', embedding_vector)
            
            # Save to database
            self.db.add(embedding_record)
            await self.db.commit()
            await self.db.refresh(embedding_record)
            
            log.info(f"Created {embedding_type} embedding for {'package ' + package_id if package_id else 'text'}")
            
            return {
                "id": embedding_record.id,
                "package_id": package_id,
                "embedding_type": embedding_type,
                "model_name": model_name,
                "dimension": dimension,
                "created_at": embedding_record.created_at
            }
        
        except Exception as e:
            await self.db.rollback()
            log.error(f"Error creating embedding: {str(e)}", exc_info=True)
            raise Exception(f"Failed to create embedding: {str(e)}")
    
    async def get_embedding(
        self,
        embedding_id: Optional[int] = None,
        package_id: Optional[str] = None,
        embedding_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve an embedding by ID or package ID and type.
        
        Args:
            embedding_id: ID of the embedding record
            package_id: ID of the associated data package
            embedding_type: Type of embedding to retrieve
            
        Returns:
            Dict with embedding information or None if not found
        """
        try:
            # Try to get from cache first
            cache_key = None
            if embedding_id:
                cache_key = f"{embedding_id}"
            elif package_id and embedding_type:
                cache_key = f"{package_id}:{embedding_type}"
            
            if cache_key:
                cached_embedding = await get_cached_embedding(cache_key)
                if cached_embedding:
                    log.info(f"Retrieved embedding from cache: {cache_key}")
                    return cached_embedding
            
            # Construct the query based on provided parameters
            if embedding_id:
                query = select(DataPackageEmbedding).where(DataPackageEmbedding.id == embedding_id)
            elif package_id and embedding_type:
                query = select(DataPackageEmbedding).where(
                    DataPackageEmbedding.package_id == package_id,
                    DataPackageEmbedding.embedding_type == embedding_type
                )
            else:
                raise ValueError("Either embedding_id or both package_id and embedding_type must be provided")
            
            # Execute the query
            result = await self.db.execute(query)
            embedding_record = result.scalars().first()
            
            if not embedding_record:
                return None
            
            # Parse the embedding vector from JSON or get from vector column
            if self.is_postgres and hasattr(embedding_record, 'embedding') and embedding_record.embedding is not None:
                embedding_vector = embedding_record.embedding
            else:
                embedding_vector = json.loads(embedding_record.embedding_json)
            
            # Prepare the response
            embedding_data = {
                "id": embedding_record.id,
                "package_id": embedding_record.package_id,
                "embedding_type": embedding_record.embedding_type,
                "model_name": embedding_record.model_name,
                "dimension": embedding_record.dimension,
                "embedding": embedding_vector,
                "text_content": embedding_record.text_content,
                "metadata": embedding_record.metadata,
                "created_at": embedding_record.created_at,
                "updated_at": embedding_record.updated_at
            }
            
            # Cache the embedding for future retrieval
            if cache_key:
                await cache_embedding(cache_key, embedding_data, settings.EMBEDDING_CACHE_TTL)
            
            return embedding_data
        
        except Exception as e:
            log.error(f"Error retrieving embedding: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve embedding: {str(e)}")
    
    async def vector_search(
        self,
        query_text: str,
        embedding_type: Optional[str] = None,
        top_k: Optional[int] = None,
        use_nvidia_api: bool = True,
        filter_metadata: Optional[Dict[str, Any]] = None,
        track_metrics: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        evaluation_service = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using query text.
        
        Args:
            query_text: Text to search for
            embedding_type: Optional filter for embedding type
            top_k: Number of results to return (default from settings)
            use_nvidia_api: Whether to use Nvidia API for encoding
            filter_metadata: Optional metadata filters
            track_metrics: Whether to track performance metrics
            session_id: Optional session ID for tracking
            user_id: Optional user ID for tracking
            evaluation_service: Optional evaluation service instance
            
        Returns:
            List of results with similarity scores
        """
        try:
            start_time = time.time()
            top_k = top_k or self.vector_search_top_k
            
            # Generate a cache key for this search
            query_params = {
                "query": query_text[:100],  # Limit length for cache key
                "embedding_type": embedding_type,
                "top_k": top_k,
                "use_nvidia_api": use_nvidia_api
            }
            
            if filter_metadata:
                # Sort to ensure consistent keys
                sorted_metadata = dict(sorted(filter_metadata.items()))
                query_params["filter_metadata"] = json.dumps(sorted_metadata)
            
            # Hash the parameters to create a consistent cache key
            query_hash = hashlib.md5(json.dumps(query_params).encode()).hexdigest()
            
            # Try to get from cache
            cached_results = await get_cached_vector_search(query_hash)
            if cached_results is not None:
                log.info(f"Vector search cache hit for query: {query_text[:50]}...")
                
                # Even for cache hits, track metrics if requested
                if track_metrics and evaluation_service:
                    end_time = time.time()
                    latency_ms = (end_time - start_time) * 1000
                    
                    # Add cache hit to metadata
                    metadata = {"cache_hit": True, "query_hash": query_hash}
                    
                    # Log metrics with evaluation service
                    await evaluation_service.log_retrieval_metrics(
                        query_text=query_text,
                        results=cached_results,
                        latency_ms=latency_ms,
                        user_id=user_id,
                        session_id=session_id,
                        metadata=metadata
                    )
                    
                return cached_results
            
            # Generate embedding for query text
            if use_nvidia_api:
                embedding_result = await self.llm_service.generate_embedding(
                    text=query_text,
                    model_name=self.default_model_name
                )
                query_embedding = embedding_result.get("embedding", [])
            else:
                local_model = self._get_local_model()
                query_embedding = local_model.encode(query_text).tolist()
            
            # Build the query
            if self.is_postgres:
                # Use pgvector's native similarity search
                # Convert the query embedding to a PostgreSQL array
                query = select(
                    DataPackageEmbedding,
                    func.cosine_similarity(DataPackageEmbedding.embedding, query_embedding).label("similarity")
                ).order_by(
                    func.cosine_similarity(DataPackageEmbedding.embedding, query_embedding).desc()
                )
            else:
                # For non-PostgreSQL databases, we'll need to fetch all records and compute similarity in Python
                query = select(DataPackageEmbedding)
            
            # Apply filters if provided
            if embedding_type:
                query = query.where(DataPackageEmbedding.embedding_type == embedding_type)
            
            if filter_metadata:
                for key, value in filter_metadata.items():
                    # This assumes the metadata is stored in a JSONB column or equivalent
                    # May need adjustment based on DB type and schema
                    query = query.where(DataPackageEmbedding.metadata[key].astext == str(value))
            
            # Execute the query
            if self.is_postgres:
                # For PostgreSQL, limit in the query
                query = query.limit(top_k)
                result = await self.db.execute(query)
                records = result.all()
                results = [
                    {
                        "id": record.DataPackageEmbedding.id,
                        "package_id": record.DataPackageEmbedding.package_id,
                        "embedding_type": record.DataPackageEmbedding.embedding_type,
                        "text_content": record.DataPackageEmbedding.text_content,
                        "metadata": record.DataPackageEmbedding.metadata,
                        "similarity": float(record.similarity)
                    }
                    for record in records
                ]
            else:
                # For non-PostgreSQL, compute similarity in Python
                result = await self.db.execute(query)
                records = result.scalars().all()
                
                # Compute similarity scores
                results = []
                for record in records:
                    embedding_vector = json.loads(record.embedding_json)
                    similarity = self._calculate_cosine_similarity(query_embedding, embedding_vector)
                    
                    results.append({
                        "id": record.id,
                        "package_id": record.package_id,
                        "embedding_type": record.embedding_type,
                        "text_content": record.text_content,
                        "metadata": record.metadata,
                        "similarity": similarity
                    })
                
                # Sort by similarity and take top_k
                results = sorted(results, key=lambda x: x["similarity"], reverse=True)[:top_k]
            
            # Calculate query latency
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Track metrics if requested
            if track_metrics and evaluation_service:
                # Prepare metadata
                metadata = {
                    "cache_hit": False,
                    "query_hash": query_hash,
                    "embedding_type": embedding_type,
                    "use_nvidia_api": use_nvidia_api,
                    "db_type": "postgres" if self.is_postgres else "sqlite",
                    "filter_metadata": filter_metadata
                }
                
                # Log metrics with evaluation service
                await evaluation_service.log_retrieval_metrics(
                    query_text=query_text,
                    results=results,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    session_id=session_id,
                    metadata=metadata
                )
            
            # Cache the results for future queries
            await cache_vector_search(query_hash, results, settings.SEARCH_CACHE_TTL)
            
            log.info(f"Vector search completed with {len(results)} results in {latency_ms:.2f}ms")
            return results
        
        except Exception as e:
            log.error(f"Error performing vector search: {str(e)}", exc_info=True)
            raise Exception(f"Failed to perform vector search: {str(e)}")
    
    async def hybrid_search(
        self,
        query_text: str,
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
        top_k: Optional[int] = None,
        embedding_type: Optional[str] = None,
        use_nvidia_api: bool = True,
        filter_metadata: Optional[Dict[str, Any]] = None,
        track_metrics: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        evaluation_service = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and keyword matching.
        
        Args:
            query_text: Text to search for
            semantic_weight: Weight for semantic search results (0-1)
            keyword_weight: Weight for keyword search results (0-1)
            top_k: Number of results to return
            embedding_type: Optional filter for embedding type
            use_nvidia_api: Whether to use Nvidia API for encoding
            filter_metadata: Optional metadata filters
            track_metrics: Whether to track performance metrics
            session_id: Optional session ID for tracking
            user_id: Optional user ID for tracking
            evaluation_service: Optional evaluation service instance
            
        Returns:
            List of results with combined similarity scores
        """
        try:
            start_time = time.time()
            top_k = top_k or self.vector_search_top_k
            
            # Use provided weights or defaults
            semantic_weight = semantic_weight or self.hybrid_search_weight_semantic
            keyword_weight = keyword_weight or self.hybrid_search_weight_keyword
            
            # Normalize weights to sum to 1.0
            total_weight = semantic_weight + keyword_weight
            if total_weight != 1.0 and total_weight > 0:
                semantic_weight /= total_weight
                keyword_weight /= total_weight
            
            # Generate a cache key for this search
            query_params = {
                "query": query_text[:100],  # Limit length for cache key
                "semantic_weight": semantic_weight,
                "keyword_weight": keyword_weight,
                "embedding_type": embedding_type,
                "top_k": top_k,
                "search_type": "hybrid"
            }
            
            if filter_metadata:
                # Sort to ensure consistent keys
                sorted_metadata = dict(sorted(filter_metadata.items()))
                query_params["filter_metadata"] = json.dumps(sorted_metadata)
            
            # Hash the parameters to create a consistent cache key
            query_hash = hashlib.md5(json.dumps(query_params).encode()).hexdigest()
            
            # Try to get from cache
            cached_results = await get_cached_vector_search(query_hash)
            if cached_results is not None:
                log.info(f"Hybrid search cache hit for query: {query_text[:50]}...")
                
                # Even for cache hits, track metrics if requested
                if track_metrics and evaluation_service:
                    end_time = time.time()
                    latency_ms = (end_time - start_time) * 1000
                    
                    # Add cache hit to metadata
                    metadata = {
                        "cache_hit": True, 
                        "query_hash": query_hash,
                        "search_type": "hybrid",
                        "semantic_weight": semantic_weight,
                        "keyword_weight": keyword_weight
                    }
                    
                    # Log metrics with evaluation service
                    await evaluation_service.log_retrieval_metrics(
                        query_text=query_text,
                        results=cached_results,
                        latency_ms=latency_ms,
                        user_id=user_id,
                        session_id=session_id,
                        metadata=metadata
                    )
                    
                return cached_results
            
            # Perform semantic search (using existing vector_search function)
            # Get more results than needed to have enough for reranking
            extended_top_k = min(top_k * 3, 100)  # Get 3x more results but cap at 100
            
            semantic_results = await self.vector_search(
                query_text=query_text,
                embedding_type=embedding_type,
                top_k=extended_top_k,
                use_nvidia_api=use_nvidia_api,
                filter_metadata=filter_metadata,
                track_metrics=False  # Don't track metrics for this component search
            )
            
            # Extract keywords from query for keyword search
            # Simple keyword extraction - extract words longer than 3 chars
            keywords = [word.lower() for word in re.findall(r'\b\w{3,}\b', query_text)]
            
            # Build a map of package_id to record for the semantic results
            semantic_records = {}
            for record in semantic_results:
                record_id = f"{record['id']}"
                semantic_records[record_id] = {
                    "id": record["id"],
                    "package_id": record["package_id"],
                    "embedding_type": record["embedding_type"],
                    "text_content": record["text_content"],
                    "metadata": record["metadata"],
                    "semantic_score": record["similarity"],
                    "keyword_score": 0.0,
                    "combined_score": record["similarity"] * semantic_weight
                }
            
            # Perform keyword search
            keyword_records = {}
            
            if keywords and keyword_weight > 0:
                # If using PostgreSQL, we can do text search in the database
                if self.is_postgres:
                    # Create text search query using PostgreSQL's full-text search or ILIKE
                    like_conditions = []
                    for keyword in keywords:
                        like_conditions.append(
                            DataPackageEmbedding.text_content.ilike(f"%{keyword}%")
                        )
                    
                    # Build the query
                    query = select(DataPackageEmbedding)
                    
                    # Apply filter conditions
                    if embedding_type:
                        query = query.where(DataPackageEmbedding.embedding_type == embedding_type)
                    
                    if filter_metadata and self.is_postgres:
                        for key, value in filter_metadata.items():
                            # For PostgreSQL JSONB columns
                            query = query.where(DataPackageEmbedding.metadata[key].astext == str(value))
                    
                    # Apply keyword conditions (any keyword can match)
                    if like_conditions:
                        query = query.where(or_(*like_conditions))
                    
                    # Execute the query
                    result = await self.db.execute(query.limit(extended_top_k))
                    keyword_matches = result.scalars().all()
                    
                    # Score each result based on keyword matches
                    for record in keyword_matches:
                        text_content = record.text_content.lower()
                        keyword_score = 0.0
                        
                        # Calculate keyword score based on matches
                        exact_matches = 0
                        partial_matches = 0
                        
                        for keyword in keywords:
                            if f" {keyword} " in f" {text_content} ":  # Check word boundaries
                                exact_matches += 1
                            elif keyword in text_content:
                                partial_matches += 1
                        
                        # Calculate normalized score (0-1)
                        if keywords:
                            keyword_score = (exact_matches * self.hybrid_search_boost_exact_match + partial_matches) / len(keywords)
                            keyword_score = min(1.0, keyword_score)  # Cap at 1.0
                        
                        record_id = f"{record.id}"
                        record_data = {
                            "id": record.id,
                            "package_id": record.package_id,
                            "embedding_type": record.embedding_type,
                            "text_content": record.text_content,
                            "metadata": record.metadata,
                            "keyword_score": keyword_score,
                            "semantic_score": 0.0
                        }
                        
                        keyword_records[record_id] = record_data
                
                # For non-PostgreSQL DBs, perform keyword search in Python on semantic results
                else:
                    for record in semantic_results:
                        record_id = f"{record['id']}"
                        text_content = record["text_content"].lower()
                        keyword_score = 0.0
                        
                        # Calculate keyword score based on matches
                        exact_matches = 0
                        partial_matches = 0
                        
                        for keyword in keywords:
                            if f" {keyword} " in f" {text_content} ":  # Check word boundaries
                                exact_matches += 1
                            elif keyword in text_content:
                                partial_matches += 1
                        
                        # Calculate normalized score (0-1)
                        if keywords:
                            keyword_score = (exact_matches * self.hybrid_search_boost_exact_match + partial_matches) / len(keywords)
                            keyword_score = min(1.0, keyword_score)  # Cap at 1.0
                        
                        # Store the keyword score
                        if record_id in semantic_records:
                            semantic_records[record_id]["keyword_score"] = keyword_score
                            semantic_records[record_id]["combined_score"] += keyword_score * keyword_weight
            
            # Merge semantic and keyword results
            combined_records = {}
            
            # Add all semantic records
            for record_id, record in semantic_records.items():
                combined_records[record_id] = record
            
            # Add or merge keyword records
            for record_id, record in keyword_records.items():
                if record_id in combined_records:
                    # Update keyword score if this record is already in the combined list
                    combined_records[record_id]["keyword_score"] = record["keyword_score"]
                    combined_records[record_id]["combined_score"] = (
                        combined_records[record_id]["semantic_score"] * semantic_weight +
                        record["keyword_score"] * keyword_weight
                    )
                else:
                    # Add this keyword-only record to the combined list
                    record["combined_score"] = record["keyword_score"] * keyword_weight
                    combined_records[record_id] = record
            
            # Convert the combined records to a list and sort by combined score
            results = list(combined_records.values())
            results.sort(key=lambda x: x["combined_score"], reverse=True)
            
            # Trim to the requested top_k
            results = results[:top_k]
            
            # Calculate query latency
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Track metrics if requested
            if track_metrics and evaluation_service:
                # Prepare metadata
                metadata = {
                    "cache_hit": False,
                    "query_hash": query_hash,
                    "search_type": "hybrid",
                    "semantic_weight": semantic_weight,
                    "keyword_weight": keyword_weight,
                    "db_type": "postgres" if self.is_postgres else "sqlite"
                }
                
                # Log metrics with evaluation service
                await evaluation_service.log_retrieval_metrics(
                    query_text=query_text,
                    results=results,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    session_id=session_id,
                    metadata=metadata
                )
            
            # Cache the results for future queries
            await cache_vector_search(query_hash, results, settings.SEARCH_CACHE_TTL)
            
            log.info(f"Hybrid search completed with {len(results)} results in {latency_ms:.2f}ms")
            return results
        
        except Exception as e:
            log.error(f"Error performing hybrid search: {str(e)}", exc_info=True)
            raise Exception(f"Failed to perform hybrid search: {str(e)}")
    
    async def index_data_package(
        self,
        package_id: str,
        use_nvidia_api: bool = True,
        model_name: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        max_concurrent_tasks: int = 5,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Index a data package by generating and storing embeddings for its content.
        Optimized with parallel processing for large documents.
        
        Args:
            package_id: ID of the data package to index
            use_nvidia_api: Whether to use Nvidia API for embedding generation
            model_name: Name of the model to use for embedding
            chunk_size: Maximum tokens per content chunk
            chunk_overlap: Token overlap between chunks
            max_concurrent_tasks: Maximum number of concurrent embedding tasks
            content_type: Optional type of content for specialized chunking strategies
            
        Returns:
            Dict with indexing statistics
        """
        start_time = time.time()
        
        try:
            # Get the data package content
            package_data = await self.data_service.get_data_package(package_id)
            
            if not package_data:
                raise ValueError(f"Data package {package_id} not found")
            
            # Extract content from package
            package_content = package_data.get("content", "")
            package_metadata = package_data.get("metadata", {})
            
            if not package_content and not package_metadata:
                raise ValueError(f"Data package {package_id} has no content or metadata")
            
            # Optimize chunking strategy based on content type
            if content_type:
                chunk_params = self._get_chunking_params_for_content_type(content_type, chunk_size, chunk_overlap)
                chunk_size = chunk_params["chunk_size"]
                chunk_overlap = chunk_params["chunk_overlap"]
                respect_boundaries = chunk_params["respect_boundaries"]
            else:
                respect_boundaries = True
            
            # Extract metadata as text for embedding
            metadata_text = json.dumps(package_metadata)
            
            # Chunk the content for embedding
            content_chunks = chunk_text(
                package_content, 
                max_tokens=chunk_size,
                overlap_tokens=chunk_overlap,
                respect_boundaries=respect_boundaries
            )
            
            log.info(f"Split package {package_id} into {len(content_chunks)} chunks for embedding")
            
            # Generate embeddings in parallel with rate limiting
            semaphore = asyncio.Semaphore(max_concurrent_tasks)
            
            # Create tasks for parallel processing
            async def process_chunk(chunk_text, chunk_idx):
                async with semaphore:
                    # Add chunk index to metadata for tracing
                    chunk_metadata = {
                        "chunk_index": chunk_idx,
                        "total_chunks": len(content_chunks),
                        "package_id": package_id,
                        "source": "content_chunk",
                        "chunk_size": chunk_size,
                        "chunk_overlap": chunk_overlap
                    }
                    
                    # Generate embedding
                    return await self.create_embedding(
                        text_content=chunk_text,
                        package_id=package_id,
                        embedding_type=f"content_chunk_{chunk_idx}",
                        model_name=model_name,
                        use_nvidia_api=use_nvidia_api,
                        metadata=chunk_metadata
                    )
            
            # Create and gather tasks
            content_chunk_tasks = [
                process_chunk(chunk, idx) 
                for idx, chunk in enumerate(content_chunks)
            ]
            
            # Process content chunks and metadata in parallel
            metadata_task = self.create_embedding(
                text_content=metadata_text,
                package_id=package_id,
                embedding_type="metadata",
                model_name=model_name,
                use_nvidia_api=use_nvidia_api,
                metadata={"source": "metadata", "package_id": package_id}
            )
            
            # Start all embedding tasks
            all_embedding_tasks = content_chunk_tasks + [metadata_task]
            embedding_results = await asyncio.gather(*all_embedding_tasks, return_exceptions=True)
            
            # Process results and count successful embeddings
            successful_embeddings = 0
            failed_embeddings = 0
            
            for result in embedding_results:
                if isinstance(result, Exception):
                    failed_embeddings += 1
                    log.error(f"Embedding generation failed: {str(result)}")
                else:
                    successful_embeddings += 1
            
            # Create a combined embedding for the entire package if needed
            # This is useful for high-level similarity search
            if package_content:
                # Truncate content if too long for a single embedding
                max_combined_tokens = 1000  # Adjust based on model capacity
                truncated_content = truncate_text_to_token_limit(package_content, max_combined_tokens)
                
                combined_embedding = await self.create_embedding(
                    text_content=truncated_content,
                    package_id=package_id,
                    embedding_type="combined",
                    model_name=model_name,
                    use_nvidia_api=use_nvidia_api,
                    metadata={"source": "combined", "package_id": package_id}
                )
                successful_embeddings += 1
            
            # Calculate statistics
            end_time = time.time()
            processing_time = end_time - start_time
            
            log.info(f"Indexed package {package_id} in {processing_time:.2f}s with {successful_embeddings} embeddings")
            
            return {
                "package_id": package_id,
                "total_chunks": len(content_chunks),
                "successful_embeddings": successful_embeddings,
                "failed_embeddings": failed_embeddings,
                "processing_time_seconds": processing_time,
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "model_name": model_name or self.default_model_name,
                "status": "completed"
            }
            
        except Exception as e:
            log.error(f"Error indexing data package {package_id}: {str(e)}", exc_info=True)
            return {
                "package_id": package_id,
                "status": "failed",
                "error": str(e),
                "processing_time_seconds": time.time() - start_time
            }
    
    def _get_chunking_params_for_content_type(
        self, 
        content_type: str,
        default_chunk_size: int,
        default_chunk_overlap: int
    ) -> Dict[str, Any]:
        """
        Get optimized chunking parameters for different content types.
        
        Args:
            content_type: Type of content (e.g., 'text', 'code', 'legal', 'medical')
            default_chunk_size: Default chunk size in tokens
            default_chunk_overlap: Default overlap in tokens
            
        Returns:
            Dict with chunking parameters
        """
        # Define chunking strategies for different content types
        chunking_strategies = {
            "text": {
                "chunk_size": default_chunk_size,
                "chunk_overlap": default_chunk_overlap,
                "respect_boundaries": True
            },
            "code": {
                "chunk_size": 768,  # Larger chunks for code to maintain context
                "chunk_overlap": 150,  # More overlap for code
                "respect_boundaries": True  # Try to break at function boundaries
            },
            "legal": {
                "chunk_size": 512,
                "chunk_overlap": 100,
                "respect_boundaries": True  # Try to break at paragraph/section boundaries
            },
            "medical": {
                "chunk_size": 384,
                "chunk_overlap": 75,
                "respect_boundaries": True
            },
            "conversational": {
                "chunk_size": 256,  # Smaller chunks for dialogue
                "chunk_overlap": 50,
                "respect_boundaries": True  # Break at speaker changes
            }
        }
        
        # Return parameters for the specified content type, or defaults if not found
        return chunking_strategies.get(content_type, {
            "chunk_size": default_chunk_size,
            "chunk_overlap": default_chunk_overlap,
            "respect_boundaries": True
        })
    
    async def retrieve_context(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        max_tokens: Optional[int] = None,
        model_name: Optional[str] = None,
        track_metrics: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        evaluation_service = None,
        ab_test_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve context for RAG (Retrieval Augmented Generation).
        
        Args:
            query_text: Query text for retrieval
            top_k: Number of results to retrieve
            max_tokens: Maximum tokens for context
            model_name: Optional embedding model to use
            track_metrics: Whether to track performance metrics
            session_id: Optional session ID for tracking
            user_id: Optional user ID for tracking
            evaluation_service: Optional evaluation service instance
            ab_test_name: Optional A/B test name to use for this retrieval
            
        Returns:
            Dict with retrieved context and metadata
        """
        try:
            start_time = time.time()
            
            # Apply A/B testing if requested and evaluation service is available
            ab_test_variant = None
            if ab_test_name and evaluation_service:
                ab_test_variant = await evaluation_service.get_active_ab_test_variant(
                    test_name=ab_test_name,
                    user_id=user_id,
                    session_id=session_id
                )
                
                # Apply test parameters if available
                if ab_test_variant:
                    params = ab_test_variant.get("parameters", {})
                    
                    # Override parameters with test values
                    if "top_k" in params:
                        top_k = params["top_k"]
                    if "max_tokens" in params:
                        max_tokens = params["max_tokens"]
                    if "model_name" in params:
                        model_name = params["model_name"]
            
            # Perform vector search
            search_results = await self.vector_search(
                query_text=query_text,
                top_k=top_k or self.vector_search_top_k,
                use_nvidia_api=True,  # Use Nvidia API for better results
                filter_metadata={},
                track_metrics=track_metrics,
                session_id=session_id,
                user_id=user_id,
                evaluation_service=evaluation_service
            )
            
            # Extract text content and package info
            context_items = []
            package_ids = []
            
            for result in search_results:
                if result["text_content"]:
                    # Add to context items
                    context_items.append({
                        "text": result["text_content"],
                        "package_id": result["package_id"],
                        "similarity": result["similarity"],
                        "metadata": result["metadata"]
                    })
                    
                    # Track unique package IDs
                    if result["package_id"] and result["package_id"] not in package_ids:
                        package_ids.append(result["package_id"])
            
            # Format context items into a single string with separators
            formatted_context = ""
            for i, item in enumerate(context_items):
                formatted_context += f"\n--- Context Item {i+1} ---\n"
                formatted_context += f"Source: Package {item['package_id']}\n"
                formatted_context += f"Relevance: {item['similarity']:.4f}\n\n"
                formatted_context += item["text"]
                formatted_context += "\n\n"
            
            # Calculate metrics
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            token_count = count_tokens(formatted_context)
            
            # Construct result
            result = {
                "query": query_text,
                "context": formatted_context,
                "package_ids": package_ids,
                "result_count": len(search_results),
                "token_count": token_count,
                "latency_ms": latency_ms,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Log A/B test info if applicable
            if ab_test_variant and evaluation_service:
                # Add A/B test info to the response
                result["ab_test"] = {
                    "test_id": ab_test_variant["test_id"],
                    "test_name": ab_test_variant["test_name"],
                    "variant": ab_test_variant["variant"]
                }
                
                # Get metric ID from search_results (assuming it's in the last result's metadata)
                if track_metrics and len(search_results) > 0 and "metric_id" in search_results[0].get("metadata", {}):
                    metric_id = search_results[0]["metadata"]["metric_id"]
                    
                    # Log the A/B test result
                    await evaluation_service.log_ab_test_result(
                        test_id=ab_test_variant["test_id"],
                        variant=ab_test_variant["variant"],
                        metric_id=metric_id,
                        outcome="context_retrieval",
                        score=token_count,  # Use token count as a score
                        user_id=user_id,
                        session_id=session_id,
                        metadata={"latency_ms": latency_ms}
                    )
            
            return result
        
        except Exception as e:
            log.error(f"Error retrieving context: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve context: {str(e)}")
    
    async def assemble_cross_package_context(
        self,
        query_text: str,
        max_packages: Optional[int] = None,
        max_items_per_package: int = 3,
        max_tokens: Optional[int] = None,
        use_hybrid_search: bool = True,
        semantic_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None,
        track_metrics: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        evaluation_service = None
    ) -> Dict[str, Any]:
        """
        Assemble context from multiple data packages for complex queries.
        This provides a richer context by retrieving information from different sources.
        
        Args:
            query_text: Query text for retrieval
            max_packages: Maximum number of packages to include
            max_items_per_package: Maximum items to include per package
            max_tokens: Maximum tokens for the final context
            use_hybrid_search: Whether to use hybrid search (True) or vector search (False)
            semantic_weight: Weight for semantic results in hybrid search
            keyword_weight: Weight for keyword results in hybrid search
            track_metrics: Whether to track performance metrics
            session_id: Optional session ID for tracking
            user_id: Optional user ID for tracking
            evaluation_service: Optional evaluation service instance
            
        Returns:
            Dict with assembled context from multiple packages
        """
        try:
            start_time = time.time()
            max_packages = max_packages or 5  # Default to 5 packages max
            max_tokens = max_tokens or 2000  # Default to 2000 tokens max
            
            # Step 1: Perform primary search (hybrid or vector)
            if use_hybrid_search:
                search_results = await self.hybrid_search(
                    query_text=query_text,
                    semantic_weight=semantic_weight,
                    keyword_weight=keyword_weight,
                    top_k=self.cross_package_max_items,
                    track_metrics=False  # We'll track metrics for the final assembled result
                )
            else:
                search_results = await self.vector_search(
                    query_text=query_text, 
                    top_k=self.cross_package_max_items,
                    track_metrics=False
                )
            
            # Step 2: Group results by package
            packages = {}
            for result in search_results:
                package_id = result.get("package_id")
                if not package_id:
                    continue
                
                if package_id not in packages:
                    packages[package_id] = []
                
                # Add this result to the package group with its score
                # Use combined_score if available (hybrid search), otherwise use similarity
                score = result.get("combined_score", result.get("similarity", 0))
                
                packages[package_id].append({
                    "id": result.get("id"),
                    "text_content": result.get("text_content", ""),
                    "metadata": result.get("metadata", {}),
                    "score": score,
                    "embedding_type": result.get("embedding_type", "")
                })
            
            # Step 3: Sort packages by their best result score
            package_scores = []
            for pkg_id, items in packages.items():
                # Sort items within this package by score
                items.sort(key=lambda x: x["score"], reverse=True)
                
                # Calculate a package score based on top items
                best_score = items[0]["score"] if items else 0
                package_scores.append((pkg_id, best_score, items))
            
            # Sort packages by their best score
            package_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Limit to max_packages
            package_scores = package_scores[:max_packages]
            
            # Step 4: Assemble context by taking top items from each package
            all_context_items = []
            total_tokens = 0
            
            for pkg_id, pkg_score, items in package_scores:
                # Get package metadata for additional context
                package_data = await self.data_service.get_data_package(pkg_id)
                package_name = package_data.get("name", "") if package_data else ""
                package_type = package_data.get("package_type", "") if package_data else ""
                
                # Take top N items from this package, respecting token limit
                pkg_items = []
                for item in items[:max_items_per_package]:
                    item_tokens = count_tokens(item["text_content"])
                    
                    # Check if adding this item would exceed the token limit
                    if max_tokens and (total_tokens + item_tokens > max_tokens) and all_context_items:
                        # If we already have some items, stop adding more
                        break
                    
                    # Add this item's tokens to the total
                    total_tokens += item_tokens
                    
                    # Create a context item with package metadata
                    context_item = {
                        "text": item["text_content"],
                        "package_id": pkg_id,
                        "package_name": package_name,
                        "package_type": package_type,
                        "score": item["score"],
                        "metadata": item["metadata"],
                    }
                    
                    pkg_items.append(context_item)
                    all_context_items.append(context_item)
            
            # Step 5: Format the assembled context
            formatted_context = ""
            package_contexts = {}
            
            # Group by package for better organization in the final context
            for item in all_context_items:
                pkg_id = item["package_id"]
                if pkg_id not in package_contexts:
                    package_contexts[pkg_id] = {
                        "name": item["package_name"],
                        "type": item["package_type"],
                        "items": []
                    }
                
                package_contexts[pkg_id]["items"].append(item)
            
            # Format context with package headers
            for pkg_id, pkg_context in package_contexts.items():
                formatted_context += f"\n=== Package: {pkg_context['name']} (ID: {pkg_id}) ===\n"
                formatted_context += f"Type: {pkg_context['type']}\n\n"
                
                for i, item in enumerate(pkg_context["items"]):
                    formatted_context += f"--- Item {i+1} (Relevance: {item['score']:.4f}) ---\n"
                    formatted_context += item["text"]
                    formatted_context += "\n\n"
            
            # Calculate metrics
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Construct the result
            result = {
                "query": query_text,
                "context": formatted_context,
                "package_count": len(package_contexts),
                "item_count": len(all_context_items),
                "token_count": count_tokens(formatted_context),
                "latency_ms": latency_ms,
                "packages": [{"id": pkg_id, "name": pkg["name"], "item_count": len(pkg["items"])} 
                            for pkg_id, pkg in package_contexts.items()],
                "search_type": "hybrid" if use_hybrid_search else "vector",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Track metrics if requested
            if track_metrics and evaluation_service:
                await evaluation_service.log_retrieval_metrics(
                    query_text=query_text,
                    results=all_context_items,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={
                        "search_type": "cross_package",
                        "use_hybrid_search": use_hybrid_search,
                        "package_count": len(package_contexts),
                        "token_count": result["token_count"]
                    }
                )
            
            log.info(f"Assembled cross-package context with {result['package_count']} packages and {result['item_count']} items")
            return result
            
        except Exception as e:
            log.error(f"Error assembling cross-package context: {str(e)}", exc_info=True)
            raise Exception(f"Failed to assemble cross-package context: {str(e)}")
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score
        """
        # Convert to numpy arrays
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate cosine similarity
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    async def batch_process_packages(
        self,
        package_ids: List[str],
        use_nvidia_api: bool = True,
        model_name: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        max_concurrent_packages: int = 3,
        max_concurrent_tasks_per_package: int = 5,
        content_types: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Process multiple data packages in parallel with controlled concurrency.
        
        Args:
            package_ids: List of package IDs to process
            use_nvidia_api: Whether to use Nvidia API for embeddings
            model_name: Optional embedding model to use
            chunk_size: Maximum token size for each chunk
            chunk_overlap: Overlap tokens between chunks
            max_concurrent_packages: Maximum packages to process in parallel
            max_concurrent_tasks_per_package: Maximum concurrent tasks per package
            content_types: Optional dict mapping package IDs to content types
            
        Returns:
            Dict with batch processing statistics
        """
        start_time = time.time()
        
        if not package_ids:
            return {
                "status": "error", 
                "message": "No package IDs provided",
                "processing_time_seconds": 0
            }
        
        # Initialize content types if not provided
        content_types = content_types or {}
        
        # Create a semaphore to limit concurrent package processing
        package_semaphore = asyncio.Semaphore(max_concurrent_packages)
        
        # Function to process a single package with the semaphore
        async def process_package(package_id: str):
            async with package_semaphore:
                content_type = content_types.get(package_id)
                return await self.index_data_package(
                    package_id=package_id,
                    use_nvidia_api=use_nvidia_api,
                    model_name=model_name,
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap,
                    max_concurrent_tasks=max_concurrent_tasks_per_package,
                    content_type=content_type
                )
        
        # Create tasks for all packages
        tasks = [process_package(pkg_id) for pkg_id in package_ids]
        
        try:
            # Process packages with controlled concurrency
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Calculate statistics
            successful = 0
            failed = 0
            total_chunks = 0
            failed_packages = []
            
            for idx, result in enumerate(results):
                if isinstance(result, Exception):
                    failed += 1
                    failed_packages.append({
                        "package_id": package_ids[idx],
                        "error": str(result)
                    })
                elif result.get("status") == "failed":
                    failed += 1
                    failed_packages.append({
                        "package_id": package_ids[idx],
                        "error": result.get("error", "Unknown error")
                    })
                else:
                    successful += 1
                    total_chunks += result.get("total_chunks", 0)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            return {
                "status": "completed",
                "total_packages": len(package_ids),
                "successful_packages": successful,
                "failed_packages": failed,
                "failed_details": failed_packages if failed > 0 else None,
                "total_chunks": total_chunks,
                "processing_time_seconds": processing_time,
                "throughput_packages_per_second": successful / processing_time if processing_time > 0 else 0
            }
        
        except Exception as e:
            log.error(f"Error in batch processing: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Batch processing failed: {str(e)}",
                "processing_time_seconds": time.time() - start_time
            }

    async def query_expansion_search(
        self,
        query_text: str,
        top_k: Optional[int] = None,
        use_hybrid_search: bool = True,
        max_expansions: int = 3,
        expansion_model: Optional[str] = None,
        track_metrics: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        evaluation_service = None
    ) -> Dict[str, Any]:
        """
        Enhance search by automatically expanding the query with related terms.
        This can improve recall for queries where the user's terminology may differ from content.
        
        Args:
            query_text: Original query text
            top_k: Number of results to return
            use_hybrid_search: Whether to use hybrid search (True) or vector search (False)
            max_expansions: Maximum number of expanded queries to generate
            expansion_model: Optional model to use for query expansion
            track_metrics: Whether to track performance metrics
            session_id: Optional session ID for tracking
            user_id: Optional user ID for tracking
            evaluation_service: Optional evaluation service instance
            
        Returns:
            Dict with search results and expanded queries
        """
        try:
            start_time = time.time()
            top_k = top_k or self.vector_search_top_k
            
            # Step 1: Generate expanded queries using LLM
            expanded_queries = [query_text]  # Always include the original query
            
            # Build a prompt for query expansion
            expansion_prompt = f"""Your task is to generate {max_expansions} different versions of the 
            following query that maintain the same intent but use different wording, terminology,
            or phrasing. This will help improve retrieval by capturing different ways the information
            might be expressed in documents.
            
            Original query: "{query_text}"
            
            Generate only the expanded queries, one per line. Do not include explanations."""
            
            try:
                # Generate expanded queries using LLM
                expansion_result = await self.llm_service.generate_completion(
                    prompt=expansion_prompt,
                    model=expansion_model or "gpt-3.5-turbo",
                    max_tokens=250,
                    temperature=0.7
                )
                
                # Parse expanded queries from result
                expansion_text = expansion_result.get("text", "")
                for line in expansion_text.strip().split("\n"):
                    line = line.strip()
                    # Skip empty lines or lines with just numbers/bullets
                    if line and not line[0].isdigit() and not line.startswith("•") and not line.startswith("-"):
                        # Remove quotation marks if present
                        line = line.strip('"\'')
                        if line and line != query_text and line not in expanded_queries:
                            expanded_queries.append(line)
                            
                            # Limit to max_expansions
                            if len(expanded_queries) > max_expansions:
                                break
                
                log.info(f"Generated {len(expanded_queries)-1} expanded queries for: {query_text}")
                
            except Exception as e:
                log.warning(f"Query expansion failed, proceeding with original query only: {str(e)}")
            
            # Step 2: Search with each expanded query
            all_results = []
            query_results = {}
            
            # Perform searches in parallel
            async def search_with_query(q):
                if use_hybrid_search:
                    results = await self.hybrid_search(
                        query_text=q,
                        top_k=top_k,
                        track_metrics=False
                    )
                else:
                    results = await self.vector_search(
                        query_text=q,
                        top_k=top_k,
                        track_metrics=False
                    )
                return q, results
            
            # Create tasks for all queries
            search_tasks = [search_with_query(q) for q in expanded_queries]
            expanded_results = await asyncio.gather(*search_tasks)
            
            # Process results from each query
            for query, results in expanded_results:
                query_results[query] = results
                all_results.extend(results)
            
            # Step 3: Deduplicate results based on embedding IDs
            seen_ids = set()
            unique_results = []
            
            for result in all_results:
                result_id = result.get("id")
                if result_id not in seen_ids:
                    seen_ids.add(result_id)
                    unique_results.append(result)
            
            # Step 4: Rerank results - prioritize those appearing in multiple expanded queries
            result_counts = {}
            for result in all_results:
                result_id = result.get("id")
                if result_id not in result_counts:
                    result_counts[result_id] = 0
                result_counts[result_id] += 1
            
            # Add a boost factor based on appearance in multiple queries
            for result in unique_results:
                result_id = result.get("id")
                count = result_counts.get(result_id, 1)
                
                # Add a boost to the score based on frequency across queries
                boost = min(count / len(expanded_queries), 0.5)  # Cap at 0.5 boost
                
                # Apply the boost to the existing score
                original_score = result.get("combined_score", result.get("similarity", 0))
                result["original_score"] = original_score
                result["boosted_score"] = original_score * (1 + boost)
                result["query_count"] = count
            
            # Sort by boosted score
            unique_results.sort(key=lambda x: x.get("boosted_score", 0), reverse=True)
            
            # Take the top_k results
            final_results = unique_results[:top_k]
            
            # Calculate metrics
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Construct the result
            result = {
                "original_query": query_text,
                "expanded_queries": expanded_queries,
                "results": final_results,
                "result_count": len(final_results),
                "latency_ms": latency_ms,
                "search_type": "query_expansion",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Track metrics if requested
            if track_metrics and evaluation_service:
                await evaluation_service.log_retrieval_metrics(
                    query_text=query_text,
                    results=final_results,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={
                        "search_type": "query_expansion",
                        "expanded_query_count": len(expanded_queries),
                        "use_hybrid_search": use_hybrid_search
                    }
                )
            
            log.info(f"Query expansion search completed with {len(final_results)} results in {latency_ms:.2f}ms")
            return result
            
        except Exception as e:
            log.error(f"Error in query expansion search: {str(e)}", exc_info=True)
            raise Exception(f"Failed to perform query expansion search: {str(e)}")
    
    async def faceted_search(
        self,
        query_text: str,
        facets: Dict[str, List[str]],
        facet_weights: Optional[Dict[str, float]] = None,
        use_hybrid_search: bool = True,
        top_k: Optional[int] = None,
        track_metrics: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        evaluation_service = None
    ) -> Dict[str, Any]:
        """
        Perform faceted search that combines semantic/hybrid search with metadata filtering.
        
        Args:
            query_text: Text to search for
            facets: Dict of facet names to list of values to include
            facet_weights: Optional weights for each facet (higher = more important)
            use_hybrid_search: Whether to use hybrid search (True) or vector search (False)
            top_k: Number of results to return
            track_metrics: Whether to track performance metrics
            session_id: Optional session ID for tracking
            user_id: Optional user ID for tracking
            evaluation_service: Optional evaluation service instance
            
        Returns:
            Dict with search results grouped by facets
        """
        try:
            start_time = time.time()
            top_k = top_k or self.vector_search_top_k
            
            # Validate facets
            if not facets:
                facets = {}
            
            # Initialize facet weights if not provided
            if not facet_weights:
                facet_weights = {facet: 1.0 for facet in facets}
            
            # Normalize facet weights
            total_weight = sum(facet_weights.values())
            if total_weight > 0:
                facet_weights = {k: v/total_weight for k, v in facet_weights.items()}
            
            # Create filter metadata for the initial search
            # Note: We'll do a broad search first, then filter and rerank
            filter_metadata = {}
            
            # Perform search (hybrid or vector)
            if use_hybrid_search:
                initial_results = await self.hybrid_search(
                    query_text=query_text,
                    top_k=top_k * 3,  # Get more results initially to allow for filtering
                    filter_metadata=filter_metadata,
                    track_metrics=False
                )
            else:
                initial_results = await self.vector_search(
                    query_text=query_text,
                    top_k=top_k * 3,
                    filter_metadata=filter_metadata,
                    track_metrics=False
                )
            
            # Filter and rerank results based on facets
            faceted_results = []
            
            for result in initial_results:
                metadata = result.get("metadata", {})
                
                # Calculate facet match score
                facet_match_score = 0.0
                matched_facets = 0
                
                for facet_name, facet_values in facets.items():
                    if not facet_values:
                        continue
                        
                    # Get facet value from result metadata
                    result_facet_value = metadata.get(facet_name)
                    
                    # Check if the result matches any of the requested facet values
                    if result_facet_value is not None:
                        # Handle list/array values
                        if isinstance(result_facet_value, list):
                            # Check for any overlap between the lists
                            matches = set(result_facet_value) & set(facet_values)
                            if matches:
                                match_score = len(matches) / len(facet_values)
                                facet_match_score += match_score * facet_weights.get(facet_name, 1.0)
                                matched_facets += 1
                        # Handle string/scalar values
                        elif result_facet_value in facet_values:
                            facet_match_score += facet_weights.get(facet_name, 1.0)
                            matched_facets += 1
                
                # Only include results that match at least one facet if facets were specified
                if not facets or matched_facets > 0:
                    # Get the original similarity or combined score
                    original_score = result.get("combined_score", result.get("similarity", 0))
                    
                    # Calculate a combined score that accounts for both semantic and facet matching
                    # Weight: 70% original score, 30% facet match score
                    combined_score = (original_score * 0.7) + (facet_match_score * 0.3)
                    
                    # Create a new result with facet information
                    faceted_result = {**result}
                    faceted_result["facet_match_score"] = facet_match_score
                    faceted_result["matched_facets"] = matched_facets
                    faceted_result["original_score"] = original_score
                    faceted_result["faceted_score"] = combined_score
                    
                    faceted_results.append(faceted_result)
            
            # Sort by combined score
            faceted_results.sort(key=lambda x: x.get("faceted_score", 0), reverse=True)
            
            # Take the top_k results
            faceted_results = faceted_results[:top_k]
            
            # Group results by facet for the response
            facet_groups = {}
            for facet_name in facets.keys():
                facet_groups[facet_name] = {}
                
                # Create a sub-group for each facet value
                for facet_value in facets[facet_name]:
                    facet_groups[facet_name][facet_value] = []
                    
                    # Add results that match this facet value
                    for result in faceted_results:
                        metadata = result.get("metadata", {})
                        result_facet_value = metadata.get(facet_name)
                        
                        if result_facet_value is not None:
                            # Handle list values
                            if isinstance(result_facet_value, list) and facet_value in result_facet_value:
                                facet_groups[facet_name][facet_value].append(result)
                            # Handle scalar values
                            elif result_facet_value == facet_value:
                                facet_groups[facet_name][facet_value].append(result)
            
            # Calculate metrics
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # Construct the result
            result = {
                "query": query_text,
                "facets": facets,
                "facet_weights": facet_weights,
                "results": faceted_results,
                "facet_groups": facet_groups,
                "result_count": len(faceted_results),
                "latency_ms": latency_ms,
                "search_type": "faceted",
                "use_hybrid_search": use_hybrid_search,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Track metrics if requested
            if track_metrics and evaluation_service:
                await evaluation_service.log_retrieval_metrics(
                    query_text=query_text,
                    results=faceted_results,
                    latency_ms=latency_ms,
                    user_id=user_id,
                    session_id=session_id,
                    metadata={
                        "search_type": "faceted",
                        "facets": facets,
                        "use_hybrid_search": use_hybrid_search
                    }
                )
            
            log.info(f"Faceted search completed with {len(faceted_results)} results in {latency_ms:.2f}ms")
            return result
            
        except Exception as e:
            log.error(f"Error in faceted search: {str(e)}", exc_info=True)
            raise Exception(f"Failed to perform faceted search: {str(e)}")


# Dependency for FastAPI
async def get_embedding_service(
    db: AsyncSession = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service),
    data_service: DataService = Depends(get_data_service)
) -> EmbeddingService:
    """
    Get embedding service instance for dependency injection.
    """
    return EmbeddingService(db, llm_service, data_packaging_service, data_service) 