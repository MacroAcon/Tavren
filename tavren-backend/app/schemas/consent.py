"""
Pydantic schemas for consent-related operations.
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
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

class ConsentEventResponse(BaseModel):
    """Model for consent event responses with additional fields"""
    id: int = Field(..., description="Unique identifier for the consent event")
    user_id: str = Field(..., description="ID of the user associated with this consent event")
    offer_id: str = Field(..., description="ID of the offer associated with this consent event")
    action: str = Field(..., description="Action taken (opt_in, opt_out, withdraw, grant_partial, etc.)")
    timestamp: datetime = Field(..., description="When the consent event occurred")
    user_reason: Optional[str] = Field(None, description="User-provided reason for this consent action")
    reason_category: Optional[str] = Field(None, description="Categorized reason (privacy, trust, complexity, etc.)")
    verification_hash: Optional[str] = Field(None, description="Verification hash for tamper evidence")
    prev_hash: Optional[str] = Field(None, description="Hash of the previous event in the chain")

    model_config = {
        "from_attributes": True  # Modern Pydantic v2 attribute for ORM mode
    }

class ConsentLedgerExport(BaseModel):
    """Model for exporting the consent ledger"""
    events: List[ConsentEventResponse] = Field(..., description="List of consent events")
    exported_at: datetime = Field(default_factory=datetime.now, description="When the export was created")
    total_events: int = Field(..., description="Total number of events in the export")

class LedgerVerificationResult(BaseModel):
    """Model for ledger verification results"""
    verified: bool = Field(..., description="Whether the ledger integrity is verified")
    users_checked: int = Field(..., description="Number of users checked")
    events_checked: int = Field(..., description="Number of events checked")
    inconsistencies: List[Dict[str, Any]] = Field([], description="Details of any inconsistencies found")

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

    model_config = {
        "json_schema_extra": {
            "example": {
                "access": ACCESS_FULL,
                "trust_score": 0.95
            }
        }
    }

class FilteredOffer(BaseModel):
    """Schema for filtered offers based on sensitivity."""
    title: str
    description: str
    sensitivity_level: str = Field(..., description="Sensitivity level (low, medium, high)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Share location data",
                "description": "Share your approximate location data for improved service",
                "sensitivity_level": SENSITIVITY_MEDIUM
            }
        }
    }

class SuggestionSuccessStats(BaseModel):
    """Schema for suggestion success statistics."""
    suggestions_offered: int
    suggestions_accepted: int
    acceptance_rate: float  # Percentage rounded to 2 decimals 