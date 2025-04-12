from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
import logging

from app.models import Reward, PayoutRequest, ConsentEvent

log = logging.getLogger("app")

class TrustService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_user_trust_score(self, user_id: str) -> float:
        """
        Calculate a trust score for a user based on their interaction history.
        Factors: Reward count, successful payout count.
        """
        log.debug(f"[TrustService] Calculating trust score for user {user_id}")
        try:
            reward_count_query = select(func.count(Reward.id)).where(Reward.user_id == user_id)
            reward_count_result = await self.db.execute(reward_count_query)
            reward_count = reward_count_result.scalar_one_or_none() or 0

            successful_payouts_query = select(func.count(PayoutRequest.id)).where(
                and_(PayoutRequest.user_id == user_id, PayoutRequest.status == "paid")
            )
            successful_payouts_result = await self.db.execute(successful_payouts_query)
            successful_payouts = successful_payouts_result.scalar_one_or_none() or 0

            trust_score = min(100.0, (reward_count * 2) + (successful_payouts * 5))
            log.debug(f"[TrustService] User {user_id} trust score: {trust_score}")
            return trust_score
        except Exception as e:
            log.error(f"[TrustService] Error calculating user trust score for {user_id}: {str(e)}", exc_info=True)
            return 50.0 # Default score on error

    async def calculate_buyer_trust_score(self, buyer_id: str) -> float:
        """
        Calculate trust score for a specific buyer based on declined consent events.
        """
        log.debug(f"[TrustService] Calculating trust score for buyer {buyer_id}")
        try:
            buyer_offer_pattern = f"buyer-{buyer_id}-offer-%"
            query = select(func.count(ConsentEvent.id)).filter(
                ConsentEvent.action == "declined",
                ConsentEvent.offer_id.like(buyer_offer_pattern)
            )
            result = await self.db.execute(query)
            decline_count = result.scalar_one_or_none() or 0

            trust_score = max(0.0, 100.0 - (decline_count * 5.0))
            log.debug(f"[TrustService] Buyer {buyer_id} trust score: {trust_score}")
            return trust_score
        except Exception as e:
            log.error(f"[TrustService] Error calculating buyer trust score for {buyer_id}: {str(e)}", exc_info=True)
            return 50.0 # Default score on error 