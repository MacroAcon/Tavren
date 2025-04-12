from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean
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