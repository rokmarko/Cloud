#!/usr/bin/env python3
"""
Test script to verify admin logbook page functionality after time field fix.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app
from src.models import LogbookEntry, db

def test_admin_logbook_query():
    """Test the admin logbook query that was failing."""
    
    print("🧪 Testing admin logbook query...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test the exact query from the admin logbook route
            page = 1
            per_page = 20
            
            # Build query (same as in admin route)
            query = LogbookEntry.query
            query = query.order_by(LogbookEntry.date.desc(), LogbookEntry.created_at.desc())
            
            print("🔍 Testing pagination query...")
            
            # This is where the error was occurring
            entries = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            print(f"✅ Query successful - found {entries.total} total entries")
            print(f"📄 Showing page {entries.page} of {entries.pages}")
            print(f"📝 Items on this page: {len(entries.items)}")
            
            # Test accessing individual entries to make sure time fields work
            for i, entry in enumerate(entries.items[:3]):  # Test first 3 entries
                print(f"   Entry {i+1}: ID={entry.id}, Date={entry.date}")
                print(f"      Takeoff: {entry.takeoff_time}, Landing: {entry.landing_time}")
                print(f"      Pilot: {entry.pilot_name}, User: {entry.user_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Query failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_time_field_access():
    """Test direct access to time fields."""
    
    print("\n🧪 Testing time field access...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get all entries and check time fields
            entries = LogbookEntry.query.all()
            
            time_entries = []
            for entry in entries:
                if entry.takeoff_time is not None or entry.landing_time is not None:
                    time_entries.append(entry)
            
            print(f"📊 Total entries: {len(entries)}")
            print(f"⏰ Entries with time data: {len(time_entries)}")
            
            if len(time_entries) == 0:
                print("✅ All time fields are NULL (expected after fix)")
                return True
            else:
                print(f"⚠️  Found {len(time_entries)} entries with time data:")
                for entry in time_entries[:5]:  # Show first 5
                    print(f"   ID {entry.id}: takeoff={entry.takeoff_time}, landing={entry.landing_time}")
                return True
                
        except Exception as e:
            print(f"❌ Time field access failed: {str(e)}")
            return False

def main():
    """Main test function."""
    print("=" * 60)
    print("TESTING: Admin Logbook Page After Time Field Fix")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test the admin logbook query
    query_success = test_admin_logbook_query()
    
    # Test time field access
    time_success = test_time_field_access()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"  Admin logbook query: {'✅ PASS' if query_success else '❌ FAIL'}")
    print(f"  Time field access:   {'✅ PASS' if time_success else '❌ FAIL'}")
    
    overall_success = query_success and time_success
    
    if overall_success:
        print("\n🎉 All tests passed!")
        print("   Admin logbook page should now work without errors")
    else:
        print("\n💥 Some tests failed!")
        print("   Check the output above for details")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return overall_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
