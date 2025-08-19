#!/usr/bin/env python3
"""
Test script for ThingsBoard authentication functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.thingsboard_sync import ThingsBoardSyncService

def test_authentication():
    """Test ThingsBoard authentication."""
    # Load environment variables
    load_dotenv()
    
    print("ThingsBoard Authentication Test")
    print("=" * 40)
    
    # Check if credentials are configured
    thingsboard_url = os.getenv('THINGSBOARD_URL')
    thingsboard_username = os.getenv('THINGSBOARD_USERNAME')
    thingsboard_password = os.getenv('THINGSBOARD_PASSWORD')
    thingsboard_tenant_id = os.getenv('THINGSBOARD_TENANT_ID')
    
    print(f"ThingsBoard URL: {thingsboard_url}")
    print(f"Username: {thingsboard_username}")
    print(f"Password: {'*' * len(thingsboard_password) if thingsboard_password else 'Not set'}")
    print(f"Tenant ID: {thingsboard_tenant_id}")
    print()
    
    if not all([thingsboard_url, thingsboard_username, thingsboard_password]):
        print("❌ Error: Missing required ThingsBoard credentials in .env file")
        return False
    
    # Initialize the sync service
    sync_service = ThingsBoardSyncService()
    
    # Test authentication
    print("Testing authentication...")
    try:
        result = sync_service.test_authentication()
        if result:
            print("✅ Authentication successful!")
            
            # Get authentication status
            auth_status = sync_service.get_authentication_status()
            print(f"Authenticated: {auth_status.get('authenticated', False)}")
            print(f"Last check: {auth_status.get('last_check', 'Unknown')}")
            if auth_status.get('error'):
                print(f"Error: {auth_status['error']}")
            
        else:
            print("❌ Authentication failed!")
            auth_status = sync_service.get_authentication_status()
            if auth_status.get('error'):
                print(f"Error: {auth_status['error']}")
            
    except Exception as e:
        print(f"❌ Exception during authentication: {str(e)}")
        return False
    
    return result

if __name__ == "__main__":
    success = test_authentication()
    sys.exit(0 if success else 1)
