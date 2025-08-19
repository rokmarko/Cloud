#!/usr/bin/env python3
"""
Simple test to verify CSRF exemption works for API endpoints
"""

from src.app import create_app
import json

def test_api_routes():
    """Test the API routes can be accessed without CSRF tokens"""
    app = create_app()
    
    with app.test_client() as client:
        # Test health endpoint (no auth required)
        print("Testing health endpoint...")
        response = client.get('/api/external/health')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        print()
        
        # Test claim-device endpoint (should fail due to missing API key, not CSRF)
        print("Testing claim-device endpoint without API key...")
        response = client.post('/api/external/claim-device', 
                             json={'user_email': 'test@example.com', 'device_name': 'Test', 'device_id': 'test123'})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        print()
        
        # Test claim-device endpoint with API key
        print("Testing claim-device endpoint with API key...")
        headers = {'X-API-Key': 'kanardia-external-api-key-2025-change-in-production'}
        response = client.post('/api/external/claim-device', 
                             json={'user_email': 'test@example.com', 'device_name': 'Test Device', 'device_id': 'test123'},
                             headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.get_json()}")
        print()

if __name__ == '__main__':
    test_api_routes()
