import pytest
from httpx import AsyncClient
import json
import uuid
from datetime import datetime

# Helper function to create a test A2A request message
def create_test_request(data_type="app_usage", access_level="anonymous_short_term", compensation=0.5):
    return {
        "a2a_version": "0.1",
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "sender": "agent:buyer/test-org",
        "recipient": "agent:tavren/anon:user1",
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
                "source": "test_agent"
            },
            "mcp_context": {
                "purpose": "testing",
                "expiry": datetime.now().isoformat()
            }
        }
    }

@pytest.mark.asyncio
async def test_agent_message_processing(async_client: AsyncClient, override_get_db):
    """Test the agent message processing endpoint."""
    
    # Create a test request message for an acceptable data access
    test_message = create_test_request()
    
    # Get auth headers (will need to implement a test auth fixture)
    # For now, we'll assume auth is disabled for testing or handled by a fixture
    
    response = await async_client.post("/api/agent/message", json=test_message)
    assert response.status_code == 200
    
    data = response.json()
    assert data["message_type"] == "RESPONSE"
    assert data["sender"] == test_message["recipient"]
    assert data["recipient"] == test_message["sender"]
    assert data["content"]["body"]["status"] == "accepted"
    assert "data_payload" in data["content"]["body"]
    assert "consent_id" in data["metadata"]["tavren"]
    assert data["metadata"]["tavren"]["consent_id"] is not None

@pytest.mark.asyncio
async def test_agent_message_decline(async_client: AsyncClient, override_get_db):
    """Test the agent message processing when request should be declined."""
    
    # Create a test request message that should be declined
    test_message = create_test_request(access_level="precise_persistent")
    
    response = await async_client.post("/api/agent/message", json=test_message)
    assert response.status_code == 200
    
    data = response.json()
    assert data["message_type"] == "RESPONSE"
    assert data["content"]["body"]["status"] == "declined"
    assert "data_payload" not in data["content"]["body"]
    assert "alternative_suggestion" in data["content"]["body"]
    assert data["metadata"]["tavren"]["consent_id"] is None

@pytest.mark.asyncio
async def test_agent_message_validation(async_client: AsyncClient, override_get_db):
    """Test validation of incoming agent messages."""
    
    # Create an invalid message (missing required fields)
    invalid_message = {
        "sender": "agent:buyer/test-org",
        "message_type": "REQUEST",
        # Missing other required fields
    }
    
    response = await async_client.post("/api/agent/message", json=invalid_message)
    assert response.status_code == 400
    
    # Response should contain error details
    data = response.json()
    assert "detail" in data
    assert "missing" in data["detail"].lower()

@pytest.mark.asyncio
async def test_agent_logs(async_client: AsyncClient, override_get_db):
    """Test the agent logs endpoint."""
    
    response = await async_client.get("/api/agent/logs/user1")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "logs" in data
    assert isinstance(data["logs"], list)