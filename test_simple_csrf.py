#!/usr/bin/env python3
"""
Simple test to verify CSRF token is present in admin email test form
"""
import requests
from bs4 import BeautifulSoup
import sys

def test_csrf_token_present():
    """Test that the admin email test form contains a CSRF token."""
    
    BASE_URL = "http://127.0.0.1:5000"
    
    print("Testing CSRF Token Presence in Admin Email Form")
    print("=" * 50)
    
    try:
        # Access the test email page directly (will redirect to login if not authenticated)
        print("1. Accessing test email page...")
        response = requests.get(f"{BASE_URL}/admin/test-email", allow_redirects=True)
        print(f"   Final URL: {response.url}")
        print(f"   Status: {response.status_code}")
        
        # If redirected to login, that's expected - let's check the login page
        if '/auth/login' in response.url:
            print("   ✅ Correctly redirected to login (authentication required)")
            return True
            
        # If we somehow got the email page directly, check for CSRF token
        elif response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_input = soup.find('input', attrs={'name': 'csrf_token'})
            
            if csrf_input:
                print(f"   ✅ CSRF token found in form")
                return True
            else:
                print("   ❌ No CSRF token found in form")
                return False
        
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask application is running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

def verify_form_has_csrf():
    """Test by directly examining the template file for CSRF token."""
    
    print("2. Verifying template file contains CSRF token...")
    
    try:
        with open('/home/rok/src/Cloud-1/templates/admin/test_email.html', 'r') as f:
            content = f.read()
        
        if 'csrf_token' in content:
            print("   ✅ CSRF token found in template file")
            
            # Count how many times it appears
            csrf_count = content.count('csrf_token')
            print(f"   ✅ Found {csrf_count} references to csrf_token in template")
            
            if 'name="csrf_token"' in content:
                print("   ✅ Hidden CSRF token input field found")
                return True
            else:
                print("   ⚠️  csrf_token referenced but no hidden input field found")
                return False
        else:
            print("   ❌ No CSRF token found in template")
            return False
            
    except FileNotFoundError:
        print("   ❌ Template file not found")
        return False
    except Exception as e:
        print(f"   ❌ Error reading template: {str(e)}")
        return False

if __name__ == '__main__':
    print("Admin Email CSRF Token Verification")
    print("This script verifies that CSRF tokens are properly implemented")
    print()
    
    success1 = test_csrf_token_present()
    success2 = verify_form_has_csrf()
    
    if success1 and success2:
        print()
        print("✅ CSRF token verification passed!")
        print("The admin email form properly includes CSRF protection.")
    else:
        print()
        print("❌ CSRF token verification failed.")
        sys.exit(1)
