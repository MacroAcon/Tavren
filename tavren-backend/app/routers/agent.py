from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import uuid
from typing import Dict, Any
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas import UserDisplay
from app.auth import get_current_active_user
from app.services.data_packaging import DataPackagingService, get_data_packaging_service

# Get logger
log = logging.getLogger("app")

# Create router
router = APIRouter(
    prefix="/api/agent",
    tags=["agent"]
)

# Mock user preference data (in production, this would come from the database)
# In a real implementation, this would be fetched from the user's consent wallet
USER_PREFERENCES = {
    "user1": {
        "user_id": "user1",
        "preference_profile": {
            "app_usage": {
                "accepted_tiers": ["anonymous_short_term"],
                "rejected_tiers": ["precise_persistent"]
            },
            "location": {
                "accepted_tiers": ["anonymous_short_term"],
                "rejected_tiers": ["precise_persistent", "anonymous_persistent"]
            }
        }
    }
}

# Function to check if request aligns with user preferences
async def check_consent_alignment(request: Dict[str, Any], user_id: str, db: AsyncSession) -> tuple[bool, str]:
    """Check if the agent request aligns with user's consent preferences."""
    try:
        # In production, fetch user preferences from database
        # In this mock implementation, we use the in-memory dictionary
        user_preferences = USER_PREFERENCES.get(user_id)
        if not user_preferences:
            return False, f"User {user_id} not found or has no preference profile"
        
        data_type = request["content"]["body"]["data_type"]
        access_level = request["content"]["body"]["access_level"]
        
        # Check if data type exists in user preferences
        if data_type not in user_preferences["preference_profile"]:
            return False, f"Data type '{data_type}' not available for sharing"
        
        # Check if access level is accepted for this data type
        if access_level not in user_preferences["preference_profile"][data_type]["accepted_tiers"]:
            return False, f"Access level '{access_level}' rejected for '{data_type}'"
        
        return True, "Request aligned with user consent preferences"
    except KeyError as e:
        log.error(f"Missing field in request: {e}", exc_info=True)
        return False, f"Invalid request format: missing required field {e}"
    except Exception as e:
        log.error(f"Error checking consent alignment: {e}", exc_info=True)
        return False, "Error validating consent alignment"

@router.post("/message", response_model=Dict[str, Any])
async def process_agent_message(
    message: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserDisplay = Depends(get_current_active_user),
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service)
):
    """
    Process incoming A2A messages from external agents.
    
    This endpoint handles requests from external agents seeking data,
    validates them against user consent preferences, and generates
    appropriate responses with A2A + MCP formatting.
    """
    log.info(f"Processing agent message of type {message.get('message_type', 'UNKNOWN')}")
    
    try:
        # Validate request format (basic checks)
        required_fields = ["a2a_version", "message_id", "timestamp", "sender", "recipient", "message_type", "content"]
        for field in required_fields:
            if field not in message:
                raise HTTPException(status_code=400, detail=f"Invalid message format: missing '{field}'")
        
        # Extract user_id from recipient field
        # Expected format: "agent:tavren/anon:<user_id>"
        recipient = message["recipient"]
        try:
            user_id_part = recipient.split("/")[-1]
            if user_id_part.startswith("anon:"):
                user_id = user_id_part[5:]
            else:
                user_id = user_id_part
        except:
            raise HTTPException(status_code=400, detail=f"Invalid recipient format: {recipient}")
        
        # Generate response based on message type
        if message["message_type"] == "REQUEST":
            # Validate consent alignment
            is_aligned, reason = await check_consent_alignment(message, user_id, db)
            
            # Create response message
            response = {
                "a2a_version": message["a2a_version"],
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "sender": message["recipient"],  # Swap sender/recipient
                "recipient": message["sender"],
                "message_type": "RESPONSE",
                "content": {
                    "format": "application/json",
                    "body": {
                        "request_id": message["message_id"],
                        "status": "accepted" if is_aligned else "declined",
                        "reason": reason
                    }
                },
                "metadata": {
                    "epistemic_status": {
                        "confidence": "high",
                        "source": "tavren_consent_engine"
                    },
                    "mcp_context": message["metadata"].get("mcp_context", {}),
                    "tavren": {
                        "consent_id": str(uuid.uuid4()) if is_aligned else None,
                        "user_trust_score": 85,  # Mock value - would be fetched from user profile
                        "agent_version": "tavren-agent-v3"
                    }
                }
            }
            
            # If accepted, include data payload details
            if is_aligned:
                data_type = message["content"]["body"]["data_type"]
                consent_id = response["metadata"]["tavren"]["consent_id"]
                purpose = message["metadata"].get("mcp_context", {}).get("purpose", "unspecified")
                
                # Update to point to the new payload endpoint
                response["content"]["body"]["data_payload"] = {
                    "format": "anonymized_json",
                    "availability": "immediate",
                    "access_url": f"/api/agent/data/payload/{consent_id}"
                }
                
                # In a real implementation, we would log the consent action and reward
                # db.add(ConsentEvent(user_id=user_id, offer_id=consent_id, action="accepted"))
                # db.add(Reward(user_id=user_id, offer_id=consent_id, amount=message["content"]["body"]["compensation"]))
                # await db.commit()
                
            # If declined, include alternative suggestion if possible
            else:
                data_type = message["content"]["body"]["data_type"]
                access_level = message["content"]["body"]["access_level"]
                compensation = message["content"]["body"].get("compensation", 0)
                
                # Get user preferences and suggest alternative if possible
                user_preferences = USER_PREFERENCES.get(user_id)
                if user_preferences and data_type in user_preferences["preference_profile"]:
                    accepted_tiers = user_preferences["preference_profile"][data_type]["accepted_tiers"]
                    if accepted_tiers:
                        response["content"]["body"]["alternative_suggestion"] = {
                            "data_type": data_type,
                            "access_level": accepted_tiers[0],
                            "estimated_compensation": round(compensation * 0.8, 2)
                        }
            
            # Log action
            action = "accepted" if is_aligned else "declined"
            log.info(f"Agent request {action}: {message['message_id']} (User: {user_id})")
            
            return response
            
        elif message["message_type"] == "RESPONSE":
            # Handle response messages (future implementation)
            log.info(f"Received RESPONSE message: {message['message_id']}")
            # For now, just echo back a simple acknowledgment
            return {
                "a2a_version": message["a2a_version"],
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "sender": message["recipient"],
                "recipient": message["sender"],
                "message_type": "INFORMATION",
                "content": {
                    "format": "application/json",
                    "body": {
                        "acknowledged": True,
                        "response_id": message["message_id"]
                    }
                }
            }
            
        else:
            # Handle other message types
            log.warning(f"Unsupported message type: {message['message_type']}")
            return {
                "a2a_version": message["a2a_version"],
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "sender": message["recipient"],
                "recipient": message["sender"],
                "message_type": "INFORMATION",
                "content": {
                    "format": "application/json",
                    "body": {
                        "status": "error",
                        "detail": f"Unsupported message type: {message['message_type']}"
                    }
                }
            }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        log.error(f"Error processing agent message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/logs/{user_id}")
async def get_agent_logs(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Get logs of agent interactions for a specific user.
    
    This endpoint retrieves the history of A2A message exchanges for a user.
    In production, this would query the database for message logs.
    """
    # This is a placeholder - in production, fetch real logs from database
    log.info(f"Fetching agent logs for user {user_id}")
    
    # Mock response for now
    return {
        "user_id": user_id,
        "total_messages": 0,
        "logs": []
    }

@router.get("/data/payload/{consent_id}")
async def get_data_payload(
    consent_id: str,
    db: AsyncSession = Depends(get_db),
    data_packaging_service: DataPackagingService = Depends(get_data_packaging_service)
):
    """
    Retrieve packaged data payload for an approved consent request.
    
    This endpoint serves the actual data that was approved in a previous
    agent message exchange. It uses the consent_id to verify authorization
    and packages the data according to the original access level.
    """
    log.info(f"Data payload requested for consent ID: {consent_id}")
    
    # In a real implementation, we would:
    # 1. Verify that the consent_id exists and is valid
    # 2. Check that it hasn't expired
    # 3. Retrieve the original request details (user_id, data_type, access_level)
    
    # For the POC, we'll use mock values
    # In production, these would be fetched from the database based on consent_id
    user_id = "user1"
    data_type = "app_usage"
    access_level = "anonymous_short_term"
    purpose = "retail_insights"
    
    try:
        # Package the data based on the original request parameters
        packaged_data = await data_packaging_service.package_data(
            user_id=user_id,
            data_type=data_type,
            access_level=access_level,
            consent_id=consent_id,
            purpose=purpose
        )
        
        # Log the data access
        log.info(f"Data payload served for consent ID {consent_id} ({data_type})")
        
        return packaged_data
        
    except Exception as e:
        log.error(f"Error generating data payload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating data payload: {str(e)}")

@router.get("/exchanges/{user_id}")
async def get_agent_exchanges(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserDisplay = Depends(get_current_active_user)
):
    """
    Get history of agent exchanges for a specific user.
    
    This endpoint retrieves all agent request-response exchanges
    for a user, including their consent decisions and compensation.
    """
    log.info(f"Fetching agent exchanges for user {user_id}")
    
    # In production, fetch real exchanges from database
    # For POC, return mock data
    
    # Generate some mock exchanges
    exchanges = [
        {
            "exchange_id": "ex_001",
            "timestamp": (datetime.now().replace(microsecond=0) - timedelta(days=2, hours=3)).isoformat(),
            "buyer_id": "org123",
            "data_type": "app_usage",
            "access_level": "anonymous_short_term",
            "purpose": "retail_behavioral_insights",
            "compensation": 0.55,
            "status": "accepted",
            "consent_id": "consent_aa1"
        },
        {
            "exchange_id": "ex_002",
            "timestamp": (datetime.now().replace(microsecond=0) - timedelta(days=1, hours=5)).isoformat(),
            "buyer_id": "org456",
            "data_type": "location",
            "access_level": "precise_persistent",
            "purpose": "transportation_optimization",
            "compensation": 0.85,
            "status": "declined",
            "alternative_suggested": True,
            "alternative": {
                "access_level": "anonymous_short_term",
                "compensation": 0.65
            }
        },
        {
            "exchange_id": "ex_003",
            "timestamp": datetime.now().replace(microsecond=0).isoformat(),
            "buyer_id": "org789",
            "data_type": "browsing_history",
            "access_level": "anonymous_short_term",
            "purpose": "content_recommendations",
            "compensation": 0.40,
            "status": "accepted",
            "consent_id": "consent_cc3"
        }
    ]
    
    return {
        "user_id": user_id,
        "total_exchanges": len(exchanges),
        "exchanges": exchanges
    }
