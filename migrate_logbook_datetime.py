#!/usr/bin/env python3
"""
Migration script to update LogbookEntry model from separate date/time fields to datetime fields.

This script:
1. Creates new takeoff_datetime and landing_datetime columns
2. Migrates existing data from date + takeoff_time/landing_time to new datetime columns
3. Drops the old date, takeoff_time, and landing_time columns

Run this script after updating the model but before deploying to production.
"""

import sys
import os
from datetime import datetime, date, time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import LogbookEntry
from sqlalchemy import text

def migrate_logbook_datetime():
    """Migrate LogbookEntry from date/time fields to datetime fields."""
    
    app = create_app()
    
    with app.app_context():
        print("Starting LogbookEntry datetime migration...")
        
        try:
            # Step 1: Add new datetime columns as nullable first (check if they already exist)
            print("Step 1: Adding new datetime columns...")
            
            with db.engine.connect() as conn:
                # Check if columns already exist
                try:
                    result = conn.execute(text("PRAGMA table_info(logbook_entry);"))
                    columns = [row[1] for row in result.fetchall()]
                    
                    if 'takeoff_datetime' not in columns:
                        conn.execute(text("ALTER TABLE logbook_entry ADD COLUMN takeoff_datetime DATETIME NULL;"))
                        print("Added takeoff_datetime column")
                    else:
                        print("takeoff_datetime column already exists")
                    
                    if 'landing_datetime' not in columns:
                        conn.execute(text("ALTER TABLE logbook_entry ADD COLUMN landing_datetime DATETIME NULL;"))
                        print("Added landing_datetime column")
                    else:
                        print("landing_datetime column already exists")
                    
                    conn.commit()
                except Exception as e:
                    print(f"Error adding columns: {e}")
                    # Try the direct approach if PRAGMA fails
                    try:
                        conn.execute(text("ALTER TABLE logbook_entry ADD COLUMN takeoff_datetime DATETIME NULL;"))
                    except:
                        pass  # Column might already exist
                    try:
                        conn.execute(text("ALTER TABLE logbook_entry ADD COLUMN landing_datetime DATETIME NULL;"))
                    except:
                        pass  # Column might already exist
                    conn.commit()
            
            print("New columns added successfully.")
            
            # Step 2: Migrate existing data
            print("Step 2: Migrating existing data...")
            
            # Get all existing logbook entries using raw SQL to avoid model conflicts
            with db.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, date, takeoff_time, landing_time 
                    FROM logbook_entry 
                    WHERE date IS NOT NULL
                """))
                
                entries = result.fetchall()
            print(f"Found {len(entries)} entries to migrate...")
            
            migration_count = 0
            with db.engine.connect() as conn:
                for entry in entries:
                    entry_id, entry_date, takeoff_time, landing_time = entry
                    
                    # Parse date string to date object if needed
                    if isinstance(entry_date, str):
                        entry_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
                    elif isinstance(entry_date, datetime):
                        entry_date = entry_date.date()
                    
                    # Create takeoff datetime
                    if takeoff_time:
                        if isinstance(takeoff_time, str):
                            # Parse time string - handle different formats
                            try:
                                takeoff_time = datetime.strptime(takeoff_time, '%H:%M:%S').time()
                            except ValueError:
                                try:
                                    takeoff_time = datetime.strptime(takeoff_time, '%H:%M:%S.%f').time()
                                except ValueError:
                                    # If all else fails, default to start of day
                                    takeoff_time = time(10, 0, 0)
                        takeoff_dt = datetime.combine(entry_date, takeoff_time)
                    else:
                        # Default to start of day if no takeoff time
                        takeoff_dt = datetime.combine(entry_date, time(0, 0, 0))
                    
                    # Create landing datetime
                    if landing_time:
                        if isinstance(landing_time, str):
                            # Parse time string - handle different formats
                            try:
                                landing_time = datetime.strptime(landing_time, '%H:%M:%S').time()
                            except ValueError:
                                try:
                                    landing_time = datetime.strptime(landing_time, '%H:%M:%S.%f').time()
                                except ValueError:
                                    # If all else fails, default to end of takeoff hour
                                    landing_time = time(takeoff_time.hour + 1, 0, 0) if takeoff_time else time(23, 59, 59)
                        landing_dt = datetime.combine(entry_date, landing_time)
                        
                        # Handle flights that cross midnight
                        if landing_dt < takeoff_dt:
                            from datetime import timedelta
                            landing_dt = landing_dt + timedelta(days=1)
                    else:
                        # Default to end of day if no landing time
                        landing_dt = datetime.combine(entry_date, time(23, 59, 59))
                    
                    # Update the entry with new datetime values
                    conn.execute(text("""
                        UPDATE logbook_entry 
                        SET takeoff_datetime = :takeoff_dt, landing_datetime = :landing_dt 
                        WHERE id = :entry_id
                    """), {"takeoff_dt": takeoff_dt, "landing_dt": landing_dt, "entry_id": entry_id})
                    
                    migration_count += 1
                    if migration_count % 10 == 0:
                        print(f"Migrated {migration_count} entries...")
                
                conn.commit()
            
            print(f"Successfully migrated {migration_count} entries.")
            
            # Step 3: Check if all entries have the new datetime values
            print("Step 3: Validating migration...")
            
            with db.engine.connect() as conn:
                null_count = conn.execute(text("""
                    SELECT COUNT(*) FROM logbook_entry 
                    WHERE takeoff_datetime IS NULL OR landing_datetime IS NULL
                """)).scalar()
            
            if null_count > 0:
                print(f"Warning: {null_count} entries still have NULL datetime values!")
                print("Migration completed with warnings.")
                return False
            
            # Step 4: Drop old columns (SQLite doesn't support dropping columns easily, so we'll recreate the table)
            print("Step 4: Recreating table without old columns...")
            
            with db.engine.connect() as conn:
                # SQLite approach: create new table, copy data, drop old table, rename new table
                conn.execute(text("""
                    CREATE TABLE logbook_entry_new (
                        id INTEGER PRIMARY KEY,
                        takeoff_datetime DATETIME NOT NULL,
                        landing_datetime DATETIME NOT NULL,
                        aircraft_type VARCHAR(50) NOT NULL,
                        aircraft_registration VARCHAR(20) NOT NULL,
                        departure_airport VARCHAR(10) NOT NULL,
                        arrival_airport VARCHAR(10) NOT NULL,
                        flight_time FLOAT NOT NULL,
                        pilot_in_command_time FLOAT DEFAULT 0.0,
                        dual_time FLOAT DEFAULT 0.0,
                        instrument_time FLOAT DEFAULT 0.0,
                        night_time FLOAT DEFAULT 0.0,
                        cross_country_time FLOAT DEFAULT 0.0,
                        landings_day INTEGER DEFAULT 0,
                        landings_night INTEGER DEFAULT 0,
                        remarks TEXT,
                        pilot_name VARCHAR(100),
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        user_id INTEGER,
                        device_id INTEGER,
                        FOREIGN KEY (user_id) REFERENCES user (id),
                        FOREIGN KEY (device_id) REFERENCES device (id)
                    );
                """))
                
                # Copy all data to new table
                conn.execute(text("""
                    INSERT INTO logbook_entry_new 
                    SELECT id, takeoff_datetime, landing_datetime, aircraft_type, aircraft_registration,
                           departure_airport, arrival_airport, flight_time, pilot_in_command_time,
                           dual_time, instrument_time, night_time, cross_country_time,
                           landings_day, landings_night, remarks, pilot_name,
                           created_at, updated_at, user_id, device_id
                    FROM logbook_entry;
                """))
                
                # Drop old table and rename new one
                conn.execute(text("DROP TABLE logbook_entry;"))
                conn.execute(text("ALTER TABLE logbook_entry_new RENAME TO logbook_entry;"))
                conn.commit()
            
            print("Table recreated successfully without old columns.")
            
            print("Migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            return False

def rollback_migration():
    """Rollback the datetime migration (add back old columns)."""
    
    print("Rollback not implemented for SQLite. Please restore from backup if needed.")
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_migration()
    else:
        success = migrate_logbook_datetime()
    
    sys.exit(0 if success else 1)
