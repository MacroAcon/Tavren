"""
Pydantic schemas for payment, reward, and wallet operations.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.constants.payment import (
    PAYOUT_STATUS_PENDING,
    PAYOUT_STATUS_PAID,
    PAYOUT_STATUS_FAILED
)

class RewardBase(BaseModel):
    """Base schema for rewards."""
    user_id: str
    offer_id: str
    amount: float

class RewardCreate(RewardBase):
    """Schema for creating rewards."""
    pass

class RewardDisplay(RewardBase):
    """Schema for displaying rewards."""
    id: int
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }

class WalletBalance(BaseModel):
    """Schema for wallet balance."""
    user_id: str
    total_earned: float
    total_claimed: float
    available_balance: float
    is_claimable: bool  # Flag for payout eligibility

class PayoutRequestBase(BaseModel):
    """Base schema for payout requests."""
    user_id: str
    amount: float

class PayoutRequestCreate(PayoutRequestBase):
    """Schema for creating payout requests."""
    pass

class PayoutRequestDisplay(PayoutRequestBase):
    """Schema for displaying payout requests."""
    id: int
    timestamp: datetime
    status: str = Field(..., description="Status of the payout (pending, paid, failed)")
    paid_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "user_id": "user123",
                "amount": 25.50,
                "timestamp": "2023-04-01T12:00:00",
                "status": PAYOUT_STATUS_PENDING,
                "paid_at": None
            }
        }
    }

class AutoProcessSummary(BaseModel):
    """Schema for automatic payout process summary."""
    total_pending: int
    processed: int
    marked_paid: int
    skipped_low_trust: int
    skipped_high_amount: int
    skipped_other_error: int

    model_config = {
        "from_attributes": True
    } 