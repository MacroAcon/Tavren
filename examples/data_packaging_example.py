#!/usr/bin/env python3
"""
Example script demonstrating the Tavren Data Packaging layer.

This script simulates a full workflow of:
1. Creating consent
2. Requesting data as a buyer
3. Examining the packaged data with different anonymization levels
4. Using the access token to retrieve data
5. Creating rewards based on data delivery

To run:
python examples/data_packaging_example.py

Note: This requires a running Tavren backend server.
"""

import sys
import os
import json
import asyncio
import httpx
from datetime import datetime
from typing import Dict, Any, List
from pprint import pprint

# Constants
API_URL = "http://localhost:8000"
TEST_USER_ID = "example_user_123"
TEST_BUYER_ID = "example_buyer_456"
TEST_OFFER_ID = "special-offer-789"

# Sample data types to demonstrate
DATA_TYPES = ["app_usage", "location", "browsing_history", "health", "financial"]

# Different access levels to demonstrate
ACCESS_LEVELS = [
    "precise_persistent",
    "precise_short_term",
    "anonymous_persistent",
    "anonymous_short_term"
]

async def create_consent_event() -> str:
    """Create a consent event for testing."""
    print("\n=== Creating Consent Event ===")
    
    async with httpx.AsyncClient() as client:
        # Register an accepted consent event
        response = await client.post(
            f"{API_URL}/api/consent/accept",
            json={
                "user_id": TEST_USER_ID,
                "offer_id": TEST_OFFER_ID,
                "action": "accepted",
                "timestamp": datetime.now().isoformat(),
                "user_reason": "Testing data packaging"
            }
        )
        
        if response.status_code != 200:
            print(f"Error creating consent: {response.text}")
            return None
            
        data = response.json()
        consent_id = data.get("id")
        print(f"Created consent record with ID: {consent_id}")
        return consent_id

async def request_data_package(data_type: str, access_level: str) -> Dict[str, Any]:
    """Request a data package from the API."""
    print(f"\n=== Requesting {data_type} data with {access_level} access ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/data-packages",
            json={
                "user_id": TEST_USER_ID,
                "data_type": data_type,
                "access_level": access_level,
                "consent_id": TEST_OFFER_ID,  # Using the offer ID as consent ID for simplicity
                "purpose": "example demonstration",
                "buyer_id": TEST_BUYER_ID,
                "trust_tier": "standard"
            }
        )
        
        if response.status_code != 200:
            print(f"Error requesting data package: {response.text}")
            return None
            
        data = response.json()
        print(f"Received data package with ID: {data['package_id']}")
        return data

async def examine_package(package: Dict[str, Any]):
    """Examine the contents of a data package."""
    print("\n=== Examining Data Package ===")
    print(f"Package ID: {package['package_id']}")
    print(f"Created at: {package['created_at']}")
    print(f"Data type: {package['data_type']}")
    print(f"Access level: {package['access_level']}")
    print(f"Anonymization level: {package['anonymization_level']}")
    print(f"Purpose: {package['purpose']}")
    print(f"Expires at: {package['expires_at']}")
    
    # Check metadata
    print("\n--- Metadata ---")
    print(f"Record count: {package['metadata']['record_count']}")
    print(f"Schema version: {package['metadata']['schema_version']}")
    print(f"Data quality score: {package['metadata']['data_quality_score']}")
    
    # Check content (limit to first 2 records if it's a list)
    print("\n--- Content Sample ---")
    content = package['content']
    if isinstance(content, list):
        for i, record in enumerate(content[:2]):
            print(f"\nRecord {i+1}:")
            pprint(record)
        if len(content) > 2:
            print(f"\n... and {len(content) - 2} more records")
    else:
        pprint(content)

async def validate_access_token(package_id: str, access_token: str) -> bool:
    """Validate an access token for a data package."""
    print("\n=== Validating Access Token ===")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/api/data-packages/validate-token",
            json={
                "package_id": package_id,
                "access_token": access_token
            }
        )
        
        if response.status_code != 200:
            print(f"Error validating token: {response.text}")
            return False
            
        data = response.json()
        print(f"Token valid: {data.get('valid', False)}")
        if data.get('valid'):
            print(f"Expires at: {data.get('expires_at')}")
        else:
            print(f"Reason: {data.get('reason')}")
            
        return data.get('valid', False)

async def compare_anonymization_levels():
    """Compare different anonymization levels for the same data."""
    print("\n=== Comparing Anonymization Levels ===")
    
    data_type = "location"  # Location data is good for demonstrating anonymization
    packages = {}
    
    # Request the same data type with different access levels
    for access_level in ACCESS_LEVELS:
        package = await request_data_package(data_type, access_level)
        if package:
            packages[access_level] = package
    
    # Compare the first record in each package
    if not packages:
        print("Failed to retrieve any packages for comparison")
        return
        
    print("\nComparing the first record in each package:")
    
    for access_level, package in packages.items():
        content = package['content']
        if not isinstance(content, list) or not content:
            print(f"{access_level}: No records")
            continue
            
        record = content[0]
        
        # Create a simplified view for comparison
        simplified = {
            "access_level": access_level,
            "anonymization": package['anonymization_level'],
        }
        
        # Add relevant fields for comparison
        if data_type == "location":
            if "latitude" in record and "longitude" in record:
                simplified["coordinates"] = f"{record['latitude']}, {record['longitude']}"
            if "timestamp" in record:
                simplified["timestamp"] = record["timestamp"]
            if "accuracy" in record:
                simplified["accuracy"] = record["accuracy"]
                
        print(f"\n{access_level} ({package['anonymization_level']}):")
        pprint(simplified)

async def simulate_buyer_api():
    """Simulate using the buyer API for requesting data."""
    print("\n=== Simulating Buyer API ===")
    
    # First, check available data types
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_URL}/api/buyers/data/available-types")
        if response.status_code != 200:
            print(f"Error getting available data types: {response.text}")
            return
            
        data_types = response.json()
        print("Available data types:")
        for dt in data_types:
            print(f"- {dt['name']}: {dt['description']}")
        
        # Request data through buyer API
        response = await client.post(
            f"{API_URL}/api/buyers/data/request",
            json={
                "user_id": TEST_USER_ID,
                "data_type": "app_usage",
                "access_level": "anonymous_short_term",
                "consent_id": TEST_OFFER_ID,
                "purpose": "buyer api demonstration",
                "buyer_id": TEST_BUYER_ID
            }
        )
        
        if response.status_code != 200:
            print(f"Error requesting data through buyer API: {response.text}")
            return
            
        data = response.json()
        print(f"\nReceived data package with ID: {data['package_id']}")
        print(f"Access level: {data['access_level']}")
        print(f"Anonymization level: {data['anonymization_level']}")
        print(f"Record count: {data['metadata']['record_count']}")

async def cleanup():
    """Clean up any test data created."""
    print("\n=== Cleaning Up ===")
    # In a real implementation, we would delete the test consent records
    # and any other test data created
    print("Cleanup complete")

async def main():
    """Main function demonstrating data packaging workflow."""
    print("=== Tavren Data Packaging Example ===")
    
    try:
        # Create consent
        consent_id = await create_consent_event()
        if not consent_id:
            print("Failed to create consent, exiting...")
            return
            
        # Request a data package
        package = await request_data_package("app_usage", "anonymous_short_term")
        if not package:
            print("Failed to request data package, exiting...")
            return
            
        # Examine the package
        await examine_package(package)
        
        # Validate access token
        token_valid = await validate_access_token(
            package['package_id'],
            package['access_token']
        )
        
        # Compare anonymization levels
        await compare_anonymization_levels()
        
        # Simulate buyer API
        await simulate_buyer_api()
        
        # Clean up
        await cleanup()
        
    except Exception as e:
        print(f"Error in example: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 