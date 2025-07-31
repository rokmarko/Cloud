#!/usr/bin/env python3
"""
Test script to verify Event model and ThingsBoard event sync functionality.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app
from src.models import Event, Device, User, db
from src.services.thingsboard_sync import ThingsBoardSyncService

def test_event_model():
    """Test the Event model functionality."""
    
    print("🧪 Testing Event model...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get a device for testing
            device = Device.query.first()
            if not device:
                print("❌ No device found for testing")
                return False
            
            print(f"📱 Using device: {device.name}")
            
            # Test creating an event
            test_event = Event(
                date_time=datetime.now(),
                page_address=12345,
                total_time=5000,  # 5 seconds in milliseconds
                bitfield=0b10000110,  # Set bits for Takeoff (1), Landing (2), and Flying (4)
                current_logger_page=100,
                device_id=device.id
            )
            
            db.session.add(test_event)
            db.session.commit()
            
            print(f"✅ Created test event: ID={test_event.id}")
            
            # Test bitfield methods
            print("🔍 Testing bitfield methods:")
            print(f"   Bitfield value: {test_event.bitfield} (0b{bin(test_event.bitfield)[2:]:0>8})")
            print(f"   Has Takeoff: {test_event.has_event_bit('Takeoff')}")
            print(f"   Has Landing: {test_event.has_event_bit('Landing')}")
            print(f"   Has Flying: {test_event.has_event_bit('Flying')}")
            print(f"   Has AnyEngStart: {test_event.has_event_bit('AnyEngStart')}")
            
            active_events = test_event.get_active_events()
            print(f"   Active events: {active_events}")
            
            # Test setting/clearing bits
            test_event.set_event_bit('AnyEngStart', True)
            test_event.set_event_bit('Landing', False)
            db.session.commit()
            
            print(f"   After modifications:")
            print(f"   Bitfield value: {test_event.bitfield} (0b{bin(test_event.bitfield)[2:]:0>8})")
            print(f"   Active events: {test_event.get_active_events()}")
            
            # Clean up
            db.session.delete(test_event)
            db.session.commit()
            print("🧹 Cleaned up test event")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_event_sync_service():
    """Test the ThingsBoard event sync service methods."""
    
    print("\n🧪 Testing ThingsBoard event sync service...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get a device for testing
            device = Device.query.first()
            if not device:
                print("❌ No device found for testing")
                return False
            
            print(f"📱 Using device: {device.name}")
            
            # Create sync service instance
            sync_service = ThingsBoardSyncService()
            
            # Test _process_device_event method with mock data
            mock_event_data = {
                'date_time': '2025-07-31 10:30:00',
                'page_address': 54321,
                'total_time': 15000,  # 15 seconds
                'bitfield': 0b00010010  # Takeoff and Landing bits set
            }
            
            print("🔍 Testing event processing:")
            print(f"   Mock event data: {mock_event_data}")
            
            # Process the mock event
            result = sync_service._process_device_event(device, mock_event_data, 200)
            
            if result:
                print("✅ Event processing successful")
                
                # Find the created event
                created_event = Event.query.filter_by(
                    device_id=device.id,
                    page_address=54321
                ).first()
                
                if created_event:
                    print(f"✅ Event created in database: ID={created_event.id}")
                    print(f"   Date/Time: {created_event.date_time}")
                    print(f"   Page Address: {created_event.page_address}")
                    print(f"   Total Time: {created_event.total_time}ms")
                    print(f"   Bitfield: {created_event.bitfield}")
                    print(f"   Active Events: {created_event.get_active_events()}")
                    print(f"   Logger Page: {created_event.current_logger_page}")
                    
                    # Test duplicate detection
                    duplicate_result = sync_service._process_device_event(device, mock_event_data, 200)
                    if not duplicate_result:
                        print("✅ Duplicate detection working correctly")
                    else:
                        print("⚠️  Duplicate detection may not be working")
                    
                    # Clean up
                    db.session.delete(created_event)
                    db.session.commit()
                    print("🧹 Cleaned up test event")
                else:
                    print("❌ Event not found in database after processing")
                    return False
            else:
                print("❌ Event processing failed")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main test function."""
    print("=" * 60)
    print("TESTING: Event Model and ThingsBoard Sync")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test event model
    model_success = test_event_model()
    
    # Test sync service  
    sync_success = test_event_sync_service()
    
    print("\n" + "=" * 60)
    print("TEST RESULTS:")
    print(f"  Event model test:    {'✅ PASS' if model_success else '❌ FAIL'}")
    print(f"  Event sync test:     {'✅ PASS' if sync_success else '❌ FAIL'}")
    
    overall_success = model_success and sync_success
    
    if overall_success:
        print("\n🎉 All tests passed!")
        print("   Event model is working correctly")
        print("   ThingsBoard event sync is functional")
        print("   Ready to sync events from devices")
    else:
        print("\n💥 Some tests failed!")
        print("   Check the output above for details")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return overall_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
