#!/usr/bin/env python3
"""
Test manual sync functionality
"""

import os
import sys
import requests
from bs4 import BeautifulSoup

def test_manual_sync():
    """Test the manual sync trigger."""
    base_url = "http://127.0.0.1:5000"
    
    print("Manual Sync Test")
    print("=" * 20)
    
    # Create a session
    session = requests.Session()
    
    try:
        # Get the login page to establish session
        print("1. Getting login page...")
        response = session.get(f"{base_url}/auth/login")
        if response.status_code != 200:
            print(f"❌ Failed to get login page: {response.status_code}")
            return False
        
        # Extract CSRF token from login form
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_input = soup.find('input', attrs={'name': 'csrf_token'})
        if not csrf_input:
            print("❌ No CSRF token found in login form")
            return False
        
        csrf_token = csrf_input.get('value')
        print(f"✅ CSRF token found: {csrf_token[:20]}...")
        
        # Try to access sync page (this will redirect to login for unauthenticated user)
        print("\n2. Testing sync page access...")
        response = session.get(f"{base_url}/admin/sync")
        
        if response.status_code == 200:
            print("✅ Admin sync page accessible")
            
            # Parse the page to check authentication status
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for authentication status indicators
            success_alerts = soup.find_all('div', class_='alert-success')
            danger_alerts = soup.find_all('div', class_='alert-danger')
            warning_alerts = soup.find_all('div', class_='alert-warning')
            
            print(f"   Authentication status indicators:")
            print(f"   - Success alerts: {len(success_alerts)}")
            print(f"   - Error alerts: {len(danger_alerts)}")
            print(f"   - Warning alerts: {len(warning_alerts)}")
            
            # Look for the manual sync button
            sync_forms = soup.find_all('form', action=lambda x: x and 'sync/run' in x)
            if sync_forms:
                print(f"✅ Found {len(sync_forms)} manual sync form(s)")
            else:
                print("❌ No manual sync forms found")
            
            # Look for CSRF tokens in forms
            csrf_inputs = soup.find_all('input', attrs={'name': 'csrf_token'})
            print(f"✅ Found {len(csrf_inputs)} CSRF token(s) in page")
            
        elif response.status_code in [302, 401]:
            print("⚠️  Redirected to login (expected for unauthenticated user)")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            return False
        
        print("\n✅ Manual sync page test completed!")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask application")
        print("   Make sure the app is running on http://127.0.0.1:5000")
        return False
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_manual_sync()
    exit(0 if success else 1)
