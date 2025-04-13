import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.utils.consent_validator import ConsentValidator
from app.services.consent_ledger import ConsentLedgerService

# Test data
USER_ID = "test_user_123"
DATA_SCOPE = "location"
PURPOSE = "insight_generation"

# Mock consent events with different scenarios
MOCK_EVENTS = {
    "no_consent": [],
    "valid_consent": [
        MagicMock(
            id=1,
            user_id=USER_ID,
            action="opt_in",
            scope=DATA_SCOPE,
            purpose=PURPOSE,
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user"
        )
    ],
    "revoked_consent": [
        MagicMock(
            id=1,
            user_id=USER_ID,
            action="opt_in",
            scope=DATA_SCOPE,
            purpose=PURPOSE,
            timestamp=datetime.now() - timedelta(days=2),
            initiated_by="user"
        ),
        MagicMock(
            id=2,
            user_id=USER_ID,
            action="opt_out",
            scope=DATA_SCOPE,
            purpose=PURPOSE,
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user"
        )
    ],
    "partial_consent": [
        MagicMock(
            id=1,
            user_id=USER_ID,
            action="opt_in",
            scope="purchase_data",
            purpose=PURPOSE,
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user"
        )
    ],
    "different_purpose": [
        MagicMock(
            id=1,
            user_id=USER_ID,
            action="opt_in",
            scope=DATA_SCOPE,
            purpose="ad_targeting",
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user"
        )
    ],
    "global_consent": [
        MagicMock(
            id=1,
            user_id=USER_ID,
            action="opt_in",
            scope="all",
            purpose="all",
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user"
        )
    ],
    "dsr_restriction": [
        MagicMock(
            id=1,
            user_id=USER_ID,
            action="opt_in",
            scope="all",
            purpose="all",
            timestamp=datetime.now() - timedelta(days=10),
            initiated_by="user"
        ),
        MagicMock(
            id=2,
            user_id=USER_ID,
            action="dsr_request",
            scope="all",
            purpose="regulatory_compliance",
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user_dsr",
            offer_id="dsr_audit",
            consent_metadata={"dsr_type": "processing_restriction", "restriction_reason": "Test restriction"}
        )
    ],
    "dsr_system_restriction": [
        MagicMock(
            id=1,
            user_id=USER_ID,
            action="opt_in",
            scope="all",
            purpose="all",
            timestamp=datetime.now() - timedelta(days=10),
            initiated_by="user"
        ),
        MagicMock(
            id=2,
            user_id=USER_ID,
            action="opt_out",
            scope="all",
            purpose="all",
            timestamp=datetime.now() - timedelta(days=1),
            initiated_by="user_dsr",
            offer_id="system_restriction"
        )
    ]
}

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()

@pytest.fixture
def mock_consent_ledger():
    """Create a mock consent ledger service."""
    ledger = AsyncMock(spec=ConsentLedgerService)
    return ledger

@pytest.fixture
def consent_validator(mock_db, mock_consent_ledger):
    """Create a consent validator with mocked dependencies."""
    validator = ConsentValidator(mock_db)
    
    # Replace the ConsentLedgerService instantiation
    def mock_ledger(*args, **kwargs):
        return mock_consent_ledger
    
    # Apply the mock
    with patch('app.utils.consent_validator.ConsentLedgerService', side_effect=mock_ledger):
        yield validator

@pytest.mark.asyncio
async def test_no_consent(consent_validator, mock_consent_ledger):
    """Test validation when user has no consent history."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["no_consent"]
    
    # Execute
    is_allowed, details = await consent_validator.is_processing_allowed(
        USER_ID, DATA_SCOPE, PURPOSE
    )
    
    # Verify
    assert is_allowed is False
    assert "No consent history found" in details["reason"]
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_valid_consent(consent_validator, mock_consent_ledger):
    """Test validation when user has given valid consent."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["valid_consent"]
    
    # Execute
    is_allowed, details = await consent_validator.is_processing_allowed(
        USER_ID, DATA_SCOPE, PURPOSE
    )
    
    # Verify
    assert is_allowed is True
    assert details["status"] == "allowed"
    assert details["consent_id"] == 1
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_revoked_consent(consent_validator, mock_consent_ledger):
    """Test validation when user has revoked consent."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["revoked_consent"]
    
    # Execute
    is_allowed, details = await consent_validator.is_processing_allowed(
        USER_ID, DATA_SCOPE, PURPOSE
    )
    
    # Verify
    assert is_allowed is False
    assert "Consent revoked" in details["reason"]
    assert details["consent_id"] == 2
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_partial_consent(consent_validator, mock_consent_ledger):
    """Test validation when user has consented to a different scope."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["partial_consent"]
    
    # Execute
    is_allowed, details = await consent_validator.is_processing_allowed(
        USER_ID, DATA_SCOPE, PURPOSE
    )
    
    # Verify
    assert is_allowed is False
    assert "No consent found" in details["reason"]
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_different_purpose(consent_validator, mock_consent_ledger):
    """Test validation when user has consented to a different purpose."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["different_purpose"]
    
    # Execute
    is_allowed, details = await consent_validator.is_processing_allowed(
        USER_ID, DATA_SCOPE, PURPOSE
    )
    
    # Verify
    assert is_allowed is False
    assert "No consent found" in details["reason"]
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_global_consent(consent_validator, mock_consent_ledger):
    """Test validation when user has given global consent."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["global_consent"]
    
    # Execute
    is_allowed, details = await consent_validator.is_processing_allowed(
        USER_ID, DATA_SCOPE, PURPOSE
    )
    
    # Verify
    assert is_allowed is True
    assert details["status"] == "allowed"
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_active_consent_scopes(consent_validator, mock_consent_ledger):
    """Test retrieving active consent scopes."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["global_consent"]
    
    # Execute
    active_scopes = await consent_validator.get_active_consent_scopes(USER_ID)
    
    # Verify
    assert "all" in active_scopes
    assert "all" in active_scopes["all"]
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_check_dsr_restrictions_none(consent_validator, mock_consent_ledger):
    """Test checking DSR restrictions when none exist."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["valid_consent"]
    
    # Execute
    has_restrictions, details = await consent_validator.check_dsr_restrictions(USER_ID)
    
    # Verify
    assert has_restrictions is False
    assert details["status"] == "no_restrictions"
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_check_dsr_restrictions_exists(consent_validator, mock_consent_ledger):
    """Test checking DSR restrictions when a processing restriction exists."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["dsr_restriction"]
    
    # Execute
    has_restrictions, details = await consent_validator.check_dsr_restrictions(USER_ID)
    
    # Verify
    assert has_restrictions is True
    assert details["status"] == "restricted"
    assert details["reason"] == "DSR processing restriction"
    assert details["restriction_type"] == "dsr_request"
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_check_dsr_system_restriction(consent_validator, mock_consent_ledger):
    """Test checking DSR restrictions when a system restriction exists."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["dsr_system_restriction"]
    
    # Execute
    has_restrictions, details = await consent_validator.check_dsr_restrictions(USER_ID)
    
    # Verify
    assert has_restrictions is True
    assert details["status"] == "restricted"
    assert details["reason"] == "DSR global opt-out"
    assert details["restriction_type"] == "system_restriction"
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID)

@pytest.mark.asyncio
async def test_is_processing_allowed_with_dsr_restriction(consent_validator, mock_consent_ledger):
    """Test that DSR restrictions override regular consent validation."""
    # Setup
    mock_consent_ledger.get_user_history.return_value = MOCK_EVENTS["dsr_restriction"]
    
    # Execute
    is_allowed, details = await consent_validator.is_processing_allowed(
        USER_ID, DATA_SCOPE, PURPOSE
    )
    
    # Verify
    assert is_allowed is False
    assert "Processing restricted due to Data Subject Request" in details["reason"]
    assert "dsr_details" in details
    assert details["dsr_details"]["status"] == "restricted"
    mock_consent_ledger.get_user_history.assert_called_once_with(USER_ID) 