#!/usr/bin/env python3
"""
Test script to verify authentication status values in sync.html
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.thingsboard_sync import ThingsBoardSyncService

def test_auth_status():
    """Test the authentication status values."""
    # Load environment variables
    load_dotenv()
    
    print("ThingsBoard Authentication Status Test")
    print("=" * 45)
    
    # Initialize the sync service
    sync_service = ThingsBoardSyncService()
    
    print("1. Testing initial authentication status...")
    auth_status = sync_service.get_authentication_status()
    print(f"   Initial auth_status: {auth_status}")
    print()
    
    print("2. Testing authentication attempt...")
    success = sync_service.test_authentication()
    print(f"   Authentication result: {success}")
    print()
    
    print("3. Testing auth status after authentication...")
    auth_status = sync_service.get_authentication_status()
    print(f"   Updated auth_status:")
    for key, value in auth_status.items():
        print(f"     {key}: {value}")
    print()
    
    print("4. Testing template fields...")
    template_checks = {
        'authenticated': auth_status.get('authenticated'),
        'last_check': auth_status.get('last_check'),
        'error': auth_status.get('error'),
    }
    
    print("   Template field values:")
    for field, value in template_checks.items():
        status = "✅" if value is not None else "❌"
        print(f"     {field}: {value} {status}")
    
    print()
    
    # Test the template logic
    print("5. Testing template logic scenarios...")
    
    if auth_status:
        if auth_status.get('authenticated'):
            print("   ✅ Template would show: Connected (success alert)")
            if auth_status.get('last_check'):
                last_check_str = auth_status['last_check'].strftime('%H:%M:%S')
                print(f"      Last verified: {last_check_str}")
            else:
                print("      Last verified: Unknown")
        else:
            print("   ❌ Template would show: Authentication Failed (danger alert)")
            error_msg = auth_status.get('error') or 'Check credentials and server connectivity'
            print(f"      Error: {error_msg}")
    else:
        print("   ⚠️  Template would show: Status Unknown (warning alert)")
    
    print()
    print("✅ Authentication status test completed!")
    
    return success

if __name__ == "__main__":
    success = test_auth_status()
    sys.exit(0 if success else 1)
