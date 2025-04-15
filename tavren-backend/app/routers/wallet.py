from fastapi import APIRouter, Depends, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from typing import List

from app.database import get_db
from app.models import Reward, PayoutRequest
from app.schemas import (
    RewardCreate,
    RewardDisplay,
    WalletBalance,
    PayoutRequestCreate,
    PayoutRequestDisplay,
    AutoProcessSummary,
    UserDisplay
)
from app.services.wallet_service import WalletService
from app.services.payout_service import PayoutService
from app.exceptions import (
    InsufficientBalanceError,
    BelowMinimumThresholdError,
    InvalidStatusTransitionError,
    PayoutProcessingError
)
from app.config import settings
from app.auth import get_current_active_user
from app.utils.response_utils import handle_exception
from app.utils.db_utils import get_by_id_or_404, safe_commit
from app.logging.log_utils import log_api_request, log_exception
from app.constants.status import HTTP_500_INTERNAL_SERVER_ERROR
from app.constants.payment import (
    PAYOUT_STATUS_PENDING,
    PAYOUT_STATUS_FAILED
)

# Get logger
log = logging.getLogger("app")

# Create router for rewards
reward_router = APIRouter(
    prefix="/api/rewards",
    tags=["rewards"]
)

@reward_router.post("", response_model=RewardDisplay)
async def create_reward(reward: RewardCreate, db = Depends(get_db)):
    """
    Create a new reward for a user.
    
    This endpoint records when a user earns a reward for a consent action.
    """
    log_api_request(endpoint="/api/rewards", method="POST", params=reward.dict())
    log.info(f"Creating reward of {reward.amount} for user {reward.user_id}")
    
    try:
        db_reward = Reward(**reward.dict())
        db.add(db_reward)
        await safe_commit(db)
        await db.refresh(db_reward)
        log.info(f"Reward {db_reward.id} created successfully")
        return db_reward
    except Exception as e:
        log_exception(e, context="create_reward", user_id=reward.user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error creating reward.")

@reward_router.get("/history/{user_id}", response_model=List[RewardDisplay])
async def get_reward_history(user_id: str, db = Depends(get_db)):
    """
    Get reward history for a specific user.
    """
    log_api_request(endpoint=f"/api/rewards/history/{user_id}", method="GET")
    log.info(f"Getting reward history for user {user_id}")
    
    try:
        query = select(Reward).filter(Reward.user_id == user_id).order_by(Reward.timestamp.desc())
        result = await db.execute(query)
        rewards = result.scalars().all()
        log.info(f"Found {len(rewards)} rewards for user {user_id}")
        return rewards
    except Exception as e:
        log_exception(e, context="get_reward_history", user_id=user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error fetching reward history.")

# Create router for wallet
wallet_router = APIRouter(
    prefix="/api/wallet",
    tags=["wallet"]
)

@wallet_router.get("/{user_id}", response_model=WalletBalance)
async def get_wallet_balance(user_id: str, db = Depends(get_db)):
    """
    Get wallet balance for a specific user.
    
    This endpoint calculates a user's total earnings, claimed amount,
    and available balance, as well as whether they can make a payout claim.
    """
    log_api_request(endpoint=f"/api/wallet/{user_id}", method="GET")
    log.info(f"Getting wallet balance for user {user_id}")
    
    try:
        wallet_service = WalletService(db)
        # Get balance details from service
        balance_info = await wallet_service.calculate_user_balance(user_id)
        
        # Determine if balance is claimable (above threshold)
        is_claimable = balance_info["available_balance"] >= settings.MINIMUM_PAYOUT_THRESHOLD
        
        wallet_balance = WalletBalance(
            user_id=user_id,
            total_earned=balance_info["total_earned"],
            total_claimed=balance_info["total_claimed"],
            available_balance=balance_info["available_balance"],
            is_claimable=is_claimable
        )
        
        log.info(f"User {user_id} wallet balance: ${wallet_balance.available_balance:.2f}, claimable: {wallet_balance.is_claimable}")
        return wallet_balance
    except Exception as e:
        log_exception(e, context="get_wallet_balance", user_id=user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error fetching wallet balance.")

@wallet_router.post("/claim", response_model=PayoutRequestDisplay)
async def request_payout(request: PayoutRequestCreate, db = Depends(get_db)):
    """
    Request a payout from the wallet.
    
    This endpoint allows users to claim their available balance.
    Uses WalletService to handle creation logic.
    """
    log_api_request(endpoint="/api/wallet/claim", method="POST", params=request.dict())
    log.info(f"Processing payout request of ${request.amount} for user {request.user_id}")
    
    try:
        wallet_service = WalletService(db)
        # Create payout request using the service method
        payout_request = await wallet_service.create_payout_request(request.user_id, request.amount)
        log.info(f"Payout request {payout_request.id} created successfully by service")
        return payout_request
    except (InsufficientBalanceError, BelowMinimumThresholdError) as e:
        # Let specific exceptions propagate
        raise
    except Exception as e:
        # Catch unexpected errors during service call
        log_exception(e, context="request_payout", user_id=request.user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error creating payout request.")

@wallet_router.get("/payouts/{user_id}", response_model=List[PayoutRequestDisplay])
async def get_payout_history(user_id: str, db = Depends(get_db)):
    """
    Get payout history for a specific user.
    """
    log_api_request(endpoint=f"/api/wallet/payouts/{user_id}", method="GET")
    log.info(f"Getting payout history for user {user_id}")
    
    try:
        query = select(PayoutRequest).filter(PayoutRequest.user_id == user_id).order_by(PayoutRequest.timestamp.desc())
        result = await db.execute(query)
        payouts = result.scalars().all()
        log.info(f"Found {len(payouts)} payout requests for user {user_id}")
        return payouts
    except Exception as e:
        log_exception(e, context="get_payout_history", user_id=user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error fetching payout history.")

# Create router for payout administration
payout_router = APIRouter(
    prefix="/api/payouts",
    tags=["payouts"]
)

@payout_router.post("/{payout_id}/mark-paid", response_model=PayoutRequestDisplay)
async def mark_payout_paid(payout_id: int, db = Depends(get_db), current_user: UserDisplay = Depends(get_current_active_user)):
    """
    Mark a payout request as paid.
    
    This endpoint is for administrators to confirm a payout has been processed.
    """
    log_api_request(endpoint=f"/api/payouts/{payout_id}/mark-paid", method="POST")
    log.info(f"Marking payout {payout_id} as paid")
    
    try:
        wallet_service = WalletService(db)
        payout = await wallet_service.get_payout_request_or_404(payout_id)
        
        if payout.status != PAYOUT_STATUS_PENDING:
            log.warning(f"Cannot mark payout {payout_id} as paid - current status: {payout.status}")
            raise InvalidStatusTransitionError(f"Cannot mark payout as paid. Current status: {payout.status}")
        
        await wallet_service.process_payout_paid(payout)
        await db.refresh(payout) # Refresh needed after commit in service
        return payout
    except InvalidStatusTransitionError:
        # Already handled with appropriate status code
        raise
    except Exception as e:
        log_exception(e, context=f"mark_payout_paid: {payout_id}")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to mark payout {payout_id} as paid.")

@payout_router.post("/{payout_id}/mark-failed", response_model=PayoutRequestDisplay)
async def mark_payout_failed(payout_id: int, db = Depends(get_db), current_user: UserDisplay = Depends(get_current_active_user)):
    """
    Mark a payout request as failed.
    
    This endpoint is for administrators to indicate a payout processing failure.
    """
    log_api_request(endpoint=f"/api/payouts/{payout_id}/mark-failed", method="POST")
    log.info(f"Marking payout {payout_id} as failed")
    
    try:
        wallet_service = WalletService(db)
        payout = await wallet_service.get_payout_request_or_404(payout_id)
        
        if payout.status != PAYOUT_STATUS_PENDING:
            log.warning(f"Cannot mark payout {payout_id} as failed - current status: {payout.status}")
            raise InvalidStatusTransitionError(f"Cannot mark payout as failed. Current status: {payout.status}")
        
        # Update payout status to failed
        payout.status = PAYOUT_STATUS_FAILED
        db.add(payout)
        await safe_commit(db)
        await db.refresh(payout)
        
        log.info(f"Payout {payout_id} marked as failed")
        return payout
    except InvalidStatusTransitionError:
        # Already handled with appropriate status code
        raise
    except Exception as e:
        log_exception(e, context=f"mark_payout_failed: {payout_id}")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to mark payout {payout_id} as failed.")

@payout_router.post("/process-auto", response_model=AutoProcessSummary)
async def process_automatic_payouts(db = Depends(get_db), current_user: UserDisplay = Depends(get_current_active_user)):
    """
    Process pending payouts automatically using PayoutService.
    """
    log_api_request(endpoint="/api/payouts/process-auto", method="POST")
    log.info("Endpoint triggered for automatic payout processing")

    try:
        payout_service = PayoutService(db)
        summary = await payout_service.process_automatic_payouts()
        log.info(f"Automatic payout processing complete via service. Summary: {summary.dict()}")
        return summary
    except PayoutProcessingError as e:
        # Handle specific processing errors if needed, otherwise re-raise or convert
        log_exception(e, context="process_automatic_payouts")
        raise
    except Exception as e:
        log_exception(e, context="process_automatic_payouts")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Unexpected internal server error during automatic payout.") 