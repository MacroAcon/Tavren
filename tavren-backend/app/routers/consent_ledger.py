from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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

@consent_ledger_router.get("/export", response_model=List[Dict[str, Any]])
async def export_consent_ledger(
    start_date: Optional[datetime] = Query(None, description="Filter events after this date"),
    end_date: Optional[datetime] = Query(None, description="Filter events before this date"),
    db: AsyncSession = Depends(get_db),
    consent_ledger_service: ConsentLedgerService = Depends(get_consent_ledger_service),
    current_user = Depends(get_current_active_user)
):
    """
    Export the full consent ledger for auditing.
    
    Returns all consent events in the ledger, optionally filtered by date range.
    This endpoint requires administrator privileges.
    """
    log_api_request(endpoint="/api/consent-ledger/export", method="GET", params={
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None
    })
    
    log.info(f"Exporting consent ledger (date range: {start_date} to {end_date})")
    
    try:
        events = await consent_ledger_service.export_ledger(start_date, end_date)
        return events
    except Exception as e:
        log_exception(e, context="export_consent_ledger")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Failed to export consent ledger")

@consent_ledger_router.get("/verify", response_model=LedgerVerificationResult)
async def verify_ledger_integrity(
    user_id: Optional[str] = Query(None, description="Optional user ID to verify only that user's events"),
    db: AsyncSession = Depends(get_db),
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