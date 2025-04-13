import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import io

from app.main import app
from app.services.dsr_service import DSRService
from app.utils.rate_limit import RateLimiter

# Mock the get_current_user_id dependency to return test user
TEST_USER_ID = "test_user_123"

def mock_get_current_user_id():
    return TEST_USER_ID

# Mock the rate limiter check to always allow
async def mock_check_rate_limit(*args, **kwargs):
    return True

async def mock_update_rate_limit(*args, **kwargs):
    pass

# Apply the mock for authentication
app.dependency_overrides = {}

@pytest.fixture
def client():
    """Test client fixture."""
    with patch("app.routers.dsr.get_current_user_id", mock_get_current_user_id):
        with patch.object(RateLimiter, "check_rate_limit", mock_check_rate_limit):
            with patch.object(RateLimiter, "update_rate_limit", mock_update_rate_limit):
                with TestClient(app) as client:
                    yield client

@pytest.fixture
def mock_dsr_service():
    """Mock DSR service fixture."""
    service = AsyncMock(spec=DSRService)
    
    # Configure generate_data_export mock
    file_obj = io.StringIO('{"test": "data"}')
    service.generate_data_export.return_value = (file_obj, "application/json")
    
    # Configure delete_user_data mock
    service.delete_user_data.return_value = {
        "user_id": TEST_USER_ID,
        "timestamp": datetime.now().isoformat(),
        "deleted_categories": ["user_profile", "rewards_history"],
        "preserved_categories": ["consent_history", "payout_history"]
    }
    
    # Configure restrict_user_processing mock
    service.restrict_user_processing.return_value = {
        "user_id": TEST_USER_ID,
        "restriction_applied": True,
        "restriction_scope": "all",
        "timestamp": datetime.now().isoformat(),
        "consent_event_id": 123
    }
    
    return service

@pytest.mark.asyncio
async def test_export_user_data(client, mock_dsr_service):
    """Test the export user data endpoint."""
    with patch("app.routers.dsr.get_dsr_service", return_value=mock_dsr_service):
        response = client.get("/api/dsr/export?format=json")
        
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert "Content-Disposition" in response.headers
        assert "attachment" in response.headers["Content-Disposition"]
        
        # Verify service was called correctly
        mock_dsr_service.generate_data_export.assert_called_once_with(
            user_id=TEST_USER_ID,
            include_consent=True,
            include_rewards=True,
            include_payouts=True,
            format="json"
        )

@pytest.mark.asyncio
async def test_delete_user_data(client, mock_dsr_service):
    """Test the delete user data endpoint."""
    with patch("app.routers.dsr.get_dsr_service", return_value=mock_dsr_service):
        response = client.post("/api/dsr/delete?delete_profile=true&delete_consent=false")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["status"] == "success"
        assert "results" in response_data
        assert response_data["results"]["user_id"] == TEST_USER_ID
        assert "deleted_categories" in response_data["results"]
        assert "preserved_categories" in response_data["results"]
        
        # Verify service was called correctly
        mock_dsr_service.delete_user_data.assert_called_once_with(
            user_id=TEST_USER_ID,
            delete_profile=True,
            delete_consent=False
        )

@pytest.mark.asyncio
async def test_restrict_data_processing(client, mock_dsr_service):
    """Test the restrict data processing endpoint."""
    with patch("app.routers.dsr.get_dsr_service", return_value=mock_dsr_service):
        response = client.post("/api/dsr/restrict?restriction_scope=all&restriction_reason=Testing")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["status"] == "success"
        assert "results" in response_data
        assert response_data["results"]["user_id"] == TEST_USER_ID
        assert response_data["results"]["restriction_applied"] is True
        assert response_data["results"]["restriction_scope"] == "all"
        
        # Verify service was called correctly
        mock_dsr_service.restrict_user_processing.assert_called_once_with(
            user_id=TEST_USER_ID,
            restriction_scope="all",
            restriction_reason="Testing"
        )

@pytest.mark.asyncio
async def test_rate_limit_handling(client, mock_dsr_service):
    """Test that rate limiting is handled properly."""
    # Override the mock to simulate rate limit exceeded
    async def mock_rate_limit_exceeded(*args, **kwargs):
        return False
    
    # Test rate limiting for export endpoint
    with patch("app.routers.dsr.get_dsr_service", return_value=mock_dsr_service):
        with patch.object(RateLimiter, "check_rate_limit", mock_rate_limit_exceeded):
            with patch.object(RateLimiter, "get_last_request_time", 
                              return_value=datetime.now() - timedelta(days=1)):
                
                response = client.get("/api/dsr/export")
                
                assert response.status_code == 429
                assert "Retry-After" in response.headers
                assert "rate limit exceeded" in response.json()["detail"].lower()
                
                # Service should not be called when rate limited
                mock_dsr_service.generate_data_export.assert_not_called() 