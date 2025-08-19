#!/usr/bin/env python3
"""
Test script to verify Event model write_address field functionality
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import Event, Device


def test_event_write_address():
    """Test the Event model write_address field."""
    
    app = create_app()
    
    with app.app_context():
        print("Testing Event write_address field...")
        
        # Get a sample event
        event = Event.query.first()
        if event:
            print(f"Sample Event {event.id}:")
            print(f"  device_id: {event.device_id}")
            print(f"  page_address: {event.page_address}")
            print(f"  write_address: {event.write_address}")
            print(f"  total_time: {event.total_time}")
            
            if event.device:
                print(f"  device.name: {event.device.name}")
                print(f"  device.current_logger_page: {event.device.current_logger_page}")
        else:
            print("No events found in database")
            
        # Test creating a new event with write_address
        sample_device = Device.query.first()
        if sample_device:
            print(f"\nTesting new event creation with device {sample_device.id}...")
            
            # Create a test event (don't save to database)
            test_event = Event(
                page_address=123456,
                write_address=sample_device.current_logger_page,
                total_time=3600000,  # 1 hour in milliseconds
                bitfield=0,
                device_id=sample_device.id
            )
            
            print(f"Test event:")
            print(f"  page_address: {test_event.page_address}")
            print(f"  write_address: {test_event.write_address}")
            print(f"  device_id: {test_event.device_id}")
            print("✅ Event model accepts write_address field")
        else:
            print("No devices found for testing")


if __name__ == '__main__':
    test_event_write_address()
