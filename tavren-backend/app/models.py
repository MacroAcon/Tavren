from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, JSON
from sqlalchemy.sql import func
from .database import Base

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