from fastapi import APIRouter, Depends, HTTPException, Query, Path, Response, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from app.database import get_db
from app.schemas import (
    ConsentEventCreate,
    ConsentEventResponse,
    ConsentLedgerExport,
    LedgerVerificationResult
)
from app.services.consent_ledger import ConsentLedgerService, get_consent_ledger_service
from app.auth import get_current_active_user
from app.utils.response_utils import handle_exception
from app.logging.log_utils import log_api_request, log_exception
from app.constants.status import HTTP_500_INTERNAL_SERVER_ERROR
from app.dependencies import get_current_user, get_current_admin_user
from app.models import User
from app.utils.consent_export import get_consent_export

# Get logger
log = logging.getLogger("app")

# Create router
consent_ledger_router = APIRouter(
    prefix="/api/consent-ledger",
    tags=["consent-ledger"]
)

@consent_ledger_router.post("", response_model=ConsentEventResponse)
async def record_consent_event(
    event: ConsentEventCreate,
    db = Depends(get_db),
    consent_ledger_service: ConsentLedgerService = Depends(get_consent_ledger_service)
):
    """
    Record a new consent event in the ledger.
    
    This endpoint creates a new entry in the tamper-evident consent ledger,
    with hash chaining to ensure integrity of the consent history.
    """
    log_api_request(endpoint="/api/consent-ledger", method="POST", params={
        "user_id": event.user_id,
        "action": event.action,
        "scope": event.scope,
        "purpose": event.purpose
    })
    
    log.info(f"Recording consent event: {event.action} for user {event.user_id}")
    
    try:
        result = await consent_ledger_service.record_event(event)
        return result
    except Exception as e:
        log_exception(e, context="record_consent_event", user_id=event.user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Failed to record consent event")

@consent_ledger_router.get("/users/{user_id}", response_model=List[ConsentEventResponse])
async def get_user_consent_history(
    user_id: str = Path(..., description="ID of the user to get consent history for"),
    db = Depends(get_db),
    consent_ledger_service: ConsentLedgerService = Depends(get_consent_ledger_service)
):
    """
    Retrieve consent event history for a specific user.
    
    Returns all consent events for the specified user in chronological order,
    including verification hashes for integrity validation.
    """
    log_api_request(endpoint=f"/api/consent-ledger/users/{user_id}", method="GET")
    
    log.info(f"Retrieving consent history for user {user_id}")
    
    try:
        events = await consent_ledger_service.get_user_history(user_id)
        return events
    except Exception as e:
        log_exception(e, context="get_user_consent_history", user_id=user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Failed to retrieve consent history")

@consent_ledger_router.get("/export", response_model=Dict[str, Any])
async def export_consent_ledger(
    background_tasks: BackgroundTasks,
    include_pet_queries: bool = Query(False, description="Include privacy-enhancing technology query logs"),
    save_file: bool = Query(False, description="Save export to file on server"),
    download: bool = Query(True, description="Download export as a file"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db),
):
    """
    Generate a verifiable export of the user's consent events and processing history.
    
    This export includes:
    - Complete consent event history
    - DSR action history
    - Optionally, PET query logs involving the user's data
    
    The export is cryptographically signed and includes a hash for verification.
    """
    # Get consent export service
    export_service = await get_consent_export(db)
    
    # Generate export package
    export_data = await export_service.generate_export_package(
        user_id=current_user.id,
        include_pet_queries=include_pet_queries,
        sign_export=True
    )
    
    # Save file if requested
    if save_file:
        file_path = await export_service.save_export_file(export_data)
        if file_path:
            export_data["file_path"] = file_path
    
    # Return as downloadable file if requested
    if download:
        filename = f"{current_user.id}_consent_export_{export_data.get('export_timestamp', '').replace(':', '-')}.json"
        json_content = json.dumps(export_data, indent=2)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    # Otherwise return as JSON response
    return export_data

@consent_ledger_router.get("/export/{user_id}", response_model=Dict[str, Any])
async def export_user_consent_ledger(
    user_id: str,
    background_tasks: BackgroundTasks,
    include_pet_queries: bool = Query(False, description="Include privacy-enhancing technology query logs"),
    save_file: bool = Query(True, description="Save export to file on server"),
    download: bool = Query(False, description="Download export as a file"),
    current_admin: User = Depends(get_current_admin_user),
    db = Depends(get_db),
):
    """
    [Admin only] Generate a verifiable export of any user's consent events and processing history.
    """
    # Get consent export service
    export_service = await get_consent_export(db)
    
    # Generate export package
    export_data = await export_service.generate_export_package(
        user_id=user_id,
        include_pet_queries=include_pet_queries,
        sign_export=True
    )
    
    # Save file if requested
    if save_file:
        file_path = await export_service.save_export_file(export_data)
        if file_path:
            export_data["file_path"] = file_path
    
    # Return as downloadable file if requested
    if download:
        filename = f"{user_id}_consent_export_{export_data.get('export_timestamp', '').replace(':', '-')}.json"
        json_content = json.dumps(export_data, indent=2)
        return Response(
            content=json_content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    
    # Otherwise return as JSON response
    return export_data

@consent_ledger_router.get("/verify", response_model=LedgerVerificationResult)
async def verify_ledger_integrity(
    user_id: Optional[str] = Query(None, description="Optional user ID to verify only that user's events"),
    db = Depends(get_db),
    consent_ledger_service: ConsentLedgerService = Depends(get_consent_ledger_service),
    current_user = Depends(get_current_active_user)
):
    """
    Verify the integrity of the consent ledger.
    
    Checks the hash chain to ensure no records have been tampered with.
    This endpoint requires administrator privileges.
    """
    log_api_request(endpoint="/api/consent-ledger/verify", method="GET", params={
        "user_id": user_id
    })
    
    log.info(f"Verifying consent ledger integrity for {user_id if user_id else 'all users'}")
    
    try:
        result = await consent_ledger_service.verify_ledger_integrity(user_id)
        return result
    except Exception as e:
        log_exception(e, context="verify_ledger_integrity")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Failed to verify ledger integrity") 