from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, JSON, ForeignKey, UniqueConstraint, case
from sqlalchemy.sql import func
from datetime import datetime
from .database import Base
from sqlalchemy.dialects.postgresql import JSONB
from .config import settings
import json
import numpy as np

# Import pgvector's Vector type if using PostgreSQL
if settings.DATABASE_URL.startswith('postgresql'):
    from pgvector.sqlalchemy import Vector

class ConsentEvent(Base):
    __tablename__ = "consent_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    offer_id = Column(String, index=True)
    action = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_reason = Column(Text, nullable=True)
    reason_category = Column(String(32), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True) # Timestamp for processing
    metadata = Column(JSON, nullable=True)  # Store additional consent information (scope, purpose, etc.)

class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    offer_id = Column(String, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class PayoutRequest(Base):
    __tablename__ = "payout_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="pending", index=True) # e.g., pending, paid, failed
    paid_at = Column(DateTime(timezone=True), nullable=True) # Timestamp for processing

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class DataPackageAudit(Base):
    """
    Model to track data packaging operations for audit purposes.
    Records all data package creations, access attempts, and other operations.
    """
    __tablename__ = "data_package_audits"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    operation = Column(String, index=True)  # created, accessed, expired, etc.
    package_id = Column(String, index=True)
    user_id = Column(String, index=True)
    consent_id = Column(String, index=True)
    buyer_id = Column(String, nullable=True, index=True)
    data_type = Column(String)
    access_level = Column(String)
    anonymization_level = Column(String)
    record_count = Column(Integer)
    purpose = Column(String)
    status = Column(String, default="success")  # success, error, warning
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)  # Additional context as needed
    
    def __repr__(self):
        return f"<DataPackageAudit(id={self.id}, operation={self.operation}, package_id={self.package_id})>"

class DataPackageEmbedding(Base):
    """
    Model for storing embeddings of data packages to enable vector search capabilities.
    Uses pgvector extension for PostgreSQL or simulates vector storage for SQLite.
    """
    __tablename__ = "data_package_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String, index=True)
    embedding_type = Column(String, index=True)  # e.g., 'content', 'metadata', 'combined'
    model_name = Column(String)  # Name of the model used for generating the embedding
    dimension = Column(Integer)  # Dimension of the embedding vector
    
    # Conditionally use pgvector Vector type or fallback to JSON string
    if settings.DATABASE_URL.startswith('postgresql'):
        # Use PostgreSQL vector type from pgvector
        embedding = Column(Vector(settings.EMBEDDING_DIMENSION))
    
    # Always keep JSON serialized version for backup and cross-DB compatibility
    embedding_json = Column(Text)
    
    # Text search index to help with hybrid search
    text_content = Column(Text, nullable=True)  # Original text that was embedded
    # Metadata about the embedding
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationship to data package audit (optional)
    audit_id = Column(Integer, ForeignKey("data_package_audits.id"), nullable=True)
    
    __table_args__ = (
        UniqueConstraint('package_id', 'embedding_type', name='uix_package_embedding_type'),
    )
    
    def get_embedding_vector(self):
        """
        Returns the embedding vector, handling both pgvector and JSON storage methods.
        """
        if settings.DATABASE_URL.startswith('postgresql') and hasattr(self, 'embedding') and self.embedding is not None:
            return self.embedding
        else:
            # Fallback to JSON if vector not available
            return json.loads(self.embedding_json)
    
    def __repr__(self):
        return f"<DataPackageEmbedding(id={self.id}, package_id={self.package_id}, model={self.model_name})>"

class RetrievalMetric(Base):
    """
    Model for storing RAG retrieval metrics and performance data.
    Tracks query, results, relevance, and performance metrics.
    """
    __tablename__ = "retrieval_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    query_text = Column(Text)  # Original query text
    result_count = Column(Integer)  # Number of results returned
    latency_ms = Column(Float)  # Query processing time in milliseconds
    user_id = Column(String, index=True, nullable=True)  # Optional user ID
    session_id = Column(String, index=True)  # Session ID for grouping queries
    timestamp = Column(DateTime(timezone=True), index=True)  # When the query was executed
    
    # List of returned package IDs (stored as JSON array)
    result_package_ids = Column(JSON, default=list)
    
    # List of known relevant package IDs (for evaluation)
    relevant_package_ids = Column(JSON, nullable=True)
    
    # Evaluation metrics
    precision = Column(Float, nullable=True)  # Precision score
    recall = Column(Float, nullable=True)  # Recall score
    mrr = Column(Float, nullable=True)  # Mean Reciprocal Rank
    ndcg = Column(Float, nullable=True)  # Normalized Discounted Cumulative Gain
    user_rating = Column(Integer, nullable=True)  # User rating (1-5)
    
    # Additional metadata
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<RetrievalMetric(id={self.id}, query={self.query_text[:20]}..., results={self.result_count})>"

class RetrievalFeedback(Base):
    """
    Model for storing user feedback on RAG results.
    """
    __tablename__ = "retrieval_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    metric_id = Column(Integer, ForeignKey("retrieval_metrics.id"), index=True)
    user_id = Column(String, index=True, nullable=True)  # User who provided feedback
    rating = Column(Integer)  # User rating (1-5)
    feedback_text = Column(Text, nullable=True)  # Optional text feedback
    
    # Lists of helpful and unhelpful result IDs
    helpful_result_ids = Column(JSON, default=list)
    unhelpful_result_ids = Column(JSON, default=list)
    
    timestamp = Column(DateTime(timezone=True), index=True)
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<RetrievalFeedback(id={self.id}, metric_id={self.metric_id}, rating={self.rating})>"

class ABTestConfig(Base):
    """
    Model for A/B testing configurations for RAG strategies.
    """
    __tablename__ = "ab_test_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # Test name (e.g., "chunk_size_test")
    description = Column(Text, nullable=True)  # Test description
    variants = Column(JSON)  # Dictionary of test variants and their parameters
    traffic_allocation = Column(JSON)  # Traffic allocation by variant
    active = Column(Boolean, default=True)  # Whether this test is active
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<ABTestConfig(id={self.id}, name={self.name}, active={self.active})>"

class EmbeddingParameter(Base):
    """
    Model for storing embedding parameter configurations for fine-tuning.
    """
    __tablename__ = "embedding_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Parameter set name
    model_name = Column(String, index=True)  # Associated model name
    parameters = Column(JSON)  # Embedding parameters (dimensions, training params, etc.)
    description = Column(Text, nullable=True)  # Description of parameter set
    active = Column(Boolean, default=False)  # Whether these are the active parameters
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    metadata = Column(JSON, default=dict)
    
    __table_args__ = (
        # Only one active parameter set per model
        UniqueConstraint('model_name', 'active', name='uix_model_active_params',
                         postgresql_where=active.is_(True)),
    )
    
    def __repr__(self):
        return f"<EmbeddingParameter(id={self.id}, name={self.name}, model={self.model_name})>"