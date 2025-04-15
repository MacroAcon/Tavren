"""
API router for LLM operations.
Provides endpoints for processing data with LLMs, generating embeddings, and managing LLM integrations.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.llm_service import LLMService, get_llm_service
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.schemas import LLMProcessRequest, LLMProcessResponse, EmbeddingRequest, EmbeddingResponse, RAGRequest, RAGGenerationRequest, RAGGenerationResponse
from app.auth import get_current_active_user
from app.schemas import UserDisplay

# Set up logging
log = logging.getLogger("app")

# Create router
llm_router = APIRouter(
    prefix="/api/llm",
    tags=["llm-integration"]
)

@llm_router.post("/process", response_model=LLMProcessResponse)
async def process_with_llm(
    request: LLMProcessRequest,
    db = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Process packaged data with the connected LLM.
    
    This endpoint takes packaged data and sends it to the LLM (Nvidia's model)
    with appropriate context and instructions.
    
    Returns the processed results from the LLM.
    """
    try:
        log.info(f"Processing data with LLM for package {request.package_id}")
        
        result = await llm_service.process_data(
            package_id=request.package_id,
            instructions=request.instructions,
            model_config=request.model_config,
            max_tokens=request.max_tokens
        )
        
        log.info(f"Successfully processed data with LLM, request ID: {result.request_id}")
        return result
        
    except Exception as e:
        log.error(f"Error processing with LLM: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing with LLM: {str(e)}")

@llm_router.post("/embedding", response_model=EmbeddingResponse)
async def generate_embedding(
    request: EmbeddingRequest,
    db = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Generate embeddings for the specified data using Nvidia's embedqa model.
    
    This endpoint takes either packaged data by ID or direct text and 
    generates vector embeddings suitable for retrieval operations.
    
    Returns the embedding vectors with metadata.
    """
    try:
        log.info(f"Generating embeddings for {'package ' + request.package_id if request.package_id else 'direct text input'}")
        
        embedding_result = await llm_service.generate_embedding(
            text=request.text,
            package_id=request.package_id,
            model_name=request.model_name
        )
        
        log.info(f"Successfully generated embeddings, request ID: {embedding_result.request_id}")
        return embedding_result
        
    except Exception as e:
        log.error(f"Error generating embeddings: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating embeddings: {str(e)}")

@llm_router.post("/rag", response_model=RAGGenerationResponse)
async def retrieval_augmented_generation(
    request: RAGGenerationRequest,
    db = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Perform retrieval augmented generation (RAG).
    
    This endpoint combines vector search to find relevant context,
    then uses that context to generate a more informed LLM response.
    
    Returns the generated response and metadata about retrieved context.
    """
    try:
        log.info(f"Performing RAG for query: {request.query[:50]}...")
        
        # Step 1: Retrieve relevant context
        context_result = await embedding_service.retrieve_context(
            query_text=request.query,
            top_k=request.top_k,
            max_tokens=request.context_max_tokens
        )
        
        # Step 2: Process with the enhanced RAG method
        generation_result = await llm_service.process_rag(
            query=request.query,
            context=context_result['context'],
            instructions=request.instructions,
            model_name=request.model_name,
            max_tokens=request.response_max_tokens,
            temperature=request.temperature
        )
        
        # Step 3: Return combined result
        response = {
            "request_id": generation_result["request_id"],
            "query": request.query,
            "response": generation_result["result"],
            "context_packages": context_result["package_ids"],
            "context_count": context_result["result_count"],
            "model_used": generation_result["model_used"],
            "usage": generation_result["usage"],
            "timestamp": generation_result["timestamp"]
        }
        
        log.info(f"Successfully performed RAG, request ID: {response['request_id']}")
        return response
        
    except Exception as e:
        log.error(f"Error performing RAG: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error performing RAG: {str(e)}")

@llm_router.get("/models", response_model=List[Dict[str, Any]])
async def list_available_models(
    db = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    List available LLM models from the connected provider (Nvidia).
    
    Returns details about the models including capabilities, context window sizes,
    and other relevant parameters.
    """
    try:
        log.info("Retrieving available LLM models")
        
        models = await llm_service.list_models()
        
        log.info(f"Successfully retrieved {len(models)} models")
        return models
        
    except Exception as e:
        log.error(f"Error retrieving LLM models: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving LLM models: {str(e)}")

@llm_router.get("/status", response_model=Dict[str, Any])
async def check_llm_connection_status(
    db = Depends(get_db),
    llm_service: LLMService = Depends(get_llm_service),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Check the connection status with the LLM provider.
    
    Tests the connection to the Nvidia API and verifies authentication
    and service availability.
    
    Returns status details and diagnostic information.
    """
    try:
        log.info("Checking LLM connection status")
        
        status = await llm_service.check_connection()
        
        log.info(f"LLM connection status: {status.get('status', 'unknown')}")
        return status
        
    except Exception as e:
        log.error(f"Error checking LLM connection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error checking LLM connection: {str(e)}") 