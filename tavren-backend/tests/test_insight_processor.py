import pytest
import pandas as pd
import numpy as np
from app.utils.insight_processor import process_insight, QueryType, PrivacyMethod
from app.utils.consent_validator import ConsentValidator

# Test constants
USER_ID = "test_user_123"
DATA_SCOPE = "store_visits"
PURPOSE = "insight_generation"

# Sample data for testing
@pytest.fixture
def sample_store_visits_df():
    # Create sample data with 3 users visiting 3 store categories
    data = []
    users = [1, 2, 3]
    categories = ["grocery", "clothing", "electronics"]
    
    for user_id in users:
        for category in categories:
            # Each user has different visit patterns
            if category == "grocery":
                visits = 5 if user_id == 1 else (3 if user_id == 2 else 4)
            elif category == "clothing":
                visits = 2 if user_id == 1 else (4 if user_id == 2 else 1)
            else:  # electronics
                visits = 1 if user_id == 1 else (2 if user_id == 2 else 3)
            
            # Add visits to data
            for _ in range(visits):
                data.append({
                    "user_id": user_id,
                    "store_category": category,
                    "district": "test",
                    "is_weekend": 0
                })
    
    return pd.DataFrame(data)

@pytest.fixture
def sample_smpc_data():
    # Create sample data for SMPC with 2 parties
    party1_data = {
        "users": [1, 2],
        "data": pd.DataFrame([
            {"user_id": 1, "store_category": "grocery", "district": "north", "is_weekend": 0, "party_id": 0},
            {"user_id": 1, "store_category": "grocery", "district": "north", "is_weekend": 0, "party_id": 0},
            {"user_id": 1, "store_category": "clothing", "district": "north", "is_weekend": 0, "party_id": 0},
            {"user_id": 2, "store_category": "grocery", "district": "south", "is_weekend": 0, "party_id": 0},
            {"user_id": 2, "store_category": "electronics", "district": "south", "is_weekend": 0, "party_id": 0},
        ])
    }
    
    party2_data = {
        "users": [3, 4],
        "data": pd.DataFrame([
            {"user_id": 3, "store_category": "grocery", "district": "east", "is_weekend": 0, "party_id": 1},
            {"user_id": 3, "store_category": "clothing", "district": "east", "is_weekend": 0, "party_id": 1},
            {"user_id": 4, "store_category": "electronics", "district": "west", "is_weekend": 0, "party_id": 1},
            {"user_id": 4, "store_category": "electronics", "district": "west", "is_weekend": 0, "party_id": 1},
        ])
    }
    
    return [party1_data, party2_data]

@pytest.fixture
def sample_data():
    """Create sample DataFrame for testing."""
    data = {
        'user_id': ['test_user_123', 'user2', 'user3'],
        'store_category': ['Grocery', 'Electronics', 'Clothing'],
        'visit_count': [5, 3, 4]
    }
    return pd.DataFrame(data)

# Mock consent validator with different response scenarios
@pytest.fixture
def mock_consent_validator():
    """Create a mock consent validator with configurable responses."""
    validator = AsyncMock(spec=ConsentValidator)
    return validator

def test_process_insight_dp(sample_store_visits_df):
    """Test processing insight with DP method"""
    # Set random seed for reproducible results in the test
    np.random.seed(42)
    
    # Process with epsilon=10 (high accuracy)
    result = process_insight(
        data=sample_store_visits_df,
        query_type=QueryType.AVERAGE_STORE_VISITS,
        pet_method=PrivacyMethod.DP,
        epsilon=10.0
    )
    
    # Verify structure
    assert "result" in result
    assert "metadata" in result
    
    # Verify metadata
    assert result["metadata"]["query_type"] == QueryType.AVERAGE_STORE_VISITS
    assert result["metadata"]["pet_method"] == PrivacyMethod.DP
    assert result["metadata"]["epsilon"] == 10.0
    assert "processing_time_ms" in result["metadata"]
    
    # Verify categories in result
    assert set(result["result"].keys()) == {"grocery", "clothing", "electronics"}
    
    # With epsilon=10, results should be close to true values
    # True values: grocery=4, clothing=2.33, electronics=2
    for category, value in result["result"].items():
        assert value >= 0  # Non-negative
        if category == "grocery":
            assert abs(value - 4.0) < 1.0  # Should be close to true value
        elif category == "clothing":
            assert abs(value - 2.33) < 1.0
        elif category == "electronics":
            assert abs(value - 2.0) < 1.0

def test_input_validation():
    """Test input validation for the process_insight function"""
    # Invalid data type
    with pytest.raises(ValueError, match="Data must be a pandas DataFrame"):
        process_insight("invalid data", QueryType.AVERAGE_STORE_VISITS, PrivacyMethod.DP, 1.0)
    
    # Invalid query type
    with pytest.raises(ValueError, match="Query type .* not supported"):
        process_insight(pd.DataFrame(), "invalid_query", PrivacyMethod.DP, 1.0)
    
    # Invalid PET method
    with pytest.raises(ValueError, match="Privacy method .* not supported"):
        process_insight(pd.DataFrame(), QueryType.AVERAGE_STORE_VISITS, "invalid_method", 1.0)
    
    # Missing epsilon for DP
    with pytest.raises(ValueError, match="Epsilon parameter is required"):
        process_insight(pd.DataFrame(), QueryType.AVERAGE_STORE_VISITS, PrivacyMethod.DP)
    
    # Invalid epsilon
    with pytest.raises(ValueError, match="Epsilon must be a positive number"):
        process_insight(pd.DataFrame(), QueryType.AVERAGE_STORE_VISITS, PrivacyMethod.DP, -1.0)

def test_dp_different_epsilon(sample_store_visits_df):
    """Test DP with different epsilon values to verify privacy-utility tradeoff"""
    # Set random seed for reproducible results
    np.random.seed(42)
    
    # Process with high epsilon (10.0) - high accuracy
    high_accuracy = process_insight(
        data=sample_store_visits_df,
        query_type=QueryType.AVERAGE_STORE_VISITS,
        pet_method=PrivacyMethod.DP,
        epsilon=10.0
    )["result"]
    
    # Process with low epsilon (0.1) - high privacy
    high_privacy = process_insight(
        data=sample_store_visits_df,
        query_type=QueryType.AVERAGE_STORE_VISITS,
        pet_method=PrivacyMethod.DP,
        epsilon=0.1
    )["result"]
    
    # Calculate average error for both results
    true_values = {
        "grocery": 4.0,       # (5+3+4)/3
        "clothing": 2.33,     # (2+4+1)/3
        "electronics": 2.0    # (1+2+3)/3
    }
    
    high_accuracy_error = sum(abs(high_accuracy[k] - v) for k, v in true_values.items()) / 3
    high_privacy_error = sum(abs(high_privacy[k] - v) for k, v in true_values.items()) / 3
    
    # High privacy (low epsilon) should have higher error
    assert high_privacy_error > high_accuracy_error
    
    # Print for visibility (will show in pytest output)
    print(f"\nHigh accuracy error (ε=10.0): {high_accuracy_error:.2f}")
    print(f"High privacy error (ε=0.1): {high_privacy_error:.2f}")
    print(f"High accuracy results: {high_accuracy}")
    print(f"High privacy results: {high_privacy}")

# Skip SMPC test by default since it imports external modules
@pytest.mark.skip(reason="SMPC test requires external module and is slow")
def test_process_insight_smpc(sample_smpc_data):
    """Test processing insight with SMPC method"""
    result = process_insight(
        data=sample_smpc_data,
        query_type=QueryType.AVERAGE_STORE_VISITS,
        pet_method=PrivacyMethod.SMPC
    )
    
    # Verify structure
    assert "result" in result
    assert "metadata" in result
    
    # Verify metadata
    assert result["metadata"]["query_type"] == QueryType.AVERAGE_STORE_VISITS
    assert result["metadata"]["pet_method"] == PrivacyMethod.SMPC
    assert "processing_time_ms" in result["metadata"]
    
    # SMPC results should reflect true counts - might be harder to test exactly
    # since the SMPC simulation uses random shares
    assert set(result["result"].keys()) >= {"grocery", "clothing", "electronics"} 

@pytest.mark.asyncio
async def test_process_insight_with_valid_consent(sample_data, mock_consent_validator):
    """Test processing insights when user has valid consent."""
    # Configure mock to return valid consent
    mock_consent_validator.is_processing_allowed.return_value = (
        True, 
        {
            "status": "allowed",
            "consent_id": 1,
            "granted_at": datetime.now().isoformat(),
            "user_id": USER_ID,
            "scope": DATA_SCOPE,
            "purpose": PURPOSE
        }
    )
    
    # Process with DP method
    result = await process_insight(
        data=sample_data,
        query_type=QueryType.AVERAGE_STORE_VISITS.value,
        pet_method=PrivacyMethod.DP.value,
        epsilon=1.0,
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE,
        consent_validator=mock_consent_validator
    )
    
    # Verify results
    assert "result" in result
    assert "metadata" in result
    assert result["metadata"]["status"] == "success"
    assert result["metadata"]["consent_validated"] is True
    assert result["metadata"]["user_id"] == USER_ID
    assert result["metadata"]["data_scope"] == DATA_SCOPE
    
    # Verify consent validation was called correctly
    mock_consent_validator.is_processing_allowed.assert_called_once_with(
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE
    )

@pytest.mark.asyncio
async def test_process_insight_with_denied_consent(sample_data, mock_consent_validator):
    """Test processing insights when user has denied consent."""
    # Configure mock to return denied consent
    mock_consent_validator.is_processing_allowed.return_value = (
        False, 
        {
            "reason": "Consent revoked for store_visits",
            "required_action": "opt_in",
            "revoked_at": datetime.now().isoformat(),
            "user_id": USER_ID,
            "scope": DATA_SCOPE,
            "purpose": PURPOSE,
            "consent_id": 2
        }
    )
    
    # Process with DP method
    result = await process_insight(
        data=sample_data,
        query_type=QueryType.AVERAGE_STORE_VISITS.value,
        pet_method=PrivacyMethod.DP.value,
        epsilon=1.0,
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE,
        consent_validator=mock_consent_validator
    )
    
    # Verify results indicate rejection
    assert result["result"] is None
    assert result["metadata"]["status"] == "rejected"
    assert "error" in result["metadata"]
    assert "error_details" in result["metadata"]
    
    # Verify consent validation was called correctly
    mock_consent_validator.is_processing_allowed.assert_called_once_with(
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE
    )

@pytest.mark.asyncio
async def test_process_insight_with_consent_validation_error(sample_data, mock_consent_validator):
    """Test processing insights when consent validation raises an error."""
    # Configure mock to raise an exception
    mock_consent_validator.is_processing_allowed.side_effect = Exception("Database connection error")
    
    # Process with DP method
    result = await process_insight(
        data=sample_data,
        query_type=QueryType.AVERAGE_STORE_VISITS.value,
        pet_method=PrivacyMethod.DP.value,
        epsilon=1.0,
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE,
        consent_validator=mock_consent_validator
    )
    
    # Verify results indicate error
    assert result["result"] is None
    assert result["metadata"]["status"] == "error"
    assert "error" in result["metadata"]
    assert "Database connection error" in result["metadata"]["error_details"]["message"]
    
    # Verify consent validation was called correctly
    mock_consent_validator.is_processing_allowed.assert_called_once_with(
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE
    )

@pytest.mark.asyncio
async def test_process_insight_without_consent_validator(sample_data):
    """Test processing insights when no consent validator is provided."""
    # Process with DP method but no consent validator
    result = await process_insight(
        data=sample_data,
        query_type=QueryType.AVERAGE_STORE_VISITS.value,
        pet_method=PrivacyMethod.DP.value,
        epsilon=1.0,
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE
    )
    
    # Verify processing occurred successfully without consent validation
    assert "result" in result
    assert "metadata" in result
    assert result["metadata"]["status"] == "success"
    assert "consent_validated" not in result["metadata"]

@pytest.mark.asyncio
async def test_process_insight_without_user_data(sample_data, mock_consent_validator):
    """Test processing insights when user ID or data scope is not provided."""
    # Process with DP method but no user ID
    result = await process_insight(
        data=sample_data,
        query_type=QueryType.AVERAGE_STORE_VISITS.value,
        pet_method=PrivacyMethod.DP.value,
        epsilon=1.0,
        consent_validator=mock_consent_validator
    )
    
    # Verify processing occurred without consent validation
    assert "result" in result
    assert "metadata" in result
    assert result["metadata"]["status"] == "success"
    assert "consent_validated" not in result["metadata"]
    
    # Verify consent validation was not called
    mock_consent_validator.is_processing_allowed.assert_not_called()

@pytest.mark.asyncio
async def test_process_insight_with_validation_error(sample_data, mock_consent_validator):
    """Test processing insights with invalid input parameters."""
    # Process with invalid epsilon value
    result = await process_insight(
        data=sample_data,
        query_type=QueryType.AVERAGE_STORE_VISITS.value,
        pet_method=PrivacyMethod.DP.value,
        epsilon=-1.0,  # Invalid epsilon
        user_id=USER_ID,
        data_scope=DATA_SCOPE,
        purpose=PURPOSE,
        consent_validator=mock_consent_validator
    )
    
    # Verify results indicate input validation error
    assert result["result"] is None
    assert result["metadata"]["status"] == "error"
    assert "error" in result["metadata"]
    assert "Input validation failed" in result["metadata"]["error"]
    
    # Verify consent validation was not attempted
    mock_consent_validator.is_processing_allowed.assert_not_called() 