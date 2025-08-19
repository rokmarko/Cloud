#!/usr/bin/env python3
"""
Migration script to add write_address field to Event model and populate it.

This script:
1. Adds the write_address column to the events table
2. Sets write_address for all events linked to a device_id using device.current_logger_page
3. Updates the database schema
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, Event, Device
from sqlalchemy import text


def migrate_event_write_address():
    """Add write_address field and populate it for existing events."""
    
    app = create_app()
    
    with app.app_context():
        print("Starting Event write_address migration...")
        
        # Check if write_address column already exists
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(event)"))
                columns = [row[1] for row in result]
                
                if 'write_address' not in columns:
                    print("Adding write_address column to events table...")
                    conn.execute(text("ALTER TABLE event ADD COLUMN write_address BIGINT"))
                    conn.commit()
                    print("✅ Added write_address column")
                else:
                    print("ℹ️  write_address column already exists")
                
        except Exception as e:
            print(f"❌ Error adding column: {e}")
            return False
        
        # Get all events with their device information
        print("Retrieving events and device information...")
        
        try:
            events_updated = 0
            events_without_device = 0
            
            # Get all events
            events = Event.query.all()
            print(f"Found {len(events)} events to process")
            
            for event in events:
                if event.device_id and event.device:
                    # Set write_address to device's current_logger_page
                    if event.device.current_logger_page is not None:
                        event.write_address = event.device.current_logger_page
                        events_updated += 1
                    else:
                        # If device doesn't have current_logger_page, set to None (already default)
                        event.write_address = None
                        events_updated += 1
                else:
                    events_without_device += 1
                    print(f"⚠️  Event {event.id} has no linked device")
            
            # Commit all changes
            if events_updated > 0:
                db.session.commit()
                print(f"✅ Updated write_address for {events_updated} events")
            
            if events_without_device > 0:
                print(f"⚠️  {events_without_device} events had no linked device")
                
            print("Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error updating events: {e}")
            db.session.rollback()
            return False


def verify_migration():
    """Verify the migration was successful."""
    
    app = create_app()
    
    with app.app_context():
        print("\nVerifying migration...")
        
        try:
            # Check column exists
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(event)"))
                columns = [row[1] for row in result]
            
            if 'write_address' not in columns:
                print("❌ write_address column not found!")
                return False
                
            print("✅ write_address column exists")
            
            # Check some sample data
            events_with_write_address = Event.query.filter(Event.write_address.isnot(None)).count()
            total_events = Event.query.count()
            
            print(f"📊 Statistics:")
            print(f"   Total events: {total_events}")
            print(f"   Events with write_address: {events_with_write_address}")
            print(f"   Events without write_address: {total_events - events_with_write_address}")
            
            # Show a few examples
            if events_with_write_address > 0:
                sample_events = Event.query.filter(Event.write_address.isnot(None)).limit(5).all()
                print(f"📝 Sample events with write_address:")
                for event in sample_events:
                    print(f"   Event {event.id}: write_address={event.write_address}, device={event.device_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error verifying migration: {e}")
            return False


def rollback_migration():
    """Rollback the migration by removing the write_address column."""
    
    app = create_app()
    
    with app.app_context():
        print("Rolling back write_address migration...")
        
        try:
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            print("⚠️  SQLite doesn't support DROP COLUMN. Manual rollback required:")
            print("   1. Create backup of database")
            print("   2. Recreate event table without write_address column")
            print("   3. Copy data from backup excluding write_address")
            
            return False
            
        except Exception as e:
            print(f"❌ Error during rollback: {e}")
            return False


if __name__ == '__main__':
    print("Event write_address Migration Script")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'rollback':
            success = rollback_migration()
        elif command == 'verify':
            success = verify_migration()
        else:
            print("Usage: python migrate_event_write_address.py [verify|rollback]")
            success = migrate_event_write_address()
            if success:
                verify_migration()
    else:
        # Default: run migration
        success = migrate_event_write_address()
        if success:
            verify_migration()
    
    if not success:
        sys.exit(1)
    
    print("\n✅ Migration completed successfully!")
