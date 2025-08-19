#!/usr/bin/env python3
"""
Test creating pilot mappings via the web interface
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

from src.app import create_app, db
from src.models import User, Device, Pilot, LogbookEntry

def test_pilot_mapping_creation():
    """Test creating pilot mappings and verify they work correctly."""
    
    app = create_app()
    
    with app.app_context():
        print("=== Testing Pilot Mapping Creation ===\n")
        
        # Get available users and devices
        users = User.query.filter_by(is_active=True).all()
        devices = Device.query.filter_by(is_active=True).all()
        
        print(f"Available users: {len(users)}")
        for user in users:
            print(f"  - {user.email} (ID: {user.id})")
        
        print(f"\nAvailable devices: {len(devices)}")
        for device in devices:
            print(f"  - {device.name} ({device.registration}) (ID: {device.id})")
        
        # Check existing pilot mappings
        existing_pilots = Pilot.query.all()
        print(f"\nExisting pilot mappings: {len(existing_pilots)}")
        for pilot in existing_pilots:
            print(f"  - '{pilot.pilot_name}' -> {pilot.user.email} on {pilot.device.name}")
        
        # Check unmapped pilots in logbook entries
        unmapped_pilots = db.session.query(LogbookEntry.pilot_name.distinct().label('pilot_name'))\
            .filter(LogbookEntry.pilot_name.isnot(None))\
            .filter(~LogbookEntry.pilot_name.in_(
                db.session.query(Pilot.pilot_name)
            )).all()
        
        print(f"\nUnmapped pilots in logbook: {len(unmapped_pilots)}")
        for pilot in unmapped_pilots:
            pilot_name = pilot.pilot_name
            entry_count = LogbookEntry.query.filter_by(pilot_name=pilot_name).count()
            print(f"  - '{pilot_name}' ({entry_count} entries)")
        
        # Test the pilot resolution methods
        print("\n=== Testing Pilot Resolution ===")
        sample_entries = LogbookEntry.query.filter(LogbookEntry.pilot_name.isnot(None)).limit(5).all()
        
        for entry in sample_entries:
            pilot_mapping = entry.get_pilot_mapping()
            actual_user = entry.get_actual_pilot_user()
            
            print(f"\nEntry: {entry.aircraft_registration} on {entry.date}")
            print(f"  Pilot name: '{entry.pilot_name}'")
            print(f"  Device: {entry.device.name if entry.device else 'None'}")
            print(f"  Pilot mapping: {pilot_mapping}")
            if pilot_mapping:
                print(f"  Mapped to: {pilot_mapping.user.email}")
            print(f"  Actual pilot user: {actual_user.email if actual_user else 'None'}")
            print(f"  Entry user: {entry.user.email if entry.user else 'None'}")

if __name__ == '__main__':
    test_pilot_mapping_creation()
