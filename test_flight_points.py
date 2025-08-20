#!/usr/bin/env python3
"""
Test script to verify flight points processing functionality.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models import db, LogbookEntry, Device
from src.app import create_app
from src.services.thingsboard_sync import thingsboard_sync

def test_flight_points_processing():
    """Test flight points processing for existing logbook entries."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find a device with external_device_id
            device = Device.query.filter(
                Device.external_device_id.isnot(None),
                Device.external_device_id != ''
            ).first()
            
            if not device:
                print("No devices with external_device_id found for testing")
                return
            
            print(f"Testing flight points processing for device: {device.name} ({device.external_device_id})")
            
            # Count logbook entries without flight points fetched
            unfetched_entries = LogbookEntry.query.filter(
                LogbookEntry.device_id == device.id,
                LogbookEntry.flight_points_fetched != True
            ).count()
            
            print(f"Found {unfetched_entries} logbook entries without flight points fetch attempts")
            
            if unfetched_entries == 0:
                print("No entries need flight points processing")
                return
            
            # Run the flight points processing
            print("Running flight points processing...")
            result = thingsboard_sync.process_existing_flights_for_points(device, max_entries=5)
            
            print(f"Processing results:")
            print(f"  Total candidates: {result['total_candidates']}")
            print(f"  Processed: {result['processed']}")
            print(f"  Successful: {result['successful']}")
            print(f"  Failed: {result['failed']}")
            print(f"  Errors: {len(result['errors'])}")
            
            for error in result['errors']:
                print(f"  Error: {error}")
            
        except Exception as e:
            print(f"Error during test: {e}")
            raise

if __name__ == '__main__':
    test_flight_points_processing()
    print("Test completed!")
