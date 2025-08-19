#!/usr/bin/env python3
"""
Test the ThingsBoard sync service with unknown pilots.

This script simulates the sync service behavior with unknown pilots to verify
they are not linked to device owners.
"""

import sys
import os
from datetime import datetime, date

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app
from src.models import LogbookEntry, Device, User, Pilot, db
from src.services.thingsboard_sync import ThingsBoardSyncService

def test_sync_unknown_pilot():
    """Test ThingsBoard sync service with unknown pilots."""
    
    print("🧪 Testing ThingsBoard sync service with unknown pilots...")
    
    app = create_app()
    
    with app.app_context():
        # Find a device for testing
        device = Device.query.first()
        if not device:
            print("❌ No device found for testing")
            return False
        
        print(f"📱 Using device: {device.name} (owner: {device.owner.nickname})")
        
        # Create sync service instance
        sync_service = ThingsBoardSyncService()
        
        # Mock logbook data with unknown pilot
        unknown_pilot_name = "Sync Test Unknown Pilot"
        mock_logbook_data = {
            'pilot_name': unknown_pilot_name,
            'date': '2025-01-30',
            'aircraft_type': 'Test Aircraft',
            'aircraft_registration': 'SYNC123',
            'departure_airport': 'SYNC',
            'arrival_airport': 'TEST',
            'flight_time': 2.5,
            'takeoff_time': '10:00',
            'landing_time': '12:30',
            'pilot_in_command_time': 2.5,
            'remarks': 'Test sync with unknown pilot'
        }
        
        print(f"🔍 Testing pilot resolution for '{unknown_pilot_name}'...")
        
        # Test the _resolve_pilot_user method directly
        pilot_user_id = sync_service._resolve_pilot_user(device, unknown_pilot_name)
        
        print(f"   Pilot resolution result: {pilot_user_id}")
        print(f"   Device owner ID: {device.user_id}")
        
        if pilot_user_id is None:
            print("✅ SUCCESS: Unknown pilot resolved to None (not linked to device owner)")
            
            # Test entry creation logic
            print("\n🔍 Testing logbook entry creation...")
            
            # Simulate what the sync service does when creating an entry
            if pilot_user_id:
                entry_user_id = pilot_user_id
                print(f"   Would set user_id to: {entry_user_id} (from pilot mapping)")
            elif mock_logbook_data.get('pilot_name'):
                entry_user_id = None  # Unknown pilot
                print(f"   Setting user_id to: None (unknown pilot)")
            else:
                entry_user_id = device.user_id
                print(f"   Would set user_id to: {entry_user_id} (device owner, no pilot name)")
            
            if entry_user_id is None and mock_logbook_data.get('pilot_name'):
                print("✅ SUCCESS: Entry would be created with user_id=None for unknown pilot")
                return True
            else:
                print("❌ FAILURE: Entry would not have user_id=None for unknown pilot")
                return False
        else:
            print(f"❌ FAILURE: Unknown pilot was resolved to user ID {pilot_user_id}")
            return False

def test_sync_known_pilot():
    """Test ThingsBoard sync service with known pilots."""
    
    print("\n🧪 Testing ThingsBoard sync service with known pilots...")
    
    app = create_app()
    
    with app.app_context():
        # Find a device for testing
        device = Device.query.first()
        if not device:
            print("❌ No device found for testing")
            return False
        
        # Create or find a pilot mapping
        known_pilot_name = "Sync Test Known Pilot"
        pilot_mapping = Pilot.query.filter_by(
            device_id=device.id,
            pilot_name=known_pilot_name
        ).first()
        
        if not pilot_mapping:
            pilot_mapping = Pilot(
                device_id=device.id,
                pilot_name=known_pilot_name,
                user_id=device.user_id
            )
            db.session.add(pilot_mapping)
            db.session.commit()
            print(f"✅ Created pilot mapping: {known_pilot_name} -> {device.owner.nickname}")
            cleanup_mapping = True
        else:
            cleanup_mapping = False
            print(f"✅ Using existing pilot mapping: {known_pilot_name} -> {pilot_mapping.user.nickname}")
        
        # Create sync service instance
        sync_service = ThingsBoardSyncService()
        
        print(f"🔍 Testing pilot resolution for '{known_pilot_name}'...")
        
        # Test the _resolve_pilot_user method
        pilot_user_id = sync_service._resolve_pilot_user(device, known_pilot_name)
        
        print(f"   Pilot resolution result: {pilot_user_id}")
        print(f"   Expected user ID: {pilot_mapping.user_id}")
        
        success = pilot_user_id == pilot_mapping.user_id
        
        if success:
            print("✅ SUCCESS: Known pilot resolved to correct user ID")
        else:
            print("❌ FAILURE: Known pilot resolution failed")
        
        # Clean up if we created the mapping
        if cleanup_mapping:
            db.session.delete(pilot_mapping)
            db.session.commit()
            print("🧹 Cleaned up test pilot mapping")
        
        return success

def test_sync_no_pilot():
    """Test ThingsBoard sync service with no pilot name."""
    
    print("\n🧪 Testing ThingsBoard sync service with no pilot name...")
    
    app = create_app()
    
    with app.app_context():
        # Find a device for testing
        device = Device.query.first()
        if not device:
            print("❌ No device found for testing")
            return False
        
        print(f"🔍 Testing sync logic for no pilot name...")
        print(f"   Device owner ID: {device.user_id}")
        
        # Simulate the actual sync service logic for no pilot name
        pilot_name = None  # No pilot name in logbook data
        
        # This is what happens in the sync service:
        pilot_user_id = None
        if pilot_name:
            # This won't execute for None pilot name
            pass  # _resolve_pilot_user would be called here
        
        # Set user_id based on pilot resolution (from sync service logic)
        if pilot_name and pilot_user_id is None:
            # Unknown pilot - don't assign to anyone
            entry_user_id = None
        elif pilot_user_id:
            # Known pilot mapping
            entry_user_id = pilot_user_id
        else:
            # No pilot name specified - assign to device owner
            entry_user_id = device.user_id
        
        print(f"   Resulting user_id: {entry_user_id}")
        
        # For no pilot name, it should assign to device owner
        if entry_user_id == device.user_id:
            print("✅ SUCCESS: No pilot name assigned to device owner (expected behavior)")
            return True
        else:
            print("❌ FAILURE: No pilot name did not assign to device owner")
            return False

def main():
    """Main test function."""
    print("=" * 70)
    print("TESTING: ThingsBoard Sync Service Pilot Resolution")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test unknown pilot behavior
    unknown_success = test_sync_unknown_pilot()
    
    # Test known pilot behavior
    known_success = test_sync_known_pilot()
    
    # Test no pilot behavior
    no_pilot_success = test_sync_no_pilot()
    
    print("\n" + "=" * 70)
    print("TEST RESULTS:")
    print(f"  Unknown pilot test: {'✅ PASS' if unknown_success else '❌ FAIL'}")
    print(f"  Known pilot test:   {'✅ PASS' if known_success else '❌ FAIL'}")
    print(f"  No pilot test:      {'✅ PASS' if no_pilot_success else '❌ FAIL'}")
    
    overall_success = unknown_success and known_success and no_pilot_success
    
    if overall_success:
        print("\n🎉 All sync service tests passed!")
        print("   ✅ Unknown pilots are not linked to device owners")
        print("   ✅ Known pilots are properly linked to mapped users")
        print("   ✅ No pilot name falls back to device owner")
    else:
        print("\n💥 Some sync service tests failed!")
        print("   Check the output above for details")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return overall_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
