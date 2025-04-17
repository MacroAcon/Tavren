"""
API Router for buyer-facing data operations.
Provides endpoints for buyers to request and access data packages.
"""

import logging
from typing import Dict, Any, List, TYPE_CHECKING, Annotated
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Security

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import DataPackageRequest, DataPackageResponse, DataAccessRequest, DataSchemaInfo
from app.services.data_service import DataService, get_data_service

# Set up logging
log = logging.getLogger("app")

# Create router
buyer_data_router = APIRouter(
    prefix="/api/buyers/data",
    tags=["buyer-data"]
)

# Using Annotated helps FastAPI distinguish dependency injection from response model fields,
# preventing errors when a response_model is defined on a route that depends on non-Pydantic types like AsyncSession.
DataServiceDep = Annotated[DataService, Depends(get_data_service)]

@buyer_data_router.post("/request", response_model=DataPackageResponse)
async def request_data_package(
    request: DataPackageRequest,
    data_service: DataServiceDep
):
    """
    Request a data package for a specific user and data type.
    
    This endpoint allows buyers to request data based on existing consent.
    It validates the consent, applies appropriate anonymization based on
    the buyer's trust tier, and returns a secure data package.
    
    The request must include:
    - user_id: ID of the user whose data is being requested
    - data_type: Type of data being requested
    - access_level: Requested access level
    - consent_id: ID of the consent record
    - purpose: Purpose for data use
    
    Returns a data package with content and access token.
    """
    try:
        log.info(f"Buyer requesting data for user {request.user_id}, type {request.data_type}")
        
        # Since this is a buyer-facing API, we need to use the appropriate service
        # that wraps the data packaging with additional checks
        data_package = await data_service.prepare_data_for_buyer(
            user_id=request.user_id,
            buyer_id=request.buyer_id or "unknown_buyer",  # Buyer ID should be from auth token
            offer_id=request.consent_id,  # Using consent_id as offer_id for now
            data_type=request.data_type,
            purpose=request.purpose
        )
        
        log.info(f"Successfully created data package {data_package['package_id']} for buyer")
        return data_package
        
    except Exception as e:
        log.error(f"Error requesting data package: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process data package request"
        )

@buyer_data_router.get("/{package_id}", response_model=DataPackageResponse)
async def get_data_package(
    package_id: Annotated[str, Path(..., description="The ID of the data package")],
    access_token: Annotated[str, Query(..., description="Access token for the data package")],
    data_service: DataServiceDep
):
    """
    Retrieve a previously created data package using the access token.
    
    Args:
        package_id: ID of the data package to retrieve
        access_token: Access token provided when the package was created
        
    Returns:
        The data package if the access token is valid
    """
    try:
        log.info(f"Buyer requesting access to data package {package_id}")
        
        # For now, we'll use the data packaging service directly
        # In a full implementation, this would go through the data_service
        # with additional security checks
        
        # First validate the token
        is_valid, details = await data_service.data_packaging_service.validate_access_token(
            access_token, package_id
        )
        
        if not is_valid:
            log.warning(f"Invalid access token for package {package_id}: {details.get('reason')}")
            raise HTTPException(status_code=401, detail="Invalid or expired access token")
        
        # Get the package
        package, error = await data_service.data_packaging_service.get_package_by_id(package_id)
        
        if not package:
            log.warning(f"Data package {package_id} not found or could not be retrieved")
            raise HTTPException(status_code=404, detail="Data package not found")
        
        log.info(f"Successfully retrieved data package {package_id} for buyer")
        return package
        
    except Exception as e:
        log.error(f"Error retrieving data package {package_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve data package"
        )

@buyer_data_router.get("/types", response_model=List[DataSchemaInfo])
async def get_available_data_types(
    data_service: DataServiceDep
):
    """
    Get a list of available data types that buyers can request.
    
    Returns information about each data type including:
    - Name
    - Description
    - Required access level
    - Schema details
    """
    try:
        # This is a simplified implementation
        # In a full system, this would come from a configuration or database
        data_types = [
            {
                "type": "app_usage",
                "name": "Application Usage Data",
                "description": "User application usage patterns including app opens, time spent, and interactions",
                "access_levels": ["precise_persistent", "precise_short_term", "anonymous_persistent", "anonymous_short_term"],
                "sample_fields": ["app_id", "timestamp", "duration", "action"]
            },
            {
                "type": "location",
                "name": "Location Data",
                "description": "User location data including coordinates, accuracy, and timestamps",
                "access_levels": ["precise_persistent", "precise_short_term", "anonymous_persistent", "anonymous_short_term"],
                "sample_fields": ["timestamp", "latitude", "longitude", "accuracy"]
            },
            {
                "type": "browsing_history",
                "name": "Web Browsing History",
                "description": "User web browsing history including URLs, page titles, and duration",
                "access_levels": ["precise_persistent", "precise_short_term", "anonymous_persistent", "anonymous_short_term"],
                "sample_fields": ["timestamp", "url", "duration", "page_title"]
            },
            {
                "type": "health",
                "name": "Health Data",
                "description": "User health metrics like heart rate, steps, sleep data",
                "access_levels": ["anonymous_persistent", "anonymous_short_term"],
                "sample_fields": ["timestamp", "type", "measurement", "unit"]
            },
            {
                "type": "financial",
                "name": "Financial Data",
                "description": "User financial transaction data including amounts, categories, and merchants",
                "access_levels": ["anonymous_short_term"],
                "sample_fields": ["timestamp", "type", "amount", "currency"]
            }
        ]
        
        return data_types
    except Exception as e:
        log.error(f"Error retrieving available data types: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve available data types"
        ) 