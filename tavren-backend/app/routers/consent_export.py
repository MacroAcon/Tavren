from typing import Optional, Dict, Any
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from app.db.session import get_db
from app.models.user import User
from app.auth.dependencies import get_current_user, get_current_admin_user
from app.utils.consent_export import ConsentExportService, get_consent_export
from app.utils.rate_limit import RateLimiter

# Create router
router = APIRouter(
    prefix="/api/consent-ledger/export",
    tags=["consent-export"]
)

logger = logging.getLogger(__name__)
rate_limiter = RateLimiter()

# Rate limit keys
EXPORT_RATE_LIMIT_PREFIX = "consent_export"


@router.get("/{user_id}")
async def export_user_consent(
    user_id: str = Path(..., description="User ID to export consent data for"),
    include_pet_queries: bool = Query(False, description="Include PET query logs in export"),
    format: str = Query("json", description="Export format (json or file)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    export_service: ConsentExportService = Depends(get_consent_export),
    db = Depends(get_db)
):
    """
    Generate an export of consent and processing history for a user.
    
    Users can only export their own data unless they are an admin.
    Rate limited to 1 request per 24 hours for regular users.
    """
    # Verify authorization
    is_admin = hasattr(current_user, "is_admin") and current_user.is_admin
    if current_user.id != user_id and not is_admin:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You can only export your own consent data"
        )
    
    # Check rate limit (except for admins)
    if not is_admin:
        rate_limit_key = f"{EXPORT_RATE_LIMIT_PREFIX}:{user_id}"
        if not rate_limiter.check_rate_limit(rate_limit_key, max_requests=1, period_seconds=86400):  # 24 hours
            last_request = rate_limiter.get_last_request_time(rate_limit_key)
            retry_seconds = 86400 - (int(time.time()) - last_request)
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after_seconds": retry_seconds
                },
                headers={"Retry-After": str(retry_seconds)}
            )
    
    try:
        # Generate export package
        export_data = await export_service.generate_export_package(
            user_id=user_id,
            include_pet_queries=include_pet_queries,
            sign_export=True
        )
        
        # Update rate limit after successful generation
        if not is_admin:
            rate_limiter.update_rate_limit(rate_limit_key)
        
        # Return as JSON or save to file
        if format.lower() == "json":
            return export_data
        else:
            # Save to file and return file path
            file_path = await export_service.save_export_file(export_data)
            
            # Return file download
            return FileResponse(
                path=file_path,
                filename=f"consent_export_{user_id}.json",
                media_type="application/json"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating consent export: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate export"
        )


@router.get("/verify/{export_id}")
async def verify_export(
    export_id: str = Path(..., description="Export ID to verify"),
    export_data: Dict[str, Any] = None,
    export_service: ConsentExportService = Depends(get_consent_export),
    current_user: User = Depends(get_current_user)
):
    """
    Verify the authenticity and integrity of an export package.
    """
    if not export_data:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Export data must be provided"
        )
    
    # Check that the export ID matches
    if export_data.get("export_id") != export_id:
        return {
            "valid": False,
            "reason": "Export ID mismatch"
        }
    
    # Verify hash and signature
    is_valid = await export_service.verify_export_signature(export_data)
    
    return {
        "valid": is_valid,
        "export_id": export_id,
        "timestamp": export_data.get("export_timestamp")
    }


@router.get("/admin/{user_id}")
async def admin_export_user_consent(
    user_id: str = Path(..., description="User ID to export consent data for"),
    include_pet_queries: bool = Query(True, description="Include PET query logs in export"),
    format: str = Query("json", description="Export format (json or file)"),
    current_admin: User = Depends(get_current_admin_user),
    export_service: ConsentExportService = Depends(get_consent_export),
    db = Depends(get_db)
):
    """
    Admin endpoint to generate an export of consent and processing history for any user.
    Not rate limited and includes additional information for compliance verification.
    """
    try:
        # Generate export package with admin privileges
        export_data = await export_service.generate_export_package(
            user_id=user_id,
            include_pet_queries=include_pet_queries,
            sign_export=True
        )
        
        # Return as JSON or save to file
        if format.lower() == "json":
            return export_data
        else:
            # Save to file and return file path
            file_path = await export_service.save_export_file(export_data)
            
            # Return file download
            return FileResponse(
                path=file_path,
                filename=f"admin_consent_export_{user_id}.json",
                media_type="application/json"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating admin consent export: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate export"
        ) 