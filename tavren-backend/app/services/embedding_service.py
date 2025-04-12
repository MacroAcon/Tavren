"""
Embedding service for processing, storing, and retrieving vector embeddings.
Provides functionality for semantic search and retrieval augmented generation.
"""

import logging
import json
import numpy as np
import time
from typing import Dict, Any, List, Optional, Tuple, Union
from fastapi import Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sentence_transformers import SentenceTransformer
import uuid
from datetime import datetime

from app.database import get_db
from app.models import DataPackageEmbedding, DataPackage
from app.config import settings
from app.services.llm_service import LLMService, get_llm_service
from app.services.data_packaging import DataPackagingService, get_data_packaging_service
from app.services.data_service import DataService, get_data_service
from app.utils.text_utils import count_tokens, truncate_text_to_token_limit, chunk_text

# Set up logging
log = logging.getLogger("app")

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
        
        # Local embedding model for smaller operations or fallback
        self._local_model = None
        
        log.info(f"Embedding Service initialized with dimension {self.vector_dimension}")
    
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
            
            # Parse the embedding vector from JSON
            embedding_vector = json.loads(embedding_record.embedding_json)
            
            return {
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
        Perform vector search using a query text.
        
        Args:
            query_text: Text to search for
            embedding_type: Type of embeddings to search
            top_k: Number of results to return
            use_nvidia_api: Whether to use Nvidia API for query embedding
            filter_metadata: Filter results by metadata fields
            
        Returns:
            List of search results with similarity scores
        """
        try:
            # Use specified parameters or defaults
            top_k = top_k or self.vector_search_top_k
            
            # Generate query embedding
            if use_nvidia_api:
                # Use Nvidia's API for embedding generation
                embedding_result = await self.llm_service.generate_embedding(
                    text=query_text,
                    model_name=self.default_model_name
                )
                query_embedding = embedding_result.get("embedding", [])
            else:
                # Use local model for embedding generation
                local_model = self._get_local_model()
                query_embedding = local_model.encode(query_text).tolist()
            
            # Retrieve all embeddings from database (optimized for smaller dataset)
            # For larger datasets, this would need to be optimized with a vector database
            query = select(DataPackageEmbedding)
            if embedding_type:
                query = query.where(DataPackageEmbedding.embedding_type == embedding_type)
            
            result = await self.db.execute(query)
            embedding_records = result.scalars().all()
            
            # Calculate similarity scores and rank results
            search_results = []
            for record in embedding_records:
                # Parse stored embedding
                stored_embedding = json.loads(record.embedding_json)
                
                # Calculate cosine similarity
                similarity = self._calculate_cosine_similarity(query_embedding, stored_embedding)
                
                # Apply metadata filtering if specified
                if filter_metadata and record.metadata:
                    # Check if all filter conditions are met
                    if not all(record.metadata.get(k) == v for k, v in filter_metadata.items() if k in record.metadata):
                        continue
                
                # Add to results
                search_results.append({
                    "id": record.id,
                    "package_id": record.package_id,
                    "similarity": float(similarity),
                    "text_content": record.text_content,
                    "metadata": record.metadata,
                    "embedding_type": record.embedding_type,
                    "created_at": record.created_at
                })
            
            # Sort by similarity (highest first) and take top k
            search_results.sort(key=lambda x: x["similarity"], reverse=True)
            search_results = search_results[:top_k]
            
            log.info(f"Vector search found {len(search_results)} results for query: {query_text[:50]}...")
            return search_results
        
        except Exception as e:
            log.error(f"Error performing vector search: {str(e)}", exc_info=True)
            raise Exception(f"Failed to perform vector search: {str(e)}")
    
    async def index_data_package(
        self,
        package_id: str,
        use_nvidia_api: bool = True,
        model_name: Optional[str] = None,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Create embeddings for a data package and its components.
        
        Args:
            package_id: ID of the data package to index
            use_nvidia_api: Whether to use Nvidia API for embeddings
            model_name: Optional embedding model to use
            chunk_size: Maximum token size for each chunk
            chunk_overlap: Overlap tokens between chunks
            
        Returns:
            Dict with indexing results
        """
        try:
            # Get the data package
            package_data, error = await self.data_packaging_service.get_package_by_id(package_id)
            if error:
                raise Exception(f"Failed to retrieve data package: {error.get('reason')}")
            
            # Extract package data
            data_content = package_data.get("content", {})
            data_metadata = package_data.get("metadata", {})
            
            # Convert package content to string for embedding
            if isinstance(data_content, dict) or isinstance(data_content, list):
                content_text = json.dumps(data_content)
            else:
                content_text = str(data_content)
            
            # Create content embedding
            content_result = await self.create_embedding(
                text_content=content_text,
                package_id=package_id,
                embedding_type="content",
                use_nvidia_api=use_nvidia_api,
                metadata={
                    "data_type": data_metadata.get("data_type", "unknown"),
                    "record_count": data_metadata.get("record_count", 0),
                    "schema_version": data_metadata.get("schema_version", "unknown")
                }
            )
            
            # Create metadata embedding if available
            metadata_result = None
            if data_metadata:
                metadata_text = json.dumps(data_metadata)
                metadata_result = await self.create_embedding(
                    text_content=metadata_text,
                    package_id=package_id,
                    embedding_type="metadata",
                    use_nvidia_api=use_nvidia_api,
                    metadata={
                        "data_type": data_metadata.get("data_type", "unknown")
                    }
                )
            
            # Combine content and metadata with clear separation
            full_text = f"CONTENT:\n{content_text}\n\nMETADATA:\n{metadata_text}"
            
            # Check if we need chunking based on token count
            total_tokens = count_tokens(full_text)
            
            # Create chunks if needed
            if total_tokens > chunk_size:
                # Advanced semantic chunking
                chunks = chunk_text(
                    text=full_text,
                    max_tokens=chunk_size,
                    overlap_tokens=chunk_overlap,
                    respect_boundaries=True
                )
                log.info(f"Split package into {len(chunks)} chunks")
            else:
                chunks = [full_text]
            
            # Create embeddings for each chunk
            embedding_ids = []
            for i, chunk in enumerate(chunks):
                # Create chunk embedding
                embedding_data = await self.create_embedding(
                    text=chunk,
                    package_id=package_id,
                    embedding_type="content",
                    use_nvidia_api=use_nvidia_api,
                    metadata={
                        "data_type": data_metadata.get("data_type", "unknown"),
                        "record_count": data_metadata.get("record_count", 0),
                        "schema_version": data_metadata.get("schema_version", "unknown")
                    }
                )
                
                # Store the embedding
                embedding_model = await self.get_embedding(embedding_data["id"], package_id, "content")
                embedding_ids.append(embedding_model["id"])
                
                log.info(f"Indexed chunk {i+1}/{len(chunks)} for package {package_id}")
            
            # Return results
            return {
                "package_id": package_id,
                "embeddings_created": len(embedding_ids),
                "embedding_ids": embedding_ids,
                "total_tokens": total_tokens,
                "chunks": len(chunks),
                "model": model_name or self.default_model_name,
                "data_type": data_metadata.get("data_type", "unknown"),
                "record_count": data_metadata.get("record_count", 0),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            log.error(f"Error indexing data package: {str(e)}", exc_info=True)
            raise Exception(f"Failed to index data package: {str(e)}")
    
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