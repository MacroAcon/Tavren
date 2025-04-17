"""
Example optimized router using the new utilities.

This shows how to use the router factory and CRUD utilities to create
a router with minimal code.
"""

from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any

from ..database import get_db
from ..models import ConsentEvent, Reward
from ..schemas.consent import ConsentEventCreate, ConsentEventResponse
from ..schemas.payment import RewardCreate, RewardDisplay
from ..utils.router_factory import generate_crud_router
from ..utils.crud_utils import format_success_response, format_error_response, get_by_id_or_404
from ..dependencies import get_current_user, get_current_active_user

# Custom handler for getting consent events by user
async def get_user_consent_events(
    user_id: str,
    skip: int = Query(0, description="Number of records to skip"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get consent events for a specific user."""
    # Verify user is authorized
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's consent events"
        )
    
    # Query events
    query = ConsentEvent.__table__.select().where(
        ConsentEvent.user_id == user_id
    ).offset(skip).limit(limit)
    
    result = await db.execute(query)
    events = result.fetchall()
    
    return format_success_response(
        data=events,
        message=f"Retrieved {len(events)} consent events for user {user_id}"
    )

# Generate consent event router
consent_event_router = generate_crud_router(
    model=ConsentEvent,
    create_schema=ConsentEventCreate,
    response_schema=ConsentEventResponse,
    prefix="/consent-events",
    tags=["consent"],
    auth_dependency=get_current_active_user,
    # Add custom handlers
    custom_handlers={
        "get_user_events": get_user_consent_events
    },
    # Configure additional route
    route_config={
        "get_user_events": {
            "path": "/user/{user_id}",
            "methods": ["GET"],
            "summary": "Get user consent events",
            "description": "Retrieve all consent events for a specific user"
        }
    }
)

# Custom handler for user rewards
async def get_user_rewards(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get rewards for a specific user."""
    # Security check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this user's rewards"
        )
    
    # Query rewards
    query = Reward.__table__.select().where(Reward.user_id == user_id)
    result = await db.execute(query)
    rewards = result.fetchall()
    
    # Calculate total
    total_rewards = sum(r.amount for r in rewards)
    
    return format_success_response(
        data={
            "rewards": rewards,
            "total": total_rewards
        },
        message=f"Retrieved {len(rewards)} rewards for user {user_id}"
    )

# Generate reward router with custom handlers
reward_router = generate_crud_router(
    model=Reward,
    create_schema=RewardCreate,
    response_schema=RewardDisplay,
    prefix="/rewards",
    tags=["payment"],
    auth_dependency=get_current_active_user,
    # Add custom handlers
    custom_handlers={
        "get_user_rewards": get_user_rewards
    },
    # Configure routes
    route_config={
        "get_user_rewards": {
            "path": "/user/{user_id}",
            "methods": ["GET"],
            "summary": "Get user rewards",
            "description": "Retrieve all rewards for a specific user"
        },
        # Override default routes
        "create": {
            "auth_dependency": get_current_active_user  # Only active users can create
        }
    },
    # Exclude some default routes
    exclude_routes=["delete"]  # Don't allow reward deletion
) 