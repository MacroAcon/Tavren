import json
import hashlib
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import ConsentEvent
from app.schemas import ConsentEventCreate, ConsentEventResponse
from app.config import get_settings
from app.utils.db_utils import safe_commit

# Get logger
log = logging.getLogger("app")
settings = get_settings()

class ConsentLedgerService:
    """
    Service for recording and verifying consent events in a tamper-evident ledger.
    
    Provides functionality to:
    - Record consent events (opt-in, opt-out, withdraw, modifications)
    - Retrieve consent history for a specific user
    - Export the full ledger for auditing
    - Verify the integrity of the ledger through hash chaining
    
    The ledger is designed to be append-only with each entry linked to previous
    entries through cryptographic hashing to ensure tamper-resistance.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_path = os.path.join(settings.DATA_DIR, "consent_ledger.jsonl")
        self._ensure_storage_exists()
    
    async def record_event(self, event: ConsentEventCreate) -> ConsentEventResponse:
        """
        Records a new consent event in the ledger with hash chaining for tamper evidence.
        
        Args:
            event: The consent event to record
            
        Returns:
            The recorded event with its assigned ID and verification hash
        """
        log.info(f"Recording consent event: {event.action} for user {event.user_id}")
        
        try:
            # Get the hash of the previous event for chaining
            prev_hash = await self._get_latest_hash(event.user_id)
            
            # Create a new database event
            db_event = ConsentEvent(
                user_id=event.user_id,
                offer_id=event.offer_id if hasattr(event, 'offer_id') else None,
                action=event.action,
                timestamp=datetime.now(),
                user_reason=event.user_reason if hasattr(event, 'user_reason') else None,
                reason_category=event.reason_category if hasattr(event, 'reason_category') else None,
                metadata=event.metadata if hasattr(event, 'metadata') else None
            )
            
            # Add to database
            self.db.add(db_event)
            await safe_commit(self.db)
            await self.db.refresh(db_event)
            
            # Generate verification hash that includes the previous hash for chaining
            verification_hash = self._generate_hash(
                str(db_event.id),
                db_event.user_id,
                db_event.action,
                db_event.timestamp.isoformat(),
                prev_hash
            )
            
            # Write to file storage (append-only for additional security)
            event_record = {
                "id": db_event.id,
                "user_id": db_event.user_id,
                "action": db_event.action,
                "timestamp": db_event.timestamp.isoformat(),
                "offer_id": db_event.offer_id,
                "scope": event.scope if hasattr(event, 'scope') else None,
                "purpose": event.purpose if hasattr(event, 'purpose') else None,
                "initiated_by": event.initiated_by if hasattr(event, 'initiated_by') else "user",
                "reason": db_event.user_reason,
                "reason_category": db_event.reason_category,
                "metadata": db_event.metadata,
                "prev_hash": prev_hash,
                "hash": verification_hash
            }
            
            # Append to file storage
            with open(self.file_path, 'a') as f:
                f.write(json.dumps(event_record) + '\n')
            
            response = ConsentEventResponse(
                id=db_event.id,
                user_id=db_event.user_id,
                action=db_event.action,
                timestamp=db_event.timestamp,
                verification_hash=verification_hash,
                prev_hash=prev_hash,
                offer_id=db_event.offer_id,
                scope=event.scope if hasattr(event, 'scope') else None,
                purpose=event.purpose if hasattr(event, 'purpose') else None,
                initiated_by=event.initiated_by if hasattr(event, 'initiated_by') else "user",
            )
            
            log.info(f"Consent event {db_event.id} recorded successfully with hash {verification_hash[:8]}...")
            return response
        
        except Exception as e:
            log.error(f"Error recording consent event: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to record consent event: {str(e)}")
    
    async def get_user_history(self, user_id: str) -> List[ConsentEventResponse]:
        """
        Retrieves the complete consent history for a specific user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of consent events for the user in chronological order
        """
        log.info(f"Retrieving consent history for user {user_id}")
        
        try:
            # Query the database for user's consent events
            stmt = select(ConsentEvent).where(
                ConsentEvent.user_id == user_id
            ).order_by(ConsentEvent.timestamp)
            
            result = await self.db.execute(stmt)
            db_events = result.scalars().all()
            
            # Read the file ledger to get hash information
            file_events = self._read_user_ledger_events(user_id)
            
            # Map file events by database ID for easy lookup
            file_events_by_id = {str(event.get('id')): event for event in file_events}
            
            # Combine database and file data
            events = []
            for db_event in db_events:
                file_event = file_events_by_id.get(str(db_event.id), {})
                
                events.append(ConsentEventResponse(
                    id=db_event.id,
                    user_id=db_event.user_id,
                    action=db_event.action,
                    timestamp=db_event.timestamp,
                    verification_hash=file_event.get('hash'),
                    prev_hash=file_event.get('prev_hash'),
                    offer_id=db_event.offer_id,
                    scope=file_event.get('scope'),
                    purpose=file_event.get('purpose'),
                    initiated_by=file_event.get('initiated_by', 'user'),
                ))
            
            log.info(f"Found {len(events)} consent events for user {user_id}")
            return events
        
        except Exception as e:
            log.error(f"Error retrieving consent history: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to retrieve consent history: {str(e)}")
    
    async def export_ledger(self, start_date: Optional[datetime] = None, 
                           end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Exports the full consent ledger, optionally filtered by date range.
        
        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of all consent events in the ledger
        """
        log.info("Exporting consent ledger")
        
        try:
            # Read all events from the file ledger
            events = self._read_all_ledger_events()
            
            # Apply date filtering if specified
            if start_date or end_date:
                filtered_events = []
                for event in events:
                    event_date = datetime.fromisoformat(event['timestamp'])
                    
                    if start_date and event_date < start_date:
                        continue
                    
                    if end_date and event_date > end_date:
                        continue
                    
                    filtered_events.append(event)
                
                events = filtered_events
            
            log.info(f"Exported {len(events)} consent events from ledger")
            return events
        
        except Exception as e:
            log.error(f"Error exporting consent ledger: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to export consent ledger: {str(e)}")
    
    async def verify_ledger_integrity(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Verifies the integrity of the consent ledger by checking the hash chain.
        
        Args:
            user_id: Optional user ID to verify only that user's events
            
        Returns:
            Verification result with details of any inconsistencies
        """
        log.info(f"Verifying consent ledger integrity for {user_id if user_id else 'all users'}")
        
        try:
            # Read events to verify
            events = self._read_user_ledger_events(user_id) if user_id else self._read_all_ledger_events()
            
            # Sort events by user and timestamp for proper verification
            events.sort(key=lambda e: (e['user_id'], e['timestamp']))
            
            # Group events by user
            user_events = {}
            for event in events:
                user_id = event['user_id']
                if user_id not in user_events:
                    user_events[user_id] = []
                user_events[user_id].append(event)
            
            # Verify each user's chain
            results = {
                "verified": True,
                "users_checked": len(user_events),
                "events_checked": len(events),
                "inconsistencies": []
            }
            
            for user_id, user_events in user_events.items():
                prev_hash = None
                
                for i, event in enumerate(user_events):
                    # First event should have null or empty prev_hash
                    if i == 0:
                        if event['prev_hash'] not in (None, "", "0"):
                            results["verified"] = False
                            results["inconsistencies"].append({
                                "user_id": user_id,
                                "event_id": event['id'],
                                "issue": "First event has non-null prev_hash",
                                "expected": None,
                                "found": event['prev_hash']
                            })
                    else:
                        # Check that prev_hash matches the hash of the previous event
                        if event['prev_hash'] != prev_hash:
                            results["verified"] = False
                            results["inconsistencies"].append({
                                "user_id": user_id,
                                "event_id": event['id'],
                                "issue": "Hash chain broken",
                                "expected": prev_hash,
                                "found": event['prev_hash']
                            })
                    
                    # Verify current event's hash
                    expected_hash = self._generate_hash(
                        str(event['id']),
                        event['user_id'],
                        event['action'],
                        event['timestamp'],
                        event['prev_hash']
                    )
                    
                    if event['hash'] != expected_hash:
                        results["verified"] = False
                        results["inconsistencies"].append({
                            "user_id": user_id,
                            "event_id": event['id'],
                            "issue": "Event hash mismatch",
                            "expected": expected_hash,
                            "found": event['hash']
                        })
                    
                    # Update prev_hash for next iteration
                    prev_hash = event['hash']
            
            log.info(f"Ledger verification completed: integrity {'maintained' if results['verified'] else 'compromised'}")
            return results
        
        except Exception as e:
            log.error(f"Error verifying consent ledger: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to verify consent ledger: {str(e)}")
    
    def _ensure_storage_exists(self) -> None:
        """Ensures the data directory and ledger file exist"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                pass  # Create empty file
    
    async def _get_latest_hash(self, user_id: str) -> str:
        """
        Gets the hash of the most recent event for a user to use in hash chaining.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            The hash of the latest event or "0" if no previous events
        """
        # Read from file for better performance than DB query
        events = self._read_user_ledger_events(user_id)
        
        if not events:
            return "0"  # Initial hash for first event
        
        # Sort by timestamp and get the most recent
        events.sort(key=lambda e: e['timestamp'], reverse=True)
        return events[0]['hash']
    
    def _generate_hash(self, event_id: str, user_id: str, action: str, 
                      timestamp: str, prev_hash: str) -> str:
        """
        Generates a verification hash for a consent event.
        
        Args:
            event_id: The ID of the event
            user_id: The ID of the user
            action: The consent action
            timestamp: The timestamp of the event
            prev_hash: The hash of the previous event
            
        Returns:
            A SHA-256 hash of the event data
        """
        # Normalize inputs by converting them to strings and concatenating
        data = f"{event_id}:{user_id}:{action}:{timestamp}:{prev_hash}"
        
        # Generate SHA-256 hash
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _read_user_ledger_events(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Reads all events for a specific user from the file ledger.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of events for the user
        """
        events = []
        
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    event = json.loads(line)
                    if event['user_id'] == user_id:
                        events.append(event)
        except FileNotFoundError:
            # File doesn't exist yet, return empty list
            pass
        
        return events
    
    def _read_all_ledger_events(self) -> List[Dict[str, Any]]:
        """
        Reads all events from the file ledger.
        
        Returns:
            List of all events in the ledger
        """
        events = []
        
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    events.append(json.loads(line))
        except FileNotFoundError:
            # File doesn't exist yet, return empty list
            pass
        
        return events

async def get_consent_ledger_service(db: AsyncSession) -> ConsentLedgerService:
    """Dependency for getting consent ledger service instance"""
    return ConsentLedgerService(db) 