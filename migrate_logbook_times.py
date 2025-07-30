#!/usr/bin/env python3
"""
Migration script to add takeoff_time and landing_time columns to LogbookEntry table
and migrate existing flight_time data.
"""

import os
import sys
from datetime import datetime, time, timedelta
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from models import db, LogbookEntry

def migrate_logbook_times():
    """Migrate existing logbook entries to use takeoff and landing times."""
    # Load environment variables
    load_dotenv()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("LogbookEntry Time Migration")
        print("=" * 35)
        
        try:
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('logbook_entry')]
            
            has_takeoff_time = 'takeoff_time' in columns
            has_landing_time = 'landing_time' in columns
            has_flight_time = 'flight_time' in columns
            
            print(f"Current columns: {', '.join(columns)}")
            print(f"Has takeoff_time: {has_takeoff_time}")
            print(f"Has landing_time: {has_landing_time}")
            print(f"Has flight_time: {has_flight_time}")
            print()
            
            # Add new columns if they don't exist
            if not has_takeoff_time or not has_landing_time:
                print("Adding new time columns...")
                
                # Add columns using raw SQL (safer for migrations)
                if not has_takeoff_time:
                    db.engine.execute("ALTER TABLE logbook_entry ADD COLUMN takeoff_time TIME")
                    print("✅ Added takeoff_time column")
                
                if not has_landing_time:
                    db.engine.execute("ALTER TABLE logbook_entry ADD COLUMN landing_time TIME")
                    print("✅ Added landing_time column")
                
                db.session.commit()
                print()
            
            # Migrate existing data
            entries = LogbookEntry.query.filter(
                LogbookEntry.takeoff_time.is_(None) | 
                LogbookEntry.landing_time.is_(None)
            ).all()
            
            print(f"Found {len(entries)} entries to migrate...")
            
            for i, entry in enumerate(entries):
                # For existing entries, we'll estimate takeoff and landing times
                # based on the flight_time duration
                
                # Default takeoff time to 10:00 AM if not set
                if not entry.takeoff_time:
                    entry.takeoff_time = time(10, 0)  # 10:00 AM
                
                # Calculate landing time based on flight_time if not set
                if not entry.landing_time and hasattr(entry, '_flight_time_db'):
                    flight_duration_hours = getattr(entry, '_flight_time_db', 1.0)
                    
                    # Convert flight time to timedelta
                    flight_duration = timedelta(hours=flight_duration_hours)
                    
                    # Calculate landing time
                    takeoff_dt = datetime.combine(entry.date, entry.takeoff_time)
                    landing_dt = takeoff_dt + flight_duration
                    entry.landing_time = landing_dt.time()
                elif not entry.landing_time:
                    # Default to 1 hour flight if no flight_time available
                    takeoff_dt = datetime.combine(entry.date, entry.takeoff_time)
                    landing_dt = takeoff_dt + timedelta(hours=1)
                    entry.landing_time = landing_dt.time()
                
                # Update progress
                if (i + 1) % 10 == 0 or i == len(entries) - 1:
                    print(f"   Migrated {i + 1}/{len(entries)} entries...")
            
            # Commit all changes
            db.session.commit()
            
            print(f"✅ Successfully migrated {len(entries)} logbook entries")
            
            # Verify migration
            print("\n📊 Verification:")
            total_entries = LogbookEntry.query.count()
            entries_with_times = LogbookEntry.query.filter(
                LogbookEntry.takeoff_time.isnot(None) & 
                LogbookEntry.landing_time.isnot(None)
            ).count()
            
            print(f"   Total entries: {total_entries}")
            print(f"   Entries with times: {entries_with_times}")
            print(f"   Migration complete: {entries_with_times == total_entries}")
            
            # Show sample entries
            print("\n📝 Sample migrated entries:")
            sample_entries = LogbookEntry.query.limit(3).all()
            for entry in sample_entries:
                print(f"   {entry.date} {entry.aircraft_registration}: "
                      f"{entry.takeoff_time} → {entry.landing_time} "
                      f"({entry.flight_time}h)")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = migrate_logbook_times()
    sys.exit(0 if success else 1)
