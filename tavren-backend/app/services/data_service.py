"""
Data Service for coordinating data operations across packaging, consent, and buyers.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import ConsentEvent
from app.services.data_packaging import DataPackagingService, get_data_packaging_service
from app.services.trust_service import TrustService
from app.database import get_db

# Set up logging
log = logging.getLogger("app")

class DataService:
    """
    Central service that coordinates data operations across the platform.
    Handles the workflow for preparing and delivering data to buyers
    based on consent permissions and trust tiers.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.data_packaging_service = DataPackagingService(db)
        self.trust_service = TrustService(db)
    
    async def prepare_data_for_buyer(
        self, 
        user_id: str, 
        buyer_id: str, 
        offer_id: str, 
        data_type: str,
        purpose: str
    ) -> Dict[str, Any]:
        """
        Main workflow for preparing user data for a buyer.
        
        Args:
            user_id: ID of the user whose data is being requested
            buyer_id: ID of the data buyer
            offer_id: ID of the specific offer that was accepted
            data_type: Type of data being requested (e.g., "app_usage", "location")
            purpose: Purpose for data use
        
        Returns:
            Data package with appropriate anonymization and security
        
        Raises:
            HTTPException: If consent is not valid or other errors occur
        """
        try:
            log.info(f"Preparing {data_type} data for user {user_id} for buyer {buyer_id}")
            
            # 1. Verify active consent for this offer
            consent_id = await self._verify_active_consent(user_id, offer_id)
            if not consent_id:
                log.warning(f"No active consent found for user {user_id} and offer {offer_id}")
                raise HTTPException(
                    status_code=403, 
                    detail="No active consent found for this offer"
                )
            
            # 2. Get buyer trust tier
            buyer_trust_tier = await self._get_buyer_trust_tier(buyer_id)
            
            # 3. Determine appropriate access level based on offer and trust tier
            access_level = await self._determine_access_level(offer_id, buyer_trust_tier)
            
            # 4. Package data with appropriate anonymization
            data_package = await self.data_packaging_service.package_data(
                user_id=user_id,
                data_type=data_type,
                access_level=access_level,
                consent_id=consent_id,
                purpose=purpose,
                buyer_id=buyer_id,
                trust_tier=buyer_trust_tier
            )
            
            # 5. Trigger reward creation (would be implemented elsewhere)
            await self._trigger_reward(user_id, buyer_id, offer_id, data_package["package_id"])
            
            log.info(f"Successfully prepared data package {data_package['package_id']}")
            return data_package
            
        except HTTPException:
            raise
        except Exception as e:
            log.error(f"Error preparing data for buyer: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error preparing data: {str(e)}"
            )
    
    async def _verify_active_consent(self, user_id: str, offer_id: str) -> Optional[str]:
        """
        Verify that the user has active consent for the specified offer.
        
        Returns:
            Consent ID if valid consent exists, None otherwise
        """
        # Query for an accepted consent event for this user and offer
        stmt = select(ConsentEvent).where(
            ConsentEvent.user_id == user_id,
            ConsentEvent.offer_id == offer_id,
            ConsentEvent.action == "accepted"
        ).order_by(ConsentEvent.timestamp.desc())
        
        result = await self.db.execute(stmt)
        consent_record = result.scalar_one_or_none()
        
        if consent_record:
            return str(consent_record.id)
        return None
    
    async def _get_buyer_trust_tier(self, buyer_id: str) -> str:
        """
        Get the trust tier for a buyer based on their trust score.
        
        Returns:
            Trust tier ("low", "standard", or "high")
        """
        try:
            # Get trust score from trust service
            buyer_access = await self.trust_service.get_buyer_access_level(buyer_id)
            trust_score = buyer_access.trust_score
            
            # Determine tier based on trust score
            # This logic could be moved to the TrustService
            if trust_score < 0.3:
                return "low"
            elif trust_score > 0.7:
                return "high"
            else:
                return "standard"
        except Exception as e:
            log.warning(f"Error getting buyer trust tier: {str(e)}")
            # Default to standard tier if there's an error
            return "standard"
    
    async def _determine_access_level(self, offer_id: str, trust_tier: str) -> str:
        """
        Determine the appropriate access level based on the offer and trust tier.
        
        In a real implementation, this would examine the offer details.
        For this POC, we'll use a simple mapping.
        
        Returns:
            Access level string (e.g., "anonymous_short_term")
        """
        # Placeholder - in a real implementation, we would:
        # 1. Fetch the offer details from a database
        # 2. Extract the requested access level from the offer
        # 3. Potentially adjust based on trust tier
        
        # For now, use a simple mapping based on offer_id
        offer_num = int(offer_id.split("-")[-1]) if offer_id.split("-")[-1].isdigit() else 0
        
        # Map to different access levels based on offer number
        access_levels = [
            "precise_persistent",
            "precise_short_term",
            "anonymous_persistent",
            "anonymous_short_term"
        ]
        
        base_level = access_levels[offer_num % len(access_levels)]
        
        # Adjust based on trust tier - reduce access for low trust buyers
        if trust_tier == "low" and "precise" in base_level:
            # Downgrade precise to anonymous but keep persistence
            return base_level.replace("precise", "anonymous")
            
        return base_level
    
    async def _trigger_reward(self, user_id: str, buyer_id: str, offer_id: str, package_id: str) -> None:
        """
        Trigger reward creation for a successful data package delivery.
        
        In a real implementation, this would create a reward in the database
        and potentially notify the user.
        """
        # Placeholder - would integrate with reward service
        log.info(f"Would create reward for user {user_id} for data package {package_id}")
        # In a real implementation:
        # await reward_service.create_reward(user_id, offer_id, amount)
        pass

async def get_data_service(db: AsyncSession) -> DataService:
    """Dependency for getting the data service."""
    return DataService(db) 