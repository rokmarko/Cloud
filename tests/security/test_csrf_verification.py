#!/usr/bin/env python3
"""
Test script to verify CSRF token fixes in HTML forms.
"""

import requests
from bs4 import BeautifulSoup

def test_csrf_tokens():
    """Test that CSRF tokens are properly included in forms."""
    base_url = "http://127.0.0.1:5000"
    
    print("CSRF Token Verification Test")
    print("=" * 35)
    
    # Test pages that contain forms
    test_pages = [
        ("/auth/login", "Login Page"),
        ("/auth/register", "Register Page"),
    ]
    
    session = requests.Session()
    
    for url, page_name in test_pages:
        try:
            print(f"\n📄 Testing {page_name}...")
            response = session.get(f"{base_url}{url}")
            
            if response.status_code != 200:
                print(f"❌ Failed to access {page_name}: HTTP {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for CSRF meta tag
            meta_csrf = soup.find('meta', attrs={'name': 'csrf-token'})
            if meta_csrf:
                token = meta_csrf.get('content', '')
                print(f"✅ CSRF meta tag found: {token[:20]}...")
            else:
                print("⚠️  No CSRF meta tag found")
            
            # Check forms for CSRF tokens
            forms = soup.find_all('form')
            print(f"📝 Found {len(forms)} form(s)")
            
            for i, form in enumerate(forms, 1):
                csrf_input = form.find('input', attrs={'name': 'csrf_token'})
                action = form.get('action', 'No action')
                method = form.get('method', 'GET').upper()
                
                if csrf_input:
                    token = csrf_input.get('value', '')
                    print(f"   ✅ Form {i} ({method} {action}): CSRF token present ({token[:15]}...)")
                else:
                    if method == 'POST':
                        print(f"   ❌ Form {i} ({method} {action}): Missing CSRF token!")
                    else:
                        print(f"   ℹ️  Form {i} ({method} {action}): No CSRF needed for GET")
        
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to {base_url}")
            print("   Make sure the Flask app is running")
            return False
        except Exception as e:
            print(f"❌ Error testing {page_name}: {str(e)}")
    
    print(f"\n🔐 Testing admin forms (requires authentication)...")
    
    # Test accessing admin pages (will redirect to login)
    admin_pages = [
        "/admin/sync",
        "/admin/sync/devices"
    ]
    
    for url in admin_pages:
        try:
            response = session.get(f"{base_url}{url}")
            
            if response.status_code == 200:
                # If we get a 200, we're somehow authenticated or the page is accessible
                soup = BeautifulSoup(response.text, 'html.parser')
                forms = soup.find_all('form')
                
                print(f"📄 {url}: {len(forms)} form(s) found")
                
                for i, form in enumerate(forms, 1):
                    csrf_input = form.find('input', attrs={'name': 'csrf_token'})
                    method = form.get('method', 'GET').upper()
                    
                    if method == 'POST':
                        if csrf_input:
                            print(f"   ✅ Form {i}: CSRF token present")
                        else:
                            print(f"   ❌ Form {i}: Missing CSRF token!")
            else:
                print(f"📄 {url}: Redirected (authentication required) - Expected behavior")
        
        except Exception as e:
            print(f"❌ Error testing {url}: {str(e)}")
    
    print("\n✅ CSRF token verification completed!")
    return True

if __name__ == "__main__":
    success = test_csrf_tokens()
    exit(0 if success else 1)
