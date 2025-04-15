"""
Router for RAG evaluation and feedback endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.evaluation_service import EvaluationService, get_evaluation_service
from app.services.embedding_service import EmbeddingService, get_embedding_service
from app.auth import get_current_active_user

# Create router
router = APIRouter(
    prefix="/evaluation",
    tags=["evaluation"],
    responses={404: {"description": "Not found"}},
)

# --- Pydantic Models ---

class FeedbackCreate(BaseModel):
    """Model for creating user feedback."""
    metric_id: int
    rating: int = Field(..., ge=1, le=5)
    user_id: Optional[str] = None
    feedback_text: Optional[str] = None
    helpful_result_ids: Optional[List[str]] = None
    unhelpful_result_ids: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ABTestCreate(BaseModel):
    """Model for creating A/B tests."""
    name: str
    description: str
    variants: Dict[str, Any]
    active: bool = True
    traffic_allocation: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None

class ABTestResult(BaseModel):
    """Model for recording A/B test results."""
    test_id: int
    variant: str
    metric_id: int
    outcome: str
    score: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EmbeddingParameterCreate(BaseModel):
    """Model for creating embedding parameters."""
    name: str
    parameters: Dict[str, Any]
    model_name: str
    description: Optional[str] = None
    active: bool = False
    metadata: Optional[Dict[str, Any]] = None

# --- API Endpoints ---

@router.post("/feedback", response_model=Dict[str, Any])
async def create_feedback(
    feedback: FeedbackCreate,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Record user feedback for a retrieval operation.
    
    Args:
        feedback: Feedback data
        
    Returns:
        Feedback information
    """
    try:
        # Use current user ID if not provided
        if not feedback.user_id and current_user:
            feedback.user_id = current_user.get("id")
            
        result = await evaluation_service.record_user_feedback(
            metric_id=feedback.metric_id,
            rating=feedback.rating,
            user_id=feedback.user_id,
            feedback_text=feedback.feedback_text,
            helpful_result_ids=feedback.helpful_result_ids,
            unhelpful_result_ids=feedback.unhelpful_result_ids,
            metadata=feedback.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/metrics", response_model=List[Dict[str, Any]])
async def get_metrics(
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    include_feedback: bool = False,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get retrieval metrics, optionally filtered by parameters.
    
    Args:
        user_id: Optional user ID filter
        session_id: Optional session ID filter
        start_date: Optional start date filter
        end_date: Optional end date filter
        limit: Maximum number of records to return
        include_feedback: Whether to include feedback data
        
    Returns:
        List of metric records
    """
    try:
        # Use current user ID if not provided
        if not user_id and current_user:
            user_id = current_user.get("id")
            
        metrics = await evaluation_service.get_retrieval_metrics(
            user_id=user_id,
            session_id=session_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            include_feedback=include_feedback
        )
        return metrics
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ab-tests", response_model=Dict[str, Any])
async def create_ab_test(
    test: ABTestCreate,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create an A/B test configuration.
    
    Args:
        test: A/B test configuration
        
    Returns:
        A/B test information
    """
    try:
        result = await evaluation_service.create_ab_test(
            name=test.name,
            description=test.description,
            variants=test.variants,
            active=test.active,
            traffic_allocation=test.traffic_allocation,
            metadata=test.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ab-tests/{test_name}/variant", response_model=Dict[str, Any])
async def get_ab_test_variant(
    test_name: str = Path(..., description="Name of the A/B test"),
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get an active A/B test variant for a user or session.
    
    Args:
        test_name: Name of the A/B test
        user_id: Optional user ID for consistent variant assignment
        session_id: Optional session ID if user is anonymous
        
    Returns:
        Dict with selected variant or None if no active test
    """
    try:
        # Use current user ID if not provided
        if not user_id and current_user:
            user_id = current_user.get("id")
            
        variant = await evaluation_service.get_active_ab_test_variant(
            test_name=test_name,
            user_id=user_id,
            session_id=session_id
        )
        
        if not variant:
            raise HTTPException(status_code=404, detail=f"No active A/B test found with name: {test_name}")
            
        return variant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ab-tests/result", response_model=Dict[str, Any])
async def log_ab_test_result(
    result: ABTestResult,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Log the result of an A/B test for a specific user interaction.
    
    Args:
        result: A/B test result data
        
    Returns:
        Dict with result information
    """
    try:
        # Use current user ID if not provided
        if not result.user_id and current_user:
            result.user_id = current_user.get("id")
            
        log_result = await evaluation_service.log_ab_test_result(
            test_id=result.test_id,
            variant=result.variant,
            metric_id=result.metric_id,
            outcome=result.outcome,
            score=result.score,
            user_id=result.user_id,
            session_id=result.session_id,
            metadata=result.metadata
        )
        return log_result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/ab-tests/{test_id}/results", response_model=Dict[str, Any])
async def get_ab_test_results(
    test_id: int = Path(..., description="ID of the A/B test"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get aggregated results for an A/B test.
    
    Args:
        test_id: ID of the A/B test
        start_date: Optional start date filter
        end_date: Optional end date filter
        
    Returns:
        Dict with test results by variant
    """
    try:
        results = await evaluation_service.get_ab_test_results(
            test_id=test_id,
            start_date=start_date,
            end_date=end_date
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/embedding-parameters", response_model=Dict[str, Any])
async def register_embedding_parameters(
    parameters: EmbeddingParameterCreate,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Register a set of embedding parameters for fine-tuning.
    
    Args:
        parameters: Embedding parameter data
        
    Returns:
        Dict with parameter information
    """
    try:
        result = await evaluation_service.register_embedding_parameters(
            name=parameters.name,
            parameters=parameters.parameters,
            model_name=parameters.model_name,
            description=parameters.description,
            active=parameters.active,
            metadata=parameters.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/embedding-parameters", response_model=Dict[str, Any])
async def get_active_embedding_parameters(
    model_name: Optional[str] = None,
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get the active embedding parameters for models.
    
    Args:
        model_name: Optional model name filter
        
    Returns:
        Dict with active parameter sets by model
    """
    try:
        parameters = await evaluation_service.get_active_embedding_parameters(
            model_name=model_name
        )
        return parameters
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-retrieval", response_model=Dict[str, Any])
async def test_retrieval(
    query: str = Body(..., embed=True),
    user_id: Optional[str] = Body(None, embed=True),
    session_id: Optional[str] = Body(None, embed=True),
    top_k: Optional[int] = Body(None, embed=True),
    ab_test_name: Optional[str] = Body(None, embed=True),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    evaluation_service: EvaluationService = Depends(get_evaluation_service),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Test retrieval with evaluation metrics.
    
    Args:
        query: Query text
        user_id: Optional user ID
        session_id: Optional session ID
        top_k: Optional number of results
        ab_test_name: Optional A/B test name
        
    Returns:
        Dict with retrieval results and metrics
    """
    try:
        # Use current user ID if not provided
        if not user_id and current_user:
            user_id = current_user.get("id")
            
        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            
        # Retrieve context with full evaluation
        context = await embedding_service.retrieve_context(
            query_text=query,
            top_k=top_k,
            track_metrics=True,
            session_id=session_id,
            user_id=user_id,
            evaluation_service=evaluation_service,
            ab_test_name=ab_test_name
        )
        
        return context
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 