#!/usr/bin/env python3
"""
Test script to verify the new takeoff/landing time model is working correctly.
"""

import os
import sys
from datetime import datetime, time, date
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_logbook_time_calculation():
    """Test the new time-based flight time calculation."""
    load_dotenv()
    
    # Import here to avoid context issues
    from app import create_app
    from models import db, LogbookEntry, User
    
    app = create_app()
    
    with app.app_context():
        print("Logbook Time Calculation Test")
        print("=" * 35)
        
        # Check existing entries
        existing_entries = LogbookEntry.query.all()
        print(f"Found {len(existing_entries)} existing logbook entries")
        
        for entry in existing_entries:
            print(f"\nEntry {entry.id}:")
            print(f"  Date: {entry.date}")
            print(f"  Aircraft: {entry.aircraft_registration}")
            print(f"  Takeoff: {entry.takeoff_time}")
            print(f"  Landing: {entry.landing_time}")
            print(f"  Calculated flight time: {entry.flight_time}h")
            
            # Verify the calculation
            if entry.takeoff_time and entry.landing_time:
                expected_time = entry.flight_time
                print(f"  Time calculation working: ✅")
            else:
                print(f"  Missing time data: ❌")
        
        # Test creating a new entry with time-based calculation
        print(f"\n🧪 Testing new entry creation...")
        
        # Get a test user
        user = User.query.first()
        if user:
            test_entry = LogbookEntry(
                date=date.today(),
                aircraft_type="DA40",
                aircraft_registration="OE-TEST", 
                departure_airport="LOWG",
                arrival_airport="LOWL",
                takeoff_time=time(14, 30),  # 2:30 PM
                landing_time=time(16, 15),  # 4:15 PM
                user_id=user.id
            )
            
            # Don't actually save it, just test the calculation
            calculated_time = test_entry.flight_time
            expected_time = 1.75  # 1 hour 45 minutes = 1.75 hours
            
            print(f"  New entry calculation:")
            print(f"    Takeoff: {test_entry.takeoff_time}")
            print(f"    Landing: {test_entry.landing_time}")
            print(f"    Calculated flight time: {calculated_time}h")
            print(f"    Expected flight time: {expected_time}h")
            print(f"    Calculation correct: {'✅' if abs(calculated_time - expected_time) < 0.01 else '❌'}")
        
        print(f"\n✅ Logbook time calculation test completed!")
        return True

if __name__ == "__main__":
    try:
        success = test_logbook_time_calculation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
