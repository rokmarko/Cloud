#!/usr/bin/env python3
"""
Script to create and manage pilot mappings between users and devices.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import User, Device, Pilot


def create_pilot_mapping(pilot_name: str, user_email: str, device_name: str) -> bool:
    """Create a pilot mapping."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find user by email
            user = User.query.filter_by(email=user_email, is_active=True).first()
            if not user:
                print(f"❌ User with email '{user_email}' not found")
                return False
            
            # Find device by name
            device = Device.query.filter_by(name=device_name, is_active=True).first()
            if not device:
                print(f"❌ Device with name '{device_name}' not found")
                return False
            
            # Check if mapping already exists
            existing = Pilot.query.filter_by(
                pilot_name=pilot_name,
                device_id=device.id
            ).first()
            
            if existing:
                print(f"⚠️  Pilot mapping already exists: '{pilot_name}' on device '{device_name}' -> {existing.user.email}")
                return True
            
            # Create new pilot mapping
            pilot_mapping = Pilot(
                pilot_name=pilot_name,
                user_id=user.id,
                device_id=device.id
            )
            
            db.session.add(pilot_mapping)
            db.session.commit()
            
            print(f"✅ Created pilot mapping: '{pilot_name}' on device '{device_name}' -> {user.email}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating pilot mapping: {str(e)}")
            return False


def list_pilot_mappings():
    """List all pilot mappings."""
    
    app = create_app()
    
    with app.app_context():
        try:
            mappings = Pilot.query.filter_by(is_active=True).all()
            
            if not mappings:
                print("ℹ️  No pilot mappings found")
                return
            
            print(f"📋 Pilot Mappings ({len(mappings)} total):")
            print("=" * 60)
            
            for mapping in mappings:
                print(f"• '{mapping.pilot_name}' on {mapping.device.name} -> {mapping.user.email}")
            
        except Exception as e:
            print(f"❌ Error listing pilot mappings: {str(e)}")


def list_available_resources():
    """List available users and devices."""
    
    app = create_app()
    
    with app.app_context():
        try:
            users = User.query.filter_by(is_active=True).all()
            devices = Device.query.filter_by(is_active=True).all()
            
            print("👥 Available Users:")
            for user in users:
                print(f"  • {user.email} ({user.nickname})")
            
            print(f"\n🛩️  Available Devices:")
            for device in devices:
                print(f"  • {device.name} ({device.registration or 'No registration'})")
            
        except Exception as e:
            print(f"❌ Error listing resources: {str(e)}")


def interactive_create():
    """Interactive pilot mapping creation."""
    
    print("🧑‍✈️ Create Pilot Mapping")
    print("=" * 25)
    
    list_available_resources()
    
    print(f"\nEnter pilot mapping details:")
    pilot_name = input("Pilot name (as it appears in logbook): ").strip()
    user_email = input("User email: ").strip()
    device_name = input("Device name: ").strip()
    
    if not pilot_name or not user_email or not device_name:
        print("❌ All fields are required")
        return
    
    create_pilot_mapping(pilot_name, user_email, device_name)


def show_help():
    """Show help information."""
    print("Pilot Mapping Management Script")
    print("=" * 32)
    print()
    print("This script manages pilot mappings between users and devices.")
    print("Pilot mappings allow logbook entries to be linked to specific pilots")
    print("based on pilot names found in ThingsBoard sync data.")
    print()
    print("Usage:")
    print("  python manage_pilot_mappings.py                           # Interactive mode")
    print("  python manage_pilot_mappings.py --list                    # List all mappings")
    print("  python manage_pilot_mappings.py --resources               # Show available users/devices")
    print("  python manage_pilot_mappings.py --create NAME EMAIL DEVICE # Create mapping")
    print("  python manage_pilot_mappings.py --help                    # Show this help")
    print()
    print("Examples:")
    print("  python manage_pilot_mappings.py --create 'John Doe' john@example.com 'Aircraft-1'")
    print("  python manage_pilot_mappings.py --list")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h', 'help']:
            show_help()
        elif arg == '--list':
            list_pilot_mappings()
        elif arg == '--resources':
            list_available_resources()
        elif arg == '--create' and len(sys.argv) == 5:
            pilot_name, user_email, device_name = sys.argv[2], sys.argv[3], sys.argv[4]
            create_pilot_mapping(pilot_name, user_email, device_name)
        else:
            print(f"❌ Unknown argument or incorrect usage: {' '.join(sys.argv[1:])}")
            print("Use --help for usage information.")
    else:
        interactive_create()
