import pytest
from httpx import AsyncClient # Use AsyncClient for async tests
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Reward, PayoutRequest
from app.config import settings

pytestmark = pytest.mark.asyncio # Mark all tests in this module as async

# --- Helper to get auth headers ---
# We'll need this to test protected endpoints
async def get_auth_headers(client: AsyncClient, username: str = "testuser", password: str = "testpass") -> dict:
    # First, register the user (assuming /register endpoint exists and is unprotected for tests)
    # In a real scenario, you might pre-populate users or have a fixture
    await client.post("/api/auth/register", json={"username": username, "email": f"{username}@test.com", "password": password})

    # Then, log in to get the token
    login_data = {"username": username, "password": password}
    response = await client.post("/api/auth/token", data=login_data)
    response.raise_for_status() # Raise exception for bad status codes
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

# --- Test reward creation --- #
async def test_create_reward(async_client: AsyncClient): # Use async_client fixture
    """Test that rewards can be created and stored correctly."""
    reward_data = {
        "user_id": "reward_user",
        "offer_id": "offer-123",
        "amount": 5.0
    }
    response = await async_client.post("/api/rewards", json=reward_data) # Use await
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == reward_data["user_id"]
    assert data["offer_id"] == reward_data["offer_id"]
    assert data["amount"] == reward_data["amount"]
    assert "id" in data
    assert "timestamp" in data

async def test_create_reward_invalid_data(async_client: AsyncClient):
    """Test reward creation fails with invalid data."""
    reward_data = {
        "user_id": "invalid_reward_user",
        "offer_id": "offer-invalid",
        "amount": -5.0
    }
    response = await async_client.post("/api/rewards", json=reward_data) # Use await
    assert response.status_code == 422

# --- Test wallet balance calculation --- #
async def test_wallet_balance(async_client: AsyncClient, session: AsyncSession): # Use async session fixture
    """Test wallet balance is correctly calculated."""
    user_id = "wallet_user_async"

    # Create rewards directly in the DB using the async session
    session.add(Reward(user_id=user_id, offer_id="o1", amount=10.0))
    session.add(Reward(user_id=user_id, offer_id="o2", amount=15.0))
    await session.commit()

    response = await async_client.get(f"/api/wallet/{user_id}") # Use await
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user_id
    assert data["total_earned"] == 25.0
    assert data["available_balance"] == 25.0
    assert data["is_claimable"]

    # Add a pending payout
    session.add(PayoutRequest(user_id=user_id, amount=20.0, status="pending"))
    await session.commit()

    response = await async_client.get(f"/api/wallet/{user_id}") # Use await
    assert response.status_code == 200
    data = response.json()
    assert data["total_earned"] == 25.0
    assert data["total_claimed"] == 20.0
    assert data["available_balance"] == 5.0
    assert data["is_claimable"] == (5.0 >= settings.MINIMUM_PAYOUT_THRESHOLD)

async def test_wallet_balance_non_existent_user(async_client: AsyncClient):
    """Test fetching wallet balance for a non-existent user."""
    response = await async_client.get("/api/wallet/non_existent_user_async") # Use await
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "non_existent_user"
    assert data["total_earned"] == 0.0
    assert data["total_claimed"] == 0.0
    assert data["available_balance"] == 0.0
    assert data["is_claimable"] == False
    # TODO: Confirm this is the desired behavior for non-existent users.
    # Maybe return 404 instead? Depends on requirements.

# --- Test payout request --- #
async def test_payout_request(async_client: AsyncClient, session: AsyncSession):
    """Test creating a payout request."""
    user_id = "payout_user_async"
    session.add(Reward(user_id=user_id, offer_id="o1", amount=50.0))
    await session.commit()

    payout_data = {"user_id": user_id, "amount": 25.0}
    response = await async_client.post("/api/wallet/claim", json=payout_data) # Use await
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == user_id
    assert data["amount"] == 25.0
    assert data["status"] == "pending"
    
    # Try to request more than available
    payout_data["amount"] = 50.0
    response = await async_client.post("/api/wallet/claim", json=payout_data) # Use await
    assert response.status_code == 400
    
    # Try to request below minimum threshold
    payout_data["amount"] = 1.0
    response = await async_client.post("/api/wallet/claim", json=payout_data) # Use await
    assert response.status_code == 400

async def test_payout_request_non_existent_user(async_client: AsyncClient):
    """Test requesting payout for a non-existent user."""
    payout_data = {
        "user_id": "non_existent_payout_user_async",
        "amount": settings.MINIMUM_PAYOUT_THRESHOLD + 1.0
    }
    response = await async_client.post("/api/wallet/claim", json=payout_data) # Use await
    assert response.status_code == 400

async def test_payout_request_below_minimum_explicit(async_client: AsyncClient, session: AsyncSession):
    """Test explicitly requesting below minimum."""
    user_id = "below_min_user_async"
    session.add(Reward(user_id=user_id, offer_id="o_min", amount=settings.MINIMUM_PAYOUT_THRESHOLD + 5.0))
    await session.commit()

    payout_data = {
        "user_id": user_id,
        "amount": settings.MINIMUM_PAYOUT_THRESHOLD - 1.0
    }
    response = await async_client.post("/api/wallet/claim", json=payout_data) # Use await
    assert response.status_code == 400

# --- Test payout administration (Requires Auth) --- #
async def test_payout_administration(async_client: AsyncClient, session: AsyncSession):
    """Test marking payouts as paid or failed (requires auth)."""
    user_id = "admin_test_user_async"
    session.add(Reward(user_id=user_id, offer_id="o1", amount=100.0))
    payout = PayoutRequest(user_id=user_id, amount=50.0, status="pending")
    session.add(payout)
    await session.commit()
    await session.refresh(payout)
    payout_id = payout.id

    auth_headers = await get_auth_headers(async_client, username="admin_user", password="adminpass")

    # Mark as paid
    response = await async_client.post(f"/api/payouts/{payout_id}/mark-paid", headers=auth_headers) # Use await + headers
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "paid"

    # Try to mark again (should fail)
    response = await async_client.post(f"/api/payouts/{payout_id}/mark-paid", headers=auth_headers) # Use await + headers
    assert response.status_code == 400

    # Create another payout
    payout2 = PayoutRequest(user_id=user_id, amount=25.0, status="pending")
    session.add(payout2)
    await session.commit()
    await session.refresh(payout2)
    payout2_id = payout2.id

    # Mark as failed
    response = await async_client.post(f"/api/payouts/{payout2_id}/mark-failed", headers=auth_headers) # Use await + headers
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "failed"

async def test_payout_administration_unauthorized(async_client: AsyncClient, session: AsyncSession):
    """Test accessing admin endpoints without auth."""
    user_id = "admin_unauth_user_async"
    payout = PayoutRequest(user_id=user_id, amount=10.0, status="pending")
    session.add(payout)
    await session.commit()
    await session.refresh(payout)
    payout_id = payout.id

    response = await async_client.post(f"/api/payouts/{payout_id}/mark-paid") # No headers
    assert response.status_code == 401 # Unauthorized

    response = await async_client.post(f"/api/payouts/{payout_id}/mark-failed") # No headers
    assert response.status_code == 401 # Unauthorized

async def test_payout_administration_non_existent_payout(async_client: AsyncClient):
    """Test administering a non-existent payout (requires auth)."""
    auth_headers = await get_auth_headers(async_client, username="admin_user_nonexist", password="adminpass")
    non_existent_payout_id = 999999
    response = await async_client.post(f"/api/payouts/{non_existent_payout_id}/mark-paid", headers=auth_headers) # Use await + headers
    assert response.status_code == 404

    response = await async_client.post(f"/api/payouts/{non_existent_payout_id}/mark-failed", headers=auth_headers) # Use await + headers
    assert response.status_code == 404

# --- Test payout history --- #
async def test_payout_history(async_client: AsyncClient, session: AsyncSession):
    """Test retrieving payout history."""
    user_id = "history_user_async"
    session.add(Reward(user_id=user_id, offer_id="o1", amount=100.0))
    session.add(PayoutRequest(user_id=user_id, amount=20.0, status="paid"))
    session.add(PayoutRequest(user_id=user_id, amount=30.0, status="pending"))
    session.add(PayoutRequest(user_id=user_id, amount=10.0, status="failed"))
    await session.commit()

    response = await async_client.get(f"/api/wallet/payouts/{user_id}") # Use await
    assert response.status_code == 200
    data = response.json()
    
    assert len(data) == 3
    
    # Check that all statuses are present
    statuses = [payout["status"] for payout in data]
    assert "paid" in statuses
    assert "pending" in statuses
    assert "failed" in statuses

async def test_payout_history_non_existent_user(async_client: AsyncClient):
    """Test retrieving payout history for non-existent user."""
    response = await async_client.get("/api/wallet/payouts/non_existent_history_user_async") # Use await
    assert response.status_code == 200
    assert response.json() == []

# --- Test automatic payout processing (Requires Auth) --- #
async def test_automatic_payout_processing(async_client: AsyncClient, session: AsyncSession):
    """Test the automatic payout processing endpoint (requires auth)."""
    auth_headers = await get_auth_headers(async_client, username="auto_payout_admin", password="adminpass")

    # Setup: Create users and payouts with different trust scores/amounts
    # User 1: High trust, valid amount
    user1 = "auto_user_1"
    session.add(Reward(user_id=user1, offer_id="r1", amount=100.0))
    await session.commit()
    trust_service = TrustService(session) # Need service for setup checks
    # Add rewards/payouts to ensure high trust score
    for _ in range(20): session.add(Reward(user_id=user1, offer_id=f"r{_+2}", amount=1.0))
    for _ in range(5): session.add(PayoutRequest(user_id=user1, amount=1.0, status="paid"))
    await session.commit()
    user1_trust = await trust_service.calculate_user_trust_score(user1)
    assert user1_trust >= settings.AUTO_PAYOUT_MIN_TRUST_SCORE
    session.add(PayoutRequest(user_id=user1, amount=settings.AUTO_PAYOUT_MAX_AMOUNT - 1, status="pending"))

    # User 2: Low trust, valid amount
    user2 = "auto_user_2"
    session.add(Reward(user_id=user2, offer_id="r1", amount=100.0))
    await session.commit()
    user2_trust = await trust_service.calculate_user_trust_score(user2)
    assert user2_trust < settings.AUTO_PAYOUT_MIN_TRUST_SCORE
    session.add(PayoutRequest(user_id=user2, amount=settings.AUTO_PAYOUT_MAX_AMOUNT - 1, status="pending"))

    # User 3: High trust, high amount
    user3 = "auto_user_3"
    # Use same setup as user1 for high trust
    session.add(Reward(user_id=user3, offer_id="r1", amount=200.0))
    for _ in range(20): session.add(Reward(user_id=user3, offer_id=f"r{_+2}", amount=1.0))
    for _ in range(5): session.add(PayoutRequest(user_id=user3, amount=1.0, status="paid"))
    await session.commit()
    user3_trust = await trust_service.calculate_user_trust_score(user3)
    assert user3_trust >= settings.AUTO_PAYOUT_MIN_TRUST_SCORE
    session.add(PayoutRequest(user_id=user3, amount=settings.AUTO_PAYOUT_MAX_AMOUNT + 1, status="pending"))

    await session.commit()

    # Execute endpoint
    response = await async_client.post("/api/payouts/process-auto", headers=auth_headers) # Use await + headers
    assert response.status_code == 200
    data = response.json()

    # Assert summary
    assert data["total_pending"] == 3
    assert data["processed"] == 3
    assert data["marked_paid"] == 1 # Only user1 should be paid
    assert data["skipped_low_trust"] == 1 # User2
    assert data["skipped_high_amount"] == 1 # User3
    assert data["skipped_other_error"] == 0

    # Verify status in DB
    res1 = await session.execute(select(PayoutRequest).filter_by(user_id=user1, status="pending"))
    assert res1.scalar_one_or_none() is None # Should now be paid
    res2 = await session.execute(select(PayoutRequest).filter_by(user_id=user2, status="pending"))
    assert res2.scalar_one_or_none() is not None # Should still be pending
    res3 = await session.execute(select(PayoutRequest).filter_by(user_id=user3, status="pending"))
    assert res3.scalar_one_or_none() is not None # Should still be pending

# --- Add Reward History Test --- #
async def test_reward_history(async_client: AsyncClient, session: AsyncSession):
    """Test retrieving reward history for a user."""
    user_id = "reward_history_user_async"
    session.add(Reward(user_id=user_id, offer_id="offer_hist_1", amount=1.0))
    session.add(Reward(user_id=user_id, offer_id="offer_hist_2", amount=2.5))
    await session.commit()

    response = await async_client.get(f"/api/rewards/history/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["amount"] == 2.5 # Should be newest first
    assert data[1]["amount"] == 1.0

async def test_reward_history_non_existent_user(async_client: AsyncClient):
    """Test retrieving reward history for a non-existent user."""
    response = await async_client.get("/api/rewards/history/non_existent_reward_user")
    assert response.status_code == 200
    assert response.json() == []

# TODO: Add tests for concurrency
# TODO: Add tests for database error handling (mocking needed) 