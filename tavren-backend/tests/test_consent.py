import pytest
from fastapi.testclient import TestClient

from app.models import ConsentEvent

# Test consent log endpoint
def test_log_consent_event(client):
    """Test that consent events are properly logged to the database."""
    event_data = {
        "user_id": "test_user_1",
        "offer_id": "buyer-1-offer-abc",
        "action": "declined",
        "reason_category": "privacy",
        "user_reason": "Too invasive"
    }
    response = client.post("/api/consent/decline", json=event_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "logged"
    assert "id" in data
    assert isinstance(data["id"], int)

def test_log_consent_event_invalid_data(client):
    """Test logging consent event with invalid data (e.g., missing fields)."""
    # Missing 'action'
    invalid_data = {
        "user_id": "invalid_user",
        "offer_id": "offer-invalid",
        "reason_category": "other"
    }
    response = client.post("/api/consent/decline", json=invalid_data)
    assert response.status_code == 422 # Unprocessable Entity

    # Invalid 'action' value
    invalid_data_2 = {
        "user_id": "invalid_user_2",
        "offer_id": "offer-invalid-2",
        "action": "maybe", # Invalid action
        "reason_category": "other"
    }
    response = client.post("/api/consent/decline", json=invalid_data_2)
    assert response.status_code == 422 # Unprocessable Entity
    # TODO: Add test case for excessively long user_reason if there's a limit.

# Test consent reason statistics endpoint
def test_get_reason_stats(client):
    """Test that reason statistics are properly calculated."""
    # First create some data
    client.post("/api/consent/decline", json={
        "user_id": "stats_user", "offer_id": "o1", "action": "declined", "reason_category": "privacy"
    })
    client.post("/api/consent/decline", json={
        "user_id": "stats_user", "offer_id": "o2", "action": "declined", "reason_category": "cost"
    })
    client.post("/api/consent/decline", json={
        "user_id": "stats_user", "offer_id": "o3", "action": "declined", "reason_category": "privacy"
    })
    
    # Then query the statistics
    response = client.get("/api/dashboard/reason-stats")
    assert response.status_code == 200
    data = response.json()
    
    # Convert to dict for easier assertion, order might vary
    stats_dict = {item["reason_category"]: item["count"] for item in data}
    assert stats_dict["privacy"] == 2
    assert stats_dict["cost"] == 1

def test_get_reason_stats_empty(client):
    """Test getting reason statistics when there are no declined events."""
    # Ensure clean state if tests run independently
    # (Though conftest fixture handles DB cleanup)
    response = client.get("/api/dashboard/reason-stats")
    assert response.status_code == 200
    assert response.json() == []

# Test agent training data export
def test_agent_training_export(client, override_get_db):
    """Test that agent training data is properly exported."""
    # Create a declined event
    db = next(override_get_db())
    db_event = ConsentEvent(
        user_id="training_user",
        offer_id="buyer-2-offer-xyz",
        action="declined",
        reason_category="privacy",
        user_reason="I don't want to share my data"
    )
    db.add(db_event)
    db.commit()
    
    # Get training data
    response = client.get("/api/consent/export/agent-training-log")
    assert response.status_code == 200
    data = response.json()
    
    # Should have at least one training example
    assert len(data) > 0
    
    # Find our specific example
    example = None
    for item in data:
        if "buyer-2-offer-xyz" in item["input"]:
            example = item
            break
    
    assert example is not None
    assert example["context"]["reason_category"] == "privacy"
    assert "declines offers like privacy" in example["context"]["user_profile"]
    assert "Recommend alternative" in example["expected_output"]

def test_agent_training_export_no_data(client):
    """Test agent training data export when no consent events exist."""
    response = client.get("/api/consent/export/agent-training-log")
    assert response.status_code == 200
    assert response.json() == [] # Should return empty list

# Test suggestion success statistics
def test_suggestion_success_stats(client):
    """Test that suggestion success statistics are properly calculated."""
    # Create some data
    client.post("/api/consent/decline", json={
        "user_id": "suggestion_user", 
        "offer_id": "offer-123", 
        "action": "declined", 
        "reason_category": "privacy"
    })
    client.post("/api/consent/decline", json={
        "user_id": "suggestion_user", 
        "offer_id": "offer-456", 
        "action": "declined", 
        "reason_category": "trust"
    })
    
    # Add an accepted suggestion
    event_data = {
        "user_id": "suggestion_user",
        "offer_id": "alternative-offer-789",
        "action": "accepted",
        "reason_category": "suggested_alternative"
    }
    response = client.post("/api/consent/decline", json=event_data)
    assert response.status_code == 200
    
    # Query suggestion stats
    response = client.get("/api/dashboard/suggestion-success")
    assert response.status_code == 200
    data = response.json()
    
    # TODO: Expand this test once the suggestion success logic is finalized
    assert "suggestions_offered" in data
    assert "suggestions_accepted" in data
    assert "acceptance_rate" in data

    # TODO: Add more detailed tests for suggestion success stats:
    # - Case with zero suggestions offered.
    # - Case with suggestions offered but none accepted.
    # - Case with multiple accepted suggestions.
    # - Consider filtering by buyer ID or time range if implemented.

def test_suggestion_success_stats_no_data(client):
    """Test suggestion success statistics when no relevant events exist."""
    response = client.get("/api/dashboard/suggestion-success")
    assert response.status_code == 200
    data = response.json()
    # Default state should probably be zeros
    assert data["suggestions_offered"] == 0
    assert data["suggestions_accepted"] == 0
    assert data["acceptance_rate"] == 0.0
    # TODO: Verify this matches the endpoint's actual behavior for no data. 