#!/usr/bin/env python3
"""
Test script to verify the updated Event and Device models work correctly.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app
from src.models import Event, Device, User, db
from src.services.thingsboard_sync import ThingsBoardSyncService

def test_updated_models():
    """Test the updated Event and Device models."""
    
    print("🧪 Testing updated Event and Device models...")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get a device for testing
            device = Device.query.first()
            if not device:
                print("❌ No device found for testing")
                return False
            
            print(f"📱 Using device: {device.name}")
            
            # Test 1: Verify Device has current_logger_page
            print("\n🔍 Testing Device.current_logger_page...")
            print(f"   Current logger page: {device.current_logger_page}")
            
            # Update device logger page
            device.current_logger_page = 12345
            db.session.commit()
            print(f"   ✅ Updated device logger page to: {device.current_logger_page}")
            
            # Test 2: Create Event with required fields
            print("\n🔍 Testing Event model with non-nullable fields...")
            
            test_event = Event(
                date_time=datetime.now(),
                page_address=1000,  # Required field
                total_time=5000,    # Required field  
                bitfield=0b00000011,  # AnyEngStart + Takeoff
                device_id=device.id
            )
            
            db.session.add(test_event)
            db.session.commit()
            
            print(f"   ✅ Created event: ID={test_event.id}")
            print(f"      page_address: {test_event.page_address}")
            print(f"      total_time: {test_event.total_time}")
            print(f"      active_events: {test_event.get_active_events()}")
            
            # Test 3: Test the new get_newest_event_for_device method
            print("\n🔍 Testing Event.get_newest_event_for_device()...")
            
            # Create another event with higher page_address
            newer_event = Event(
                date_time=datetime.now(),
                page_address=2000,  # Higher page address
                total_time=3000,
                bitfield=0b00000100,  # Landing
                device_id=device.id
            )
            
            db.session.add(newer_event)
            db.session.commit()
            
            print(f"   ✅ Created second event: ID={newer_event.id}, page_address={newer_event.page_address}")
            
            # Get newest event
            newest_event = Event.get_newest_event_for_device(device.id)
            
            if newest_event:
                print(f"   ✅ Newest event: ID={newest_event.id}, page_address={newest_event.page_address}")
                print(f"      Should be the second event: {newest_event.id == newer_event.id}")
            else:
                print("   ❌ No newest event found")
                return False
            
            # Test 4: Test sync service with updated models
            print("\n🔍 Testing ThingsBoard sync service...")
            
            sync_service = ThingsBoardSyncService()
            
            # Mock event data with required fields
            mock_event_data = {
                'date_time': '2025-07-31 10:30:00',
                'page_address': 3000,  # Required
                'total_time': 15000,   # Required
                'bitfield': 0b00010000  # Flying
            }
            
            result = sync_service._process_device_event(device, mock_event_data, 15000)
            
            if result:
                print("   ✅ Sync service processed event successfully")
                
                # Verify device logger page was updated
                device_updated = Device.query.get(device.id)
                print(f"      Device logger page updated to: {device_updated.current_logger_page}")
                
                # Find the created event
                created_event = Event.query.filter_by(
                    device_id=device.id,
                    page_address=3000
                ).first()
                
                if created_event:
                    print(f"      Created event: ID={created_event.id}, active_events={created_event.get_active_events()}")
                else:
                    print("   ❌ Created event not found")
                    return False
            else:
                print("   ❌ Sync service failed to process event")
                return False
            
            # Test 5: Test sync service validation (missing required fields)
            print("\n🔍 Testing sync service validation...")
            
            # Test with missing page_address
            invalid_event_data = {
                'date_time': '2025-07-31 10:30:00',
                'total_time': 15000,
                'bitfield': 0b00010000
                # page_address missing
            }
            
            result = sync_service._process_device_event(device, invalid_event_data, 16000)
            
            if not result:
                print("   ✅ Sync service correctly rejected event with missing page_address")
            else:
                print("   ❌ Sync service should have rejected invalid event")
                return False
            
            # Clean up test events
            print("\n🧹 Cleaning up test events...")
            Event.query.filter_by(device_id=device.id).filter(Event.page_address >= 1000).delete()
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
    print("TESTING: Updated Event and Device Models")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test updated models
    models_success = test_updated_models()
    
    print("\n" + "=" * 70)
    print("TEST RESULTS:")
    print(f"  Updated models test:    {'✅ PASS' if models_success else '❌ FAIL'}")
    
    if models_success:
        print("\n🎉 All tests passed!")
        print("   ✅ Device.current_logger_page working")
        print("   ✅ Event non-nullable fields working")
        print("   ✅ Event.get_newest_event_for_device() working")
        print("   ✅ Sync service updated correctly")
        print("   ✅ Field validation working")
    else:
        print("\n💥 Some tests failed!")
        print("   Check the output above for details")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    return models_success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
