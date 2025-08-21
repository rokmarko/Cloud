#!/usr/bin/env python3
"""
Create demo data for KanardiaCloud documentation screenshots
"""
import sys
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, User, Device, Checklist, ChecklistItem, Pilot, LogbookEntry

def create_demo_user():
    """Create a demo admin user"""
    app = create_app()
    with app.app_context():
        # Check if demo user already exists
        existing_user = User.query.filter_by(username='demo').first()
        if existing_user:
            print("Demo user already exists")
            return existing_user
        
        # Create demo user
        demo_user = User(
            username='demo',
            email='demo@kanardia.com',
            password_hash=generate_password_hash('demo123'),
            is_admin=True,
            date_format='DD/MM/YYYY',
            created_at=datetime.utcnow()
        )
        
        db.session.add(demo_user)
        db.session.commit()
        print(f"Created demo user: {demo_user.username}")
        return demo_user

def create_demo_pilot():
    """Create a demo pilot"""
    app = create_app()
    with app.app_context():
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            print("Demo user not found")
            return None
            
        # Check if demo pilot already exists
        existing_pilot = Pilot.query.filter_by(name='John Smith').first()
        if existing_pilot:
            print("Demo pilot already exists")
            return existing_pilot
            
        pilot = Pilot(
            name='John Smith',
            license_number='PPL-12345',
            email='john.smith@example.com',
            phone='+1-555-0123',
            user_id=demo_user.id
        )
        
        db.session.add(pilot)
        db.session.commit()
        print(f"Created demo pilot: {pilot.name}")
        return pilot

def create_demo_device():
    """Create a demo device"""
    app = create_app()
    with app.app_context():
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            print("Demo user not found")
            return None
            
        # Check if demo device already exists
        existing_device = Device.query.filter_by(device_name='Demo Nesis').first()
        if existing_device:
            print("Demo device already exists")
            return existing_device
            
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
        print(f"Created demo device: {device.device_name}")
        return device

def create_demo_checklist():
    """Create a demo checklist"""
    app = create_app()
    with app.app_context():
        demo_user = User.query.filter_by(username='demo').first()
        if not demo_user:
            print("Demo user not found")
            return None
            
        # Check if demo checklist already exists
        existing_checklist = Checklist.query.filter_by(name='Pre-Flight Check - Cessna 172').first()
        if existing_checklist:
            print("Demo checklist already exists")
            return existing_checklist
            
        checklist = Checklist(
            name='Pre-Flight Check - Cessna 172',
            aircraft_type='Cessna 172',
            description='Standard pre-flight inspection checklist for Cessna 172',
            user_id=demo_user.id,
            created_at=datetime.utcnow(),
            xml_content='''<?xml version="1.0" encoding="UTF-8"?>
<checklist>
    <name>Pre-Flight Check - Cessna 172</name>
    <aircraft>Cessna 172</aircraft>
    <sections>
        <section name="External Inspection">
            <item>Pitot tube - CLEAR</item>
            <item>Landing gear - CHECK condition</item>
            <item>Tires - CHECK condition</item>
            <item>Wing surfaces - CHECK for damage</item>
            <item>Control surfaces - CHECK freedom of movement</item>
        </section>
        <section name="Interior Check">
            <item>Seat belts - FASTEN</item>
            <item>Circuit breakers - CHECK</item>
            <item>Fuel selector - BOTH</item>
            <item>Mixture - RICH</item>
            <item>Propeller - HIGH RPM</item>
        </section>
        <section name="Engine Start">
            <item>Throttle - CRACKED OPEN</item>
            <item>Beacon light - ON</item>
            <item>Mixture - RICH</item>
            <item>Master switch - ON</item>
            <item>Prime - AS REQUIRED</item>
            <item>Clear prop - ANNOUNCE</item>
            <item>Ignition - START</item>
        </section>
    </sections>
</checklist>'''
        )
        
        db.session.add(checklist)
        db.session.commit()
        
        # Create checklist items
        items_data = [
            # External Inspection
            ("Pitot tube - CLEAR", 1, "External Inspection", False),
            ("Landing gear - CHECK condition", 2, "External Inspection", False),
            ("Tires - CHECK condition", 3, "External Inspection", False),
            ("Wing surfaces - CHECK for damage", 4, "External Inspection", False),
            ("Control surfaces - CHECK freedom of movement", 5, "External Inspection", False),
            # Interior Check
            ("Seat belts - FASTEN", 6, "Interior Check", False),
            ("Circuit breakers - CHECK", 7, "Interior Check", False),
            ("Fuel selector - BOTH", 8, "Interior Check", False),
            ("Mixture - RICH", 9, "Interior Check", False),
            ("Propeller - HIGH RPM", 10, "Interior Check", False),
            # Engine Start
            ("Throttle - CRACKED OPEN", 11, "Engine Start", False),
            ("Beacon light - ON", 12, "Engine Start", False),
            ("Mixture - RICH", 13, "Engine Start", False),
            ("Master switch - ON", 14, "Engine Start", False),
            ("Prime - AS REQUIRED", 15, "Engine Start", False),
            ("Clear prop - ANNOUNCE", 16, "Engine Start", False),
            ("Ignition - START", 17, "Engine Start", False),
        ]
        
        for text, order, section, is_checked in items_data:
            item = ChecklistItem(
                text=text,
                order=order,
                section=section,
                is_checked=is_checked,
                checklist_id=checklist.id
            )
            db.session.add(item)
        
        db.session.commit()
        print(f"Created demo checklist: {checklist.name} with {len(items_data)} items")
        return checklist

def create_demo_logbook_entries():
    """Create demo logbook entries"""
    app = create_app()
    with app.app_context():
        demo_user = User.query.filter_by(username='demo').first()
        device = Device.query.filter_by(device_name='Demo Nesis').first()
        pilot = Pilot.query.filter_by(name='John Smith').first()
        
        if not demo_user or not device or not pilot:
            print("Required data not found for logbook entries")
            return
            
        # Check if demo entries already exist
        existing_entry = LogbookEntry.query.filter_by(device_id=device.id).first()
        if existing_entry:
            print("Demo logbook entries already exist")
            return
            
        # Create sample flights
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
        
        for i, flight in enumerate(flights):
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
        print(f"Created {len(flights)} demo logbook entries")

def main():
    """Main function to create all demo data"""
    print("Creating demo data for KanardiaCloud...")
    
    try:
        demo_user = create_demo_user()
        demo_pilot = create_demo_pilot() 
        demo_device = create_demo_device()
        demo_checklist = create_demo_checklist()
        create_demo_logbook_entries()
        
        print("\n=== Demo Data Created Successfully ===")
        print("Login credentials:")
        print("  Username: demo")
        print("  Password: demo123")
        print("  Email: demo@kanardia.com")
        print("\nYou can now access the application at http://localhost:5000")
        
    except Exception as e:
        print(f"Error creating demo data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
