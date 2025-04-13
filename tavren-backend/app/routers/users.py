from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.schemas import UserDisplay
from app.models import User
from app.auth import get_current_active_user

# Get logger
log = logging.getLogger("app")

# Create router
router = APIRouter(
    prefix="/api/user",
    tags=["user"]
)

# User profile schemas
class UserProfileResponse(UserDisplay):
    fullName: str
    bio: Optional[str] = None
    avatarUrl: Optional[str] = None
    joinDate: datetime
    lastActive: datetime
    verifiedEmail: bool = False
    verifiedPhone: bool = False
    twoFactorEnabled: bool = False

class UserProfileUpdate(BaseModel):
    fullName: Optional[str] = None
    email: Optional[str] = None
    bio: Optional[str] = None

# Notification preferences schema
class NotificationPreferences(BaseModel):
    emailNotifications: bool = True
    pushNotifications: bool = True
    smsNotifications: bool = False
    preferredContactMethod: str = "email"  # email, sms, push, all, none

# User preferences schema
class UserPreferences(BaseModel):
    privacyPosture: str = "balanced"  # conservative, balanced, liberal
    consentPosture: str = "moderate"  # strict, moderate, relaxed
    autoAcceptTrustedSources: bool = True
    autoRejectLowTrust: bool = True
    minimumTrustTier: int = 3
    
# Trust score schema
class TrustScoreResponse(BaseModel):
    overall_score: float  # 0.0 - 1.0 score
    data_quality_score: float
    participation_score: float
    consistency_score: float
    factors: Dict[str, float]
    last_updated: datetime

# Compensation model schema
class CompensationBreakdown(BaseModel):
    base_rate: float
    quality_multiplier: float
    participation_bonus: float
    total_rate: float
    estimated_monthly: float
    historical_average: float

# Get user profile
@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's profile information
    """
    log.info(f"Fetching profile for user: {current_user.username}")
    
    # In a real implementation, you would fetch additional profile data
    # For now, we'll create a mock response based on the user model
    profile = UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_active=current_user.is_active,
        fullName=f"{current_user.username.title()} User",  # Mock name
        bio="Privacy conscious user",
        avatarUrl=f"https://i.pravatar.cc/150?u={current_user.username}",
        joinDate=datetime.now() - timedelta(days=90),  # Mock join date
        lastActive=datetime.now(),
        verifiedEmail=True,
        verifiedPhone=False,
        twoFactorEnabled=False
    )
    
    return profile

# Update user profile
@router.patch("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's profile information
    """
    log.info(f"Updating profile for user: {current_user.username}")
    
    # In a real implementation, you would update the user record
    # For now, we'll just return a mock updated profile
    
    # Validate email if provided (just a basic check for demo)
    if profile_update.email and "@" not in profile_update.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    profile = UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=profile_update.email or current_user.email,
        is_active=current_user.is_active,
        fullName=profile_update.fullName or f"{current_user.username.title()} User",
        bio=profile_update.bio or "Privacy conscious user",
        avatarUrl=f"https://i.pravatar.cc/150?u={current_user.username}",
        joinDate=datetime.now() - timedelta(days=90),
        lastActive=datetime.now(),
        verifiedEmail=True,
        verifiedPhone=False,
        twoFactorEnabled=False
    )
    
    return profile

# Get user preferences
@router.get("/preferences", response_model=UserPreferences)
async def get_user_preferences(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's privacy and consent preferences
    """
    log.info(f"Fetching preferences for user: {current_user.username}")
    
    # In a real implementation, you would fetch from the database
    # For now, we'll return default preferences
    preferences = UserPreferences(
        privacyPosture="balanced",
        consentPosture="moderate",
        autoAcceptTrustedSources=True,
        autoRejectLowTrust=True,
        minimumTrustTier=3
    )
    
    return preferences

# Update user preferences
@router.patch("/preferences", response_model=dict)
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's privacy and consent preferences
    """
    log.info(f"Updating preferences for user: {current_user.username}")
    
    # In a real implementation, you would update the database
    # For now, we'll just return a success message
    
    return {"success": True, "message": "Preferences updated successfully"}

# Get notification settings
@router.get("/notifications", response_model=NotificationPreferences)
async def get_notification_settings(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's notification preferences
    """
    log.info(f"Fetching notification settings for user: {current_user.username}")
    
    # In a real implementation, you would fetch from the database
    # For now, we'll return default notification settings
    notifications = NotificationPreferences(
        emailNotifications=True,
        pushNotifications=True,
        smsNotifications=False,
        preferredContactMethod="email"
    )
    
    return notifications

# Update notification settings
@router.patch("/notifications", response_model=dict)
async def update_notification_settings(
    notifications: NotificationPreferences,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the current user's notification preferences
    """
    log.info(f"Updating notification settings for user: {current_user.username}")
    
    # In a real implementation, you would update the database
    # For now, we'll just return a success message
    
    return {"success": True, "message": "Notification settings updated successfully"}

# Get trust score
@router.get("/trust-score", response_model=TrustScoreResponse)
async def get_trust_score(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's trust score and factors contributing to it
    """
    log.info(f"Fetching trust score for user: {current_user.username}")
    
    # In a real implementation, you would calculate this from user history
    # For now, we'll return mock data
    trust_score = TrustScoreResponse(
        overall_score=0.87,
        data_quality_score=0.92,
        participation_score=0.85,
        consistency_score=0.84,
        factors={
            "consent_compliance": 0.95,
            "data_freshness": 0.88,
            "response_rate": 0.82,
            "verification_level": 0.90,
            "review_accuracy": 0.79
        },
        last_updated=datetime.now() - timedelta(days=2)
    )
    
    return trust_score

# Get compensation model
@router.get("/compensation-breakdown", response_model=CompensationBreakdown)
async def get_compensation_breakdown(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current user's compensation model details
    """
    log.info(f"Fetching compensation breakdown for user: {current_user.username}")
    
    # In a real implementation, you would calculate this based on user activity
    # For now, we'll return mock data
    compensation = CompensationBreakdown(
        base_rate=0.15,  # $0.15 per data point
        quality_multiplier=1.25,  # 25% bonus for high quality data
        participation_bonus=0.05,  # $0.05 bonus for consistent participation
        total_rate=0.23,  # $0.23 effective rate per data point
        estimated_monthly=18.40,  # $18.40 estimated monthly earnings
        historical_average=22.75  # $22.75 historical monthly average
    )
    
    return compensation 