#!/usr/bin/env python3
"""
Test script to simulate ThingsBoard sync with pilot names
"""

import sys
import os
from datetime import datetime, date, time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import Device, LogbookEntry, Pilot
from src.services.thingsboard_sync import thingsboard_sync


def test_pilot_sync():
    """Test pilot name handling in sync."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get a device for testing
            device = Device.query.filter_by(name="Roko2").first()
            if not device:
                print("❌ Device 'Roko2' not found")
                return
            
            print(f"✅ Using device: {device.name} (ID: {device.id})")
            
            # Test data with pilot names
            test_entries = [
                {
                    'date': '2025-07-31',
                    'aircraft_registration': 'I-D871',
                    'aircraft_type': 'Nesis IV',
                    'departure_airport': 'LJLJ',
                    'arrival_airport': 'LJMB',
                    'takeoff_time': '10:00',
                    'landing_time': '11:30',
                    'pilot_name': 'Test Pilot',  # This should map to existing pilot mapping
                    'remarks': 'Test flight with known pilot'
                },
                {
                    'date': '2025-07-31',
                    'aircraft_registration': 'I-D871',
                    'aircraft_type': 'Nesis IV',
                    'departure_airport': 'LJMB',
                    'arrival_airport': 'LJLJ',
                    'takeoff_time': '14:00',
                    'landing_time': '15:15',
                    'pilot_name': 'Unknown Pilot',  # This should fall back to device owner
                    'remarks': 'Test flight with unknown pilot'
                },
                {
                    'date': '2025-07-31',
                    'aircraft_registration': 'I-D871',
                    'aircraft_type': 'Nesis IV',
                    'departure_airport': 'LJLJ',
                    'arrival_airport': 'LJCE',
                    'takeoff_time': '16:00',
                    'landing_time': '17:00',
                    # No pilot_name - should use device owner
                    'remarks': 'Test flight without pilot name'
                }
            ]
            
            print(f"\n🧪 Testing pilot name handling...")
            
            # Process each test entry
            for i, entry_data in enumerate(test_entries, 1):
                print(f"\n--- Test Entry {i} ---")
                print(f"Pilot name: {entry_data.get('pilot_name', 'None')}")
                
                try:
                    # Use the internal method directly for testing
                    created = thingsboard_sync._create_logbook_entry(device, entry_data)
                    
                    if created:
                        print(f"✅ Created logbook entry")
                        
                        # Find the created entry
                        entry = LogbookEntry.query.filter_by(
                            device_id=device.id,
                            date=datetime.strptime(entry_data['date'], '%Y-%m-%d').date(),
                            pilot_name=entry_data.get('pilot_name')
                        ).first()
                        
                        if entry:
                            pilot_mapping = entry.get_pilot_mapping()
                            actual_user = entry.get_actual_pilot_user()
                            
                            print(f"   • Pilot name in entry: {entry.pilot_name}")
                            print(f"   • Assigned to user ID: {entry.user_id}")
                            print(f"   • Actual pilot user: {actual_user.email if actual_user else 'None'}")
                            print(f"   • Has pilot mapping: {'Yes' if pilot_mapping else 'No'}")
                            
                    else:
                        print(f"⚠️  Entry already exists or creation failed")
                        
                except Exception as e:
                    print(f"❌ Error creating entry: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            print(f"\n✅ Test completed successfully!")
            
            # Show summary
            total_entries = LogbookEntry.query.filter_by(device_id=device.id).count()
            entries_with_pilot_names = LogbookEntry.query.filter(
                LogbookEntry.device_id == device.id,
                LogbookEntry.pilot_name.isnot(None)
            ).count()
            
            print(f"\n📊 Summary:")
            print(f"   • Total entries for device: {total_entries}")
            print(f"   • Entries with pilot names: {entries_with_pilot_names}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Test failed: {str(e)}")


if __name__ == "__main__":
    print("🧑‍✈️ Testing Pilot Name Handling in Sync")
    print("=" * 40)
    test_pilot_sync()
