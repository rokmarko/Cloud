#!/usr/bin/env python3
"""
Test script to verify CSRF token functionality for admin email test
"""
import requests
from bs4 import BeautifulSoup
import sys

def test_admin_email_csrf():
    """Test that the admin email test form properly handles CSRF tokens."""
    
    BASE_URL = "http://127.0.0.1:5000"
    session = requests.Session()
    
    print("Testing Admin Email CSRF Token Functionality")
    print("=" * 50)
    
    try:
        # Step 1: Try to access login page (if needed)
        print("1. Getting login page...")
        login_response = session.get(f"{BASE_URL}/auth/login")
        print(f"   Login page status: {login_response.status_code}")
        
        # Extract CSRF token from login form
        soup = BeautifulSoup(login_response.text, 'html.parser')
        csrf_input = soup.find('input', attrs={'name': 'csrf_token'})
        if not csrf_input:
            print("   ❌ No CSRF token found in login form")
            return False
        
        csrf_token = csrf_input.get('value')
        print(f"   ✅ CSRF token found: {csrf_token[:20]}...")
        
        # Step 2: Login with admin credentials
        print("2. Logging in as admin...")
        login_data = {
            'email': 'admin@kanardia.test',
            'password': 'admin123',
            'csrf_token': csrf_token,
            'submit': 'Sign In'
        }
        
        login_result = session.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"   Login result status: {login_result.status_code}")
        
        if login_result.status_code != 200 or 'dashboard' not in login_result.url:
            print("   ❌ Login failed")
            return False
        
        print("   ✅ Successfully logged in as admin")
        
        # Step 3: Access the test email page
        print("3. Accessing test email page...")
        email_page_response = session.get(f"{BASE_URL}/admin/test-email")
        print(f"   Email page status: {email_page_response.status_code}")
        
        if email_page_response.status_code != 200:
            print("   ❌ Could not access test email page")
            return False
        
        # Check if CSRF token is present in the form
        email_soup = BeautifulSoup(email_page_response.text, 'html.parser')
        csrf_input = email_soup.find('input', attrs={'name': 'csrf_token'})
        
        if not csrf_input:
            print("   ❌ No CSRF token found in email test form")
            return False
        
        csrf_token = csrf_input.get('value')
        print(f"   ✅ CSRF token found in form: {csrf_token[:20]}...")
        
        # Step 4: Try to submit the form with CSRF token
        print("4. Testing form submission with CSRF token...")
        email_data = {
            'recipient_email': 'test@example.com',
            'csrf_token': csrf_token
        }
        
        form_response = session.post(f"{BASE_URL}/admin/test-email", data=email_data)
        print(f"   Form submission status: {form_response.status_code}")
        
        if form_response.status_code == 200:
            # Check for success message in the response
            if 'Test email sent successfully' in form_response.text or 'Failed to send test email' in form_response.text:
                print("   ✅ Form submitted successfully with CSRF token")
                return True
            else:
                print("   ⚠️  Form submitted but no clear success/failure message found")
                return True
        else:
            print(f"   ❌ Form submission failed with status {form_response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask application is running on port 5000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == '__main__':
    print("Admin Email CSRF Token Test")
    print("This script tests that the admin email functionality properly handles CSRF tokens")
    print()
    
    success = test_admin_email_csrf()
    
    if success:
        print()
        print("✅ CSRF token functionality is working correctly!")
    else:
        print()
        print("❌ CSRF token test failed.")
        sys.exit(1)
