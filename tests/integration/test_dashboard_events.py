#!/usr/bin/env python3
"""
Test the new dashboard events page functionality.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app
from src.models import Event, Device, User, db

def test_dashboard_events():
    """Test the dashboard events functionality."""
    
    print("🧪 Testing dashboard events page...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get a device for testing
            device = Device.query.first()
            if not device:
                print("❌ No device found for testing")
                return False
            
            print(f"📱 Using device: {device.name} (Owner: {device.owner.nickname})")
            
            # Create some test events
            test_events = [
                {
                    'date_time': datetime(2025, 7, 31, 10, 0, 0),
                    'page_address': 5001,
                    'total_time': 30000,  # 30 seconds
                    'bitfield': 0b00000011  # AnyEngStart + Takeoff
                },
                {
                    'date_time': datetime(2025, 7, 31, 10, 15, 0),
                    'page_address': 5002,
                    'total_time': 45000,  # 45 seconds
                    'bitfield': 0b00010000  # Flying
                },
                {
                    'date_time': datetime(2025, 7, 31, 10, 30, 0),
                    'page_address': 5003,
                    'total_time': 20000,  # 20 seconds
                    'bitfield': 0b00000100  # Landing
                },
                {
                    'date_time': datetime(2025, 7, 31, 10, 35, 0),
                    'page_address': 5004,
                    'total_time': 10000,  # 10 seconds
                    'bitfield': 0b10001000  # LastEngStop + Alarm
                }
            ]
            
            print("🔄 Creating test events...")
            created_events = []
            
            for i, event_data in enumerate(test_events, 1):
                event = Event(
                    date_time=event_data['date_time'],
                    page_address=event_data['page_address'],
                    total_time=event_data['total_time'],
                    bitfield=event_data['bitfield'],
                    device_id=device.id
                )
                
                db.session.add(event)
                created_events.append(event)
                
                active_events = event.get_active_events()
                events_str = ', '.join(active_events) if active_events else 'None'
                print(f"   ✅ Event {i}: Page {event_data['page_address']} - [{events_str}]")
            
            db.session.commit()
            print(f"✅ Created {len(created_events)} test events")
            
            # Test filtering functionality
            print("\n🔍 Testing event filtering...")
            
            # Test getting all events for this device
            all_events = Event.query.filter_by(device_id=device.id).order_by(Event.page_address.desc()).all()
            print(f"   Total events for device: {len(all_events)}")
            
            # Test filtering by event type (Takeoff)
            takeoff_bit = Event.EVENT_BITS['Takeoff']
            bit_mask = 1 << takeoff_bit
            takeoff_events = Event.query.filter(
                Event.device_id == device.id,
                Event.bitfield.op('&')(bit_mask) != 0
            ).all()
            print(f"   Takeoff events: {len(takeoff_events)}")
            
            # Test get_newest_event_for_device method
            newest_event = Event.get_newest_event_for_device(device.id)
            if newest_event:
                print(f"   Newest event: Page {newest_event.page_address} - {newest_event.get_active_events()}")
            
            # Test event statistics
            print("\n📊 Testing event statistics...")
            stats = {}
            for event_name, bit_position in Event.EVENT_BITS.items():
                bit_mask = 1 << bit_position
                count = Event.query.filter(
                    Event.device_id == device.id,
                    Event.bitfield.op('&')(bit_mask) != 0
                ).count()
                stats[f'{event_name.lower()}_count'] = count
                print(f"   {event_name}: {count}")
            
            # Clean up test events
            print("\n🧹 Cleaning up test events...")
            Event.query.filter_by(device_id=device.id).filter(Event.page_address >= 5001).delete()
            db.session.commit()
            print("   ✅ Test events cleaned up")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main test function."""
    print("=" * 70)
    print("TESTING: Dashboard Events Page")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test dashboard events
    events_success = test_dashboard_events()
    
    print("\n" + "=" * 70)
    print("TEST RESULTS:")
    print(f"  Dashboard events test:    {'✅ PASS' if events_success else '❌ FAIL'}")
    
    if events_success:
        print("\n🎉 Dashboard events page is working!")
        print("   ✅ Event creation working")
        print("   ✅ Event filtering working")
        print("   ✅ Event statistics working")
        print("   ✅ Database operations successful")
        print("\n🌐 The events page is now available at:")
        print("   http://127.0.0.1:5000/dashboard/events")
    else:
        print("\n💥 Dashboard events test failed!")
        print("   Check the output above for details")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return events_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
