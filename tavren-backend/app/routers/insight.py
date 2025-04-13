from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import os
import pandas as pd
import time
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas.insight import InsightRequest, InsightResponse, ApiInfoResponse
from app.utils.insight_processor import process_insight, QueryType, PrivacyMethod, check_dsr_restrictions
from app.utils.consent_validator import ConsentValidator, get_consent_validator
from app.utils.rate_limit import RateLimiter, get_rate_limiter

# Create logger for this module
log = logging.getLogger("app")

# Create router with prefix and tags
insight_router = APIRouter(
    prefix="/api",
    tags=["Insights"],
    responses={404: {"description": "Not Found"}},
)

# Create a specific rate limiter for insights (more strict than general API)
INSIGHT_RATE_LIMIT = 60 * 5  # 5 minutes in seconds

# Example data for fallback
def get_example_data(query_type: QueryType) -> List[Dict[str, Any]]:
    """Get example data for the specified query type."""
    log.info(f"Using example data for {query_type}")
    
    if query_type == QueryType.AVERAGE_STORE_VISITS:
        # Create example data as a list of dictionaries
        return [
            {'user_id': 'u1', 'store_category': 'Grocery', 'visit_count': 5},
            {'user_id': 'u2', 'store_category': 'Grocery', 'visit_count': 3},
            {'user_id': 'u3', 'store_category': 'Grocery', 'visit_count': 4},
            {'user_id': 'u1', 'store_category': 'Electronics', 'visit_count': 1},
            {'user_id': 'u2', 'store_category': 'Electronics', 'visit_count': 2},
            {'user_id': 'u3', 'store_category': 'Electronics', 'visit_count': 1},
            {'user_id': 'u1', 'store_category': 'Clothing', 'visit_count': 3},
            {'user_id': 'u2', 'store_category': 'Clothing', 'visit_count': 4},
            {'user_id': 'u3', 'store_category': 'Clothing', 'visit_count': 2}
        ]
    
    # Default fallback - empty list (should not reach here due to validation)
    return []

@insight_router.post("/insight", response_model=InsightResponse, status_code=status.HTTP_200_OK)
async def process_insight_request(
    request: InsightRequest,
    db: AsyncSession = Depends(get_db),
    consent_validator: ConsentValidator = Depends(get_consent_validator),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
) -> InsightResponse:
    """
    Process an insight request with the specified privacy-enhancing technology.
    
    This endpoint is currently marked as EXPERIMENTAL and is intended for internal testing
    and partner demonstrations.
    
    Args:
        request: Insight request details including dataset, query type, privacy method
        db: Database session
        consent_validator: Validator to check user consent
        rate_limiter: Rate limiter for controlling request frequency
        
    Returns:
        Processed insight result with privacy guarantees
        
    Raises:
        HTTPException: If processing fails or consent is not granted
    """
    # Log the request (excluding raw data for brevity)
    log.info(f"Processing insight request: query_type={request.query_type}, privacy_method={request.privacy_method}")
    
    # Rate limit check if we have a user ID
    if request.user_id:
        rate_limit_key = f"insight:{request.user_id}"
        if not await rate_limiter.check_rate_limit(rate_limit_key, limit=5, period=INSIGHT_RATE_LIMIT):
            last_request = await rate_limiter.get_last_request_time(rate_limit_key)
            if last_request:
                reset_time = last_request + timedelta(seconds=INSIGHT_RATE_LIMIT)
                retry_after = int((reset_time - datetime.now()).total_seconds())
                
                # Return a 429 Too Many Requests response with Retry-After header
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded for insight requests. Please try again later.",
                    headers={"Retry-After": str(retry_after)}
                )
    
    start_time = time.time()
    
    try:
        # Process the data from the request
        try:
            # Convert data to list of dictionaries format expected by the processor
            data = []
            if hasattr(request, 'data') and request.data:
                if request.data_format == "csv":
                    # Parse CSV string to pandas DataFrame
                    df = pd.read_csv(pd.StringIO(request.data))
                    # Convert DataFrame to list of dictionaries
                    data = df.to_dict('records')
                elif request.data_format == "json":
                    # Parse JSON directly
                    if isinstance(request.data, str):
                        import json
                        data = json.loads(request.data)
                    else:
                        data = request.data
            
            if not data:
                log.warning("No data provided or could not parse data. Using example data.")
                data = get_example_data(request.query_type)
                
        except Exception as e:
            log.warning(f"Error processing request data: {str(e)}. Using example data instead.")
            data = get_example_data(request.query_type)
        
        # Extract user IDs from data for DSR checks
        user_ids = list(set(item.get('user_id') for item in data if 'user_id' in item))
        
        # Check for DSR restrictions before processing
        can_process, restricted_users, restriction_msg = await check_dsr_restrictions(db, user_ids)
        if not can_process:
            log.warning(f"DSR restriction detected: {restriction_msg}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Processing restricted",
                    "message": "One or more users have requested processing restrictions",
                    "restricted_user_count": len(restricted_users)
                }
            )
        
        # Prepare privacy parameters
        privacy_params = {}
        if request.privacy_method == PrivacyMethod.DP:
            privacy_params["epsilon"] = request.epsilon if hasattr(request, "epsilon") else 1.0
            privacy_params["delta"] = request.delta if hasattr(request, "delta") else 1e-5
        elif request.privacy_method == PrivacyMethod.SMPC:
            privacy_params["min_parties"] = request.min_parties if hasattr(request, "min_parties") else 2
        
        # Set default purpose if not provided
        purpose = request.purpose if hasattr(request, 'purpose') and request.purpose else "insight_generation"
        
        # Call the insight processor
        result = await process_insight(
            data=data, 
            query_type=request.query_type, 
            privacy_method=request.privacy_method, 
            privacy_params=privacy_params,
            validate_consent=True,
            db=db,
            user_id_field='user_id'
        )
        
        # Check for processing errors
        if not result.get("success", False):
            error_msg = result.get("error", "Unknown processing error")
            log.error(f"Processing error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Processing error",
                    "message": error_msg
                }
            )
        
        # Extract processed result and metadata
        processed_result = result.get("result", {})
        metadata = result.get("metadata", {})
        
        # Add additional timing information
        processing_time = time.time() - start_time
        metadata["api_processing_time_ms"] = round(processing_time * 1000, 2)
        
        # Update rate limiter if we have a user ID
        if request.user_id:
            await rate_limiter.update_rate_limit(f"insight:{request.user_id}")
        
        # Create response
        response = InsightResponse(
            processed_result=processed_result,
            privacy_method_used=request.privacy_method,
            metadata=metadata
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions to preserve status code
        raise
    except ValueError as e:
        log.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except NotImplementedError as e:
        log.error(f"Implementation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(e)
        )
    except Exception as e:
        log.error(f"Error processing insight request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing insight: {str(e)}"
        )

@insight_router.get("/info", response_model=ApiInfoResponse, status_code=status.HTTP_200_OK)
async def get_api_info() -> ApiInfoResponse:
    """
    Get information about the insight API, including supported query types,
    privacy methods, and example payload structure.
    
    Returns:
        API information including supported features and example payload
    """
    # List of supported query types
    supported_query_types = [qt.value for qt in QueryType]
    
    # List of supported privacy methods
    supported_privacy_methods = [pm.value for pm in PrivacyMethod]
    
    # Example payload for reference
    example_payload = {
        "data": "user_id,store_category,visit_count\nu1,Grocery,5\nu2,Grocery,3\nu3,Grocery,4",
        "query_type": "average_store_visits",
        "privacy_method": "differential_privacy",
        "epsilon": 1.0,
        "data_format": "csv"
    }
    
    return ApiInfoResponse(
        supported_query_types=supported_query_types,
        supported_privacy_methods=supported_privacy_methods,
        example_payload=example_payload
    ) 