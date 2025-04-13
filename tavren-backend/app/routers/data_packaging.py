"""
API router for data packaging operations.
Provides endpoints for packaging data, validating tokens, and retrieving package details.
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Security
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.schemas import (
    DataPackageRequest, 
    DataPackageResponse, 
    DataAccessRequest,
    DataPackageAuditResponse,
    DataSchemaInfo
)
from app.models import DataPackageAudit
from app.services.data_packaging import DataPackagingService, get_data_packaging_service
from app.utils.consent_validator import ConsentValidator, get_consent_validator
from app.utils.consent_decorator import requires_consent

# Set up logging
log = logging.getLogger("app")

# Create router
data_packaging_router = APIRouter(
    prefix="/api/data-packages",
    tags=["data-packaging"]
)

@data_packaging_router.post("", response_model=DataPackageResponse)
@requires_consent(
    data_scope=lambda request: request.data_type,
    purpose=lambda request: request.purpose,
    user_id_extractor=lambda request: request.user_id
)
async def create_data_package(
    request: DataPackageRequest, 
    db: AsyncSession = Depends(get_db),
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service),
    consent_validator: ConsentValidator = Depends(get_consent_validator)
):
    """
    Package user data according to the specified parameters.
    
    - Validates consent permissions through the @requires_consent decorator
    - Retrieves and anonymizes data
    - Formats according to schemas
    - Includes audit trail
    
    Returns the packaged data with metadata.
    """
    try:
        log.info(f"Received data package request for user {request.user_id}, type {request.data_type}")
        
        packaged_data = await data_packaging_service.package_data(
            user_id=request.user_id,
            data_type=request.data_type,
            access_level=request.access_level,
            consent_id=request.consent_id,
            purpose=request.purpose,
            buyer_id=request.buyer_id,
            trust_tier=request.trust_tier
        )
        
        log.info(f"Successfully created data package {packaged_data['package_id']}")
        return packaged_data
    
    except Exception as e:
        log.error(f"Error creating data package: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error packaging data: {str(e)}")

@data_packaging_router.get("/{package_id}", response_model=DataPackageResponse)
async def get_data_package(
    package_id: str = Path(..., description="The ID of the data package to retrieve"),
    access_token: Optional[str] = Query(None, description="Access token for the package"),
    db: AsyncSession = Depends(get_db),
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service)
):
    """
    Retrieve a data package by its ID.
    
    - Requires a valid access token
    - Token is validated for expiry and proper permissions
    - Decrypts content if needed
    
    Returns the data package if access is authorized.
    """
    try:
        log.info(f"Attempt to retrieve data package {package_id}")
        
        # Validate access token if provided
        if access_token:
            is_valid, details = await data_packaging_service.validate_access_token(access_token, package_id)
            
            if not is_valid:
                log.warning(f"Invalid access token for package {package_id}: {details.get('reason')}")
                raise HTTPException(status_code=401, detail=details.get('reason', "Invalid token"))
        
        # Get the package
        package, error = await data_packaging_service.get_package_by_id(package_id, access_token)
        
        if not package:
            log.warning(f"Data package {package_id} not found: {error.get('reason')}")
            raise HTTPException(status_code=404, detail=error.get('reason', "Package not found"))
        
        log.info(f"Successfully retrieved data package {package_id}")
        return package
    
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error retrieving data package {package_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving data package: {str(e)}")

@data_packaging_router.post("/validate-token", response_model=Dict[str, Any])
async def validate_access_token(
    request: DataAccessRequest,
    db: AsyncSession = Depends(get_db),
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service)
):
    """
    Validate an access token for a data package.
    
    - Checks token expiry
    - Verifies token is for the specified package
    - Validates signature 
    
    Returns validation result.
    """
    try:
        log.info(f"Validating access token for package {request.package_id}")
        
        is_valid, details = await data_packaging_service.validate_access_token(
            request.access_token, request.package_id
        )
        
        if not is_valid:
            log.warning(f"Invalid token validation: {details.get('reason')}")
            return {
                "valid": False,
                "reason": details.get('reason', "Invalid token")
            }
        
        log.info(f"Successfully validated token for package {request.package_id}")
        return {
            "valid": True,
            "package_id": request.package_id,
            "expires_at": details.get("exp"),
            "consent_id": details.get("consent_id")
        }
    
    except Exception as e:
        log.error(f"Error validating token: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error validating token: {str(e)}")

@data_packaging_router.get("/audit/{package_id}", response_model=List[DataPackageAuditResponse])
async def get_package_audit_trail(
    package_id: str = Path(..., description="The ID of the data package"),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the audit trail for a specific data package.
    
    Returns all audit events related to the package.
    """
    try:
        log.info(f"Retrieving audit trail for package {package_id}")
        
        # Query audit records for this package
        query = select(DataPackageAudit).where(DataPackageAudit.package_id == package_id).order_by(DataPackageAudit.timestamp)
        result = await db.execute(query)
        audit_records = result.scalars().all()
        
        if not audit_records:
            log.warning(f"No audit records found for package {package_id}")
            return []
        
        log.info(f"Found {len(audit_records)} audit records for package {package_id}")
        return audit_records
    
    except Exception as e:
        log.error(f"Error retrieving audit trail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving audit trail: {str(e)}")

@data_packaging_router.get("/schemas", response_model=List[DataSchemaInfo])
async def get_available_schemas(
    db: AsyncSession = Depends(get_db),
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service)
):
    """
    Get information about available data schemas.
    
    Returns a list of supported data types and their schema details.
    """
    # List of supported data types
    data_types = ["app_usage", "location", "browsing_history", "health", "financial"]
    
    result = []
    for data_type in data_types:
        # Get schema version for this data type
        schema_version = data_packaging_service._get_schema_version(data_type)
        
        # Get required fields
        required_fields = data_packaging_service._get_required_fields(data_type, schema_version)
        
        # Generate example data based on mock data generators in the service
        example_data = {}
        for field in required_fields:
            example_data[field] = data_packaging_service._get_default_value(field, data_type)
        
        # Add descriptions based on data type
        if data_type == "app_usage":
            description = "App usage data including timestamps, duration, and actions"
        elif data_type == "location":
            description = "Location data including coordinates, accuracy, and timestamps"
        elif data_type == "browsing_history":
            description = "Web browsing history including URLs, page titles, and visit duration"
        elif data_type == "health":
            description = "Health-related measurements like heart rate, steps, sleep data"
        elif data_type == "financial":
            description = "Financial transaction data including amounts, categories, and merchants"
        else:
            description = f"Data schema for {data_type}"
        
        # Create schema info object
        schema_info = DataSchemaInfo(
            data_type=data_type,
            schema_version=schema_version,
            required_fields=required_fields,
            description=description,
            example=example_data
        )
        
        result.append(schema_info)
    
    return result 