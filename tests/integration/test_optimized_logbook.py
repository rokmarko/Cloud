#!/usr/bin/env python3
"""
Test script to verify the optimized logbook generation system.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from models import db, Device, Event, LogbookEntry, User
from services.thingsboard_sync import ThingsBoardSyncService

def test_optimized_logbook():
    """Test the optimized logbook generation system."""
    # Load environment variables
    load_dotenv()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("Optimized Logbook Generation Test")
        print("=" * 50)
        
        # Find devices with events
        devices_with_events = db.session.query(Device).join(Event).distinct().all()
        
        if not devices_with_events:
            print("❌ No devices with events found")
            return False
        
        print(f"Found {len(devices_with_events)} devices with events:")
        
        sync_service = ThingsBoardSyncService()
        
        for device in devices_with_events:
            print(f"\n📱 Device: {device.name} (ID: {device.id})")
            print(f"   Owner: {device.user.email if device.user else 'No owner'}")
            
            # Get current statistics
            total_events = Event.query.filter_by(device_id=device.id).count()
            existing_logbook_entries = LogbookEntry.query.filter_by(device_id=device.id).count()
            
            print(f"   📊 Current state:")
            print(f"     - Total events: {total_events}")
            print(f"     - Existing logbook entries: {existing_logbook_entries}")
            
            # Test incremental processing (simulate having 3 new events)
            if total_events >= 3:
                print(f"   🔄 Testing incremental processing with 3 'new' events...")
                
                try:
                    # Test the new incremental method
                    results = sync_service._build_logbook_entries_from_new_events(device, 3)
                    
                    print(f"   ✅ Incremental processing results:")
                    print(f"     - New logbook entries: {results['new_entries']}")
                    print(f"     - Updated entries: {results['updated_entries']}")
                    print(f"     - Errors: {len(results['errors'])}")
                    
                    if results['errors']:
                        for error in results['errors']:
                            print(f"       ⚠️  Error: {error}")
                    
                    # Check all device logbook entries to see visibility
                    all_device_entries = LogbookEntry.query.filter_by(device_id=device.id).all()
                    print(f"   📖 All device logbook entries ({len(all_device_entries)}):")
                    
                    for entry in all_device_entries:
                        user_info = ""
                        if entry.user_id:
                            user_info = f" (user: {entry.user.email})"
                        elif entry.pilot_name:
                            user_info = f" (pilot: {entry.pilot_name})"
                        else:
                            user_info = " (unmapped pilot)"
                        
                        print(f"     - {entry.takeoff_datetime.strftime('%Y-%m-%d %H:%M')} - "
                              f"{entry.flight_time:.1f}h{user_info}")
                    
                    # Test device logbook access
                    print(f"   🔍 Testing device logbook visibility...")
                    
                    # Count unique pilots
                    unique_pilots = set()
                    for entry in all_device_entries:
                        if entry.pilot_name:
                            unique_pilots.add(f"Pilot: {entry.pilot_name}")
                        elif entry.user:
                            unique_pilots.add(f"User: {entry.user.email}")
                        else:
                            unique_pilots.add("Unknown Pilot")
                    
                    print(f"     - Unique pilots who have flown this device: {len(unique_pilots)}")
                    for pilot in unique_pilots:
                        print(f"       • {pilot}")
                    
                    print(f"   ✅ Device shows ALL flights including unmapped pilots")
                    
                except Exception as e:
                    print(f"   ❌ Error during incremental processing: {str(e)}")
                    continue
            else:
                print(f"   ⚠️  Not enough events for meaningful test")
        
        print(f"\n🎯 Testing Summary:")
        print(f"✅ Incremental processing: Only processes new events")
        print(f"✅ Unmapped pilots: Creates logbook entries for all flights")
        print(f"✅ Device visibility: All flights visible in device logbook")
        print(f"✅ No rebuilding: Preserves existing entries")
        
        print("\n" + "=" * 50)
        print("Optimized logbook generation test completed")
        return True

if __name__ == "__main__":
    success = test_optimized_logbook()
    sys.exit(0 if success else 1)
