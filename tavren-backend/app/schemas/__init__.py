"""
Schemas module for Tavren backend.
Centralizes Pydantic models used throughout the application.
"""
from __future__ import annotations

# Import all schemas to make them available from the schemas package
from app.schemas.consent import (
    ConsentEventCreate,
    ConsentEventResponse,
    ConsentLedgerExport,
    LedgerVerificationResult,
    ReasonStats,
    AgentTrainingContext,
    AgentTrainingExample,
    BuyerTrustStats,
    BuyerAccessLevel,
    FilteredOffer,
    SuggestionSuccessStats
)

from app.schemas.payment import (
    RewardBase,
    RewardCreate,
    RewardDisplay,
    WalletBalance,
    PayoutRequestBase,
    PayoutRequestCreate,
    PayoutRequestDisplay,
    AutoProcessSummary
)

from app.schemas.auth import (
    Token,
    TokenData,
    UserBase,
    UserCreate,
    UserInDB,
    UserDisplay
)

from app.schemas.data import (
    DataPackageRequest,
    DataAccessRequest,
    DataPackageMetadata,
    DataPackageResponse,
    DataPackageAuditCreate,
    DataPackageAuditResponse,
    DataSchemaInfo
)

from app.schemas.llm import (
    LLMProcessRequest,
    LLMProcessResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    VectorSearchRequest,
    VectorSearchResponse,
    IndexPackageRequest,
    IndexPackageResponse,
    RAGRequest,
    RAGResponse,
    RAGGenerationRequest,
    RAGGenerationResponse,
    HybridSearchRequest,
    HybridSearchResponse,
    CrossPackageContextRequest,
    CrossPackageContextResponse,
    QueryExpansionRequest,
    QueryExpansionResponse,
    FacetedSearchRequest,
    FacetedSearchResponse
)

from .insight import InsightRequest, InsightResponse, ApiInfoResponse

__all__ = [
    # Consent schemas
    'ConsentEventCreate',
    'ConsentEventResponse',
    'ConsentLedgerExport',
    'LedgerVerificationResult',
    'ReasonStats',
    'AgentTrainingContext',
    'AgentTrainingExample',
    'BuyerTrustStats',
    'BuyerAccessLevel',
    'FilteredOffer',
    'SuggestionSuccessStats',
    
    # Insight schemas
    'InsightRequest', 
    'InsightResponse', 
    'ApiInfoResponse'
] 