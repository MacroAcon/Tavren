from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
import logging
import re
from collections import defaultdict
from app.models import ConsentEvent
from app.schemas import BuyerTrustStats, BuyerAccessLevel, FilteredOffer

# Get logger
log = logging.getLogger("app")

# Mock offers data - in a real app, this would come from a database
MOCK_OFFERS = [
    FilteredOffer(title="Basic Data Share", description="Share anonymous usage stats.", sensitivity_level="low"),
    FilteredOffer(title="Contact Info Share", description="Share email for newsletters.", sensitivity_level="medium"),
    FilteredOffer(title="Location Tracking", description="Enable background location for personalized ads.", sensitivity_level="high"),
    FilteredOffer(title="Purchase History Analysis", description="Allow analysis of your purchase history.", sensitivity_level="medium"),
    FilteredOffer(title="Public Profile Data", description="Share your public profile information.", sensitivity_level="low"),
    FilteredOffer(title="Biometric Data Access", description="Allow access to fingerprint/face ID.", sensitivity_level="high"),
]

# Functions moved to BuyerService, TrustService
# async def get_buyer_trust_stats(db: AsyncSession) -> list[BuyerTrustStats]:
#    ...

# async def calculate_buyer_trust_score(buyer_id: str, db: AsyncSession) -> float:
#    ...

# async def get_buyer_access_level(buyer_id: str, db: AsyncSession) -> BuyerAccessLevel:
#    ...

# async def get_filtered_offers(buyer_id: str, db: AsyncSession) -> list[FilteredOffer]:
#    ...

# Any remaining utility functions specific to buyer context can stay here. 