import logging
import json
import io
import zipfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, BinaryIO
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConsentEvent, Reward, PayoutRequest, User
from app.services.consent_ledger import ConsentLedgerService, get_consent_ledger_service
from app.utils.consent_validator import ACTION_OPT_OUT

# Get logger
log = logging.getLogger("app")

# DSR action types
DSR_ACTION_EXPORT = "data_export"
DSR_ACTION_DELETE = "data_deletion"
DSR_ACTION_RESTRICT = "processing_restriction"

class DSRService:
    """
    Service for handling Data Subject Requests (DSRs).
    
    Provides functionality to:
    - Generate data exports for users
    - Delete user data
    - Restrict data processing for users
    
    All actions are logged to the consent ledger for audit purposes.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_data_export(self, user_id: str, include_consent: bool = True,
                                  include_rewards: bool = True, include_payouts: bool = True,
                                  format: str = "json") -> Tuple[BinaryIO, str]:
        """
        Generate a comprehensive export of all user data.
        
        Args:
            user_id: ID of the user requesting their data
            include_consent: Whether to include consent history
            include_rewards: Whether to include reward history
            include_payouts: Whether to include payout history
            format: Output format ("json" or "zip")
            
        Returns:
            Tuple of (file-like object, content_type)
        """
        log.info(f"Generating data export for user {user_id}, format: {format}")
        
        # Initialize the data dictionary
        export_data = {
            "user_id": user_id,
            "export_date": datetime.now().isoformat(),
            "data_categories": []
        }
        
        # Get user profile if it exists
        user_profile = await self._get_user_profile(user_id)
        if user_profile:
            export_data["user_profile"] = user_profile
            export_data["data_categories"].append("user_profile")
        
        # Get consent history if requested
        if include_consent:
            consent_history = await self._get_consent_history(user_id)
            if consent_history:
                export_data["consent_history"] = consent_history
                export_data["data_categories"].append("consent_history")
        
        # Get rewards history if requested
        if include_rewards:
            rewards_history = await self._get_rewards_history(user_id)
            if rewards_history:
                export_data["rewards_history"] = rewards_history
                export_data["data_categories"].append("rewards_history")
        
        # Get payout history if requested
        if include_payouts:
            payout_history = await self._get_payout_history(user_id)
            if payout_history:
                export_data["payout_history"] = payout_history
                export_data["data_categories"].append("payout_history")
        
        # Log this export request in the consent ledger
        await self._log_dsr_action(user_id, DSR_ACTION_EXPORT)
        
        # Return the data in the requested format
        if format == "json":
            file_obj = io.StringIO()
            json.dump(export_data, file_obj, indent=2)
            file_obj.seek(0)
            content_type = "application/json"
            return file_obj, content_type
        else:  # zip format
            file_obj = io.BytesIO()
            with zipfile.ZipFile(file_obj, 'w') as zip_file:
                # Add the main JSON file
                zip_file.writestr('user_data.json', json.dumps(export_data, indent=2))
                
                # Add a README
                readme_content = f"""# Data Export for User {user_id}
                
This archive contains all personal data associated with your Tavren account.
Export generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contents
- user_data.json: Main data file containing all your personal information

For questions regarding this data, please contact privacy@tavren.com
"""
                zip_file.writestr('README.md', readme_content)
            
            file_obj.seek(0)
            content_type = "application/zip"
            return file_obj, content_type
    
    async def delete_user_data(self, user_id: str, delete_profile: bool = True,
                             delete_consent: bool = False) -> Dict[str, Any]:
        """
        Delete user data from the system.
        
        Args:
            user_id: ID of the user whose data should be deleted
            delete_profile: Whether to delete the user profile
            delete_consent: Whether to delete consent records (normally preserved for audit)
            
        Returns:
            Dict with deletion results
        """
        log.info(f"Processing data deletion request for user {user_id}")
        
        deletion_results = {
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "deleted_categories": [],
            "preserved_categories": []
        }
        
        # Delete user profile if requested
        if delete_profile:
            profile_deleted = await self._delete_user_profile(user_id)
            if profile_deleted:
                deletion_results["deleted_categories"].append("user_profile")
            else:
                deletion_results["preserved_categories"].append("user_profile")
        else:
            deletion_results["preserved_categories"].append("user_profile")
        
        # Always delete rewards data (no longer needed after payment)
        rewards_deleted = await self._delete_rewards_data(user_id)
        if rewards_deleted:
            deletion_results["deleted_categories"].append("rewards_history")
        
        # Delete consent history if explicitly requested (normally preserved for audit)
        if delete_consent:
            consent_deleted = await self._delete_consent_history(user_id)
            if consent_deleted:
                deletion_results["deleted_categories"].append("consent_history")
        else:
            deletion_results["preserved_categories"].append("consent_history")
        
        # Preserve payout history for financial records
        deletion_results["preserved_categories"].append("payout_history")
        
        # Log this deletion request in the consent ledger
        await self._log_dsr_action(user_id, DSR_ACTION_DELETE)
        
        return deletion_results
    
    async def restrict_user_processing(self, user_id: str, restriction_scope: str = "all",
                                    restriction_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Restrict future data processing for a user.
        
        This creates a global opt-out record that prevents all future data processing.
        
        Args:
            user_id: ID of the user to restrict processing for
            restriction_scope: Scope of the restriction (default "all")
            restriction_reason: Optional reason for the restriction
            
        Returns:
            Dict with restriction details
        """
        log.info(f"Processing data processing restriction request for user {user_id}")
        
        # Get the consent ledger service
        consent_ledger_service = ConsentLedgerService(self.db)
        
        # Record an opt-out event with scope "all" and purpose "all"
        opt_out_event = {
            "user_id": user_id,
            "offer_id": "system_restriction",  # Special ID for system-initiated restrictions
            "action": ACTION_OPT_OUT,
            "scope": restriction_scope,
            "purpose": "all",
            "initiated_by": "user_dsr",
            "metadata": {
                "dsr_type": DSR_ACTION_RESTRICT,
                "restriction_reason": restriction_reason,
                "restriction_date": datetime.now().isoformat()
            }
        }
        
        # Create the event in the consent ledger
        from app.schemas import ConsentEventCreate
        consent_event = ConsentEventCreate(**opt_out_event)
        event_response = await consent_ledger_service.record_event(consent_event)
        
        # Log this restriction request in the DSR audit trail
        await self._log_dsr_action(user_id, DSR_ACTION_RESTRICT)
        
        return {
            "user_id": user_id,
            "restriction_applied": True,
            "restriction_scope": restriction_scope,
            "timestamp": datetime.now().isoformat(),
            "consent_event_id": event_response.id
        }
    
    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data."""
        query = select(User).where(User.username == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Return profile data (excluding sensitive fields like password)
        return {
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
    
    async def _get_consent_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's consent history."""
        # Get the consent ledger service
        consent_ledger_service = ConsentLedgerService(self.db)
        consent_history = await consent_ledger_service.get_user_history(user_id)
        
        # Convert to serializable format
        return [
            {
                "id": event.id,
                "action": event.action,
                "timestamp": event.timestamp.isoformat(),
                "scope": event.scope,
                "purpose": event.purpose,
                "verification_hash": event.verification_hash
            }
            for event in consent_history
        ]
    
    async def _get_rewards_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's reward history."""
        query = select(Reward).where(Reward.user_id == user_id).order_by(Reward.timestamp)
        result = await self.db.execute(query)
        rewards = result.scalars().all()
        
        return [
            {
                "id": reward.id,
                "offer_id": reward.offer_id,
                "amount": reward.amount,
                "timestamp": reward.timestamp.isoformat()
            }
            for reward in rewards
        ]
    
    async def _get_payout_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's payout history."""
        query = select(PayoutRequest).where(PayoutRequest.user_id == user_id).order_by(PayoutRequest.timestamp)
        result = await self.db.execute(query)
        payouts = result.scalars().all()
        
        return [
            {
                "id": payout.id,
                "amount": payout.amount,
                "status": payout.status,
                "requested_at": payout.timestamp.isoformat(),
                "paid_at": payout.paid_at.isoformat() if payout.paid_at else None
            }
            for payout in payouts
        ]
    
    async def _delete_user_profile(self, user_id: str) -> bool:
        """Delete user profile."""
        try:
            # Find user by username
            query = select(User).where(User.username == user_id)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()
            
            if not user:
                return False
            
            # Delete the user
            stmt = delete(User).where(User.id == user.id)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            log.error(f"Error deleting user profile: {str(e)}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def _delete_rewards_data(self, user_id: str) -> bool:
        """Delete user's reward data."""
        try:
            stmt = delete(Reward).where(Reward.user_id == user_id)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            log.error(f"Error deleting rewards data: {str(e)}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def _delete_consent_history(self, user_id: str) -> bool:
        """Delete user's consent history (normally preserved for audit)."""
        try:
            stmt = delete(ConsentEvent).where(ConsentEvent.user_id == user_id)
            await self.db.execute(stmt)
            await self.db.commit()
            return True
        except Exception as e:
            log.error(f"Error deleting consent history: {str(e)}", exc_info=True)
            await self.db.rollback()
            return False
    
    async def _log_dsr_action(self, user_id: str, action_type: str) -> None:
        """Log a DSR action to the consent ledger for audit purposes."""
        # Get the consent ledger service
        consent_ledger_service = ConsentLedgerService(self.db)
        
        # Create an audit event for the DSR action
        from app.schemas import ConsentEventCreate
        
        audit_event = ConsentEventCreate(
            user_id=user_id,
            offer_id="dsr_audit",  # Special ID for DSR-related actions
            action="dsr_request",
            scope="user_data",
            purpose="regulatory_compliance",
            initiated_by="user_dsr",
            metadata={
                "dsr_type": action_type,
                "request_timestamp": datetime.now().isoformat()
            }
        )
        
        # Record the event in the consent ledger
        await consent_ledger_service.record_event(audit_event)

async def get_dsr_service(db: AsyncSession) -> DSRService:
    """Dependency injection for the DSR service."""
    return DSRService(db) 