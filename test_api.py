#!/usr/bin/env python3
"""
Test script for the KanardiaCloud External API
"""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:5000/api/external"
API_KEY = "kanardia-external-api-key-2025-change-in-production"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_claim_device():
    """Test claiming a device."""
    print("Testing device claim...")
    
    payload = {
        "user_email": "test@example.com",  # Replace with actual user email
        "device_name": "Test Aircraft N123AB",
        "device_id": "test_device_001",
        "device_type": "aircraft",
        "model": "Cessna 172",
        "registration": "N123AB"
    }
    
    response = requests.post(f"{BASE_URL}/claim-device", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    return response.status_code == 201

def test_device_status():
    """Test checking device status."""
    print("Testing device status check...")
    
    device_id = "test_device_001"
    response = requests.get(f"{BASE_URL}/device-status/{device_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_unclaim_device():
    """Test unclaiming a device."""
    print("Testing device unclaim...")
    
    payload = {
        "device_id": "test_device_001"
    }
    
    response = requests.post(f"{BASE_URL}/unclaim-device", json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_invalid_api_key():
    """Test with invalid API key."""
    print("Testing invalid API key...")
    
    invalid_headers = {
        "Content-Type": "application/json",
        "X-API-Key": "invalid-key"
    }
    
    payload = {
        "user_email": "test@example.com",
        "device_name": "Test Device",
        "device_id": "test_device_invalid"
    }
    
    response = requests.post(f"{BASE_URL}/claim-device", json=payload, headers=invalid_headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def main():
    """Run all tests."""
    print("KanardiaCloud External API Test Suite")
    print("=" * 40)
    
    try:
        # Test health check (no auth required)
        test_health_check()
        
        # Test invalid API key
        test_invalid_api_key()
        
        # Test claiming a device
        claim_success = test_claim_device()
        
        if claim_success:
            # Test device status
            test_device_status()
            
            # Test unclaiming device
            test_unclaim_device()
        
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the KanardiaCloud application is running on http://localhost:5000")
        sys.exit(1)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
