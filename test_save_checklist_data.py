#!/usr/bin/env python3
"""
Test script to verify saveChecklistData functionality and the updated API route.
"""

import requests
import json
import sys

def test_save_checklist_data():
    """Test the saveChecklistData functionality with proper authentication."""
    
    # Start a session to maintain cookies
    session = requests.Session()
    
    # Test data structure (checklist format)
    test_data = {
        "Language": "en-us",
        "Voice": "Linda",
        "Root": {
            "Type": 0,
            "Name": "Root",
            "Children": [
                {
                    "Type": 0,
                    "Name": "Pre-flight",
                    "Children": [
                        {
                            "Type": 1,
                            "Name": "Check fuel level",
                            "Children": []
                        }
                    ]
                },
                {
                    "Type": 0,
                    "Name": "In-flight",
                    "Children": [
                        {
                            "Type": 1,
                            "Name": "Monitor engine parameters",
                            "Children": []
                        }
                    ]
                }
            ]
        }
    }
    
    print("🧪 Testing saveChecklistData functionality...")
    print("=" * 60)
    
    # First get login page to obtain CSRF token
    print("🔑 Getting login page for CSRF token...")
    login_page = session.get('http://127.0.0.1:5000/auth/login')
    
    if login_page.status_code != 200:
        print(f"❌ Failed to get login page: {login_page.status_code}")
        return False
    
    # Extract CSRF token from login page
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]*)"', login_page.text)
    if not csrf_match:
        print("❌ Could not find CSRF token on login page")
        return False
    
    csrf_token = csrf_match.group(1)
    print(f"✅ Found CSRF token: {csrf_token[:20]}...")
    
    # Login with credentials
    login_data = {
        'email': 'admin@test.com',
        'password': 'admin123',
        'csrf_token': csrf_token
    }
    
    print("🔑 Attempting to login...")
    login_response = session.post('http://127.0.0.1:5000/auth/login', data=login_data)
    
    if login_response.status_code == 200 and 'dashboard' in login_response.url:
        print("✅ Login successful")
    elif login_response.status_code == 302:
        print("✅ Login successful (redirected)")
    else:
        print(f"❌ Login failed with status {login_response.status_code}")
        print(f"URL: {login_response.url}")
        return False
    
    # Test the API update route with json_content
    print(f"\n📊 Testing API update route with json_content...")
    
    # First try to get CSRF token from the dashboard
    dashboard_response = session.get('http://127.0.0.1:5000/dashboard/checklists')
    csrf_match = re.search(r'content="([^"]*)"[^>]*name="csrf-token"', dashboard_response.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"✅ Found dashboard CSRF token: {csrf_token[:20]}...")
    
    # Test updating checklist with ID 1
    checklist_id = 1
    update_url = f'http://127.0.0.1:5000/dashboard/api/checklist/{checklist_id}'
    
    update_data = {
        'json_content': test_data
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf_token
    }
    
    print(f"🔄 Sending PUT request to {update_url}")
    print(f"📋 Data preview: {json.dumps(test_data, indent=2)[:200]}...")
    
    response = session.put(update_url, json=update_data, headers=headers)
    
    print(f"📊 Response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ API update successful")
        try:
            response_data = response.json()
            print(f"📋 Response: {response_data}")
        except:
            print("📋 Response (text):", response.text[:200])
            
        # Verify the data was saved by loading it back
        print(f"\n🔍 Verifying data was saved...")
        load_response = session.get(f'http://127.0.0.1:5000/dashboard/api/checklist/{checklist_id}/load_json')
        
        if load_response.status_code == 200:
            print("✅ Load response successful")
            loaded_data = load_response.json()
            
            # Check if our test data matches
            if loaded_data.get('Language') == test_data['Language']:
                print("✅ Data verification successful - Language matches")
            else:
                print(f"⚠️ Data mismatch - Expected: {test_data['Language']}, Got: {loaded_data.get('Language')}")
                
            if loaded_data.get('Root', {}).get('Name') == test_data['Root']['Name']:
                print("✅ Data verification successful - Root name matches")
            else:
                print(f"⚠️ Root name mismatch")
                
            children_count = len(loaded_data.get('Root', {}).get('Children', []))
            expected_count = len(test_data['Root']['Children'])
            if children_count == expected_count:
                print(f"✅ Children count matches: {children_count}")
            else:
                print(f"⚠️ Children count mismatch - Expected: {expected_count}, Got: {children_count}")
                
        else:
            print(f"❌ Failed to verify data: {load_response.status_code}")
            
    elif response.status_code == 404:
        print("❌ Checklist not found - try creating a checklist first")
    elif response.status_code == 403:
        print("❌ Forbidden - check CSRF token or authentication")
    else:
        print(f"❌ Update failed with status {response.status_code}")
        print(f"📄 Response: {response.text[:300]}")
    
    return response.status_code == 200

if __name__ == "__main__":
    print("🧪 Testing saveChecklistData API integration...")
    print("=" * 60)
    
    try:
        success = test_save_checklist_data()
        print("\n" + "=" * 60)
        if success:
            print("🎉 Test completed successfully!")
        else:
            print("❌ Test failed!")
    except Exception as e:
        print(f"💥 Error during test: {e}")
        import traceback
        traceback.print_exc()
