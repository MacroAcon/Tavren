from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Union
from datetime import datetime

class ConsentEventBase(BaseModel):
    """Base model for consent events with common fields"""
    user_id: str = Field(..., description="ID of the user associated with this consent event")
    action: str = Field(..., description="Action taken (opt_in, opt_out, withdraw, grant_partial, etc.)")
    scope: Optional[str] = Field(None, description="Data category scope (location, purchase_data, all, etc.)")
    purpose: Optional[str] = Field(None, description="Purpose for data use (insight_generation, ad_targeting, etc.)")
    initiated_by: str = Field("user", description="Who initiated this consent action (user, system)")
    offer_id: Optional[str] = Field(None, description="ID of the offer associated with this consent event")
    user_reason: Optional[str] = Field(None, description="User-provided reason for this consent action")
    reason_category: Optional[str] = Field(None, description="Categorized reason (privacy, trust, complexity, etc.)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata for the consent event")

class ConsentEventCreate(ConsentEventBase):
    """Model for creating a new consent event"""
    pass

class ConsentEventResponse(ConsentEventBase):
    """Model for consent event responses with additional fields"""
    id: int = Field(..., description="Unique identifier for the consent event")
    timestamp: datetime = Field(..., description="When the consent event occurred")
    verification_hash: Optional[str] = Field(None, description="Verification hash for tamper evidence")
    prev_hash: Optional[str] = Field(None, description="Hash of the previous event in the chain")

    model_config = {
        "from_attributes": True
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

    model_config = {
        "from_attributes": True
    }

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

    model_config = {
        "from_attributes": True
    }

# --- Auto Process Summary Schema ---

class AutoProcessSummary(BaseModel):
    total_pending: int
    processed: int
    marked_paid: int
    skipped_low_trust: int
    skipped_high_amount: int
    skipped_other_error: int

    model_config = {
        "from_attributes": True
    }

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

    model_config = {
        "from_attributes": True
    }

class UserDisplay(UserBase): # Schema for returning user info safely
    id: int
    is_active: bool

    model_config = {
        "from_attributes": True
    }

# --- Data Packaging Schemas ---

class DataSchemaInfo(BaseModel):
    """Information about a data schema"""
    name: str = Field(..., description="Name of the schema")
    description: str = Field(..., description="Description of the schema")
    fields: List[str] = Field(..., description="List of field names in the schema")

class DataPackageRequest(BaseModel):
    """Request for a new data package"""
    schema_name: str = Field(..., description="Name of the schema to use")
    filters: Optional[Dict[str, Any]] = Field(None, description="Optional filters to apply to the data")

class DataPackageResponse(BaseModel):
    """Response containing a data package"""
    package_id: str = Field(..., description="Unique identifier for the package")
    schema_name: str = Field(..., description="Name of the schema used")
    data: Dict[str, Any] = Field(..., description="The packaged data")
    created_at: str = Field(..., description="ISO format timestamp of when the package was created")

class DataAccessRequest(BaseModel):
    """Request to access a data package"""
    package_id: str = Field(..., description="ID of the package to access")
    access_token: str = Field(..., description="Token granting access to the package")

class DataPackageMetadata(BaseModel):
    """Metadata about a data package"""
    package_id: str = Field(..., description="Unique identifier for the package")
    schema_name: str = Field(..., description="Name of the schema used")
    created_at: str = Field(..., description="ISO format timestamp of when the package was created")
    expires_at: Optional[str] = Field(None, description="ISO format timestamp of when the package expires")
    status: str = Field(..., description="Current status of the package (e.g., 'active', 'expired')")

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")

class SchemaListResponse(BaseModel):
    """Response containing list of available schemas"""
    schemas: List[DataSchemaInfo] = Field(..., description="List of available schemas")

class PackageListResponse(BaseModel):
    """Response containing list of data packages"""
    packages: List[DataPackageMetadata] = Field(..., description="List of data packages")

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

    model_config = {
        "from_attributes": True
    }

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

    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "This is a sample text to embed",
                "model_name": "text-embedding-ada-002",
                "embedding_type": "content",
                "use_nvidia_api": True
            }
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

    model_config = {
        "json_schema_extra": {
            "example": {
                "query_text": "What privacy controls are available?",
                "embedding_type": "query",
                "top_k": 5,
                "use_nvidia_api": True
            }
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

    model_config = {
        "json_schema_extra": {
            "example": {
                "package_id": "pkg_b8f9c2d1",
                "use_nvidia_api": True
            }
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

    model_config = {
        "json_schema_extra": {
            "example": {
                "query_text": "What are the privacy controls available in Tavren?",
                "top_k": 3,
                "max_tokens": 1000
            }
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

    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "What privacy controls are available to users?",
                "instructions": "Provide a concise and accurate response based on the retrieved context.",
                "top_k": 3,
                "context_max_tokens": 2000,
                "response_max_tokens": 1000,
                "temperature": 0.7
            }
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

# Schema for hybrid search requests
class HybridSearchRequest(BaseModel):
    query_text: str
    semantic_weight: Optional[float] = 0.7
    keyword_weight: Optional[float] = 0.3
    embedding_type: Optional[str] = None
    top_k: Optional[int] = None
    use_nvidia_api: bool = True
    filter_metadata: Optional[Dict[str, Any]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "query_text": "privacy controls GDPR compliance",
                "semantic_weight": 0.7,
                "keyword_weight": 0.3,
                "top_k": 5,
                "use_nvidia_api": True
            }
        }
    }

# Schema for hybrid search responses
class HybridSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    count: int
    semantic_weight: float
    keyword_weight: float
    search_type: str = "hybrid"

# Schema for cross-package context assembly requests
class CrossPackageContextRequest(BaseModel):
    query_text: str
    max_packages: Optional[int] = 5
    max_items_per_package: Optional[int] = 3
    max_tokens: Optional[int] = 2000
    use_hybrid_search: bool = True
    semantic_weight: Optional[float] = 0.7
    keyword_weight: Optional[float] = 0.3

    model_config = {
        "json_schema_extra": {
            "example": {
                "query_text": "Tavren user data privacy policies",
                "max_packages": 5,
                "max_items_per_package": 3,
                "max_tokens": 2000,
                "use_hybrid_search": True,
                "semantic_weight": 0.7,
                "keyword_weight": 0.3
            }
        }
    }

# Schema for cross-package context assembly responses
class CrossPackageContextResponse(BaseModel):
    query: str
    context: str
    package_count: int
    item_count: int
    token_count: int
    latency_ms: float
    packages: List[Dict[str, Any]]
    search_type: str
    timestamp: str

# Schema for query expansion search requests
class QueryExpansionRequest(BaseModel):
    query_text: str
    top_k: Optional[int] = None
    use_hybrid_search: bool = True
    max_expansions: Optional[int] = 3
    expansion_model: Optional[str] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "query_text": "privacy settings",
                "top_k": 5,
                "use_hybrid_search": True,
                "max_expansions": 3
            }
        }
    }

# Schema for query expansion search responses
class QueryExpansionResponse(BaseModel):
    original_query: str
    expanded_queries: List[str]
    results: List[Dict[str, Any]]
    result_count: int
    latency_ms: float
    search_type: str = "query_expansion"
    timestamp: str

# Schema for faceted search requests
class FacetedSearchRequest(BaseModel):
    query_text: str
    facets: Dict[str, List[str]]
    facet_weights: Optional[Dict[str, float]] = None
    use_hybrid_search: bool = True
    top_k: Optional[int] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "query_text": "privacy controls",
                "facets": {
                    "data_type": ["policy", "procedure"],
                    "category": ["gdpr", "ccpa"]
                },
                "facet_weights": {
                    "data_type": 0.3,
                    "category": 0.7
                },
                "use_hybrid_search": True,
                "top_k": 5
            }
        }
    }

# Schema for faceted search responses
class FacetedSearchResponse(BaseModel):
    query: str
    facets: Dict[str, List[str]]
    facet_weights: Dict[str, float]
    results: List[Dict[str, Any]]
    facet_groups: Dict[str, Dict[str, List[Dict[str, Any]]]]
    result_count: int
    latency_ms: float
    search_type: str = "faceted"
    use_hybrid_search: bool
    timestamp: str