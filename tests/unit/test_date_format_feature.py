#!/usr/bin/env python3
"""
Test script for the new user date format configuration feature.
Tests both the backend functionality and database changes.
"""

import sys
import os
import requests
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import User

def test_user_date_format_field():
    """Test that users have the date_format field and it works correctly."""
    app = create_app()
    
    with app.app_context():
        try:
            print("🧪 Testing User date_format field functionality...")
            
            # Test 1: Check if date_format field exists and has default value
            user = User.query.first()
            if not user:
                print("❌ No users found in database - create a test user first")
                return False
            
            print(f"✓ Found user: {user.email}")
            
            # Test 2: Check default date format
            if hasattr(user, 'date_format'):
                print(f"✓ User has date_format field: {user.date_format}")
                if user.date_format == '%Y-%m-%d':
                    print("✓ Default date format is correct (%Y-%m-%d)")
                else:
                    print(f"⚠️  Default date format is {user.date_format}, expected %Y-%m-%d")
            else:
                print("❌ User does not have date_format field")
                return False
            
            # Test 3: Test different date formats
            test_formats = ['%d.%m.%Y', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d']
            test_date = datetime(2025, 8, 19)
            
            print("\n📅 Testing date format rendering:")
            for fmt in test_formats:
                user.date_format = fmt
                formatted_date = test_date.strftime(user.date_format)
                print(f"  {fmt} → {formatted_date}")
            
            # Reset to default
            user.date_format = '%Y-%m-%d'
            db.session.commit()
            
            print("✓ Date format functionality test completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error during date format test: {e}")
            return False

def test_user_settings_route():
    """Test that the user settings route is accessible."""
    try:
        print("\n🌐 Testing User Settings route accessibility...")
        
        # Test GET request to settings page (should redirect to login if not authenticated)
        response = requests.get('http://127.0.0.1:5000/settings', timeout=5)
        if response.status_code in [200, 302]:  # 200 if authenticated, 302 if redirected to login
            print("✓ Settings route is accessible")
            if 'login' in response.url.lower() or response.status_code == 302:
                print("✓ Route properly requires authentication")
            return True
        else:
            print(f"❌ Settings route returned unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to Flask app: {e}")
        print("   Make sure the Flask app is running on http://127.0.0.1:5000")
        return False

def test_templates_updated():
    """Test that templates are using the new date format."""
    print("\n📄 Checking template updates...")
    
    templates_to_check = [
        'templates/base.html',
        'templates/dashboard/user_settings.html',
        'templates/dashboard/device_logbook.html',
        'templates/dashboard/index.html',
        'templates/dashboard/checklists.html'
    ]
    
    success = True
    
    for template in templates_to_check:
        template_path = os.path.join(os.path.dirname(__file__), template)
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                content = f.read()
                
            if template == 'templates/base.html':
                if 'user_settings' in content and 'settings' in content:
                    print(f"✓ {template} - Navigation link added")
                else:
                    print(f"❌ {template} - Navigation link missing")
                    success = False
                    
            elif template == 'templates/dashboard/user_settings.html':
                if 'date_format' in content and 'current_user.date_format' in content:
                    print(f"✓ {template} - User settings form implemented")
                else:
                    print(f"❌ {template} - User settings form missing")
                    success = False
                    
            elif 'current_user.date_format' in content:
                print(f"✓ {template} - Using user date format")
            else:
                print(f"❌ {template} - Not using user date format")
                success = False
        else:
            print(f"❌ {template} - File not found")
            success = False
    
    return success

def main():
    """Run all tests."""
    print("🚀 Testing KanardiaCloud Date Format Configuration Feature\n")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Database and model functionality
    if test_user_date_format_field():
        tests_passed += 1
    
    # Test 2: Route accessibility
    if test_user_settings_route():
        tests_passed += 1
        
    # Test 3: Template updates
    if test_templates_updated():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Date format configuration feature is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return False

if __name__ == '__main__':
    main()
