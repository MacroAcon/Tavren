from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models import PayoutRequest
from app.schemas import AutoProcessSummary
from app.services.trust_service import TrustService
from app.services.wallet_service import WalletService
from app.config import settings
from app.exceptions import PayoutProcessingError
from app.constants.payment import PAYOUT_STATUS_PENDING
from app.utils.db_utils import safe_commit

log = logging.getLogger("app")

class PayoutService:
    def __init__(self, db: AsyncSession):
        self.db = db
        # Services needed for payout logic
        self.trust_service = TrustService(db)
        self.wallet_service = WalletService(db)

    async def process_automatic_payouts(self) -> AutoProcessSummary:
        """
        Processes pending payouts automatically based on trust scores and amounts.
        """
        log.info("[PayoutService] Starting automatic payout processing")
        try:
            # Query for pending payouts
            query = select(PayoutRequest).filter(PayoutRequest.status == PAYOUT_STATUS_PENDING)
            result = await self.db.execute(query)
            pending_payouts = result.scalars().all()
            total_pending = len(pending_payouts)
            log.info(f"[PayoutService] Found {total_pending} pending payouts")

            # Initialize summary with zeros
            summary = AutoProcessSummary(
                total_pending=total_pending, 
                processed=0, 
                marked_paid=0,
                skipped_low_trust=0, 
                skipped_high_amount=0, 
                skipped_other_error=0
            )

            # Process each pending payout
            for payout in pending_payouts:
                summary.processed += 1
                try:
                    # Calculate trust score for this user
                    user_trust_score = await self.trust_service.calculate_user_trust_score(payout.user_id)

                    # Skip if trust score too low
                    if user_trust_score < settings.AUTO_PAYOUT_MIN_TRUST_SCORE:
                        log.warning(f"[PayoutService] Skipping payout {payout.id} (User: {payout.user_id}): Trust {user_trust_score} < {settings.AUTO_PAYOUT_MIN_TRUST_SCORE}")
                        summary.skipped_low_trust += 1
                        continue

                    # Skip if amount too high
                    if payout.amount > settings.AUTO_PAYOUT_MAX_AMOUNT:
                        log.warning(f"[PayoutService] Skipping payout {payout.id} (User: {payout.user_id}): Amount ${payout.amount} > ${settings.AUTO_PAYOUT_MAX_AMOUNT}")
                        summary.skipped_high_amount += 1
                        continue

                    # --- Placeholder for actual external payout processing --- #
                    log.info(f"[PayoutService] Processing payout {payout.id} (User: {payout.user_id}, Amount: ${payout.amount}, Trust: {user_trust_score})")
                    is_processed_successfully = True # Simulate success
                    # --- End Placeholder --- #

                    # Mark as paid if successful
                    if is_processed_successfully:
                        await self.wallet_service.process_payout_paid(payout)
                        summary.marked_paid += 1
                    else:
                        log.error(f"[PayoutService] External processing failed for payout {payout.id}. Status remains pending.")
                        summary.skipped_other_error += 1

                except Exception as process_error:
                    # Log and continue with next payout
                    log.error(f"[PayoutService] Error processing payout {payout.id}: {process_error}", exc_info=True)
                    summary.skipped_other_error += 1
                    continue

            # Log summary and return
            log.info(f"[PayoutService] Auto payout complete. Summary: {summary.dict()}")
            return summary

        except Exception as e:
            # Handle critical errors that affect the entire process
            log.error(f"[PayoutService] Critical error during auto payout: {e}", exc_info=True)
            raise PayoutProcessingError("Internal server error during automatic payout processing.") 