import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from app.main import app
from app.utils.consent_export import ConsentExportService

client = TestClient(app)

# Mock user for testing
TEST_USER_ID = "test-user-123"
ADMIN_USER_ID = "admin-user-456"

# Mock user data for authentication
@pytest.fixture
def mock_get_current_user():
    """Mock the current user dependency for regular user"""
    async def _get_current_user():
        return type('User', (), {'id': TEST_USER_ID, 'is_admin': False})
    return _get_current_user

@pytest.fixture
def mock_get_current_admin_user():
    """Mock the current user dependency for admin user"""
    async def _get_current_admin_user():
        return type('User', (), {'id': ADMIN_USER_ID, 'is_admin': True})
    return _get_current_admin_user

@pytest.fixture
def mock_consent_export_service():
    """Mock the consent export service"""
    mock_service = AsyncMock(spec=ConsentExportService)
    
    # Mock the generate_export_package method
    async def mock_generate_export(user_id, include_pet_queries, sign_export):
        return {
            "export_id": f"export-{user_id}-123",
            "export_timestamp": "2023-01-01T12:00:00Z",
            "user_id": user_id,
            "user_info": {"id": user_id, "email": f"{user_id}@example.com"},
            "consent_records": [{"id": "consent-1", "timestamp": "2023-01-01T10:00:00Z"}],
            "dsr_history": [],
            "pet_queries": [] if include_pet_queries else None,
            "verification": {
                "hash": "abc123",
                "signature": "xyz789" if sign_export else None
            }
        }
    
    # Mock the save_export_file method
    async def mock_save_export(export_data):
        return f"/tmp/consent_export_{export_data['user_id']}.json"
    
    # Mock the verify_export_signature method
    async def mock_verify_signature(export_data):
        return True
    
    mock_service.generate_export_package.side_effect = mock_generate_export
    mock_service.save_export_file.side_effect = mock_save_export
    mock_service.verify_export_signature.side_effect = mock_verify_signature
    
    return mock_service

@pytest.fixture
def mock_get_consent_export(mock_consent_export_service):
    """Dependency override for get_consent_export"""
    def _get_consent_export():
        return mock_consent_export_service
    return _get_consent_export

# Tests for the consent export endpoints
@pytest.mark.asyncio
@patch("app.routers.consent_export.get_current_user")
@patch("app.routers.consent_export.get_consent_export")
def test_export_user_consent_own_data(mock_get_export, mock_current_user, mock_consent_export_service, mock_get_current_user):
    """Test that a user can export their own consent data"""
    # Setup mocks
    mock_current_user.return_value = mock_get_current_user()
    mock_get_export.return_value = mock_consent_export_service
    
    # Make the request
    response = client.get(f"/api/consent-ledger/export/{TEST_USER_ID}")
    
    # Check results
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == TEST_USER_ID
    assert "export_id" in data
    assert "export_timestamp" in data
    assert "user_info" in data
    assert "consent_records" in data
    
    # Verify service was called correctly
    mock_consent_export_service.generate_export_package.assert_called_once_with(
        user_id=TEST_USER_ID,
        include_pet_queries=False,
        sign_export=True
    )

@pytest.mark.asyncio
@patch("app.routers.consent_export.get_current_user")
def test_export_user_consent_unauthorized(mock_current_user, mock_get_current_user):
    """Test that a user cannot export another user's data"""
    # Setup mocks to return a regular user
    mock_current_user.return_value = mock_get_current_user()
    
    # Try to access another user's data
    other_user_id = "other-user-789"
    response = client.get(f"/api/consent-ledger/export/{other_user_id}")
    
    # Check that access is denied
    assert response.status_code == 403
    assert "You can only export your own consent data" in response.json()["detail"]

@pytest.mark.asyncio
@patch("app.routers.consent_export.get_current_admin_user")
@patch("app.routers.consent_export.get_consent_export")
def test_admin_export_any_user(mock_get_export, mock_current_admin, mock_consent_export_service, mock_get_current_admin_user):
    """Test that an admin can export any user's data"""
    # Setup mocks
    mock_current_admin.return_value = mock_get_current_admin_user()
    mock_get_export.return_value = mock_consent_export_service
    
    # Target a regular user's data
    target_user_id = "target-user-789"
    
    # Make the request
    response = client.get(f"/api/consent-ledger/export/admin/{target_user_id}")
    
    # Check results
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == target_user_id
    
    # Verify service was called correctly
    mock_consent_export_service.generate_export_package.assert_called_once_with(
        user_id=target_user_id,
        include_pet_queries=True,
        sign_export=True
    )

@pytest.mark.asyncio
@patch("app.routers.consent_export.get_current_user")
@patch("app.routers.consent_export.get_consent_export")
def test_verify_export(mock_get_export, mock_current_user, mock_consent_export_service, mock_get_current_user):
    """Test verifying a consent export"""
    # Setup mocks
    mock_current_user.return_value = mock_get_current_user()
    mock_get_export.return_value = mock_consent_export_service
    
    # Create export data to verify
    export_id = "export-test-123"
    export_data = {
        "export_id": export_id,
        "export_timestamp": "2023-01-01T12:00:00Z",
        "user_id": TEST_USER_ID,
        "verification": {
            "hash": "abc123",
            "signature": "xyz789"
        }
    }
    
    # Make the request
    response = client.get(
        f"/api/consent-ledger/export/verify/{export_id}",
        json=export_data
    )
    
    # Check results
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["export_id"] == export_id
    
    # Verify service was called correctly
    mock_consent_export_service.verify_export_signature.assert_called_once_with(export_data) 