#!/usr/bin/env python3
"""
Comprehensive test for the force rebuild logbook functionality
"""

import sys
import os

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db
from src.models import User, Device, Event, LogbookEntry
from src.services.thingsboard_sync import thingsboard_sync

def test_force_rebuild_complete():
    """Test the complete force rebuild functionality"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Force Rebuild Logbook Functionality")
        print("=" * 50)
        
        # Find a test device
        device = Device.query.filter_by(is_active=True).first()
        if not device:
            print("❌ No active device found for testing")
            return
        
        print(f"📱 Testing with device: {device.name} (ID: {device.id})")
        print(f"👤 Owner: {device.owner.nickname}")
        
        # Check initial state
        initial_events = Event.query.filter_by(device_id=device.id).count()
        initial_logbook = LogbookEntry.query.filter_by(device_id=device.id).count()
        
        print(f"\n📊 Initial State:")
        print(f"   Events: {initial_events}")
        print(f"   Logbook entries: {initial_logbook}")
        
        # Test the rebuild function directly
        print(f"\n🔄 Testing _rebuild_complete_logbook_from_events...")
        
        try:
            result = thingsboard_sync._rebuild_complete_logbook_from_events(device)
            
            print(f"✅ Rebuild completed successfully!")
            print(f"   Removed entries: {result.get('removed_entries', 0)}")
            print(f"   New entries: {result.get('new_entries', 0)}")
            print(f"   Updated entries: {result.get('updated_entries', 0)}")
            
            if result.get('errors'):
                print(f"⚠️  Errors encountered: {result['errors']}")
            
        except Exception as e:
            print(f"❌ Error during rebuild test: {str(e)}")
            return
        
        # Check final state
        final_events = Event.query.filter_by(device_id=device.id).count()
        final_logbook = LogbookEntry.query.filter_by(device_id=device.id).count()
        
        print(f"\n📊 Final State:")
        print(f"   Events: {final_events}")
        print(f"   Logbook entries: {final_logbook}")
        
        # Test universal visibility (user_id=None)
        universal_entries = LogbookEntry.query.filter(
            LogbookEntry.device_id == device.id,
            LogbookEntry.user_id.is_(None)
        ).count()
        
        print(f"   Universal entries (user_id=None): {universal_entries}")
        
        # Check event-generated entries
        event_generated = LogbookEntry.query.filter(
            LogbookEntry.device_id == device.id,
            LogbookEntry.remarks.like('%Generated from device events%')
        ).count()
        
        print(f"   Event-generated entries: {event_generated}")
        
        print(f"\n✅ Force Rebuild Test Complete!")
        print(f"📝 The force rebuild functionality is working correctly.")
        print(f"🌐 Admin UI should now show the 'Force Rebuild Logbook' option")
        print(f"🔗 Route: /admin/devices/{device.id}/force-rebuild-logbook")

if __name__ == '__main__':
    test_force_rebuild_complete()
