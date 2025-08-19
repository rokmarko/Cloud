#!/usr/bin/env python3
"""
Test script for device claiming email functionality
"""
import requests
import json
import sys


def test_device_claim_email():
    """Test the device claiming API with email notification."""
    
    # Configuration
    BASE_URL = "http://127.0.0.1:5000"
    API_KEY = "TcNFCrHyv1w9uCejGgvloANlYkETd1eDoqQJKA7byh8"  # From .env file
    
    # Test data
    test_device = {
        "user_email": "rok@kanardia.eu",  # Use an existing user email
        "device_name": "Test Email Aircraft",
        "device_id": f"test_email_device_{int(__import__('time').time())}",  # Unique ID
        "device_type": "aircraft",
        "model": "Cessna 172 Email Test",
        "serial_number": "TEST-EMAIL-001",
        "registration": "N999EM"
    }
    
    print("Testing Device Claiming Email Functionality")
    print("=" * 50)
    print(f"API Endpoint: {BASE_URL}/api/external/claim-device")
    print(f"Test Device: {test_device['device_name']} for {test_device['user_email']}")
    print()
    
    try:
        # Send the device claim request
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY
        }
        
        response = requests.post(
            f"{BASE_URL}/api/external/claim-device",
            headers=headers,
            json=test_device,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print()
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Device claimed successfully!")
            print(f"   Device ID: {result['device']['id']}")
            print(f"   Device Name: {result['device']['name']}")
            print(f"   User Email: {result['user']['email']}")
            print(f"   User Nickname: {result['user']['nickname']}")
            print()
            print("📧 Email notification should have been sent!")
            print(f"   Check the inbox for: {test_device['user_email']}")
            print("   Also check spam/junk folder if not found in inbox.")
            
        elif response.status_code == 409:
            result = response.json()
            print(f"⚠️  Device already claimed: {result.get('message', 'Unknown error')}")
            print("   This is expected if running the test multiple times.")
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                print(f"   Message: {error_data.get('message', 'No message')}")
            except:
                print(f"   Response text: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure the Flask application is running on port 5000")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False
    
    return True


if __name__ == '__main__':
    print("Device Claiming Email Test")
    print("This script tests the email notification functionality")
    print("when a device is claimed via the API.")
    print()
    
    success = test_device_claim_email()
    
    if success:
        print()
        print("Next steps:")
        print("1. Check the email inbox for the notification")
        print("2. Test the admin email functionality at: http://127.0.0.1:5000/admin/test-email")
        print("3. Review the application logs for any email errors")
    else:
        print()
        print("Test failed. Please check the application logs and try again.")
        sys.exit(1)
