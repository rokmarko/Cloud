#!/usr/bin/env python3
"""
Test script to verify logbook entry generation from events.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from models import db, Device, Event
from services.thingsboard_sync import ThingsBoardSyncService

def test_logbook_from_events():
    """Test logbook entry generation from events."""
    # Load environment variables
    load_dotenv()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("Logbook from Events Test")
        print("=" * 40)
        
        # Find devices with events
        devices_with_events = db.session.query(Device).join(Event).distinct().all()
        
        if not devices_with_events:
            print("❌ No devices with events found")
            return False
        
        print(f"Found {len(devices_with_events)} devices with events:")
        
        sync_service = ThingsBoardSyncService()
        
        for device in devices_with_events:
            print(f"\nDevice: {device.name} (ID: {device.id})")
            
            # Get event counts
            total_events = Event.query.filter_by(device_id=device.id).count()
            takeoff_events = Event.query.filter_by(device_id=device.id).filter(
                Event.bitfield.op('&')(1 << 1) != 0  # Takeoff bit
            ).count()
            landing_events = Event.query.filter_by(device_id=device.id).filter(
                Event.bitfield.op('&')(1 << 2) != 0  # Landing bit
            ).count()
            
            print(f"  Total events: {total_events}")
            print(f"  Takeoff events: {takeoff_events}")
            print(f"  Landing events: {landing_events}")
            
            if takeoff_events > 0 and landing_events > 0:
                print(f"  ✅ Has takeoff/landing events - testing logbook generation")
                
                try:
                    # Test the logbook generation
                    results = sync_service._build_logbook_entries_from_events(device)
                    
                    print(f"  Results: {results['new_entries']} new logbook entries")
                    if results['errors']:
                        print(f"  Errors: {results['errors']}")
                    
                    # Commit changes
                    db.session.commit()
                    
                except Exception as e:
                    print(f"  ❌ Error: {str(e)}")
                    db.session.rollback()
            else:
                print(f"  ⚠️  Not enough takeoff/landing events for logbook generation")
        
        print("\n" + "=" * 40)
        print("Logbook from events test completed")
        return True

if __name__ == "__main__":
    success = test_logbook_from_events()
    sys.exit(0 if success else 1)
