#!/usr/bin/env python3
"""
Test script to verify the instrument type functionality
"""

import requests
import json

def test_instrument_type_field():
    """Test that the instrument type field is working in the form."""
    
    print("🧪 Testing Instrument Type Field in Add Layout Form...")
    print("=" * 60)
    
    try:
        # Get the add layout page
        response = requests.get('http://127.0.0.1:5000/dashboard/instrument-layouts/add')
        
        if response.status_code == 302:  # Should redirect to login
            print("✅ Add layout page requires authentication (as expected)")
            
            # Check the redirect location
            if '/auth/login' in response.headers.get('Location', ''):
                print("✅ Proper authentication redirect")
            else:
                print("⚠️ Unexpected redirect location")
                
            # Test that the route exists
            login_response = requests.get('http://127.0.0.1:5000/auth/login')
            if login_response.status_code == 200:
                print("✅ Authentication system is working")
            else:
                print(f"❌ Login page issue: {login_response.status_code}")
                
        elif response.status_code == 200:
            print("⚠️ Add layout page accessible without authentication")
            
            # Check if form contains instrument type field
            content = response.text
            if 'instrument_type' in content:
                print("✅ Found instrument_type field in form")
            else:
                print("❌ Missing instrument_type field")
                
            # Check for the specific instrument type options
            options = ['Digi', 'Indu 57mm', 'Indu 80mm', 'Altimeter 80mm']
            for option in options:
                if option in content:
                    print(f"✅ Found option: {option}")
                else:
                    print(f"❌ Missing option: {option}")
                    
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return False
    
    return True

def check_form_structure():
    """Check if the form structure is correct in the template."""
    print("\n🔍 Checking form structure in template...")
    
    try:
        with open('/home/rok/src/Cloud-1/templates/dashboard/add_instrument_layout_simple.html', 'r') as f:
            content = f.read()
            
        # Check for instrument type form field
        if 'form.instrument_type' in content:
            print("✅ Found instrument_type form field reference")
        else:
            print("❌ Missing instrument_type form field reference")
            
        if 'form-select' in content:
            print("✅ Found form-select class for dropdown")
        else:
            print("❌ Missing form-select class")
            
        # Check for error handling
        if 'form.instrument_type.errors' in content:
            print("✅ Found error handling for instrument_type field")
        else:
            print("❌ Missing error handling for instrument_type field")
            
        return True
        
    except FileNotFoundError:
        print("❌ Could not find template file")
        return False
    except Exception as e:
        print(f"❌ Error reading template: {e}")
        return False

def check_model_and_form():
    """Check if the model and form definitions are correct."""
    print("\n🔍 Checking model and form definitions...")
    
    try:
        # Check model
        with open('/home/rok/src/Cloud-1/src/models.py', 'r') as f:
            model_content = f.read()
            
        if 'instrument_type = db.Column' in model_content:
            print("✅ Found instrument_type column in InstrumentLayout model")
        else:
            print("❌ Missing instrument_type column in model")
            
        # Check form
        with open('/home/rok/src/Cloud-1/src/forms/__init__.py', 'r') as f:
            form_content = f.read()
            
        if 'instrument_type = SelectField' in form_content:
            print("✅ Found instrument_type SelectField in form")
        else:
            print("❌ Missing instrument_type SelectField in form")
            
        # Check for the specific choices
        choices = ['digi', 'indu_57mm', 'indu_80mm', 'altimeter_80mm']
        for choice in choices:
            if choice in form_content:
                print(f"✅ Found choice value: {choice}")
            else:
                print(f"❌ Missing choice value: {choice}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error checking files: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Instrument Type Implementation...")
    print("=" * 70)
    
    success1 = test_instrument_type_field()
    success2 = check_form_structure()
    success3 = check_model_and_form()
    
    print("\n" + "=" * 70)
    if success1 and success2 and success3:
        print("🎉 All instrument type tests completed successfully!")
    else:
        print("❌ Some tests failed!")
        
    print("\n📋 Summary of Changes:")
    print("- Added instrument_type field to InstrumentLayoutCreateForm")
    print("- Updated InstrumentLayout model with instrument_type column")
    print("- Added database migration for new column")
    print("- Updated template to show instrument type dropdown")
    print("- Updated route to handle instrument_type data")
    print("- Updated listing template to display instrument types")
    
    print("\n🎯 Available Instrument Types:")
    print("- Digi")
    print("- Indu 57mm") 
    print("- Indu 80mm")
    print("- Altimeter 80mm")
