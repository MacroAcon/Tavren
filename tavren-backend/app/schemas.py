from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
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
    reasons: Dict[str, int] # Key: reason_category, Value: count
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

# --- Authentication Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_active: bool

    class Config:
        orm_mode = True

class UserDisplay(UserBase): # Schema for returning user info safely
    id: int
    is_active: bool

    class Config:
        orm_mode = True

# --- Data Packaging Schemas ---

class DataPackageRequest(BaseModel):
    """Schema for requesting data packaging"""
    user_id: str
    data_type: str = Field(..., description="Type of data being requested (e.g., app_usage, location)")
    access_level: str = Field(..., description="Access level (precise_persistent, precise_short_term, anonymous_persistent, anonymous_short_term)")
    consent_id: str = Field(..., description="ID of the consent record for this data exchange")
    purpose: str = Field(..., description="Purpose for data use")
    buyer_id: Optional[str] = Field(None, description="ID of the data buyer")
    trust_tier: Optional[str] = Field("standard", description="Trust tier of the buyer (low, standard, high)")

class DataAccessRequest(BaseModel):
    """Schema for requesting access to a data package"""
    package_id: str
    access_token: str
    
class DataPackageMetadata(BaseModel):
    """Schema for data package metadata"""
    record_count: int
    schema_version: str
    data_quality_score: float
    buyer_id: Optional[str] = None
    trust_tier: Optional[str] = None
    encryption_status: str
    mcp_context: Dict[str, Any]

class DataPackageResponse(BaseModel):
    """Schema for data package response"""
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
    """Schema for creating audit records"""
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
    """Schema for audit record responses"""
    id: int
    timestamp: datetime
    
    class Config:
        orm_mode = True

class DataSchemaInfo(BaseModel):
    """Information about available data schemas"""
    data_type: str
    schema_version: str
    required_fields: List[str]
    description: str
    example: Dict[str, Any]

# Schema for LLM processing requests
class LLMProcessRequest(BaseModel):
    package_id: str
    instructions: str
    model_config: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None

# Schema for LLM processing responses
class LLMProcessResponse(BaseModel):
    request_id: str
    model_used: str
    package_id: str
    result: str
    usage: Dict[str, Any]
    timestamp: float

# Schema for embedding requests
class EmbeddingRequest(BaseModel):
    text: Optional[str] = None
    package_id: Optional[str] = None
    model_name: Optional[str] = None
    embedding_type: Optional[str] = "content"
    use_nvidia_api: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Sample text to embed",
                "package_id": None,
                "model_name": "llama-3_2-nv-embedqa-1b-v2",
                "embedding_type": "content",
                "use_nvidia_api": True
            }
        }

# Schema for embedding responses
class EmbeddingResponse(BaseModel):
    request_id: str
    model_used: str
    embedding: List[float]
    dimension: int
    usage: Dict[str, Any]
    timestamp: float
    package_id: Optional[str] = None

# Schema for vector search requests
class VectorSearchRequest(BaseModel):
    query_text: str
    embedding_type: Optional[str] = None
    top_k: Optional[int] = None
    use_nvidia_api: bool = True
    filter_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "User location data from last week",
                "embedding_type": "content",
                "top_k": 5,
                "use_nvidia_api": True,
                "filter_metadata": {"data_type": "location"}
            }
        }

# Schema for vector search responses
class VectorSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    count: int

# Schema for package indexing requests
class IndexPackageRequest(BaseModel):
    package_id: str
    use_nvidia_api: bool = True
    
    class Config:
        schema_extra = {
            "example": {
                "package_id": "pkg_abc123",
                "use_nvidia_api": True
            }
        }

# Schema for package indexing responses
class IndexPackageResponse(BaseModel):
    package_id: str
    embeddings_created: List[Dict[str, Any]]
    data_type: str
    record_count: int

# Schema for RAG requests
class RAGRequest(BaseModel):
    query_text: str
    top_k: Optional[int] = None
    max_tokens: Optional[int] = None
    
    class Config:
        schema_extra = {
            "example": {
                "query_text": "What locations did the user visit last weekend?",
                "top_k": 3,
                "max_tokens": 1000
            }
        }

# Schema for RAG responses
class RAGResponse(BaseModel):
    query: str
    context: str
    package_ids: List[str]
    result_count: int
    timestamp: float

# Schema for RAG generation requests
class RAGGenerationRequest(BaseModel):
    query: str
    instructions: Optional[str] = "Provide a concise and accurate response based on the retrieved context."
    model_name: Optional[str] = None
    top_k: Optional[int] = 3
    context_max_tokens: Optional[int] = 2000
    response_max_tokens: Optional[int] = 1000
    temperature: Optional[float] = 0.7
    
    class Config:
        schema_extra = {
            "example": {
                "query": "What locations did the user visit last weekend?",
                "instructions": "Provide a concise summary of the user's locations from the retrieved data.",
                "top_k": 3,
                "context_max_tokens": 2000,
                "response_max_tokens": 500,
                "temperature": 0.7
            }
        }

# Schema for RAG generation responses
class RAGGenerationResponse(BaseModel):
    request_id: str
    query: str
    response: str
    context_packages: List[str]
    context_count: int
    model_used: str
    usage: Dict[str, Any]
    timestamp: float