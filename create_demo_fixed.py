#!/usr/bin/env python3
"""
Simple demo data creation for KanardiaCloud documentation screenshots
"""
import sys
import os
import json
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, User, Device, Checklist, Pilot, LogbookEntry

def main():
    """Create demo data"""
    app = create_app()
    with app.app_context():
        print("Creating demo data for KanardiaCloud...")
        
        try:
            # Create demo user
            existing_user = User.query.filter_by(email='demo@kanardia.com').first()
            if not existing_user:
                demo_user = User(
                    nickname='demo',
                    email='demo@kanardia.com',
                    password_hash=generate_password_hash('demo123'),
                    is_admin=True,
                    is_active=True,
                    is_verified=True,
                    date_format='%d/%m/%Y',
                    created_at=datetime.utcnow()
                )
                db.session.add(demo_user)
                db.session.commit()
                print("✓ Created demo user")
            else:
                demo_user = existing_user
                print("✓ Demo user already exists")
            
            # Create demo pilot
            existing_pilot = Pilot.query.filter_by(name='John Smith').first()
            if not existing_pilot:
                pilot = Pilot(
                    name='John Smith',
                    license_number='PPL-12345',
                    email='john.smith@example.com',
                    phone='+1-555-0123',
                    user_id=demo_user.id
                )
                db.session.add(pilot)
                db.session.commit()
                print("✓ Created demo pilot")
            else:
                pilot = existing_pilot
                print("✓ Demo pilot already exists")
            
            # Create demo device
            existing_device = Device.query.filter_by(device_name='Demo Nesis').first()
            if not existing_device:
                device = Device(
                    device_id='demo-nesis-001',
                    device_name='Demo Nesis',
                    device_type='Nesis III',
                    serial_number='SN-123456',
                    user_id=demo_user.id,
                    created_at=datetime.utcnow(),
                    last_sync=datetime.utcnow()
                )
                db.session.add(device)
                db.session.commit()
                print("✓ Created demo device")
            else:
                device = existing_device
                print("✓ Demo device already exists")
                
            # Create demo checklist  
            existing_checklist = Checklist.query.filter_by(title='Pre-Flight Check - Cessna 172').first()
            if not existing_checklist:
                checklist_json = {
                    "name": "Pre-Flight Check - Cessna 172",
                    "aircraft": "Cessna 172",
                    "sections": [
                        {
                            "name": "External Inspection", 
                            "items": [
                                {"text": "Pitot tube - CLEAR", "checked": False},
                                {"text": "Landing gear - CHECK condition", "checked": False},
                                {"text": "Tires - CHECK condition", "checked": False},
                                {"text": "Wing surfaces - CHECK for damage", "checked": False},
                                {"text": "Control surfaces - CHECK freedom of movement", "checked": False}
                            ]
                        },
                        {
                            "name": "Interior Check",
                            "items": [
                                {"text": "Seat belts - FASTEN", "checked": False},
                                {"text": "Circuit breakers - CHECK", "checked": False},
                                {"text": "Fuel selector - BOTH", "checked": False},
                                {"text": "Mixture - RICH", "checked": False},
                                {"text": "Propeller - HIGH RPM", "checked": False}
                            ]
                        },
                        {
                            "name": "Engine Start",
                            "items": [
                                {"text": "Throttle - CRACKED OPEN", "checked": False},
                                {"text": "Beacon light - ON", "checked": False}, 
                                {"text": "Mixture - RICH", "checked": False},
                                {"text": "Master switch - ON", "checked": False},
                                {"text": "Prime - AS REQUIRED", "checked": False},
                                {"text": "Clear prop - ANNOUNCE", "checked": False},
                                {"text": "Ignition - START", "checked": False}
                            ]
                        }
                    ]
                }
                
                checklist = Checklist(
                    title='Pre-Flight Check - Cessna 172',
                    description='Standard pre-flight inspection checklist for Cessna 172',
                    items=json.dumps([item["text"] for section in checklist_json["sections"] for item in section["items"]]),
                    json_content=json.dumps(checklist_json),
                    user_id=demo_user.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(checklist)
                db.session.commit()
                print("✓ Created demo checklist")
            else:
                checklist = existing_checklist
                print("✓ Demo checklist already exists")
                
            # Create demo logbook entries
            existing_entry = LogbookEntry.query.filter_by(device_id=device.id).first()
            if not existing_entry:
                flights = [
                    {
                        'date': datetime.now() - timedelta(days=7),
                        'departure': 'LJLJ', 
                        'arrival': 'LJMB',
                        'aircraft': 'S5-ABC',
                        'duration': 45,
                        'description': 'Training flight - Pattern work'
                    },
                    {
                        'date': datetime.now() - timedelta(days=5),
                        'departure': 'LJMB',
                        'arrival': 'LJPZ',
                        'aircraft': 'S5-ABC', 
                        'duration': 62,
                        'description': 'Cross country navigation'
                    },
                    {
                        'date': datetime.now() - timedelta(days=3),
                        'departure': 'LJPZ',
                        'arrival': 'LJLJ',
                        'aircraft': 'S5-ABC',
                        'duration': 38,
                        'description': 'Return flight - ILS approach practice'
                    },
                    {
                        'date': datetime.now() - timedelta(days=1),
                        'departure': 'LJLJ',
                        'arrival': 'LJLJ',
                        'aircraft': 'S5-ABC',
                        'duration': 25,
                        'description': 'Local area familiarization'
                    }
                ]
                
                for flight in flights:
                    entry = LogbookEntry(
                        device_id=device.id,
                        pilot_id=pilot.id,
                        user_id=demo_user.id,
                        entry_date=flight['date'],
                        departure_airport=flight['departure'],
                        arrival_airport=flight['arrival'],
                        aircraft_registration=flight['aircraft'],
                        flight_time=flight['duration'],
                        description=flight['description'],
                        created_at=datetime.utcnow(),
                        is_manual=True
                    )
                    db.session.add(entry)
                    
                db.session.commit()
                print(f"✓ Created {len(flights)} demo logbook entries")
            else:
                print("✓ Demo logbook entries already exist")
                
            print("\n=== Demo Data Created Successfully ===")
            print("Login credentials:")
            print("  Email: demo@kanardia.com")
            print("  Password: demo123") 
            print("  Nickname: demo")
            print("\nYou can now access the application at http://localhost:5000")
            
        except Exception as e:
            print(f"Error creating demo data: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
