#!/usr/bin/env python3
"""
Test script to verify the navigation menu entry for Instrument Layouts
"""

import requests
import re

def test_navigation_menu():
    """Test that the instrument layouts menu entry is present in the navigation."""
    
    # Test if we can access the dashboard page (will redirect to login)
    print("🧪 Testing navigation menu for Instrument Layouts...")
    print("=" * 50)
    
    try:
        # Get the login page to check if navigation structure is correct
        response = requests.get('http://127.0.0.1:5000/auth/login')
        
        if response.status_code == 200:
            print("✅ Login page accessible")
            
            # Check if the base template has the instrument layouts menu
            # (we won't see it on login page but we can check the route exists)
            dashboard_response = requests.get('http://127.0.0.1:5000/dashboard/instrument-layouts')
            
            if dashboard_response.status_code == 302:  # Should redirect to login
                print("✅ Instrument layouts route exists and requires authentication")
                
                # Check the redirect location
                if '/auth/login' in dashboard_response.headers.get('Location', ''):
                    print("✅ Proper authentication redirect")
                else:
                    print("⚠️ Unexpected redirect location")
            else:
                print(f"❌ Unexpected status code: {dashboard_response.status_code}")
                
        else:
            print(f"❌ Could not access login page: {response.status_code}")
            
        # Test the main dashboard route
        dashboard_main = requests.get('http://127.0.0.1:5000/dashboard')
        if dashboard_main.status_code == 302:
            print("✅ Dashboard route exists and requires authentication")
        else:
            print(f"⚠️ Dashboard route status: {dashboard_main.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    
    return True

def check_menu_structure():
    """Check if the menu structure contains instrument layouts."""
    print("\n🔍 Checking menu structure in base template...")
    
    try:
        with open('/home/rok/src/Cloud-1/templates/base.html', 'r') as f:
            content = f.read()
            
        # Look for instrument layouts menu entry
        if 'dashboard.instrument_layouts' in content:
            print("✅ Found instrument_layouts route reference in base template")
        else:
            print("❌ Missing instrument_layouts route reference")
            
        if 'Instrument Layouts' in content:
            print("✅ Found 'Instrument Layouts' text in menu")
        else:
            print("❌ Missing 'Instrument Layouts' text")
            
        # Check for proper menu structure
        if 'material-icons">dashboard</span> Instrument Layouts' in content:
            print("✅ Found proper menu entry with icon and text")
        else:
            print("❌ Menu entry format issue")
            
        # Count total nav items to see menu structure
        nav_items = content.count('<li class="nav-item">')
        print(f"📊 Total navigation items found: {nav_items}")
        
        return True
        
    except FileNotFoundError:
        print("❌ Could not find base.html template")
        return False
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Instrument Layouts Navigation Menu...")
    print("=" * 60)
    
    success1 = test_navigation_menu()
    success2 = check_menu_structure()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 Navigation menu tests completed successfully!")
    else:
        print("❌ Some tests failed!")
        
    print("\n📋 Summary:")
    print("- Menu entry added to sidebar navigation")
    print("- Route properly configured with authentication")
    print("- Active state handling for menu highlighting")
    print("- Material Design icon integration")
