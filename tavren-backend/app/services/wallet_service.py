from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
import logging
from datetime import datetime

from app.models import Reward, PayoutRequest
from app.exceptions import ResourceNotFoundException, InsufficientBalanceError
from app.config import settings # Import settings for threshold

log = logging.getLogger("app")

class WalletService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_user_balance(self, user_id: str) -> dict:
        """
        Calculate a user's wallet balance including total earnings, claimed amount,
        and available balance.
        """
        log.debug(f"[WalletService] Calculating balance for user {user_id}")

        try:
            total_earned_query = select(func.sum(Reward.amount)).where(
                Reward.user_id == user_id
            )
            total_earned_result = await self.db.execute(total_earned_query)
            total_earned = total_earned_result.scalar_one_or_none() or 0.0

            total_claimed_query = select(func.sum(PayoutRequest.amount)).where(
                and_(
                    PayoutRequest.user_id == user_id,
                    PayoutRequest.status.in_(["paid", "pending"])
                )
            )
            total_claimed_result = await self.db.execute(total_claimed_query)
            total_claimed = total_claimed_result.scalar_one_or_none() or 0.0

            available_balance = max(0.0, total_earned - total_claimed)

            log.debug(f"[WalletService] User {user_id} balance - Earned: {total_earned}, Claimed: {total_claimed}, Available: {available_balance}")
            return {
                "total_earned": total_earned,
                "total_claimed": total_claimed,
                "available_balance": available_balance
            }
        except Exception as e:
            log.error(f"[WalletService] Error calculating balance for user {user_id}: {str(e)}", exc_info=True)
            raise

    async def process_payout_paid(self, payout: PayoutRequest):
        """
        Process a payout as paid by updating its status and timestamp.
        """
        log.info(f"[WalletService] Marking payout {payout.id} as paid for user {payout.user_id}")

        try:
            payout.status = "paid"
            payout.paid_at = datetime.utcnow()
            self.db.add(payout)
            await self.db.commit()
            log.info(f"[WalletService] Successfully marked payout {payout.id} as paid")
        except Exception as e:
            await self.db.rollback()
            log.error(f"[WalletService] Failed to mark payout {payout.id} as paid: {str(e)}", exc_info=True)
            raise

    async def get_payout_request_or_404(self, payout_id: int) -> PayoutRequest:
        """
        Get a payout request by ID or raise a 404 exception if not found.
        """
        log.debug(f"[WalletService] Looking up payout request with ID {payout_id}")
        query = select(PayoutRequest).where(PayoutRequest.id == payout_id)
        result = await self.db.execute(query)
        payout = result.scalar_one_or_none()

        if payout is None:
            log.warning(f"[WalletService] Payout request with ID {payout_id} not found")
            raise ResourceNotFoundException(f"Payout request with ID {payout_id} not found")

        return payout

    async def create_payout_request(self, user_id: str, amount: float) -> PayoutRequest:
        """
        Creates a new PayoutRequest after validating balance and threshold.
        """
        log.info(f"[WalletService] Creating payout request of ${amount} for user {user_id}")
        balance_info = await self.calculate_user_balance(user_id)
        available_balance = balance_info["available_balance"]

        if amount > available_balance:
            log.warning(f"[WalletService] Insufficient balance for {user_id}: req ${amount}, avail ${available_balance}")
            raise InsufficientBalanceError(f"Insufficient balance. Requested: ${amount}, Available: ${available_balance}")

        if amount < settings.MINIMUM_PAYOUT_THRESHOLD:
            log.warning(f"[WalletService] Payout below threshold: ${amount} < ${settings.MINIMUM_PAYOUT_THRESHOLD}")
            raise BelowMinimumThresholdError(f"Payout request (${amount}) below minimum (${settings.MINIMUM_PAYOUT_THRESHOLD})")

        payout_request = PayoutRequest(
            user_id=user_id,
            amount=amount,
            status="pending"
        )
        self.db.add(payout_request)
        await self.db.commit()
        await self.db.refresh(payout_request)
        log.info(f"[WalletService] Payout request {payout_request.id} created successfully")
        return payout_request 