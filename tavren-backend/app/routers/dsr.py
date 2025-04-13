from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.services.dsr_service import DSRService, get_dsr_service
from app.auth import get_current_user_id, oauth2_scheme
from app.schemas import UserInDB

# Rate limiting functionality
from app.utils.rate_limit import RateLimiter, get_rate_limiter

# Set up logging
log = logging.getLogger("app")

# Create router
dsr_router = APIRouter(
    prefix="/api/dsr",
    tags=["Data Subject Requests"],
    responses={404: {"description": "Not found"}},
)

# Create a DSR-specific rate limiter (1 request per 7 days)
DSR_RATE_LIMIT = 60 * 60 * 24 * 7  # 7 days in seconds

@dsr_router.get("/export",
               summary="Export user data",
               description="Generate a comprehensive export of all user data")
async def export_user_data(
    format: str = "json",
    include_consent: bool = True,
    include_rewards: bool = True,
    include_payouts: bool = True,
    db: AsyncSession = Depends(get_db),
    dsr_service: DSRService = Depends(get_dsr_service),
    user_id: str = Depends(get_current_user_id),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Generate and download a comprehensive export of the user's personal data.
    
    This endpoint processes Data Subject Access Requests (DSAR) and provides:
    - User profile information
    - Consent history (opt-ins, opt-outs)
    - Reward and transaction history
    - Payout records
    
    All exports are logged for audit purposes.
    """
    # Rate limit check
    rate_limit_key = f"dsr:export:{user_id}"
    if not await rate_limiter.check_rate_limit(rate_limit_key, limit=1, period=DSR_RATE_LIMIT):
        last_request = await rate_limiter.get_last_request_time(rate_limit_key)
        if last_request:
            reset_time = last_request + timedelta(seconds=DSR_RATE_LIMIT)
            retry_after = int((reset_time - datetime.now()).total_seconds())
            
            # Return a 429 Too Many Requests response with Retry-After header
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for data exports. Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )
    
    try:
        # Generate data export
        file_obj, content_type = await dsr_service.generate_data_export(
            user_id=user_id,
            include_consent=include_consent,
            include_rewards=include_rewards,
            include_payouts=include_payouts,
            format=format
        )
        
        # Update rate limiter
        await rate_limiter.update_rate_limit(rate_limit_key)
        
        # Determine filename based on format
        filename = f"tavren_data_export_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        filename += ".json" if format == "json" else ".zip"
        
        # Return streaming response with appropriate headers
        return StreamingResponse(
            file_obj,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    except Exception as e:
        log.error(f"Error generating data export for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating data export: {str(e)}"
        )

@dsr_router.post("/delete",
                summary="Delete user data",
                description="Delete personal data from the system")
async def delete_user_data(
    delete_profile: bool = True,
    delete_consent: bool = False,
    db: AsyncSession = Depends(get_db),
    dsr_service: DSRService = Depends(get_dsr_service),
    user_id: str = Depends(get_current_user_id),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Request deletion of personal data from the system.
    
    This endpoint processes Data Erasure Requests and:
    - Deletes user profile information (by default)
    - Deletes reward history
    - Optionally deletes consent records (normally preserved for audit)
    - Preserves payout history for legal/financial requirements
    
    All deletion requests are logged for audit purposes.
    """
    # Rate limit check
    rate_limit_key = f"dsr:delete:{user_id}"
    if not await rate_limiter.check_rate_limit(rate_limit_key, limit=1, period=DSR_RATE_LIMIT):
        last_request = await rate_limiter.get_last_request_time(rate_limit_key)
        if last_request:
            reset_time = last_request + timedelta(seconds=DSR_RATE_LIMIT)
            retry_after = int((reset_time - datetime.now()).total_seconds())
            
            # Return a 429 Too Many Requests response with Retry-After header
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for data deletion requests. Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )
    
    try:
        # Process deletion request
        deletion_results = await dsr_service.delete_user_data(
            user_id=user_id,
            delete_profile=delete_profile,
            delete_consent=delete_consent
        )
        
        # Update rate limiter
        await rate_limiter.update_rate_limit(rate_limit_key)
        
        return {
            "status": "success",
            "message": "Data deletion processed successfully",
            "results": deletion_results
        }
    
    except Exception as e:
        log.error(f"Error processing data deletion for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing data deletion: {str(e)}"
        )

@dsr_router.post("/restrict",
                summary="Restrict data processing",
                description="Restrict future processing of user data")
async def restrict_data_processing(
    restriction_scope: str = "all",
    restriction_reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    dsr_service: DSRService = Depends(get_dsr_service),
    user_id: str = Depends(get_current_user_id),
    rate_limiter: RateLimiter = Depends(get_rate_limiter)
):
    """
    Request restriction of data processing.
    
    This endpoint processes Data Processing Restriction Requests and:
    - Creates a global opt-out record to prevent future processing
    - Blocks PET queries from executing with this user's data
    - Records the restriction in the consent ledger
    
    All restriction requests are logged for audit purposes.
    """
    # Rate limit check
    rate_limit_key = f"dsr:restrict:{user_id}"
    if not await rate_limiter.check_rate_limit(rate_limit_key, limit=1, period=DSR_RATE_LIMIT):
        last_request = await rate_limiter.get_last_request_time(rate_limit_key)
        if last_request:
            reset_time = last_request + timedelta(seconds=DSR_RATE_LIMIT)
            retry_after = int((reset_time - datetime.now()).total_seconds())
            
            # Return a 429 Too Many Requests response with Retry-After header
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded for processing restriction requests. Please try again later.",
                headers={"Retry-After": str(retry_after)}
            )
    
    try:
        # Process restriction request
        restriction_results = await dsr_service.restrict_user_processing(
            user_id=user_id,
            restriction_scope=restriction_scope,
            restriction_reason=restriction_reason
        )
        
        # Update rate limiter
        await rate_limiter.update_rate_limit(rate_limit_key)
        
        return {
            "status": "success",
            "message": "Processing restriction applied successfully",
            "results": restriction_results
        }
    
    except Exception as e:
        log.error(f"Error processing restriction request for user {user_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing restriction request: {str(e)}"
        ) 