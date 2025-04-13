"""
Pydantic schemas for data packaging operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

from app.constants.consent import (
    ACCESS_PRECISE_PERSISTENT,
    ACCESS_PRECISE_SHORT_TERM,
    ACCESS_ANONYMOUS_PERSISTENT,
    ACCESS_ANONYMOUS_SHORT_TERM
)

class DataPackageRequest(BaseModel):
    """Schema for requesting data packaging."""
    user_id: str
    data_type: str = Field(..., description="Type of data being requested (e.g., app_usage, location)")
    access_level: str = Field(..., description="Access level")
    consent_id: str = Field(..., description="ID of the consent record for this data exchange")
    purpose: str = Field(..., description="Purpose for data use")
    buyer_id: Optional[str] = Field(None, description="ID of the data buyer")
    trust_tier: Optional[str] = Field("standard", description="Trust tier of the buyer (low, standard, high)")

    class Config:
        schema_extra = {
            "example": {
                "user_id": "user123",
                "data_type": "location",
                "access_level": ACCESS_ANONYMOUS_PERSISTENT,
                "consent_id": "consent456",
                "purpose": "service improvement",
                "buyer_id": "buyer789",
                "trust_tier": "standard"
            }
        }

class DataAccessRequest(BaseModel):
    """Schema for requesting access to a data package."""
    package_id: str
    access_token: str

class DataPackageMetadata(BaseModel):
    """Schema for data package metadata."""
    record_count: int
    schema_version: str
    data_quality_score: float
    buyer_id: Optional[str] = None
    trust_tier: Optional[str] = None
    encryption_status: str
    mcp_context: Dict[str, Any]

class DataPackageResponse(BaseModel):
    """Schema for data package response."""
    tavren_data_package: str
    package_id: str
    consent_id: str
    created_at: str
    data_type: str
    access_level: str
    purpose: str
    expires_at: str
    anonymization_level: str
    access_token: Optional[str] = None
    content: Union[List[Dict[str, Any]], Dict[str, Any], str]
    metadata: DataPackageMetadata
    status: Optional[str] = None
    reason: Optional[str] = None

class DataPackageAuditCreate(BaseModel):
    """Schema for creating audit records."""
    operation: str
    package_id: str
    user_id: str
    consent_id: str
    buyer_id: Optional[str] = None
    data_type: str
    access_level: str
    anonymization_level: str
    record_count: int
    purpose: str
    status: str = "success"
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DataPackageAuditResponse(DataPackageAuditCreate):
    """Schema for audit record responses."""
    id: int
    timestamp: datetime

    class Config:
        orm_mode = True

class DataSchemaInfo(BaseModel):
    """Information about available data schemas."""
    data_type: str
    schema_version: str
    required_fields: List[str]
    description: str
    example: Dict[str, Any] 