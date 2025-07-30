#!/usr/bin/env python3
"""
Test CSRF token functionality for pilot mappings with WTForms
"""

import sys
import os
import re

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app

def test_pilot_form_csrf():
    """Test that the pilot form includes CSRF tokens correctly with WTForms."""
    
    app = create_app()
    
    with app.test_client() as client:
        print("=== TESTING PILOT FORM CSRF TOKEN WITH WTFORMS ===\n")
        
        # First, get login page and extract CSRF token
        print("1. Getting login page...")
        login_page = client.get('/auth/login')
        
        if login_page.status_code == 200:
            print("✅ Login page loaded")
        else:
            print(f"❌ Failed to load login page: {login_page.status_code}")
            return
        
        # Extract CSRF token from login form
        login_html = login_page.data.decode('utf-8')
        csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', login_html)
        
        if csrf_match:
            login_csrf_token = csrf_match.group(1)
            print(f"✅ Got login CSRF token: {login_csrf_token[:20]}...")
        else:
            print("❌ Could not extract login CSRF token")
            print("Login page content snippet:")
            csrf_search = re.search(r'csrf[^>]*>', login_html)
            if csrf_search:
                print(csrf_search.group(0))
            return
        
        # Login as admin
        print("2. Logging in as admin...")
        login_response = client.post('/auth/login', data={
            'email': 'admin@kanardia.test',
            'password': 'adminpass123',
            'csrf_token': login_csrf_token
        }, follow_redirects=True)
        
        if b'Admin Dashboard' in login_response.data or login_response.status_code == 200:
            print("✅ Login successful")
        else:
            print("❌ Login failed")
            print("Response:", login_response.data.decode('utf-8')[:300])
            return
        
        # Get the pilots page
        print("3. Getting pilots page...")
        pilots_response = client.get('/admin/pilots', follow_redirects=True)
        
        if pilots_response.status_code == 200:
            print("✅ Pilots page loaded successfully")
        else:
            print(f"❌ Failed to load pilots page: {pilots_response.status_code}")
            print("Response content:", pilots_response.data.decode('utf-8')[:300])
            return
        
        # Check if CSRF token is in the HTML
        html_content = pilots_response.data.decode('utf-8')
        
        if 'name="csrf_token"' in html_content:
            print("✅ CSRF token field found in HTML")
        else:
            print("❌ CSRF token field NOT found in HTML")
            return
        
        # Extract CSRF token from the pilot form
        csrf_match = re.search(r'id="csrf_token"[^>]*value="([^"]+)"', html_content)
        if csrf_match:
            csrf_token = csrf_match.group(1)
            print(f"✅ Extracted CSRF token: {csrf_token[:20]}...")
        else:
            print("❌ Could not extract CSRF token value")
            return
        
        # Test creating a pilot mapping with CSRF token
        print("4. Testing pilot mapping creation with CSRF...")
        create_data = {
            'pilot_name': 'CSRF Test Pilot WTF',
            'user_id': '3',  # test@example.com
            'device_id': '5',  # Roko2
            'csrf_token': csrf_token
        }
        
        create_response = client.post('/admin/pilots/create', data=create_data, follow_redirects=False)
        
        if create_response.status_code == 302:
            print("✅ Pilot creation successful (redirected)")
            print(f"   Redirect location: {create_response.headers.get('Location', 'Unknown')}")
            
            # Check if the mapping was actually created by accessing the pilots page again
            verify_response = client.get('/admin/pilots')
            if 'CSRF Test Pilot WTF' in verify_response.data.decode('utf-8'):
                print("✅ Pilot mapping verified in database")
            else:
                print("⚠️  Pilot mapping not found in pilots list")
                
        elif create_response.status_code == 400:
            print("❌ CSRF validation still failed")
            print("   Response data:", create_response.data.decode('utf-8')[:200])
        else:
            print(f"⚠️  Unexpected response: {create_response.status_code}")
            print("   Response data:", create_response.data.decode('utf-8')[:200])
        
        print("\n=== CSRF TEST COMPLETE ===")

if __name__ == '__main__':
    test_pilot_form_csrf()
