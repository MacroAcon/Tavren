"""
Tests for the Data Service and its integration with consent and packaging.
"""
import pytest
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.data_service import DataService
from app.models import ConsentEvent, DataPackageAudit

# --- Test Data ---
TEST_USER_ID = "test_data_service_user"
TEST_OFFER_ID = "offer-123"
TEST_BUYER_ID = "test_buyer_1"
TEST_DATA_TYPE = "app_usage"

@pytest.fixture
async def setup_test_consent(session: AsyncSession):
    """Create test consent record for data service tests."""
    # Create an accepted consent record
    consent = ConsentEvent(
        user_id=TEST_USER_ID,
        offer_id=TEST_OFFER_ID,
        action="accepted",
        timestamp=datetime.now()
    )
    session.add(consent)
    await session.commit()
    
    # Get the ID
    result = await session.execute(
        f"SELECT id FROM consent_events WHERE user_id = '{TEST_USER_ID}' AND offer_id = '{TEST_OFFER_ID}'"
    )
    consent_id = result.scalar_one()
    
    yield consent_id
    
    # Clean up
    await session.execute(f"DELETE FROM consent_events WHERE user_id = '{TEST_USER_ID}'")
    await session.execute(f"DELETE FROM data_package_audits WHERE user_id = '{TEST_USER_ID}'")
    await session.commit()

async def test_data_service_end_to_end(async_client: AsyncClient, session: AsyncSession, setup_test_consent):
    """Test the full workflow of the data service."""
    # Create data service
    data_service = DataService(session)
    
    # Prepare data for buyer
    data_package = await data_service.prepare_data_for_buyer(
        user_id=TEST_USER_ID,
        buyer_id=TEST_BUYER_ID,
        offer_id=TEST_OFFER_ID,
        data_type=TEST_DATA_TYPE,
        purpose="testing"
    )
    
    # Verify package structure and content
    assert data_package is not None
    assert data_package["tavren_data_package"] == "1.1"
    assert data_package["package_id"] is not None
    assert data_package["data_type"] == TEST_DATA_TYPE
    assert data_package["access_token"] is not None
    assert "purpose" in data_package and data_package["purpose"] == "testing"
    
    # Verify content exists
    assert "content" in data_package
    assert data_package["content"] is not None
    
    # Verify metadata
    assert "metadata" in data_package
    assert "record_count" in data_package["metadata"]
    assert "buyer_id" in data_package["metadata"]
    assert data_package["metadata"]["buyer_id"] == TEST_BUYER_ID

async def test_data_service_consent_validation(async_client: AsyncClient, session: AsyncSession):
    """Test that data service properly validates consent."""
    # Create data service
    data_service = DataService(session)
    
    # Attempt to prepare data without consent - should raise HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await data_service.prepare_data_for_buyer(
            user_id="user_without_consent",
            buyer_id=TEST_BUYER_ID,
            offer_id="nonexistent-offer",
            data_type=TEST_DATA_TYPE,
            purpose="testing"
        )
    
    # Verify exception details
    assert excinfo.value.status_code == 403
    assert "No active consent" in excinfo.value.detail

async def test_data_service_declined_consent(async_client: AsyncClient, session: AsyncSession):
    """Test that data service rejects declined consent."""
    # Create a declined consent record
    consent = ConsentEvent(
        user_id=TEST_USER_ID,
        offer_id="declined-offer-123",
        action="declined",  # Declined consent
        timestamp=datetime.now()
    )
    session.add(consent)
    await session.commit()
    
    # Create data service
    data_service = DataService(session)
    
    # Attempt to prepare data with declined consent - should raise HTTPException
    with pytest.raises(HTTPException) as excinfo:
        await data_service.prepare_data_for_buyer(
            user_id=TEST_USER_ID,
            buyer_id=TEST_BUYER_ID,
            offer_id="declined-offer-123",
            data_type=TEST_DATA_TYPE,
            purpose="testing"
        )
    
    # Verify exception details
    assert excinfo.value.status_code == 403
    assert "No active consent" in excinfo.value.detail
    
    # Clean up
    await session.execute(f"DELETE FROM consent_events WHERE offer_id = 'declined-offer-123'")
    await session.commit()

async def test_access_level_determination(async_client: AsyncClient, session: AsyncSession):
    """Test that access levels are correctly determined."""
    # Create data service
    data_service = DataService(session)
    
    # Test different offer IDs and trust tiers
    test_cases = [
        # offer_id, trust_tier, expected_access_level
        ("offer-0", "standard", "precise_persistent"),
        ("offer-1", "standard", "precise_short_term"),
        ("offer-2", "standard", "anonymous_persistent"),
        ("offer-3", "standard", "anonymous_short_term"),
        # Low trust should downgrade precise to anonymous
        ("offer-0", "low", "anonymous_persistent"),
        ("offer-1", "low", "anonymous_short_term"),
        # But not further downgrade already anonymous levels
        ("offer-2", "low", "anonymous_persistent"),
        ("offer-3", "low", "anonymous_short_term"),
    ]
    
    for offer_id, trust_tier, expected in test_cases:
        access_level = await data_service._determine_access_level(offer_id, trust_tier)
        assert access_level == expected, f"Failed for {offer_id}, {trust_tier}"

async def test_buyer_api_end_to_end(async_client: AsyncClient, session: AsyncSession, setup_test_consent):
    """Test the buyer API endpoints for data requests."""
    # Create a consent event for this test
    consent_id = setup_test_consent
    
    # Call the request data endpoint
    response = await async_client.post(
        "/api/buyers/data/request",
        json={
            "user_id": TEST_USER_ID,
            "data_type": TEST_DATA_TYPE,
            "access_level": "anonymous_short_term",
            "consent_id": TEST_OFFER_ID,  # Using offer_id as consent_id for this test
            "purpose": "testing",
            "buyer_id": TEST_BUYER_ID
        }
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data["tavren_data_package"] == "1.1"
    assert data["package_id"] is not None
    assert data["data_type"] == TEST_DATA_TYPE
    assert "content" in data and data["content"] is not None
    
    # Get the package ID for next test
    package_id = data["package_id"]
    access_token = data["access_token"]
    
    # Call the get data endpoint
    # This would fail in a real environment since we're not persisting packages yet
    # But we can check the endpoint returns the correct error
    response = await async_client.get(
        f"/api/buyers/data/{package_id}?access_token={access_token}"
    )
    
    # Since our get_package_by_id method is not fully implemented, we expect an error
    # The status could be 404 or 500 depending on the implementation
    assert response.status_code in [404, 500]
    
    # Check the available data types endpoint
    response = await async_client.get("/api/buyers/data/available-types")
    assert response.status_code == 200
    data_types = response.json()
    assert len(data_types) > 0
    assert "type" in data_types[0]
    assert "description" in data_types[0] 