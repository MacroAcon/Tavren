from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
import logging
from datetime import datetime

from app.models import Reward, PayoutRequest
from app.exceptions import ResourceNotFoundException, InsufficientBalanceError, BelowMinimumThresholdError
from app.config import settings
from app.utils.db_utils import get_by_id_or_404, safe_commit
from app.constants.payment import (
    PAYOUT_STATUS_PENDING, 
    PAYOUT_STATUS_PAID,
    MSG_INSUFFICIENT_BALANCE,
    MSG_BELOW_THRESHOLD
)

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
            # Get total earnings from rewards
            total_earned_query = select(func.sum(Reward.amount)).where(
                Reward.user_id == user_id
            )
            total_earned_result = await self.db.execute(total_earned_query)
            total_earned = total_earned_result.scalar_one_or_none() or 0.0

            # Get total claimed in pending and paid payouts
            total_claimed_query = select(func.sum(PayoutRequest.amount)).where(
                and_(
                    PayoutRequest.user_id == user_id,
                    PayoutRequest.status.in_([PAYOUT_STATUS_PAID, PAYOUT_STATUS_PENDING])
                )
            )
            total_claimed_result = await self.db.execute(total_claimed_query)
            total_claimed = total_claimed_result.scalar_one_or_none() or 0.0

            # Calculate available balance, ensuring it's not negative
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
            payout.status = PAYOUT_STATUS_PAID
            payout.paid_at = datetime.utcnow()
            self.db.add(payout)
            await safe_commit(self.db)
            log.info(f"[WalletService] Successfully marked payout {payout.id} as paid")
        except Exception as e:
            log.error(f"[WalletService] Failed to mark payout {payout.id} as paid: {str(e)}", exc_info=True)
            raise

    async def get_payout_request_or_404(self, payout_id: int) -> PayoutRequest:
        """
        Get a payout request by ID or raise a 404 exception if not found.
        """
        log.debug(f"[WalletService] Looking up payout request with ID {payout_id}")
        # Use the shared utility function instead of duplicating code
        return await get_by_id_or_404(
            db=self.db, 
            model=PayoutRequest, 
            id_value=payout_id,
            error_message=f"Payout request with ID {payout_id} not found"
        )

    async def create_payout_request(self, user_id: str, amount: float) -> PayoutRequest:
        """
        Creates a new PayoutRequest after validating balance and threshold.
        """
        log.info(f"[WalletService] Creating payout request of ${amount} for user {user_id}")
        
        # Check available balance
        balance_info = await self.calculate_user_balance(user_id)
        available_balance = balance_info["available_balance"]

        if amount > available_balance:
            log.warning(f"[WalletService] Insufficient balance for {user_id}: req ${amount}, avail ${available_balance}")
            raise InsufficientBalanceError(f"{MSG_INSUFFICIENT_BALANCE} Requested: ${amount}, Available: ${available_balance}")

        # Check minimum threshold
        if amount < settings.MINIMUM_PAYOUT_THRESHOLD:
            log.warning(f"[WalletService] Payout below threshold: ${amount} < ${settings.MINIMUM_PAYOUT_THRESHOLD}")
            raise BelowMinimumThresholdError(f"{MSG_BELOW_THRESHOLD} Minimum: ${settings.MINIMUM_PAYOUT_THRESHOLD}")

        # Create payout request
        payout_request = PayoutRequest(
            user_id=user_id,
            amount=amount,
            status=PAYOUT_STATUS_PENDING
        )
        
        # Add to session and commit
        self.db.add(payout_request)
        await safe_commit(self.db)
        await self.db.refresh(payout_request)
        
        log.info(f"[WalletService] Payout request {payout_request.id} created successfully")
        return payout_request 