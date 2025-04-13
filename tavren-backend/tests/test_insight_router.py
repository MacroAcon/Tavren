import pytest
from fastapi.testclient import TestClient
import json
import pandas as pd
import io

from app.main import app
from app.utils.insight_processor import QueryType, PrivacyMethod

client = TestClient(app)

def test_get_api_info():
    """Test the GET /api/info endpoint."""
    response = client.get("/api/info")
    assert response.status_code == 200
    
    data = response.json()
    assert "supported_query_types" in data
    assert "supported_privacy_methods" in data
    assert "example_payload" in data
    
    # Verify supported query types
    assert QueryType.AVERAGE_STORE_VISITS.value in data["supported_query_types"]
    
    # Verify supported privacy methods
    assert PrivacyMethod.DP.value in data["supported_privacy_methods"]
    assert PrivacyMethod.SMPC.value in data["supported_privacy_methods"]
    
    # Verify example payload
    assert isinstance(data["example_payload"], dict)
    assert "data" in data["example_payload"]
    assert "query_type" in data["example_payload"]
    assert "pet_method" in data["example_payload"]

def test_process_insight_dp():
    """Test the POST /api/insight endpoint with DP method."""
    # Create test data
    test_data = pd.DataFrame({
        'user_id': ['u1', 'u2', 'u3'],
        'store_category': ['Grocery', 'Grocery', 'Grocery'],
        'visit_count': [5, 3, 4]
    })
    
    # Convert to CSV
    csv_data = test_data.to_csv(index=False)
    
    # Create request payload
    payload = {
        "data": csv_data,
        "query_type": QueryType.AVERAGE_STORE_VISITS.value,
        "pet_method": PrivacyMethod.DP.value,
        "epsilon": 1.0,
        "data_format": "csv"
    }
    
    # Make the request
    response = client.post("/api/insight", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "processed_result" in data
    assert "privacy_method_used" in data
    assert "metadata" in data
    
    # Verify privacy method
    assert data["privacy_method_used"] == PrivacyMethod.DP.value
    
    # Verify metadata
    assert "epsilon" in data["metadata"]
    assert data["metadata"]["epsilon"] == 1.0
    assert "processing_time_ms" in data["metadata"]
    
    # Verify processed result
    assert "Grocery" in data["processed_result"]
    # Value will vary due to randomness in DP, so just check it's a number
    assert isinstance(data["processed_result"]["Grocery"], (int, float))

def test_process_insight_smpc():
    """Test the POST /api/insight endpoint with SMPC method."""
    # Create test data for SMPC (list of party data)
    party_data = [
        {
            "users": ["u1", "u2"],
            "data": {
                "user_id": ["u1", "u2"],
                "store_category": ["Grocery", "Grocery"],
                "visit_count": [5, 3]
            }
        },
        {
            "users": ["u3"],
            "data": {
                "user_id": ["u3"],
                "store_category": ["Grocery"],
                "visit_count": [4]
            }
        }
    ]
    
    # Create request payload
    payload = {
        "data": json.dumps(party_data),
        "query_type": QueryType.AVERAGE_STORE_VISITS.value,
        "pet_method": PrivacyMethod.SMPC.value,
        "data_format": "json"
    }
    
    # Make the request
    response = client.post("/api/insight", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "processed_result" in data
    assert "privacy_method_used" in data
    assert "metadata" in data
    
    # Verify privacy method
    assert data["privacy_method_used"] == PrivacyMethod.SMPC.value
    
    # Verify metadata
    assert "processing_time_ms" in data["metadata"]
    
    # Verify processed result (should be exact with SMPC)
    assert "Grocery" in data["processed_result"]

def test_process_insight_invalid_query_type():
    """Test the POST /api/insight endpoint with invalid query type."""
    payload = {
        "data": "user_id,store_category,visit_count\nu1,Grocery,5",
        "query_type": "invalid_query_type",
        "pet_method": PrivacyMethod.DP.value,
        "epsilon": 1.0,
        "data_format": "csv"
    }
    
    response = client.post("/api/insight", json=payload)
    assert response.status_code == 422  # Validation error

def test_process_insight_missing_epsilon():
    """Test the POST /api/insight endpoint with missing epsilon for DP."""
    payload = {
        "data": "user_id,store_category,visit_count\nu1,Grocery,5",
        "query_type": QueryType.AVERAGE_STORE_VISITS.value,
        "pet_method": PrivacyMethod.DP.value,
        "data_format": "csv"
    }
    
    response = client.post("/api/insight", json=payload)
    assert response.status_code == 422  # Validation error
    assert "epsilon" in response.text.lower() 