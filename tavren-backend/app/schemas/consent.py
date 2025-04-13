"""
Pydantic schemas for consent-related operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime

from app.constants.consent import (
    REASON_UNSPECIFIED,
    ACCESS_FULL,
    ACCESS_LIMITED,
    ACCESS_RESTRICTED,
    SENSITIVITY_LOW,
    SENSITIVITY_MEDIUM,
    SENSITIVITY_HIGH
)

class ConsentEventCreate(BaseModel):
    """Schema for creating consent events."""
    user_id: str
    offer_id: str
    action: str
    timestamp: Optional[datetime] = None
    user_reason: Optional[str] = None
    reason_category: Optional[str] = None

class ReasonStats(BaseModel):
    """Schema for reason statistics."""
    reason_category: str
    count: int

class AgentTrainingContext(BaseModel):
    """Schema for the nested context in AgentTrainingExample."""
    user_profile: str
    reason_category: Optional[str] = REASON_UNSPECIFIED

class AgentTrainingExample(BaseModel):
    """Schema for the agent training log export."""
    input: str
    context: AgentTrainingContext
    expected_output: str

class BuyerTrustStats(BaseModel):
    """Schema for buyer-level trust statistics."""
    buyer_id: str
    decline_count: int
    reasons: Dict[str, int]  # Key: reason_category, Value: count
    trust_score: float  # Calculated score
    is_risky: bool  # Flag for low trust score

class BuyerAccessLevel(BaseModel):
    """Schema for buyer access level based on trust score."""
    access: str = Field(..., description="Access level (full, limited, restricted)")
    trust_score: float

    class Config:
        schema_extra = {
            "example": {
                "access": ACCESS_FULL,
                "trust_score": 0.95
            }
        }

class FilteredOffer(BaseModel):
    """Schema for filtered offers based on sensitivity."""
    title: str
    description: str
    sensitivity_level: str = Field(..., description="Sensitivity level (low, medium, high)")

    class Config:
        schema_extra = {
            "example": {
                "title": "Share location data",
                "description": "Share your approximate location data for improved service",
                "sensitivity_level": SENSITIVITY_MEDIUM
            }
        }

class SuggestionSuccessStats(BaseModel):
    """Schema for suggestion success statistics."""
    suggestions_offered: int
    suggestions_accepted: int
    acceptance_rate: float  # Percentage rounded to 2 decimals 