import pytest
import pandas as pd
import numpy as np
from app.utils.insight_processor import process_insight, QueryType, PrivacyMethod

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