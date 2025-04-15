import logging
from typing import Dict, Tuple, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import json
from fastapi import Depends

from app.models import ConsentEvent
from app.database import get_db
# Remove import at module level to avoid circular imports
# from app.services.consent_ledger import ConsentLedgerService, get_consent_ledger_service

# Get logger
log = logging.getLogger("app")

# Consent action constants
ACTION_OPT_IN = "opt_in"
ACTION_OPT_OUT = "opt_out"
ACTION_WITHDRAW = "withdraw"
ACTION_GRANT_PARTIAL = "grant_partial"

class ConsentValidator:
    """
    Utility class to validate if data processing is allowed based on user consent state.
    
    Performs real-time checks against the consent ledger to determine if a specific
    data processing operation is permitted based on:
    - User's consent history
    - Data scope (e.g., "location", "purchase_data")
    - Processing purpose (e.g., "insight_generation", "ad_targeting")
    
    Also handles partial revocations and purpose-specific permissions.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def check_dsr_restrictions(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if the user has any DSR-related processing restrictions.
        
        Args:
            user_id: ID of the user to check
            
        Returns:
            Tuple of (has_restrictions, details) where:
                - has_restrictions: Boolean indicating if processing is restricted
                - details: Dict with reason and relevant restriction information
        """
        log.info(f"Checking DSR restrictions for user {user_id}")
        
        # Import inside method to avoid circular imports
        from app.services.consent_ledger import ConsentLedgerService
        
        # Get the consent ledger service
        consent_ledger_service = ConsentLedgerService(self.db)
        
        # Get user's consent history
        consent_history = await consent_ledger_service.get_user_history(user_id)
        
        if not consent_history:
            # No history means no restrictions
            return False, {"status": "no_restrictions"}
        
        # Look for DSR-related restrictions
        for event in consent_history:
            # Look for system restriction events in metadata
            metadata = event.consent_metadata or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Check for restriction requests in the event metadata
            if metadata.get("dsr_type") == "processing_restriction" and event.action == "dsr_request":
                return True, {
                    "status": "restricted",
                    "reason": "DSR processing restriction",
                    "restriction_type": "dsr_request",
                    "applied_at": event.timestamp.isoformat(),
                    "scope": event.scope or "all",
                    "restriction_id": event.id
                }
            
            # Also check for global opt-outs with system_restriction offer_id
            if event.offer_id == "system_restriction" and event.action == "opt_out":
                return True, {
                    "status": "restricted",
                    "reason": "DSR global opt-out",
                    "restriction_type": "system_restriction",
                    "applied_at": event.timestamp.isoformat(),
                    "scope": event.scope or "all",
                    "restriction_id": event.id
                }
        
        # No restrictions found
        return False, {"status": "no_restrictions"}
    
    async def is_processing_allowed(
        self, 
        user_id: str, 
        data_scope: str, 
        purpose: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if data processing is allowed for the given user, scope, and purpose.
        
        Args:
            user_id: ID of the user whose data would be processed
            data_scope: Data category/scope being processed (e.g., "location")
            purpose: Purpose of the processing (e.g., "insight_generation")
            
        Returns:
            Tuple of (is_allowed, details) where:
                - is_allowed: Boolean indicating if processing is permitted
                - details: Dict with reason and relevant consent information
        """
        log.info(f"Validating consent for user {user_id}, scope '{data_scope}', purpose '{purpose}'")
        
        # First, check for DSR restrictions which override regular consent
        has_restrictions, restriction_details = await self.check_dsr_restrictions(user_id)
        if has_restrictions:
            log.warning(f"Processing disallowed due to DSR restriction for user {user_id}")
            return False, {
                "reason": "Processing restricted due to Data Subject Request",
                "dsr_details": restriction_details,
                "user_id": user_id
            }
        
        # Import inside method to avoid circular imports
        from app.services.consent_ledger import ConsentLedgerService
        
        # Get the consent ledger service
        consent_ledger_service = ConsentLedgerService(self.db)
        
        # Get user's consent history
        consent_history = await consent_ledger_service.get_user_history(user_id)
        
        if not consent_history:
            log.warning(f"No consent records found for user {user_id}")
            return False, {
                "reason": "No consent history found for user",
                "required_action": "opt_in",
                "user_id": user_id
            }
        
        # Get relevant consent events (matched by scope and purpose)
        # First check for exact scope matches
        scope_consent_events = [
            e for e in consent_history 
            if (e.scope == data_scope or e.scope == "all") and 
               (e.purpose == purpose or e.purpose == "all" or not e.purpose)
        ]
        
        # If no exact matches, look for consent events with null/empty scope
        # which might indicate global consent settings
        if not scope_consent_events:
            scope_consent_events = [
                e for e in consent_history
                if not e.scope and (e.purpose == purpose or e.purpose == "all" or not e.purpose)
            ]
        
        # Sort by timestamp (newest first)
        scope_consent_events.sort(key=lambda e: e.timestamp, reverse=True)
        
        # If there are no relevant consent events, permission is denied
        if not scope_consent_events:
            log.warning(f"No relevant consent found for user {user_id}, scope '{data_scope}', purpose '{purpose}'")
            return False, {
                "reason": f"No consent found for {data_scope} with purpose {purpose}",
                "required_action": "opt_in",
                "user_id": user_id,
                "scope": data_scope,
                "purpose": purpose
            }
        
        # Check the most recent relevant consent event
        latest_consent = scope_consent_events[0]
        
        # If the latest action is opt_out or withdraw, permission is denied
        if latest_consent.action in [ACTION_OPT_OUT, ACTION_WITHDRAW]:
            log.info(f"User {user_id} has revoked consent for {data_scope} (action: {latest_consent.action})")
            return False, {
                "reason": f"Consent revoked for {data_scope}",
                "required_action": "opt_in",
                "revoked_at": latest_consent.timestamp.isoformat(),
                "user_id": user_id,
                "scope": data_scope,
                "purpose": purpose,
                "consent_id": latest_consent.id
            }
        
        # If we've reached here, latest consent is opt_in or grant_partial
        log.info(f"Consent valid for user {user_id}, scope '{data_scope}', purpose '{purpose}'")
        return True, {
            "status": "allowed",
            "consent_id": latest_consent.id,
            "granted_at": latest_consent.timestamp.isoformat(),
            "user_id": user_id,
            "scope": data_scope,
            "purpose": purpose
        }
    
    async def get_active_consent_scopes(self, user_id: str) -> Dict[str, List[str]]:
        """
        Get all active consent scopes and purposes for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict mapping active scopes to lists of active purposes
        """
        log.info(f"Retrieving active consent scopes for user {user_id}")
        
        # Get the consent ledger service
        consent_ledger_service = ConsentLedgerService(self.db)
        
        # Get user's consent history
        consent_history = await consent_ledger_service.get_user_history(user_id)
        
        if not consent_history:
            log.warning(f"No consent records found for user {user_id}")
            return {}
        
        # Track active consents by scope and purpose
        # Structure: {scope: {purpose: latest_timestamp}}
        active_consents = {}
        
        # Process all events in chronological order
        for event in sorted(consent_history, key=lambda e: e.timestamp):
            scope = event.scope or "all"  # Default to "all" if scope is None
            purpose = event.purpose or "all"  # Default to "all" if purpose is None
            
            # Initialize scope entry if not exists
            if scope not in active_consents:
                active_consents[scope] = {}
            
            # Update purpose status based on action
            if event.action in [ACTION_OPT_IN, ACTION_GRANT_PARTIAL]:
                active_consents[scope][purpose] = event.timestamp
            elif event.action in [ACTION_OPT_OUT, ACTION_WITHDRAW]:
                # Remove purpose if it exists
                if purpose in active_consents[scope]:
                    del active_consents[scope][purpose]
                # If "all" purpose is withdrawn, remove all purposes
                elif purpose == "all":
                    active_consents[scope] = {}
                
                # If scope has no active purposes, remove it
                if not active_consents[scope]:
                    del active_consents[scope]
        
        # Convert timestamp values to purpose lists
        result = {scope: list(purposes.keys()) for scope, purposes in active_consents.items()}
        
        log.info(f"Active consent scopes for user {user_id}: {result}")
        return result
    
    async def validate_db_query(self, user_id: str, data_scope: str, purpose: str) -> bool:
        """
        Direct database query approach for validating consent status.
        More efficient for high-volume processing.
        
        Args:
            user_id: ID of the user
            data_scope: Data scope to check
            purpose: Processing purpose to check
            
        Returns:
            Boolean indicating if processing is allowed
        """
        # Find the latest relevant consent event for this user, scope, and purpose
        query = select(ConsentEvent).where(
            and_(
                ConsentEvent.user_id == user_id,
                or_(
                    # Match metadata.scope exactly
                    ConsentEvent.consent_metadata.contains({"scope": data_scope}),
                    # Match for 'all' scope
                    ConsentEvent.consent_metadata.contains({"scope": "all"}),
                    # Handle legacy events with no metadata by checking other fields
                    ConsentEvent.consent_metadata == None
                ),
                or_(
                    # Match metadata.purpose exactly
                    ConsentEvent.consent_metadata.contains({"purpose": purpose}),
                    # Match for 'all' purpose
                    ConsentEvent.consent_metadata.contains({"purpose": "all"}),
                    # Handle legacy events with no metadata
                    ConsentEvent.consent_metadata == None
                )
            )
        ).order_by(ConsentEvent.timestamp.desc()).limit(1)
        
        result = await self.db.execute(query)
        latest_event = result.scalar_one_or_none()
        
        if not latest_event:
            log.warning(f"No consent record found for user {user_id}, scope {data_scope}, purpose {purpose}")
            return False
        
        # Check if the latest action permits processing
        if latest_event.action in [ACTION_OPT_IN, ACTION_GRANT_PARTIAL]:
            return True
        
        return False

async def get_consent_validator(db = Depends(get_db)) -> ConsentValidator:
    """Dependency injection for the consent validator."""
    return ConsentValidator(db) 