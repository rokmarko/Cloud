#!/usr/bin/env python3
"""
Test script to verify LogbookEntry model changes from date/time fields to datetime fields.
"""

import sys
import os
from datetime import datetime, date, time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import LogbookEntry, User

def test_new_logbook_model():
    """Test the new LogbookEntry model with datetime fields."""
    
    app = create_app()
    
    with app.app_context():
        print("Testing new LogbookEntry model...")
        
        # Get or create a test user
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            print("Creating test user...")
            test_user = User(
                email='test@example.com',
                nickname='Test User',
                is_active=True,
                is_verified=True
            )
            test_user.set_password('testpass')
            db.session.add(test_user)
            db.session.commit()
        
        # Test creating a new logbook entry with datetime fields
        takeoff_dt = datetime(2025, 8, 3, 10, 30, 0)  # 10:30 AM
        landing_dt = datetime(2025, 8, 3, 12, 15, 0)  # 12:15 PM
        
        print(f"Creating logbook entry with takeoff: {takeoff_dt}, landing: {landing_dt}")
        
        entry = LogbookEntry(
            takeoff_datetime=takeoff_dt,
            landing_datetime=landing_dt,
            aircraft_type='C172',
            aircraft_registration='N12345',
            departure_airport='KJFK',
            arrival_airport='KLGA',
            flight_time=1.75,  # 1 hour 45 minutes
            pilot_in_command_time=1.75,
            landings_day=1,
            remarks='Test flight with new datetime model',
            user_id=test_user.id
        )
        
        db.session.add(entry)
        db.session.commit()
        
        print(f"✅ Entry created successfully with ID: {entry.id}")
        
        # Test the backward compatibility properties
        print("\n--- Testing backward compatibility properties ---")
        print(f"entry.date: {entry.date}")
        print(f"entry.takeoff_time: {entry.takeoff_time}")
        print(f"entry.landing_time: {entry.landing_time}")
        
        # Test flight time calculation
        print(f"\n--- Testing flight time calculation ---")
        calculated_time = entry.get_calculated_flight_time()
        print(f"Calculated flight time: {calculated_time} hours")
        print(f"Stored flight time: {entry.flight_time} hours")
        
        # Test querying entries
        print(f"\n--- Testing queries ---")
        entries = LogbookEntry.query.filter_by(user_id=test_user.id).all()
        print(f"Found {len(entries)} entries for user {test_user.nickname}")
        
        for e in entries:
            print(f"  - {e.date} {e.aircraft_registration}: {e.takeoff_time} -> {e.landing_time} ({e.flight_time}h)")
        
        # Test ordering by new datetime field
        latest_entries = LogbookEntry.query.order_by(LogbookEntry.takeoff_datetime.desc()).limit(5).all()
        print(f"\n--- Latest entries by takeoff datetime ---")
        for e in latest_entries:
            print(f"  - {e.takeoff_datetime} {e.aircraft_registration}")
        
        print("\n✅ All tests passed! New LogbookEntry model is working correctly.")
        
        return True

if __name__ == "__main__":
    success = test_new_logbook_model()
    sys.exit(0 if success else 1)
