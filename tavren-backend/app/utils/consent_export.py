import logging
import json
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from fastapi import Depends
import time
from uuid import uuid4
from pathlib import Path
import os
import hmac

from app.models import ConsentEvent, DSRActionLog, InsightQueryLog
from app.services.consent_ledger import ConsentLedgerService, get_consent_ledger_service
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.dsr import DSRAction
from app.utils.crypto import load_private_key, sign_data
from app.models.consent import ConsentRecord
from app.models.insight import InsightRequest
from app.models.dsr import DSRRequest

# Get logger
log = logging.getLogger("app")

class ConsentExportService:
    """
    Utility class to generate verifiable exports of user consent and processing history.
    
    Provides functions to:
    - Collect all consent events for a user
    - Gather DSR action history
    - Include PET insight query logs
    - Create a cryptographically signed export package
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self._private_key = None  # Lazy-loaded signing key
        self.export_dir = Path(settings.EXPORT_STORAGE_PATH) if hasattr(settings, "EXPORT_STORAGE_PATH") else None
        self.hmac_key = settings.EXPORT_HMAC_KEY.encode() if settings.EXPORT_HMAC_KEY else b"tavren-export-verification-key"
        
        # Ensure export directory exists if configured
        if self.export_dir:
            self.export_dir.mkdir(parents=True, exist_ok=True)
        
    async def _get_user(self, user_id: str) -> Optional[User]:
        """Get user record by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def _get_consent_events(self, user_id: str) -> List[ConsentEvent]:
        """Get all consent events for a user."""
        result = await self.db.execute(
            select(ConsentEvent).where(ConsentEvent.user_id == user_id)
            .order_by(ConsentEvent.timestamp.asc())
        )
        return result.scalars().all()

    async def _get_dsr_actions(self, user_id: str) -> List[DSRAction]:
        """Get all DSR actions for a user."""
        result = await self.db.execute(
            select(DSRAction).where(DSRAction.user_id == user_id)
            .order_by(DSRAction.timestamp.asc())
        )
        return result.scalars().all()

    async def _get_pet_queries(self, user_id: str) -> List[Dict]:
        """
        Get privacy-enhancing technology queries related to the user.
        This is a placeholder - actual implementation would depend on how
        PET queries are tracked in the database.
        """
        # Placeholder - replace with actual query logic
        return []

    def _load_signing_key(self) -> bool:
        """Load the private signing key."""
        if not hasattr(settings, "EXPORT_SIGNING_KEY_PATH"):
            log.warning("No export signing key configured, exports won't be signed")
            return False
            
        try:
            self._private_key = load_private_key(settings.EXPORT_SIGNING_KEY_PATH)
            return True
        except Exception as e:
            log.error(f"Failed to load export signing key: {e}")
            return False

    def _calculate_hash(self, data: Dict) -> str:
        """Calculate a SHA-256 hash of the export data."""
        serialized = json.dumps(data, sort_keys=True)
        return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

    def _sign_export(self, export_hash: str) -> str:
        """Sign the export hash using HMAC-SHA256."""
        signature = hmac.new(
            self.hmac_key,
            export_hash.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()

    def _generate_consent_summary(self, events: List[ConsentEvent]) -> Dict:
        """Generate a summary of consent status and history."""
        if not events:
            return {
                "active_consents": [],
                "consent_history": {
                    "granted": 0,
                    "withdrawn": 0,
                    "expired": 0
                },
                "first_consent": None,
                "last_update": None
            }
            
        # Track current consent status by purpose
        active_consents = {}
        consent_counts = {"granted": 0, "withdrawn": 0, "expired": 0}
        
        first_timestamp = events[0].timestamp
        last_timestamp = events[0].timestamp
        
        for event in events:
            last_timestamp = max(last_timestamp, event.timestamp)
            
            if event.event_type == "consent_granted":
                consent_counts["granted"] += 1
                active_consents[event.purpose] = {
                    "granted_at": event.timestamp.isoformat(),
                    "expires_at": event.expiry.isoformat() if event.expiry else None
                }
            elif event.event_type == "consent_withdrawn":
                consent_counts["withdrawn"] += 1
                if event.purpose in active_consents:
                    del active_consents[event.purpose]
            elif event.event_type == "consent_expired":
                consent_counts["expired"] += 1
                if event.purpose in active_consents:
                    del active_consents[event.purpose]
                    
        return {
            "active_consents": [
                {"purpose": purpose, **details}
                for purpose, details in active_consents.items()
            ],
            "consent_history": consent_counts,
            "first_consent": first_timestamp.isoformat(),
            "last_update": last_timestamp.isoformat()
        }

    def _format_events(self, events: List[ConsentEvent]) -> List[Dict]:
        """Format consent events for the export."""
        return [
            {
                "event_id": event.id,
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "purpose": event.purpose,
                "source": event.source,
                "expiry": event.expiry.isoformat() if event.expiry else None,
                "metadata": event.metadata
            }
            for event in events
        ]

    def _format_dsr_actions(self, actions: List[DSRAction]) -> List[Dict]:
        """Format DSR actions for the export."""
        return [
            {
                "action_id": action.id,
                "timestamp": action.timestamp.isoformat(),
                "action_type": action.action_type,
                "status": action.status,
                "request_id": action.request_id,
                "metadata": action.metadata
            }
            for action in actions
        ]

    async def generate_export_package(
        self, 
        user_id: str, 
        include_pet_queries: bool = False,
        sign_export: bool = True
    ) -> Dict:
        """
        Generate a comprehensive, verifiable export package for a user.
        
        Parameters:
        -----------
        user_id : str
            ID of the user whose data should be exported
        include_pet_queries : bool
            Whether to include privacy-enhancing technology query logs
        sign_export : bool
            Whether to digitally sign the export
            
        Returns:
        --------
        Dict containing the export data with verification hash
        """
        start_time = time.time()
        log.info(f"Generating consent export for user {user_id}")
        
        # Get user data
        user = await self._get_user(user_id)
        if not user:
            log.warning(f"User {user_id} not found")
            return {"error": "User not found"}
        
        # Get consent events
        consent_events = await self._get_consent_events(user_id)
        log.debug(f"Retrieved {len(consent_events)} consent events")
        
        # Get DSR actions
        dsr_actions = await self._get_dsr_actions(user_id)
        log.debug(f"Retrieved {len(dsr_actions)} DSR actions")
        
        # Get PET queries if requested
        pet_queries = []
        if include_pet_queries:
            pet_queries = await self._get_pet_queries(user_id)
            log.debug(f"Retrieved {len(pet_queries)} PET queries")
        
        # Generate consent summary
        consent_summary = self._generate_consent_summary(consent_events)
        
        # Prepare export data
        export_data = {
            "export_id": str(uuid4()),
            "export_timestamp": datetime.datetime.utcnow().isoformat(),
            "export_version": "1.0",
            "user_id": user_id,
            "user_details": {
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            },
            "consent_summary": consent_summary,
            "consent_events": self._format_events(consent_events),
            "dsr_actions": self._format_dsr_actions(dsr_actions),
        }
        
        if include_pet_queries:
            export_data["pet_queries"] = pet_queries
        
        # Calculate export hash for verification
        export_data["export_hash"] = self._calculate_hash(export_data)
        
        # Sign export if requested
        if sign_export:
            signature = self._sign_export(export_data["export_hash"])
            if signature:
                export_data["signature"] = signature
                log.debug(f"Export signed successfully")
        
        processing_time = time.time() - start_time
        export_data["metadata"] = {
            "processing_time_seconds": round(processing_time, 3),
            "record_counts": {
                "consent_events": len(consent_events),
                "dsr_actions": len(dsr_actions),
                "pet_queries": len(pet_queries) if include_pet_queries else 0
            }
        }
        
        log.info(f"Export generated for user {user_id} in {processing_time:.2f}s")
        return export_data
        
    async def save_export_file(self, export_data: Dict) -> Optional[str]:
        """
        Save export to a file and return the filename.
        """
        if not self.export_dir:
            log.warning("Export storage path not configured, file not saved")
            return None
            
        try:
            export_id = export_data.get("export_id", str(uuid4()))
            user_id = export_data.get("user_id", "unknown")
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            
            filename = f"{user_id}_export_{timestamp}_{export_id[:8]}.json"
            filepath = self.export_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            log.info(f"Export saved to {filepath}")
            return str(filepath)
        except Exception as e:
            log.error(f"Failed to save export file: {e}")
            return None

    async def calculate_export_hash(self, export_data: Dict[str, Any]) -> str:
        """Calculate a hash of the export data for verification."""
        # Create a deterministic JSON representation (sorted keys)
        serialized_data = json.dumps(export_data, sort_keys=True)
        # Calculate SHA-256 hash
        hash_obj = hashlib.sha256(serialized_data.encode())
        return hash_obj.hexdigest()

    async def verify_export_signature(self, export_data: Dict[str, Any]) -> bool:
        """Verify the digital signature of an export package."""
        if "hash" not in export_data or "signature" not in export_data:
            return False
        
        export_hash = export_data["hash"]
        provided_signature = export_data["signature"]
        
        # Calculate expected signature
        expected_signature = self._sign_export(export_hash)
        return hmac.compare_digest(provided_signature, expected_signature)

async def get_consent_export(db = Depends(get_db)) -> ConsentExportService:
    """Dependency injection for the consent export utility."""
    return ConsentExportService(db) 