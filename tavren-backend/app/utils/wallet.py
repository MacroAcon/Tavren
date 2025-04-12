from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, and_, select
import logging
from app.models import Reward, PayoutRequest
from app.exceptions import ResourceNotFoundException, InsufficientBalanceError
from datetime import datetime

# Get logger
log = logging.getLogger("app")

# Functions moved to WalletService, TrustService
# async def calculate_user_balance(user_id: str, db: AsyncSession) -> dict:
#     ...

# async def calculate_user_trust_score(user_id: str, db: AsyncSession) -> float:
#     ...

# async def process_payout_paid(payout: PayoutRequest, db: AsyncSession):
#     ...

# async def get_payout_request_or_404(payout_id: int, db: AsyncSession) -> PayoutRequest:
#     ...

# Any remaining utility functions specific to wallet context can stay here
# For example, if there were functions not directly tied to db operations or core service logic. 