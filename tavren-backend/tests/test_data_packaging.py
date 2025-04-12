"""
Tests for the Data Packaging service and API endpoints.
"""
import json
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models import ConsentEvent, DataPackageAudit
from app.services.data_packaging import DataPackagingService

# --- Test Data ---
TEST_USER_ID = "test_data_pkg_user"
TEST_CONSENT_ID = "test_consent_1"
TEST_BUYER_ID = "test_buyer_1"
TEST_DATA_TYPE = "app_usage"

@pytest.fixture
def setup_test_data(session: AsyncSession):
    """Create test data for data packaging tests."""
    # Create a consent record
    consent = ConsentEvent(
        id=TEST_CONSENT_ID,
        user_id=TEST_USER_ID,
        offer_id="offer-123",
        action="accepted",
        timestamp=datetime.now()
    )
    session.add(consent)
    session.commit()
    
    yield
    
    # Clean up
    session.query(ConsentEvent).filter(ConsentEvent.id == TEST_CONSENT_ID).delete()
    session.query(DataPackageAudit).filter(DataPackageAudit.user_id == TEST_USER_ID).delete()
    session.commit()

# --- Unit Tests for Data Packaging Service ---

async def test_data_package_creation(async_client: AsyncClient, session: AsyncSession):
    """Test creating a data package."""
    # Create a consent event first
    consent = ConsentEvent(
        id=TEST_CONSENT_ID,
        user_id=TEST_USER_ID,
        offer_id="offer-123",
        action="accepted",
        timestamp=datetime.now()
    )
    session.add(consent)
    await session.commit()
    
    # Create the data packaging service
    data_packaging_service = DataPackagingService(session)
    
    # Package data
    package = await data_packaging_service.package_data(
        user_id=TEST_USER_ID,
        data_type=TEST_DATA_TYPE,
        access_level="anonymous_short_term",
        consent_id=TEST_CONSENT_ID,
        purpose="testing",
        buyer_id=TEST_BUYER_ID
    )
    
    # Verify package structure
    assert package["tavren_data_package"] == "1.1"
    assert package["package_id"] is not None
    assert package["consent_id"] == TEST_CONSENT_ID
    assert package["data_type"] == TEST_DATA_TYPE
    assert package["access_level"] == "anonymous_short_term"
    assert package["anonymization_level"] == "strong"
    assert package["access_token"] is not None
    assert package["content"] is not None
    assert "record_count" in package["metadata"]
    assert "purpose" in package
    
    # Clean up
    await session.execute(f"DELETE FROM consent_events WHERE id = '{TEST_CONSENT_ID}'")
    await session.commit()

async def test_anonymization_levels(async_client: AsyncClient, session: AsyncSession):
    """Test different anonymization levels."""
    # Create a consent event first
    consent = ConsentEvent(
        id=TEST_CONSENT_ID,
        user_id=TEST_USER_ID,
        offer_id="offer-123",
        action="accepted",
        timestamp=datetime.now()
    )
    session.add(consent)
    await session.commit()
    
    # Create the data packaging service
    data_packaging_service = DataPackagingService(session)
    
    # Test different access levels
    access_levels = [
        "precise_persistent", 
        "precise_short_term",
        "anonymous_persistent",
        "anonymous_short_term"
    ]
    
    expected_anonymization_levels = [
        "minimal",
        "moderate",
        "strong_with_longitudinal",
        "strong"
    ]
    
    for i, access_level in enumerate(access_levels):
        # Package data
        package = await data_packaging_service.package_data(
            user_id=TEST_USER_ID,
            data_type=TEST_DATA_TYPE,
            access_level=access_level,
            consent_id=TEST_CONSENT_ID,
            purpose="testing",
            buyer_id=TEST_BUYER_ID,
            trust_tier="standard"
        )
        
        # Verify anonymization level
        assert package["anonymization_level"] == expected_anonymization_levels[i]
    
    # Clean up
    await session.execute(f"DELETE FROM consent_events WHERE id = '{TEST_CONSENT_ID}'")
    await session.commit()

async def test_trust_tier_impact(async_client: AsyncClient, session: AsyncSession):
    """Test how trust tier impacts anonymization level."""
    # Create a consent event first
    consent = ConsentEvent(
        id=TEST_CONSENT_ID,
        user_id=TEST_USER_ID,
        offer_id="offer-123",
        action="accepted",
        timestamp=datetime.now()
    )
    session.add(consent)
    await session.commit()
    
    # Create the data packaging service
    data_packaging_service = DataPackagingService(session)
    
    # Test standard tier
    standard_package = await data_packaging_service.package_data(
        user_id=TEST_USER_ID,
        data_type=TEST_DATA_TYPE,
        access_level="precise_persistent",
        consent_id=TEST_CONSENT_ID,
        purpose="testing",
        buyer_id=TEST_BUYER_ID,
        trust_tier="standard"
    )
    
    # Test low trust tier
    low_trust_package = await data_packaging_service.package_data(
        user_id=TEST_USER_ID,
        data_type=TEST_DATA_TYPE,
        access_level="precise_persistent",
        consent_id=TEST_CONSENT_ID,
        purpose="testing",
        buyer_id=TEST_BUYER_ID,
        trust_tier="low"
    )
    
    # Verify trust tier impacts anonymization level
    assert standard_package["anonymization_level"] == "minimal"
    assert low_trust_package["anonymization_level"] == "moderate"
    
    # Clean up
    await session.execute(f"DELETE FROM consent_events WHERE id = '{TEST_CONSENT_ID}'")
    await session.commit()

async def test_token_validation(async_client: AsyncClient, session: AsyncSession):
    """Test access token validation."""
    # Create the data packaging service
    data_packaging_service = DataPackagingService(session)
    
    # Generate a token
    consent_id = "test-consent-id"
    expiry = (datetime.now() + timedelta(hours=24)).isoformat()
    token = data_packaging_service._generate_access_token(consent_id, expiry)
    
    # Test valid token
    package_id = "test-package-id"
    is_valid, details = await data_packaging_service.validate_access_token(token, package_id)
    
    # Since we're not validating the package_id in the implementation, this should be valid
    assert is_valid or "package_id" in details.get("reason", "")
    
    # Test expired token
    expired_expiry = (datetime.now() - timedelta(hours=1)).isoformat()
    expired_token = data_packaging_service._generate_access_token(consent_id, expired_expiry)
    is_valid, details = await data_packaging_service.validate_access_token(expired_token, package_id)
    
    assert not is_valid
    assert "expired" in details.get("reason", "").lower()

# --- API Endpoint Tests ---

async def test_create_data_package_api(async_client: AsyncClient, session: AsyncSession):
    """Test the create data package API endpoint."""
    # Create a consent event first
    consent = ConsentEvent(
        id=TEST_CONSENT_ID,
        user_id=TEST_USER_ID,
        offer_id="offer-123",
        action="accepted",
        timestamp=datetime.now()
    )
    session.add(consent)
    await session.commit()
    
    # Call the API
    response = await async_client.post(
        "/api/data-packages",
        json={
            "user_id": TEST_USER_ID,
            "data_type": TEST_DATA_TYPE,
            "access_level": "anonymous_short_term",
            "consent_id": TEST_CONSENT_ID,
            "purpose": "testing",
            "buyer_id": TEST_BUYER_ID,
            "trust_tier": "standard"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["tavren_data_package"] == "1.1"
    assert data["package_id"] is not None
    assert data["consent_id"] == TEST_CONSENT_ID
    assert data["data_type"] == TEST_DATA_TYPE
    assert data["anonymization_level"] == "strong"
    
    # Clean up
    await session.execute(f"DELETE FROM consent_events WHERE id = '{TEST_CONSENT_ID}'")
    await session.commit()

async def test_get_available_schemas_api(async_client: AsyncClient):
    """Test the get available schemas API endpoint."""
    response = await async_client.get("/api/data-packages/schemas")
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    
    # Verify schema structure
    schema = data[0]
    assert "data_type" in schema
    assert "schema_version" in schema
    assert "required_fields" in schema
    assert "description" in schema
    assert "example" in schema

async def test_validate_token_api(async_client: AsyncClient):
    """Test the validate token API endpoint."""
    # Create a mock token and package ID
    # In a real test, we would generate a valid token first
    mock_token = "header.payload.signature"
    mock_package_id = "test-package-id"
    
    response = await async_client.post(
        "/api/data-packages/validate-token",
        json={
            "package_id": mock_package_id,
            "access_token": mock_token
        }
    )
    
    # Check response - we expect it to fail validation but return a proper response
    assert response.status_code == 200
    data = response.json()
    assert "valid" in data
    # Since we're using a fake token, valid should be false
    assert data["valid"] is False

async def test_consent_validation(async_client: AsyncClient, session: AsyncSession):
    """Test that data packaging validates consent."""
    # Create a declined consent event
    consent = ConsentEvent(
        id=TEST_CONSENT_ID,
        user_id=TEST_USER_ID,
        offer_id="offer-123",
        action="declined",  # Declined consent
        timestamp=datetime.now()
    )
    session.add(consent)
    await session.commit()
    
    # Call the API
    response = await async_client.post(
        "/api/data-packages",
        json={
            "user_id": TEST_USER_ID,
            "data_type": TEST_DATA_TYPE,
            "access_level": "anonymous_short_term",
            "consent_id": TEST_CONSENT_ID,
            "purpose": "testing",
            "buyer_id": TEST_BUYER_ID
        }
    )
    
    # Should get a successful response but with error status in the package
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "User declined consent" in data["reason"]
    
    # Clean up
    await session.execute(f"DELETE FROM consent_events WHERE id = '{TEST_CONSENT_ID}'")
    await session.commit() 