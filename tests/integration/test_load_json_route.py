#!/usr/bin/env python3
"""
Test script for the load_json route to verify it returns proper JSON data.
"""

import requests
import json
import sys

def test_load_json_route():
    """Test the load_json route with proper authentication."""
    
    # Start a session to maintain cookies
    session = requests.Session()
    
    # First, try to login (assuming test admin exists)
    login_data = {
        'email': 'admin@test.com',
        'password': 'admin123'
    }
    
    print("🔑 Attempting to login...")
    login_response = session.post('http://127.0.0.1:5000/auth/login', data=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed with status {login_response.status_code}")
        return False
    
    print("✅ Login successful")
    
    # Test both route patterns
    routes_to_test = [
        '/checklists/1/load_json',
        '/api/checklist/1/load_json'
    ]
    
    for route in routes_to_test:
        print(f"\n🧪 Testing route: {route}")
        
        # Make request to load_json endpoint
        response = session.get(f'http://127.0.0.1:5000{route}')
        
        print(f"📊 Response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Route responded successfully")
            
            # Check if response is valid JSON
            try:
                data = response.json()
                print(f"✅ Response is valid JSON")
                print(f"📋 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                # Check if it has the expected structure
                if isinstance(data, dict):
                    if 'Language' in data and 'Voice' in data and 'Root' in data:
                        print("✅ Response has expected checklist structure")
                        print(f"🌍 Language: {data.get('Language')}")
                        print(f"🗣️ Voice: {data.get('Voice')}")
                        if 'Root' in data and isinstance(data['Root'], dict):
                            root = data['Root']
                            print(f"🌳 Root Name: {root.get('Name')}")
                            print(f"📁 Root Children Count: {len(root.get('Children', []))}")
                    else:
                        print("⚠️ Response doesn't have expected checklist structure")
                        print(f"📄 Response content: {json.dumps(data, indent=2)[:500]}...")
                else:
                    print(f"⚠️ Response is not a dictionary: {type(data)}")
                    
            except json.JSONDecodeError:
                print("❌ Response is not valid JSON")
                print(f"📄 Response content: {response.text[:200]}...")
        else:
            print(f"❌ Route failed with status {response.status_code}")
            print(f"📄 Response: {response.text[:200]}...")
    
    return True

if __name__ == "__main__":
    print("🧪 Testing load_json route modification...")
    print("=" * 50)
    
    test_load_json_route()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
