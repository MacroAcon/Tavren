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