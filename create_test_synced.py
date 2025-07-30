#!/usr/bin/env python3
"""
Script to add some test logbook entries for verification
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import LogbookEntry, Device, User

def create_test_synced_entries():
    """Create some test synced entries"""
    app = create_app()
    
    with app.app_context():
        # Get a device to link to
        device = Device.query.filter_by(is_active=True).first()
        user = User.query.filter_by(is_active=True).first()
        
        if not device or not user:
            print("❌ No active device or user found")
            return
            
        print(f"✅ Using device: {device.name} (ID: {device.id})")
        print(f"✅ Using user: {user.nickname} (ID: {user.id})")
        
        # Create a few test synced entries
        test_entries = [
            {
                'date': datetime.now().date(),
                'aircraft_registration': device.registration or 'TEST-REG',
                'aircraft_type': 'Test Aircraft',
                'departure_airport': 'LJLJ',
                'arrival_airport': 'LJMB', 
                'flight_time': 1.5,
                'remarks': 'Test synced entry 1',
                'device_id': device.id,
                'user_id': user.id
            },
            {
                'date': datetime.now().date() - timedelta(days=1),
                'aircraft_registration': device.registration or 'TEST-REG',
                'aircraft_type': 'Test Aircraft',
                'departure_airport': 'LJMB',
                'arrival_airport': 'LJLJ',
                'flight_time': 2.0,
                'remarks': 'Test synced entry 2',
                'device_id': device.id,
                'user_id': user.id
            }
        ]
        
        for entry_data in test_entries:
            entry = LogbookEntry(**entry_data)
            db.session.add(entry)
        
        db.session.commit()
        print(f"✅ Created {len(test_entries)} test synced entries")
        
        # Verify
        synced_count = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None)).count()
        print(f"✅ Total synced entries now: {synced_count}")

if __name__ == "__main__":
    print("🧪 Creating test synced entries...")
    create_test_synced_entries()
