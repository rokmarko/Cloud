#!/usr/bin/env python3
"""
Test script to verify unknown pilot behavior after migration.

This script tests that unknown pilots are not automatically linked to device owners.
"""

import sys
import os
from datetime import datetime, date

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app
from src.models import LogbookEntry, Device, User, Pilot, db

def test_unknown_pilot_behavior():
    """Test that unknown pilots are not linked to device owners."""
    
    print("🧪 Testing unknown pilot behavior...")
    
    app = create_app()
    
    with app.app_context():
        # Find an existing device and user
        device = Device.query.first()
        user = User.query.first()
        
        if not device or not user:
            print("❌ No device or user found in database")
            return False
        
        print(f"📱 Using device: {device.name} (owner: {device.owner.nickname})")
        
        # Create a test logbook entry with an unknown pilot
        unknown_pilot_name = "Test Unknown Pilot"
        
        # Check if there's already a pilot mapping for this name
        existing_pilot = Pilot.query.filter_by(
            device_id=device.id,
            pilot_name=unknown_pilot_name
        ).first()
        
        if existing_pilot:
            print(f"⚠️  Pilot mapping already exists for '{unknown_pilot_name}', deleting it for test")
            db.session.delete(existing_pilot)
            db.session.commit()
        
        # Create a new logbook entry with unknown pilot name
        entry = LogbookEntry(
            date=date.today(),
            aircraft_type="Test Aircraft",
            aircraft_registration="TEST123",
            flight_time=1.5,
            pilot_name=unknown_pilot_name,
            device_id=device.id,
            user_id=None,  # This should remain None for unknown pilots
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(entry)
        db.session.commit()
        
        print(f"✅ Created test entry with pilot_name='{unknown_pilot_name}'")
        
        # Test the get_actual_pilot_user() method
        actual_user = entry.get_actual_pilot_user()
        
        print(f"🔍 Testing get_actual_pilot_user():")
        print(f"   entry.user_id: {entry.user_id}")
        print(f"   entry.pilot_name: {entry.pilot_name}")
        print(f"   actual_user result: {actual_user}")
        print(f"   device.user_id: {device.user_id}")
        
        # Verify the behavior
        if actual_user is None:
            print("✅ SUCCESS: Unknown pilot is not linked to device owner")
            success = True
        else:
            print(f"❌ FAILURE: Unknown pilot was linked to user {actual_user.nickname}")
            success = False
        
        # Test pilot mapping resolution
        pilot_mapping = entry.get_pilot_mapping()
        print(f"🔍 Pilot mapping result: {pilot_mapping}")
        
        if pilot_mapping is None:
            print("✅ SUCCESS: No pilot mapping found for unknown pilot")
        else:
            print(f"❌ FAILURE: Unexpected pilot mapping found: {pilot_mapping}")
            success = False
        
        # Clean up the test entry
        db.session.delete(entry)
        db.session.commit()
        print("🧹 Cleaned up test entry")
        
        return success

def test_known_pilot_behavior():
    """Test that known pilots are still properly linked."""
    
    print("\n🧪 Testing known pilot behavior...")
    
    app = create_app()
    
    with app.app_context():
        # Find an existing device
        device = Device.query.first()
        if not device:
            print("❌ No device found in database")
            return False
        
        # Find or create a pilot mapping
        known_pilot_name = "Test Known Pilot"
        pilot_mapping = Pilot.query.filter_by(
            device_id=device.id,
            pilot_name=known_pilot_name
        ).first()
        
        if not pilot_mapping:
            # Create a pilot mapping
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
        
        # Create a test logbook entry with known pilot
        entry = LogbookEntry(
            date=date.today(),
            aircraft_type="Test Aircraft",
            aircraft_registration="TEST456",
            flight_time=2.0,
            pilot_name=known_pilot_name,
            device_id=device.id,
            user_id=pilot_mapping.user_id,  # Should be set to the mapped user
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(entry)
        db.session.commit()
        
        print(f"✅ Created test entry with pilot_name='{known_pilot_name}'")
        
        # Test the get_actual_pilot_user() method
        actual_user = entry.get_actual_pilot_user()
        
        print(f"🔍 Testing get_actual_pilot_user():")
        print(f"   entry.user_id: {entry.user_id}")
        print(f"   entry.pilot_name: {entry.pilot_name}")
        print(f"   actual_user result: {actual_user.nickname if actual_user else None}")
        
        # Verify the behavior
        if actual_user and actual_user.id == pilot_mapping.user_id:
            print("✅ SUCCESS: Known pilot is properly linked to mapped user")
            success = True
        else:
            print(f"❌ FAILURE: Known pilot linking failed")
            success = False
        
        # Clean up
        db.session.delete(entry)
        if cleanup_mapping:
            db.session.delete(pilot_mapping)
        db.session.commit()
        print("🧹 Cleaned up test data")
        
        return success

def main():
    """Main test function."""
    print("=" * 60)
    print("TESTING: Unknown Pilot Behavior After Migration")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test unknown pilot behavior
    unknown_success = test_unknown_pilot_behavior()
    
    # Test known pilot behavior (should still work)
    known_success = test_known_pilot_behavior()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"  Unknown pilot test: {'✅ PASS' if unknown_success else '❌ FAIL'}")
    print(f"  Known pilot test:   {'✅ PASS' if known_success else '❌ FAIL'}")
    
    overall_success = unknown_success and known_success
    
    if overall_success:
        print("\n🎉 All tests passed!")
        print("   Unknown pilots are not linked to device owners")
        print("   Known pilots are still properly linked")
    else:
        print("\n💥 Some tests failed!")
        print("   Check the output above for details")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return overall_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
