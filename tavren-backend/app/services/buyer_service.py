from sqlalchemy.ext.asyncio import AsyncSession
import logging
import re
from collections import defaultdict

from app.models import ConsentEvent
from app.schemas import BuyerTrustStats, BuyerAccessLevel, FilteredOffer
from app.services.trust_service import TrustService

log = logging.getLogger("app")

# Mock offers data - Consider moving to config or database
MOCK_OFFERS = [
    FilteredOffer(title="Basic Data Share", description="Share anonymous usage stats.", sensitivity_level="low"),
    FilteredOffer(title="Contact Info Share", description="Share email for newsletters.", sensitivity_level="medium"),
    FilteredOffer(title="Location Tracking", description="Enable background location for personalized ads.", sensitivity_level="high"),
    FilteredOffer(title="Purchase History Analysis", description="Allow analysis of your purchase history.", sensitivity_level="medium"),
    FilteredOffer(title="Public Profile Data", description="Share your public profile information.", sensitivity_level="low"),
    FilteredOffer(title="Biometric Data Access", description="Allow access to fingerprint/face ID.", sensitivity_level="high"),
]

class BuyerService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.trust_service = TrustService(db)

    async def get_buyer_trust_stats(self) -> list[BuyerTrustStats]:
        """
        Calculates trust statistics for all buyers based on declined events.
        """
        log.debug("[BuyerService] Calculating buyer trust statistics")
        try:
            query = select(ConsentEvent).filter(ConsentEvent.action == "declined")
            result = await self.db.execute(query)
            declined_events = result.scalars().all()

            stats_by_buyer = defaultdict(lambda: {"decline_count": 0, "reasons": defaultdict(int)})
            buyer_id_pattern = re.compile(r"^buyer-(\d+)-offer-.*")

            for event in declined_events:
                match = buyer_id_pattern.match(event.offer_id)
                if not match:
                    log.warning(f"[BuyerService] Skipping event with malformed offer_id: {event.offer_id}")
                    continue
                buyer_id = match.group(1)
                reason = event.reason_category or "unspecified"
                stats_by_buyer[buyer_id]["decline_count"] += 1
                stats_by_buyer[buyer_id]["reasons"][reason] += 1

            buyer_insights = []
            for buyer_id, data in stats_by_buyer.items():
                trust_score = await self.trust_service.calculate_buyer_trust_score(buyer_id)
                is_risky = trust_score < 40.0
                buyer_insights.append(
                    BuyerTrustStats(
                        buyer_id=buyer_id,
                        decline_count=data["decline_count"],
                        reasons=dict(data["reasons"]),
                        trust_score=trust_score,
                        is_risky=is_risky
                    )
                )
            return buyer_insights
        except Exception as e:
            log.error(f"[BuyerService] Error calculating buyer trust stats: {str(e)}", exc_info=True)
            return []

    async def get_buyer_access_level(self, buyer_id: str) -> BuyerAccessLevel:
        """
        Determine the access level for a buyer based on their trust score.
        """
        log.debug(f"[BuyerService] Determining access level for buyer {buyer_id}")
        try:
            trust_score = await self.trust_service.calculate_buyer_trust_score(buyer_id)
            if trust_score >= 70.0:
                access_level = "full"
            elif trust_score >= 40.0:
                access_level = "limited"
            else:
                access_level = "restricted"
            log.debug(f"[BuyerService] Buyer {buyer_id} access: {access_level}, trust: {trust_score}")
            return BuyerAccessLevel(access=access_level, trust_score=trust_score)
        except Exception as e:
            log.error(f"[BuyerService] Error determining access level for {buyer_id}: {str(e)}", exc_info=True)
            return BuyerAccessLevel(access="restricted", trust_score=0.0)

    async def get_filtered_offers(self, buyer_id: str) -> list[FilteredOffer]:
        """
        Filter available offers based on buyer's trust score (access level).
        """
        log.debug(f"[BuyerService] Filtering offers for buyer {buyer_id}")
        try:
            access_level = await self.get_buyer_access_level(buyer_id)
            if access_level.access == "full":
                filtered_offers = MOCK_OFFERS
            elif access_level.access == "limited":
                filtered_offers = [o for o in MOCK_OFFERS if o.sensitivity_level in ["low", "medium"]]
            else: # restricted
                filtered_offers = [o for o in MOCK_OFFERS if o.sensitivity_level == "low"]
            log.debug(f"[BuyerService] Returning {len(filtered_offers)} offers for buyer {buyer_id} (Access: {access_level.access})")
            return filtered_offers
        except Exception as e:
            log.error(f"[BuyerService] Error filtering offers for {buyer_id}: {str(e)}", exc_info=True)
            return [o for o in MOCK_OFFERS if o.sensitivity_level == "low"] 