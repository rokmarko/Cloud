#!/usr/bin/env python3
"""
Test script to verify device activity check functionality.
"""

import os
import sys
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from models import db, Device
from services.thingsboard_sync import ThingsBoardSyncService

def test_device_activity_check():
    """Test the device activity check functionality."""
    # Load environment variables
    load_dotenv()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("Device Activity Check Test")
        print("=" * 40)
        
        # Initialize ThingsBoard sync service
        sync_service = ThingsBoardSyncService()
        
        # Test authentication first
        print("Testing ThingsBoard authentication...")
        auth_status = sync_service.get_authentication_status()
        print(f"Base URL: {auth_status['base_url']}")
        print(f"Username: {auth_status['username']}")
        
        if sync_service.test_authentication():
            print("✅ ThingsBoard authentication successful")
        else:
            print("❌ ThingsBoard authentication failed")
            print(f"Error: {auth_status.get('error', 'Unknown error')}")
            return False
        
        # Find devices with external_device_id
        devices = Device.query.filter(
            Device.external_device_id.isnot(None),
            Device.external_device_id != ''
        ).all()
        
        if not devices:
            print("❌ No devices with external_device_id found")
            return False
        
        print(f"\nFound {len(devices)} devices with external_device_id:")
        
        # Test device activity check for each device
        for device in devices:
            print(f"\nTesting device: {device.name} (ID: {device.external_device_id})")
            
            # Test the new device activity check
            is_active = sync_service._is_device_active_in_thingsboard(device.external_device_id)
            
            if is_active:
                print(f"✅ Device {device.name} is ACTIVE in ThingsBoard")
            else:
                print(f"⚠️  Device {device.name} is INACTIVE in ThingsBoard")
        
        print("\n" + "=" * 40)
        print("Device activity check test completed")
        return True

if __name__ == "__main__":
    success = test_device_activity_check()
    sys.exit(0 if success else 1)
