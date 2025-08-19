#!/usr/bin/env python3
"""
Test script for the new Event.logbook_entry_id field functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, Event, LogbookEntry, Device
from datetime import datetime, timezone

def test_event_logbook_linking():
    """Test the new Event.logbook_entry_id field functionality."""
    app = create_app()
    
    with app.app_context():
        try:
            # Find a device for testing
            device = Device.query.first()
            if not device:
                print("No devices found for testing")
                return
            
            print(f"Testing with device: {device.name}")
            
            # Create a test logbook entry
            test_entry = LogbookEntry(
                takeoff_datetime=datetime.now(timezone.utc),
                landing_datetime=datetime.now(timezone.utc),
                aircraft_type=device.model or 'TEST',
                aircraft_registration=device.registration or 'TEST',
                departure_airport='TEST',
                arrival_airport='TEST',
                flight_time=1.0,
                pilot_in_command_time=1.0,
                dual_time=0.0,
                instrument_time=0.0,
                night_time=0.0,
                cross_country_time=0.0,
                landings_day=1,
                landings_night=0,
                remarks='Test entry for event linking',
                pilot_name='TEST PILOT',
                user_id=None,
                device_id=device.id
            )
            
            db.session.add(test_entry)
            db.session.flush()  # Get the ID
            
            print(f"Created test logbook entry with ID: {test_entry.id}")
            
            # Create a test event
            test_event = Event(
                date_time=datetime.now(timezone.utc),
                page_address=999999,
                total_time=1000000,
                bitfield=2,  # Takeoff event
                message='Test event for linking',
                device_id=device.id,
                logbook_entry_id=test_entry.id  # Link to the logbook entry
            )
            
            db.session.add(test_event)
            db.session.commit()
            
            print(f"Created test event with ID: {test_event.id}")
            
            # Test the relationship
            linked_logbook_entry = test_event.logbook_entry
            if linked_logbook_entry:
                print(f"✓ Event successfully linked to logbook entry: {linked_logbook_entry.id}")
                print(f"  Logbook entry remarks: {linked_logbook_entry.remarks}")
            else:
                print("✗ Event not properly linked to logbook entry")
            
            # Test the reverse relationship
            linked_events = test_entry.linked_events.all()
            if linked_events:
                print(f"✓ Logbook entry has {len(linked_events)} linked events")
                for event in linked_events:
                    print(f"  Linked event ID: {event.id}, Type: {event.get_active_events()}")
            else:
                print("✗ Logbook entry has no linked events")
            
            # Clean up test data
            db.session.delete(test_event)
            db.session.delete(test_entry)
            db.session.commit()
            
            print("✓ Test completed successfully - new Event.logbook_entry_id field is working!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Test failed: {str(e)}")
            raise

if __name__ == '__main__':
    test_event_logbook_linking()
