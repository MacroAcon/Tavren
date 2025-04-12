from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest

# Assuming conftest.py setup is correct and client fixture provides TestClient
# and handles DB setup/teardown

# Import models and schemas needed for testing
from app.models import ConsentEvent, Reward, PayoutRequest
from app.schemas import ConsentEventCreate, RewardCreate, PayoutClaim # Assuming PayoutClaim schema exists
from app.config import settings

def test_read_root_dashboard(client: TestClient):
    """Test accessing the main dashboard HTML page."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    # Check if it looks like HTML content
    assert "text/html" in response.headers["content-type"]
    # Stronger check: assert b"<title>Tavren Trust Signal Dashboard</title>" in response.content
    # Note: This depends on the actual title in your index.html

def test_log_consent_event_success(client: TestClient):
    """Test successfully logging a consent event."""
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

    # Optional: Verify data was actually written to the test DB
    # This requires accessing the override_get_db fixture value somehow
    # or making another API call to retrieve the logged event.

def test_log_consent_event_missing_data(client: TestClient):
    """Test logging consent event with missing required fields (should fail)."""
    event_data = {
        "user_id": "test_user_2",
        # Missing offer_id and action
    }
    response = client.post("/api/consent/decline", json=event_data)
    assert response.status_code == 422 # FastAPI validation error

def test_get_reason_stats_empty(client: TestClient):
    """Test getting reason stats when no declined events exist."""
    response = client.get("/api/dashboard/reason-stats")
    assert response.status_code == 200
    assert response.json() == []

def test_get_reason_stats_with_data(client: TestClient):
    """Test getting reason stats after logging some declined events."""
    # Log some events first
    client.post("/api/consent/decline", json={
        "user_id": "stats_user", "offer_id": "o1", "action": "declined", "reason_category": "privacy"
    })
    client.post("/api/consent/decline", json={
        "user_id": "stats_user", "offer_id": "o2", "action": "declined", "reason_category": "cost"
    })
    client.post("/api/consent/decline", json={
        "user_id": "stats_user", "offer_id": "o3", "action": "declined", "reason_category": "privacy"
    })
    client.post("/api/consent/decline", json={
        "user_id": "stats_user", "offer_id": "o4", "action": "accepted" # Should be ignored
    })

    response = client.get("/api/dashboard/reason-stats")
    assert response.status_code == 200
    data = response.json()

    # Convert to dict for easier assertion, order might vary
    stats_dict = {item["reason_category"]: item["count"] for item in data}
    assert stats_dict == {"privacy": 2, "cost": 1}

# --- TODO: Add more tests --- 
# - Test other HTML endpoints (/buyer-dashboard, /offer-feed, etc.)
# - Test wallet balance calculation (/api/wallet/{user_id})
# - Test payout request creation (/api/wallet/claim) - success and failure (insufficient funds)
# - Test reward history (/api/rewards/history/{user_id})
# - Test payout history (/api/wallet/payouts/{user_id})
# - Test automatic payout processing (/api/payouts/process-auto)
#   - Case: No payouts
#   - Case: Payouts below threshold
#   - Case: Payouts skipped due to trust score
#   - Case: Payouts skipped due to amount limit
#   - Case: Successful payouts
# - Test helper functions directly (calculate_user_balance, calculate_user_trust_score) if needed,
#   although testing via endpoints is often preferred for integration.
# - Test edge cases (e.g., invalid user_id formats, unexpected data) 

# --- Integration Tests ---

@pytest.mark.integration
def test_full_flow_consent_reward_wallet_claim(client: TestClient, override_get_db):
    """Simulates a user declining, getting a reward, checking wallet, and claiming payout."""
    user_id = "integration_user_1"
    buyer_id = "int-buyer-1"
    offer_id_declined = f"buyer-{buyer_id}-offer-decline"
    offer_id_reward = f"buyer-{buyer_id}-offer-reward"

    # 1. Log a decline event
    decline_data = {
        "user_id": user_id,
        "offer_id": offer_id_declined,
        "action": "declined",
        "reason_category": "privacy",
        "user_reason": "Integration test decline"
    }
    response = client.post("/api/consent/decline", json=decline_data)
    assert response.status_code == 200

    # 2. Create a reward for the user
    reward_data = {
        "user_id": user_id,
        "offer_id": offer_id_reward,
        "amount": settings.MINIMUM_PAYOUT_THRESHOLD + 10.0 # Ensure claimable amount
    }
    response = client.post("/api/rewards", json=reward_data)
    assert response.status_code == 200
    reward_amount = reward_data["amount"]

    # 3. Check wallet balance
    response = client.get(f"/api/wallet/{user_id}")
    assert response.status_code == 200
    wallet_data = response.json()
    assert wallet_data["user_id"] == user_id
    assert wallet_data["total_earned"] == reward_amount
    assert wallet_data["available_balance"] == reward_amount
    assert wallet_data["is_claimable"] == True

    # 4. Claim a payout
    claim_amount = settings.MINIMUM_PAYOUT_THRESHOLD + 5.0 # Claim part of the balance
    claim_data = {
        "user_id": user_id,
        "amount": claim_amount
    }
    response = client.post("/api/wallet/claim", json=claim_data)
    assert response.status_code == 200
    payout_data = response.json()
    assert payout_data["user_id"] == user_id
    assert payout_data["amount"] == claim_amount
    assert payout_data["status"] == "pending"
    payout_id = payout_data["id"]

    # 5. Check wallet balance again (should be reduced)
    response = client.get(f"/api/wallet/{user_id}")
    assert response.status_code == 200
    wallet_data_after = response.json()
    assert wallet_data_after["available_balance"] == reward_amount - claim_amount
    assert wallet_data_after["total_claimed"] == claim_amount

    # 6. Check payout history
    response = client.get(f"/api/wallet/payouts/{user_id}")
    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["id"] == payout_id
    assert history[0]["status"] == "pending"

    # 7. Admin: Mark payout as paid
    response = client.post(f"/api/payouts/{payout_id}/mark-paid")
    assert response.status_code == 200
    assert response.json()["status"] == "paid"

    # 8. Check payout history again (status updated)
    response = client.get(f"/api/wallet/payouts/{user_id}")
    assert response.status_code == 200
    history_after = response.json()
    assert history_after[0]["status"] == "paid"

    # TODO: Add integration test for automatic payout processing triggering.
    # TODO: Add integration test covering buyer insights influencing offer feed.
    # TODO: Add integration tests for failure scenarios (e.g., claiming insufficient funds). 