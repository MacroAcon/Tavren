import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import json
import io
import pandas as pd

from app.main import app
from app.services.dsr_service import DSRService
from app.services.consent_ledger import ConsentLedgerService
from app.utils.rate_limit import RateLimiter
from app.utils.insight_processor import process_insight, QueryType, PrivacyMethod

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
        with patch("app.routers.insight.get_current_user_id", mock_get_current_user_id):
            with patch.object(RateLimiter, "check_rate_limit", mock_check_rate_limit):
                with patch.object(RateLimiter, "update_rate_limit", mock_update_rate_limit):
                    with TestClient(app) as client:
                        yield client

@pytest.fixture
def mock_dsr_service():
    """Mock DSR service fixture."""
    service = AsyncMock(spec=DSRService)
    
    # Configure restrict_user_processing mock
    service.restrict_user_processing.return_value = {
        "user_id": TEST_USER_ID,
        "restriction_applied": True,
        "restriction_scope": "all",
        "timestamp": datetime.now().isoformat(),
        "consent_event_id": 123
    }
    
    return service

@pytest.fixture
def mock_consent_ledger():
    """Mock consent ledger service."""
    service = AsyncMock(spec=ConsentLedgerService)
    
    # Default mock for get_user_history
    service.get_user_history.return_value = [
        MagicMock(
            id=1,
            user_id=TEST_USER_ID,
            action="opt_in",
            scope="all",
            purpose="all",
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user",
            consent_metadata={}
        )
    ]
    
    # Mock for record_event
    service.record_event.return_value = MagicMock(
        id=123,
        user_id=TEST_USER_ID,
        action="dsr_request",
        timestamp=datetime.now(),
        initiated_by="user_dsr"
    )
    
    return service

@pytest.mark.asyncio
async def test_dsr_restriction_affects_insight_processing(client, mock_dsr_service, mock_consent_ledger):
    """
    End-to-end test demonstrating that a DSR restriction prevents insight processing.
    
    Flow:
    1. First, process an insight request successfully
    2. Then, apply a DSR restriction via the DSR API
    3. Finally, try to process another insight and verify it is blocked
    """
    # Setup test data with the test user
    test_data = [
        {"user_id": TEST_USER_ID, "store_category": "grocery", "visit_count": 5},
        {"user_id": "other_user", "store_category": "grocery", "visit_count": 3},
        {"user_id": TEST_USER_ID, "store_category": "electronics", "visit_count": 2}
    ]
    csv_data = pd.DataFrame(test_data).to_csv(index=False)
    
    # Mock for initial insight request (no restrictions)
    def mock_no_restrictions(*args, **kwargs):
        return []
    
    # Step 1: Process insight request successfully (no DSR restrictions yet)
    with patch("app.routers.insight.check_dsr_restrictions", return_value=(True, [], "")):
        insight_payload = {
            "data": csv_data,
            "query_type": "average_store_visits",
            "privacy_method": "differential_privacy",
            "epsilon": 1.0,
            "data_format": "csv",
            "user_id": TEST_USER_ID
        }
        
        response = client.post("/api/insight", json=insight_payload)
        
        # Verify initial request was successful
        assert response.status_code == 200
        assert response.json()["processed_result"] is not None
        
    # Step 2: Apply a DSR restriction via the DSR API
    with patch("app.routers.dsr.get_dsr_service", return_value=mock_dsr_service):
        with patch("app.utils.consent_validator.ConsentLedgerService", return_value=mock_consent_ledger):
            response = client.post("/api/dsr/restrict?restriction_scope=all&restriction_reason=Testing")
            
            # Verify DSR request was successful
            assert response.status_code == 200
            assert response.json()["status"] == "success"
            
            # Now update the mock to return a restricted user for the second insight request
            mock_consent_ledger.get_user_history.return_value = [
                MagicMock(
                    id=1,
                    user_id=TEST_USER_ID,
                    action="opt_in",
                    scope="all",
                    purpose="all",
                    timestamp=datetime.now() - timedelta(days=10),
                    initiated_by="user",
                    consent_metadata={}
                ),
                MagicMock(
                    id=2,
                    user_id=TEST_USER_ID,
                    action="opt_out",
                    scope="all",
                    purpose="all",
                    timestamp=datetime.now() - timedelta(days=1),
                    initiated_by="user_dsr",
                    offer_id="system_restriction",
                    consent_metadata={}
                )
            ]
    
    # Step 3: Try to process another insight and verify it is blocked
    with patch("app.services.consent_ledger.ConsentLedgerService", return_value=mock_consent_ledger):
        response = client.post("/api/insight", json=insight_payload)
        
        # Verify request was blocked due to DSR restriction
        assert response.status_code == 403
        response_data = response.json()
        assert "Processing restricted" in response_data["detail"]["message"]

@pytest.mark.asyncio
async def test_insight_processor_directly_respects_dsr(mock_dsr_service, mock_consent_ledger):
    """
    Test that the insight processor directly respects DSR restrictions.
    This tests the function directly rather than through the API.
    """
    # Setup test data
    test_data = [
        {"user_id": TEST_USER_ID, "store_category": "grocery", "visit_count": 5},
        {"user_id": "other_user", "store_category": "grocery", "visit_count": 3}
    ]
    
    # Mock database session
    mock_db = AsyncMock()
    
    # Case 1: No DSR restrictions
    with patch("app.utils.insight_processor.ConsentLedgerService", return_value=mock_consent_ledger):
        # Configure mock to return no restrictions
        mock_consent_ledger.get_user_history.return_value = [
            MagicMock(
                id=1,
                user_id=TEST_USER_ID,
                action="opt_in",
                scope="all",
                purpose="all",
                timestamp=datetime.now() - timedelta(days=1),
                consent_metadata={}
            )
        ]
        
        # Process insight
        result = await process_insight(
            data=test_data,
            query_type=QueryType.AVERAGE_STORE_VISITS,
            privacy_method=PrivacyMethod.DP,
            privacy_params={"epsilon": 1.0},
            validate_consent=True,
            db=mock_db,
            user_id_field='user_id'
        )
        
        # Verify the result
        assert result["success"] is True
        assert result["result"] is not None
    
    # Case 2: With DSR restrictions
    with patch("app.utils.insight_processor.ConsentLedgerService", return_value=mock_consent_ledger):
        # Configure mock to return a DSR restriction
        mock_consent_ledger.get_user_history.return_value = [
            MagicMock(
                id=2,
                user_id=TEST_USER_ID,
                action="dsr_request",
                scope="all",
                purpose="regulatory_compliance",
                timestamp=datetime.now() - timedelta(days=1),
                initiated_by="user_dsr",
                offer_id="dsr_audit",
                consent_metadata={"dsr_type": "processing_restriction"}
            )
        ]
        
        # Process insight
        result = await process_insight(
            data=test_data,
            query_type=QueryType.AVERAGE_STORE_VISITS,
            privacy_method=PrivacyMethod.DP,
            privacy_params={"epsilon": 1.0},
            validate_consent=True,
            db=mock_db,
            user_id_field='user_id'
        )
        
        # Verify the result
        assert result["success"] is False
        assert "Processing restricted due to DSR" in result["error"]
        assert "restricted_users" in result["metadata"]
        assert TEST_USER_ID in result["metadata"]["restricted_users"] 