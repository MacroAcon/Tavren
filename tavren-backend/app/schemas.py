from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConsentEventCreate(BaseModel):
    user_id: str
    offer_id: str
    action: str
    timestamp: Optional[datetime] = None
    user_reason: Optional[str] = None
    reason_category: Optional[str] = None

class ReasonStats(BaseModel):
    reason_category: str
    count: int

# Schema for the nested context in AgentTrainingExample
class AgentTrainingContext(BaseModel):
    user_profile: str
    reason_category: Optional[str] = None # Match ConsentEvent

# Schema for the agent training log export
class AgentTrainingExample(BaseModel):
    input: str
    context: AgentTrainingContext
    expected_output: str

# Schema for buyer-level trust statistics
class BuyerTrustStats(BaseModel):
    buyer_id: str
    decline_count: int
    reasons: dict[str, int] # Key: reason_category, Value: count
    trust_score: float # Calculated score
    is_risky: bool # Flag for low trust score

# Schema for buyer access level based on trust score
class BuyerAccessLevel(BaseModel):
    access: str # 'full', 'limited', or 'restricted'
    trust_score: float

# Schema for filtered offers based on sensitivity
class FilteredOffer(BaseModel):
    title: str
    description: str
    sensitivity_level: str # 'low', 'medium', or 'high'

# Schema for suggestion success statistics
class SuggestionSuccessStats(BaseModel):
    suggestions_offered: int
    suggestions_accepted: int
    acceptance_rate: float # Percentage rounded to 2 decimals

# --- Reward Schemas ---

class RewardBase(BaseModel):
    user_id: str
    offer_id: str
    amount: float

class RewardCreate(RewardBase):
    pass # No extra fields needed for creation

class RewardDisplay(RewardBase):
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True # Enable ORM mode for easy conversion

# Schema for wallet balance
class WalletBalance(BaseModel):
    user_id: str
    total_earned: float
    total_claimed: float
    available_balance: float
    is_claimable: bool # New flag for payout eligibility

# --- Payout Schemas ---

class PayoutRequestBase(BaseModel):
    user_id: str
    amount: float

class PayoutRequestCreate(PayoutRequestBase):
    pass # No extra fields needed for creation

class PayoutRequestDisplay(PayoutRequestBase):
    id: int
    timestamp: datetime
    status: str # e.g., pending, paid, failed
    paid_at: Optional[datetime] = None # Include processing time

    class Config:
        orm_mode = True

# --- Auto Process Summary Schema ---

class AutoProcessSummary(BaseModel):
    total_pending: int
    processed: int
    marked_paid: int
    skipped_low_trust: int
    skipped_high_amount: int
    skipped_other_error: int

    class Config:
        orm_mode = True