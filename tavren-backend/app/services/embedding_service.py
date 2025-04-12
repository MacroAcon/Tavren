"""
Embedding service for processing, storing, and retrieving vector embeddings.
Provides functionality for semantic search and retrieval augmented generation.
"""

import logging
import json
import numpy as np
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple, Union
from fastapi import Depends
from sqlalchemy import select, desc, func
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
    from sqlalchemy.dialects.postgresql import ARRAY

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
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search using query text.
        
        Args:
            query_text: Text to search for
            embedding_type: Optional filter for embedding type
            top_k: Number of results to return (default from settings)
            use_nvidia_api: Whether to use Nvidia API for encoding
            filter_metadata: Optional metadata filters
            
        Returns:
            List of results with similarity scores
        """
        try:
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
            
            # Cache the results
            await cache_vector_search(query_hash, results, settings.SEARCH_CACHE_TTL)
            
            log.info(f"Vector search completed with {len(results)} results")
            return results
        
        except Exception as e:
            log.error(f"Error performing vector search: {str(e)}", exc_info=True)
            raise Exception(f"Failed to perform vector search: {str(e)}")
    
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
        model_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve context for RAG (Retrieval Augmented Generation).
        
        Args:
            query_text: Query text for retrieval
            top_k: Number of results to retrieve
            max_tokens: Maximum tokens for context
            model_name: Optional embedding model to use
            
        Returns:
            Dict with retrieved context and metadata
        """
        try:
            # Perform vector search
            search_results = await self.vector_search(
                query_text=query_text,
                top_k=top_k or self.vector_search_top_k,
                use_nvidia_api=True,  # Use Nvidia API for better results
                filter_metadata={}
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
            
            # Return the formatted context with metadata
            return {
                "query": query_text,
                "context": formatted_context,
                "package_ids": package_ids,
                "result_count": len(search_results),
                "token_count": count_tokens(formatted_context),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            log.error(f"Error retrieving context: {str(e)}", exc_info=True)
            raise Exception(f"Failed to retrieve context: {str(e)}")
    
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