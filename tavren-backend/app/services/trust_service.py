from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
import logging

from app.models import Reward, PayoutRequest, ConsentEvent
from app.constants.payment import PAYOUT_STATUS_PAID
from app.constants.consent import ACTION_DECLINED
from app.logging.log_utils import log_event
from app.utils.decorators import log_function_call, handle_exceptions

log = logging.getLogger("app")

class TrustService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @log_function_call
    @handle_exceptions(error_message="Error calculating user trust score", default_return=50.0, reraise=False)
    async def calculate_user_trust_score(self, user_id: str) -> float:
        """
        Calculate a trust score for a user based on their interaction history.
        Factors: Reward count, successful payout count.
        """
        # Count rewards for user
        reward_count_query = select(func.count(Reward.id)).where(Reward.user_id == user_id)
        reward_count_result = await self.db.execute(reward_count_query)
        reward_count = reward_count_result.scalar_one_or_none() or 0

        # Count successful payouts
        successful_payouts_query = select(func.count(PayoutRequest.id)).where(
            and_(PayoutRequest.user_id == user_id, PayoutRequest.status == PAYOUT_STATUS_PAID)
        )
        successful_payouts_result = await self.db.execute(successful_payouts_query)
        successful_payouts = successful_payouts_result.scalar_one_or_none() or 0

        # Calculate trust score based on activity
        trust_score = min(100.0, (reward_count * 2) + (successful_payouts * 5))
        
        log_event(
            event_type="trust_score_calculated",
            message=f"Trust score calculated for user {user_id}",
            details={"user_id": user_id, "score": trust_score, "reward_count": reward_count, "successful_payouts": successful_payouts},
            level="debug"
        )
        return trust_score

    @log_function_call
    @handle_exceptions(error_message="Error calculating buyer trust score", default_return=50.0, reraise=False)
    async def calculate_buyer_trust_score(self, buyer_id: str) -> float:
        """
        Calculate trust score for a specific buyer based on declined consent events.
        """
        # Find offers associated with this buyer
        buyer_offer_pattern = f"buyer-{buyer_id}-offer-%"
        
        # Count how many times users declined this buyer's offers
        query = select(func.count(ConsentEvent.id)).filter(
            ConsentEvent.action == ACTION_DECLINED,
            ConsentEvent.offer_id.like(buyer_offer_pattern)
        )
        result = await self.db.execute(query)
        decline_count = result.scalar_one_or_none() or 0

        # Calculate trust score based on declines (lower is worse)
        trust_score = max(0.0, 100.0 - (decline_count * 5.0))
        
        log_event(
            event_type="buyer_trust_score_calculated",
            message=f"Trust score calculated for buyer {buyer_id}",
            details={"buyer_id": buyer_id, "score": trust_score, "decline_count": decline_count},
            level="debug"
        )
        return trust_score 