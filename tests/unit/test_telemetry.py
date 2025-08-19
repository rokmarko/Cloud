#!/usr/bin/env python3
"""
Test script for telemetry functionality
"""

import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db
from src.models import Device
from src.services.thingsboard_sync import ThingsBoardSyncService

def test_telemetry():
    """Test telemetry functionality."""
    app = create_app()
    
    with app.app_context():
        try:
            # Get a device with external_device_id for testing
            device = Device.query.filter(
                Device.external_device_id.isnot(None),
                Device.external_device_id != ''
            ).first()
            
            if not device:
                print("No devices with external_device_id found for testing")
                return False
            
            print(f"Testing telemetry for device: {device.name} (ID: {device.external_device_id})")
            
            # Test telemetry service
            tb_service = ThingsBoardSyncService()
            
            # Test authentication
            print("Testing authentication...")
            if not tb_service.test_authentication():
                print("Authentication failed")
                return False
            print("Authentication successful")
            
            # Test telemetry fetch
            print("Testing telemetry fetch...")
            telemetry_data = tb_service._get_device_telemetry(device.external_device_id)
            
            if telemetry_data:
                print(f"Telemetry data received: {telemetry_data}")
                
                # Test device telemetry update
                print("Testing device telemetry update...")
                device.update_telemetry(telemetry_data)
                db.session.commit()
                
                print(f"Device telemetry updated:")
                print(f"  Status: {device.status} -> {device.status_description}")
                print(f"  Fuel: {device.fuel_quantity}")
                print(f"  Location: {device.latitude}, {device.longitude} -> {device.location_description}")
                print(f"  Altitude: {device.altitude}")
                print(f"  Speed: {device.speed}")
                print(f"  Last Update: {device.last_telemetry_update}")
                
            else:
                print("No telemetry data received")
            
            return True
            
        except Exception as e:
            print(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("Starting telemetry test...")
    success = test_telemetry()
    
    if success:
        print("Test completed successfully!")
        sys.exit(0)
    else:
        print("Test failed!")
        sys.exit(1)
