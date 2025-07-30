#!/usr/bin/env python3
"""
Script to create test manual logbook entries for demonstration
"""

import sys
import os
from datetime import datetime, date, time, timedelta

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import LogbookEntry, User

def create_test_manual_entries():
    """Create some test manual entries."""
    
    app = create_app()
    
    with app.app_context():
        # Get an active user
        user = User.query.filter_by(is_active=True).first()
        
        if not user:
            print("❌ No active user found")
            return
        
        # Create test manual entries (no device_id)
        test_entries = [
            {
                'date': date(2025, 7, 28),
                'aircraft_registration': 'S5-MANUAL1',
                'aircraft_type': 'Cessna 172',
                'departure_airport': 'LJLJ',
                'arrival_airport': 'LJCE',
                'flight_time': 1.5,
                'takeoff_time': time(9, 0),
                'landing_time': time(10, 30),
                'remarks': 'Manual training flight',
                'user_id': user.id,
                'device_id': None  # This makes it a manual entry
            },
            {
                'date': date(2025, 7, 29),
                'aircraft_registration': 'S5-MANUAL2',
                'aircraft_type': 'Piper PA-28',
                'departure_airport': 'LJCE',
                'arrival_airport': 'LJMB',
                'flight_time': 2.0,
                'takeoff_time': time(14, 0),
                'landing_time': time(16, 0),
                'remarks': 'Manual cross-country flight',
                'user_id': user.id,
                'device_id': None  # This makes it a manual entry
            },
            {
                'date': date(2025, 7, 30),
                'aircraft_registration': 'S5-MANUAL3',
                'aircraft_type': 'Diamond DA40',
                'departure_airport': 'LJMB',
                'arrival_airport': 'LJLJ',
                'flight_time': 1.25,
                'takeoff_time': time(16, 30),
                'landing_time': time(17, 45),
                'remarks': 'Manual return flight',
                'user_id': user.id,
                'device_id': None  # This makes it a manual entry
            }
        ]
        
        for entry_data in test_entries:
            entry = LogbookEntry(**entry_data)
            db.session.add(entry)
        
        db.session.commit()
        print(f"✅ Created {len(test_entries)} test manual entries")
        
        # Show updated statistics
        total = LogbookEntry.query.count()
        synced = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None)).count()
        manual = LogbookEntry.query.filter(LogbookEntry.device_id.is_(None)).count()
        
        print(f"📊 Updated statistics:")
        print(f"   • Total entries: {total}")
        print(f"   • Synced entries: {synced}")
        print(f"   • Manual entries: {manual}")

if __name__ == "__main__":
    print("🧪 Creating test manual entries...")
    create_test_manual_entries()
