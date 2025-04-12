import json
import uuid
from datetime import datetime, timedelta

# Simulate a user's consent preferences
user_preference_snapshot = {
    "user_id": "anon:4816ab",
    "preference_profile": {
        "app_usage": {
            "accepted_tiers": ["anonymous_short_term"],
            "rejected_tiers": ["precise_persistent"]
        },
        "location": {
            "accepted_tiers": ["anonymous_short_term"]
        }
    }
}

# Simulate an incoming A2A request from a buyer agent
def create_buyer_request(buyer_id, data_type, access_level, purpose, compensation):
    return {
        "a2a_version": "0.1",
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "sender": f"agent:buyer/{buyer_id}",
        "recipient": f"agent:tavren/anon:4816ab",
        "message_type": "REQUEST",
        "content": {
            "format": "application/json",
            "body": {
                "data_type": data_type,
                "access_level": access_level,
                "compensation": compensation
            }
        },
        "metadata": {
            "epistemic_status": {
                "confidence": "high",
                "source": "buyer_agent"
            },
            "mcp_context": {
                "purpose": purpose,
                "expiry": (datetime.now() + timedelta(days=7)).isoformat()
            }
        }
    }

# Function to check if request aligns with user preferences
def check_consent_alignment(request, user_preferences):
    data_type = request["content"]["body"]["data_type"]
    access_level = request["content"]["body"]["access_level"]
    
    # Check if data type exists in user preferences
    if data_type not in user_preferences["preference_profile"]:
        return False, f"Data type '{data_type}' not available for sharing"
    
    # Check if access level is accepted for this data type
    if access_level not in user_preferences["preference_profile"][data_type]["accepted_tiers"]:
        return False, f"Access level '{access_level}' rejected for '{data_type}'"
    
    return True, "Request aligned with user consent preferences"

# Generate Tavren agent response based on consent check
def create_tavren_response(request, is_aligned, reason):
    response = {
        "a2a_version": "0.1",
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "sender": request["recipient"],
        "recipient": request["sender"],
        "message_type": "RESPONSE",
        "content": {
            "format": "application/json",
            "body": {
                "request_id": request["message_id"],
                "status": "accepted" if is_aligned else "declined",
                "reason": reason
            }
        },
        "metadata": {
            "epistemic_status": {
                "confidence": "high",
                "source": "tavren_consent_engine"
            },
            "mcp_context": request["metadata"]["mcp_context"],
            "tavren": {
                "consent_id": str(uuid.uuid4()) if is_aligned else None,
                "user_trust_score": 85,
                "agent_version": "tavren-agent-v3"
            }
        }
    }
    
    # If accepted, include data payload details
    if is_aligned:
        response["content"]["body"]["data_payload"] = {
            "format": "anonymized_json",
            "availability": "immediate",
            "access_url": f"https://api.tavren.io/data/payload/{response['metadata']['tavren']['consent_id']}"
        }
    # If declined, include alternative suggestion
    else:
        alternative_access = None
        data_type = request["content"]["body"]["data_type"]
        
        # Suggest alternatives based on user preferences
        if data_type in user_preference_snapshot["preference_profile"]:
            alternative_access = user_preference_snapshot["preference_profile"][data_type]["accepted_tiers"][0] \
                if user_preference_snapshot["preference_profile"][data_type]["accepted_tiers"] else None
                
        if alternative_access:
            response["content"]["body"]["alternative_suggestion"] = {
                "data_type": data_type,
                "access_level": alternative_access,
                "estimated_compensation": round(request["content"]["body"]["compensation"] * 0.8, 2)
            }
    
    return response

# Simulate a complete exchange
def simulate_exchange():
    print("🤖 Simulating Tavren Agent Integration Demo")
    print("=" * 50)
    
    # Create a buyer request
    buyer_request = create_buyer_request(
        buyer_id="org123",
        data_type="app_usage",
        access_level="precise_persistent",  # This should be rejected based on preferences
        purpose="retail_behavioral_insights",
        compensation=0.75
    )
    
    print("📥 Incoming Buyer Request:")
    print(json.dumps(buyer_request, indent=2))
    print("\n" + "-" * 50 + "\n")
    
    # Check against user preferences
    is_aligned, reason = check_consent_alignment(buyer_request, user_preference_snapshot)
    
    # Generate Tavren response
    tavren_response = create_tavren_response(buyer_request, is_aligned, reason)
    
    print("📋 Consent Alignment Check:")
    print(f"Result: {'✅ ALIGNED' if is_aligned else '❌ NOT ALIGNED'}")
    print(f"Reason: {reason}")
    print("\n" + "-" * 50 + "\n")
    
    print("📤 Tavren Agent Response:")
    print(json.dumps(tavren_response, indent=2))
    
    # Also simulate an accepted request
    print("\n" + "=" * 50 + "\n")
    print("Simulating an alternative request that aligns with user preferences...\n")
    
    aligned_request = create_buyer_request(
        buyer_id="org123",
        data_type="app_usage",
        access_level="anonymous_short_term",  # This should be accepted
        purpose="retail_behavioral_insights",
        compensation=0.5
    )
    
    is_aligned, reason = check_consent_alignment(aligned_request, user_preference_snapshot)
    aligned_response = create_tavren_response(aligned_request, is_aligned, reason)
    
    print("📥 Incoming Buyer Request (Modified):")
    print(json.dumps(aligned_request, indent=2))
    print("\n" + "-" * 50 + "\n")
    
    print("📋 Consent Alignment Check:")
    print(f"Result: {'✅ ALIGNED' if is_aligned else '❌ NOT ALIGNED'}")
    print(f"Reason: {reason}")
    print("\n" + "-" * 50 + "\n")
    
    print("📤 Tavren Agent Response:")
    print(json.dumps(aligned_response, indent=2))

if __name__ == "__main__":
    simulate_exchange()