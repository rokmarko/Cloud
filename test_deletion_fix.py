#!/usr/bin/env python3
"""
Test script to verify that device and checklist deletion functionality works correctly.
"""

import requests
import json
from src.app import create_app, db
from src.models import User, Device, Checklist
import tempfile
import os

def test_deletion_functionality():
    """Test that deletion endpoints work correctly"""
    
    # Create test app
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            # Create all tables
            db.create_all()
            
            # Create a test user
            test_user = User(
                email='test@example.com',
                nickname='testuser',
                is_verified=True,
                is_active=True
            )
            test_user.set_password('testpassword123')
            db.session.add(test_user)
            db.session.commit()
            
            # Create test device
            test_device = Device(
                name='Test Device',
                device_type='aircraft',
                model='Test Model',
                serial_number='TEST123',
                user_id=test_user.id
            )
            db.session.add(test_device)
            
            # Create test checklist
            test_checklist = Checklist(
                title='Test Checklist',
                category='preflight',
                description='Test Description',
                items='["Item 1", "Item 2"]',
                user_id=test_user.id
            )
            db.session.add(test_checklist)
            db.session.commit()
            
            print("✅ Test data created successfully")
            
            # Test form-based device deletion (simulate login first)
            with client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
            
            # Test device deletion via form
            response = client.post(f'/devices/{test_device.id}/delete')
            print(f"Device form deletion: Status {response.status_code}")
            
            # Check if device was soft deleted
            device_after_delete = Device.query.get(test_device.id)
            if device_after_delete and not device_after_delete.is_active:
                print("✅ Device form deletion working correctly (soft delete)")
            else:
                print("❌ Device form deletion failed")
            
            # Restore device for API test
            device_after_delete.is_active = True
            db.session.commit()
            
            # Test API-based device deletion
            response = client.delete(f'/api/device/{test_device.id}')
            print(f"Device API deletion: Status {response.status_code}")
            
            if response.status_code == 200:
                device_after_api_delete = Device.query.get(test_device.id)
                if device_after_api_delete and not device_after_api_delete.is_active:
                    print("✅ Device API deletion working correctly (soft delete)")
                else:
                    print("❌ Device API deletion failed - device still active")
            else:
                print(f"❌ Device API deletion failed with status {response.status_code}")
            
            # Test checklist deletion via API
            response = client.delete(f'/api/checklist/{test_checklist.id}')
            print(f"Checklist API deletion: Status {response.status_code}")
            
            if response.status_code == 200:
                checklist_after_delete = Checklist.query.get(test_checklist.id)
                if checklist_after_delete and not checklist_after_delete.is_active:
                    print("✅ Checklist API deletion working correctly (soft delete)")
                else:
                    print("❌ Checklist API deletion failed - checklist still active")
            else:
                print(f"❌ Checklist API deletion failed with status {response.status_code}")
            
            # Test device duplication
            response = client.post(f'/api/device/{test_device.id}/duplicate')
            print(f"Device duplication: Status {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Device duplication working correctly")
            else:
                print(f"❌ Device duplication failed with status {response.status_code}")
            
            # Test checklist duplication
            response = client.post(f'/api/checklist/{test_checklist.id}/duplicate')
            print(f"Checklist duplication: Status {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Checklist duplication working correctly")
            else:
                print(f"❌ Checklist duplication failed with status {response.status_code}")

if __name__ == '__main__':
    test_deletion_functionality()
