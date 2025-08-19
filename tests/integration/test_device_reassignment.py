#!/usr/bin/env ./venv/bin/python
"""
Test script for device reassignment functionality.
Usage: ./venv/bin/python test_device_reassignment.py
"""

from src.app import create_app
from src.models import Device, User, db
from datetime import datetime

def test_device_reassignment():
    """Test device reassignment functionality."""
    app = create_app()
    
    with app.app_context():
        print("🔧 Testing Device Reassignment Functionality...")
        
        # Get test data
        devices = Device.query.filter_by(is_active=True).all()
        users = User.query.filter_by(is_active=True).all()
        
        if len(devices) < 1 or len(users) < 2:
            print("❌ Not enough test data (need at least 1 device and 2 users)")
            return False
        
        # Get a device and two different users
        test_device = devices[0]
        original_owner = test_device.owner
        new_owner = next((u for u in users if u.id != test_device.user_id), None)
        
        if not new_owner:
            print("❌ No alternative user found for reassignment")
            return False
        
        print(f"📱 Test Device: {test_device.name}")
        print(f"👤 Original Owner: {original_owner.nickname}")
        print(f"👤 New Owner: {new_owner.nickname}")
        
        # Test 1: Basic reassignment
        print("\n🧪 Test 1: Basic device reassignment")
        original_user_id = test_device.user_id
        test_device.user_id = new_owner.id
        test_device.updated_at = datetime.utcnow()
        
        try:
            db.session.commit()
            
            # Verify the change
            updated_device = Device.query.get(test_device.id)
            if updated_device.user_id == new_owner.id:
                print("✅ Device successfully reassigned")
            else:
                print("❌ Device reassignment failed")
                return False
            
            # Test 2: Revert the change
            print("\n🧪 Test 2: Reverting reassignment")
            test_device.user_id = original_user_id
            test_device.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Verify the revert
            reverted_device = Device.query.get(test_device.id)
            if reverted_device.user_id == original_user_id:
                print("✅ Device successfully reverted to original owner")
            else:
                print("❌ Device revert failed")
                return False
            
            print("\n🎉 All device reassignment tests passed!")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Database error during test: {str(e)}")
            return False

if __name__ == '__main__':
    success = test_device_reassignment()
    exit(0 if success else 1)
