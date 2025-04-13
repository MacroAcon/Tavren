from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
import logging
from typing import List

from app.database import get_db
from app.models import ConsentEvent
from app.schemas import (
    ConsentEventCreate,
    ReasonStats,
    AgentTrainingExample,
    AgentTrainingContext,
    SuggestionSuccessStats,
    UserDisplay
)
from app.auth import get_current_active_user
from app.utils.response_utils import handle_exception
from app.utils.db_utils import safe_commit
from app.logging.log_utils import log_api_request, log_exception
from app.constants.status import HTTP_500_INTERNAL_SERVER_ERROR
from app.constants.consent import (
    ACTION_DECLINED,
    ACTION_ACCEPTED,
    REASON_PRIVACY,
    REASON_TRUST,
    REASON_COMPLEXITY,
    REASON_ALTERNATIVES,
    REASON_UNSPECIFIED
)

# Get logger
log = logging.getLogger("app")

# Create router
router = APIRouter(
    prefix="/api/consent",
    tags=["consent"]
)

@router.post("/decline")
async def log_consent_event(event: ConsentEventCreate, db: AsyncSession = Depends(get_db)):
    """
    Log a consent event in the database.
    
    This endpoint records when a user declines a consent offer, including the reason.
    """
    log_api_request(endpoint="/api/consent/decline", method="POST", params=event.dict())
    log.info(f"Logging consent event for user {event.user_id}, offer {event.offer_id}, action {event.action}")
    
    try:
        db_event = ConsentEvent(**event.dict())
        db.add(db_event)
        await safe_commit(db)
        await db.refresh(db_event)
        log.info(f"Consent event {db_event.id} logged successfully.")
        return {"status": "logged", "id": db_event.id}
    except Exception as e:
        log_exception(e, context="log_consent_event", user_id=event.user_id)
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error logging consent event.")

@router.get("/export/agent-training-log", response_model=List[AgentTrainingExample])
async def export_agent_training_log(db: AsyncSession = Depends(get_db)):
    """
    Export training data for consent agent based on declined consent events.
    
    This endpoint generates training examples that can be used to train an agent
    to better handle consent scenarios.
    """
    log_api_request(endpoint="/api/consent/export/agent-training-log", method="GET")
    log.info("Exporting agent training log")
    
    try:
        query = select(ConsentEvent).filter(ConsentEvent.action == ACTION_DECLINED)
        result = await db.execute(query)
        declined_events = result.scalars().all()
        
        training_data = []
        for event in declined_events:
            reason = event.reason_category or REASON_UNSPECIFIED  # Handle null reasons
            # Construct a simplified user profile based on the reason
            context = AgentTrainingContext(
                user_profile=f"declines offers like {reason}",
                reason_category=reason
            )
            # Create a training example with input, context, and expected output
            example = AgentTrainingExample(
                input=f"Offer: Share data from offer ID {event.offer_id}",
                context=context,
                expected_output="Recommend alternative that respects user concern"
            )
            training_data.append(example)
        
        log.info(f"Exported {len(training_data)} training examples")
        return training_data
    except Exception as e:
        log_exception(e, context="export_agent_training_log")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error exporting agent training log.")


# Create a dashboard router for stats
dashboard_router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard", "consent"]
)

@dashboard_router.get("/reason-stats", response_model=list[ReasonStats])
async def get_reason_stats(db: AsyncSession = Depends(get_db), current_user: UserDisplay = Depends(get_current_active_user)):
    """
    Get statistics about reasons for declining consent.
    
    This endpoint aggregates the reasons users give for declining consent offers.
    """
    log_api_request(endpoint="/api/dashboard/reason-stats", method="GET")
    log.info("Fetching reason statistics for declined consents.")
    
    try:
        query = select(
            ConsentEvent.reason_category,
            func.count().label("count")
        ).filter(
            ConsentEvent.action == ACTION_DECLINED
        ).group_by(
            ConsentEvent.reason_category
        )
        result = await db.execute(query)
        results = result.all()
        
        stats = [ReasonStats(reason_category=reason, count=count) for reason, count in results]
        log.debug(f"Found {len(stats)} reason categories.")
        return stats
    except Exception as e:
        log_exception(e, context="get_reason_stats")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error fetching reason stats.")

@dashboard_router.get("/suggestion-success", response_model=SuggestionSuccessStats)
async def get_suggestion_success_stats(db: AsyncSession = Depends(get_db), current_user: UserDisplay = Depends(get_current_active_user)):
    """
    Get statistics about the success rate of consent alternatives.
    
    This endpoint calculates how often suggested alternatives are accepted by users.
    """
    log_api_request(endpoint="/api/dashboard/suggestion-success", method="GET")
    log.info("Fetching suggestion success statistics.")
    
    try:
        # Reasons that trigger a suggestion
        suggestion_triggers = [REASON_PRIVACY, REASON_TRUST, REASON_COMPLEXITY]
        
        # Count events where a suggestion was offered
        # These are declines with reasons in the trigger list
        suggestions_offered_query = select(func.count(ConsentEvent.id)).filter(
            ConsentEvent.action == ACTION_DECLINED,
            ConsentEvent.reason_category.in_(suggestion_triggers)
        )
        suggestions_offered_result = await db.execute(suggestions_offered_query)
        suggestions_offered = suggestions_offered_result.scalar_one_or_none() or 0 # Ensure we get 0 if None
        
        # Count events where a suggested alternative was accepted
        # In a real app, this would trace back to the original decline event
        # For demo, we'll use a pattern in the offer_id or reason_category
        # (e.g., reason_category='suggested_alternative')
        suggestions_accepted_query = select(func.count(ConsentEvent.id)).filter(
            ConsentEvent.action == ACTION_ACCEPTED,
            ConsentEvent.reason_category == REASON_ALTERNATIVES # Assuming this category marks accepted suggestions
            # Or potentially: ConsentEvent.offer_id.like("%alternative%")
        )
        suggestions_accepted_result = await db.execute(suggestions_accepted_query)
        suggestions_accepted = suggestions_accepted_result.scalar_one_or_none() or 0 # Ensure we get 0 if None
        
        # Calculate acceptance rate (avoid division by zero)
        acceptance_rate = 0.0
        if suggestions_offered > 0:
            acceptance_rate = round((suggestions_accepted / suggestions_offered) * 100, 2)
        
        log.info(f"Suggestion success stats: {suggestions_offered} offered, {suggestions_accepted} accepted, {acceptance_rate}% rate")
        
        return SuggestionSuccessStats(
            suggestions_offered=suggestions_offered,
            suggestions_accepted=suggestions_accepted,
            acceptance_rate=acceptance_rate
        )
    except Exception as e:
        log_exception(e, context="get_suggestion_success_stats")
        handle_exception(e, HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error fetching suggestion success stats.") 