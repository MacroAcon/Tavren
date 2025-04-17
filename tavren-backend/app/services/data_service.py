"""
Data Service for coordinating data operations across packaging, consent, and buyers.
"""
import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Annotated
from fastapi import HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

# Use TYPE_CHECKING for AsyncSession to avoid circular imports at runtime
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession 

from app.models import ConsentEvent
from app.services.data_packaging import DataPackagingService, get_data_packaging_service
from app.services.trust_service import TrustService
from app.database import get_db
from app.core.logging import log
from app.schemas import DataPackageRequest, DataPackageResponse, DataSchemaInfo

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

    async def create_data_package(self, request: DataPackageRequest) -> DataPackageResponse:
        """Create a new data package"""
        try:
            # Validate schema exists
            schema = await self._get_schema(request.schema_name)
            if not schema:
                raise ValueError(f"Schema {request.schema_name} not found")

            # Create package
            package_id = await self._generate_package_id()
            data = await self._fetch_data(schema, request.filters)
            
            return DataPackageResponse(
                package_id=package_id,
                schema_name=request.schema_name,
                data=data,
                created_at=datetime.utcnow().isoformat()
            )
        except Exception as e:
            log.error(f"Error creating data package: {str(e)}")
            raise

    async def get_data_package(self, package_id: str) -> DataPackageResponse:
        """Retrieve a data package by ID"""
        try:
            # Fetch package from storage
            package = await self._fetch_package(package_id)
            if not package:
                raise ValueError(f"Package {package_id} not found")
            
            return package
        except Exception as e:
            log.error(f"Error retrieving data package {package_id}: {str(e)}")
            raise

    async def get_available_schemas(self) -> List[DataSchemaInfo]:
        """Get list of available data schemas"""
        try:
            schemas = await self._fetch_schemas()
            return [
                DataSchemaInfo(
                    name=schema["name"],
                    description=schema["description"],
                    fields=schema["fields"]
                )
                for schema in schemas
            ]
        except Exception as e:
            log.error(f"Error retrieving schemas: {str(e)}")
            raise

    async def _get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """Get schema definition"""
        # Implementation would fetch from database or config
        pass

    async def _generate_package_id(self) -> str:
        """Generate a unique package ID"""
        # Implementation would generate a unique ID
        pass

    async def _fetch_data(self, schema: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Fetch data according to schema and filters"""
        # Implementation would fetch and transform data
        pass

    async def _fetch_package(self, package_id: str) -> Optional[DataPackageResponse]:
        """Fetch package from storage"""
        # Implementation would fetch from database or cache
        pass

    async def _fetch_schemas(self) -> List[Dict[str, Any]]:
        """Fetch available schemas"""
        # Implementation would fetch from database or config
        pass

# Using Annotated helps FastAPI distinguish dependency injection from response model fields,
# preventing errors when a response_model is defined on a route that depends on non-Pydantic types like AsyncSession.
async def get_data_service(db: Annotated[AsyncSession, Depends(get_db)]) -> DataService:
    """Dependency for getting the data service."""
    return DataService(db) 