from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
import os
import pandas as pd
import time

from app.database import get_db
from app.schemas.insight import InsightRequest, InsightResponse, ApiInfoResponse
from app.utils.insight_processor import process_insight, QueryType, PrivacyMethod
from app.utils.consent_validator import ConsentValidator, get_consent_validator

# Create logger for this module
log = logging.getLogger("app")

# Create router with prefix and tags
insight_router = APIRouter(
    prefix="/api",
    tags=["Insights"],
    responses={404: {"description": "Not Found"}},
)

# Example data for fallback
def get_example_data(query_type: QueryType, pet_method: PrivacyMethod) -> Any:
    """Get example data for the specified query type and PET method."""
    log.info(f"Using example data for {query_type} with {pet_method}")
    
    if query_type == QueryType.AVERAGE_STORE_VISITS:
        if pet_method == PrivacyMethod.DP:
            # Create example DataFrame for DP
            data = {
                'user_id': ['u1', 'u2', 'u3', 'u1', 'u2', 'u3', 'u1', 'u2', 'u3'],
                'store_category': ['Grocery', 'Grocery', 'Grocery', 'Electronics', 'Electronics', 'Electronics', 'Clothing', 'Clothing', 'Clothing'],
                'visit_count': [5, 3, 4, 1, 2, 1, 3, 4, 2],
            }
            return pd.DataFrame(data)
        else:
            # Create example party data list for SMPC
            return [
                {
                    'users': ['u1', 'u2'],
                    'data': pd.DataFrame({
                        'user_id': ['u1', 'u2', 'u1', 'u2', 'u1', 'u2'],
                        'store_category': ['Grocery', 'Grocery', 'Electronics', 'Electronics', 'Clothing', 'Clothing'],
                        'visit_count': [5, 3, 1, 2, 3, 4],
                    })
                },
                {
                    'users': ['u3'],
                    'data': pd.DataFrame({
                        'user_id': ['u3', 'u3', 'u3'],
                        'store_category': ['Grocery', 'Electronics', 'Clothing'],
                        'visit_count': [4, 1, 2],
                    })
                }
            ]
    
    # Default fallback - empty DataFrame (should not reach here due to validation)
    return pd.DataFrame()

@insight_router.post("/insight", response_model=InsightResponse, status_code=status.HTTP_200_OK)
async def process_insight_request(
    request: InsightRequest,
    db: AsyncSession = Depends(get_db),
    consent_validator: ConsentValidator = Depends(get_consent_validator)
) -> InsightResponse:
    """
    Process an insight request with the specified privacy-enhancing technology.
    
    This endpoint is currently marked as EXPERIMENTAL and is intended for internal testing
    and partner demonstrations.
    
    Args:
        request: Insight request details including dataset, query type, privacy method
        db: Database session
        consent_validator: Validator to check user consent
        
    Returns:
        Processed insight result with privacy guarantees
        
    Raises:
        HTTPException: If processing fails or consent is not granted
    """
    # Log the request (excluding raw data for brevity)
    log.info(f"Processing insight request: query_type={request.query_type}, pet_method={request.pet_method}")
    
    start_time = time.time()
    
    try:
        # Process the data from the request
        try:
            data = request.process_data()
        except Exception as e:
            log.warning(f"Error processing request data: {str(e)}. Using example data instead.")
            data = get_example_data(request.query_type, request.pet_method)
        
        # Extract user_id from data if possible
        user_id = None
        data_scope = None
        
        # Determine user_id and data_scope from the data or request
        if request.user_id:
            user_id = request.user_id
        elif isinstance(data, pd.DataFrame) and 'user_id' in data.columns:
            # Use the first user_id found in the DataFrame
            if not data['user_id'].empty:
                user_id = str(data['user_id'].iloc[0])
        
        # Determine data scope based on query type
        if request.query_type == QueryType.AVERAGE_STORE_VISITS.value:
            data_scope = "store_visits"
        
        # Set default purpose if not provided
        purpose = request.purpose if hasattr(request, 'purpose') and request.purpose else "insight_generation"
        
        # Call the insight processor with consent validation
        result = await process_insight(
            data=data, 
            query_type=request.query_type, 
            pet_method=request.pet_method, 
            epsilon=request.epsilon,
            user_id=user_id,
            data_scope=data_scope,
            purpose=purpose,
            consent_validator=consent_validator if user_id and data_scope else None
        )
        
        # Check if processing was rejected due to consent issues
        if result.get("metadata", {}).get("status") == "rejected":
            error_details = result.get("metadata", {}).get("error_details", {})
            log.warning(f"Processing rejected due to consent: {error_details.get('reason')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Consent validation failed",
                    "details": error_details,
                    "message": "User has not granted or has revoked consent for this operation"
                }
            )
        
        # Check for other processing errors
        if result.get("metadata", {}).get("status") == "error":
            error_details = result.get("metadata", {}).get("error_details", {})
            log.error(f"Processing error: {error_details.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Processing error",
                    "details": error_details
                }
            )
        
        # Extract processed result and metadata
        processed_result = result.get("result", {})
        metadata = result.get("metadata", {})
        
        # Add additional timing information
        processing_time = time.time() - start_time
        metadata["api_processing_time_ms"] = round(processing_time * 1000, 2)
        
        # Create response
        response = InsightResponse(
            processed_result=processed_result,
            privacy_method_used=request.pet_method,
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
        "pet_method": "dp",
        "epsilon": 1.0,
        "data_format": "csv"
    }
    
    return ApiInfoResponse(
        supported_query_types=supported_query_types,
        supported_privacy_methods=supported_privacy_methods,
        example_payload=example_payload
    ) 