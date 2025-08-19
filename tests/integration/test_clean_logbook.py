#!/usr/bin/env python3
"""
Test script to verify admin logbook page works after cleaning corrupted data.
"""

import sys
import os
from datetime import datetime, date

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app
from src.models import LogbookEntry, Device, User, db

def test_clean_logbook_functionality():
    """Test that we can add new entries and the admin page works."""
    
    print("🧪 Testing clean logbook functionality...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get a user and device for testing
            user = User.query.first()
            device = Device.query.first()
            
            if not user:
                print("❌ No user found for testing")
                return False
            
            # Create a clean test logbook entry
            test_entry = LogbookEntry(
                date=date.today(),
                aircraft_type="Test Clean Aircraft",
                aircraft_registration="CLEAN123",
                departure_airport="TEST",
                arrival_airport="PASS",
                flight_time=1.0,
                pilot_in_command_time=1.0,
                remarks="Test entry after cleanup",
                user_id=user.id,
                device_id=device.id if device else None,
                pilot_name="Test Pilot",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(test_entry)
            db.session.commit()
            
            print(f"✅ Created test entry: ID={test_entry.id}")
            
            # Test admin logbook query with the new entry
            page = 1
            per_page = 20
            
            query = LogbookEntry.query
            query = query.order_by(LogbookEntry.date.desc(), LogbookEntry.created_at.desc())
            
            # This should work now without time format errors
            entries = query.paginate(page=page, per_page=per_page, error_out=False)
            
            print(f"✅ Admin query successful - found {entries.total} total entries")
            print(f"📄 Page {entries.page} of {entries.pages}")
            print(f"📝 Items on this page: {len(entries.items)}")
            
            # Test accessing the entry data
            if entries.items:
                entry = entries.items[0]
                print(f"   First entry: ID={entry.id}, Date={entry.date}")
                print(f"   Aircraft: {entry.aircraft_type} {entry.aircraft_registration}")
                print(f"   Pilot: {entry.pilot_name}, User: {entry.user_id}")
                print(f"   Takeoff: {entry.takeoff_time}, Landing: {entry.landing_time}")
            
            # Clean up
            db.session.delete(test_entry)
            db.session.commit()
            print("🧹 Cleaned up test entry")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main test function."""
    print("=" * 60)
    print("TESTING: Clean Logbook Functionality")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = test_clean_logbook_functionality()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"  Clean logbook test: {'✅ PASS' if success else '❌ FAIL'}")
    
    if success:
        print("\n🎉 Test passed!")
        print("   Logbook table is clean and functional")
        print("   Admin logbook page should work without errors")
        print("   New entries can be added successfully")
    else:
        print("\n💥 Test failed!")
        print("   Check the output above for details")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
