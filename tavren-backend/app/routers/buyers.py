from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import List

from app.database import get_db
from app.schemas import (
    BuyerTrustStats,
    BuyerAccessLevel,
    FilteredOffer,
    UserDisplay # Added UserDisplay schema
)
from app.services.buyer_service import BuyerService # Added service
from app.auth import get_current_active_user # Added auth dependency

# Get logger
log = logging.getLogger("app")

# Create router for buyer insights
buyer_router = APIRouter(
    prefix="/api/buyers",
    tags=["buyers"]
)

@buyer_router.get("/insights", response_model=List[BuyerTrustStats])
async def get_buyer_insights(db: AsyncSession = Depends(get_db), current_user: UserDisplay = Depends(get_current_active_user)):
    """
    Get trust statistics and insights for all buyers using BuyerService.
    """
    log.info("Fetching buyer trust insights via service")
    try:
        buyer_service = BuyerService(db)
        buyer_insights = await buyer_service.get_buyer_trust_stats()
        log.info(f"Retrieved trust stats for {len(buyer_insights)} buyers via service")
        return buyer_insights
    except Exception as e:
        log.error(f"Failed to get buyer insights via service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching buyer insights.")

# Create router for offer-related endpoints
offer_router = APIRouter(
    prefix="/api/offers",
    tags=["offers"]
)

@offer_router.get("/available/{buyer_id}", response_model=BuyerAccessLevel)
async def get_buyer_access_level_endpoint(buyer_id: str, db: AsyncSession = Depends(get_db)):
    """
    Determine a buyer's access level using BuyerService.
    """
    log.info(f"Determining access level for buyer {buyer_id} via service")
    try:
        buyer_service = BuyerService(db)
        access_level = await buyer_service.get_buyer_access_level(buyer_id)
        log.info(f"Buyer {buyer_id} has access level: {access_level.access} (trust score: {access_level.trust_score}) via service")
        return access_level
    except Exception as e:
        log.error(f"Failed to determine buyer access level via service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error determining buyer access level.")

@offer_router.get("/feed/{buyer_id}", response_model=List[FilteredOffer])
async def get_offer_feed_endpoint(buyer_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get a filtered list of offers using BuyerService.
    """
    log.info(f"Getting offer feed for buyer {buyer_id} via service")
    try:
        buyer_service = BuyerService(db)
        offers = await buyer_service.get_filtered_offers(buyer_id)
        log.info(f"Returning {len(offers)} filtered offers for buyer {buyer_id} via service")
        return offers
    except Exception as e:
        log.error(f"Failed to get offers feed via service: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error fetching offer feed.") 