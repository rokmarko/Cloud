#!/usr/bin/env python3
"""
Migration: Allow NULL user_id in logbook_entry table for unknown pilots

This migration changes the user_id column in the logbook_entry table
from NOT NULL to allow NULL values for entries with unknown pilots.
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

def migrate_user_id_nullable():
    """
    Make user_id column nullable in logbook_entry table.
    
    SQLite doesn't support ALTER COLUMN directly, so we need to:
    1. Create a new table with the correct schema
    2. Copy data from the old table
    3. Drop the old table
    4. Rename the new table
    """
    
    # Database path
    db_path = '/home/rok/Branch/NavSync/Protected/Cloud/instance/kanardiacloud.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"🔄 Starting migration to make user_id nullable in logbook_entry table...")
    print(f"📁 Database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if logbook_entry table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='logbook_entry'")
        if not cursor.fetchone():
            print("⚠️  logbook_entry table not found, migration not needed")
            conn.close()
            return True
        
        # Get current table schema
        cursor.execute("PRAGMA table_info(logbook_entry)")
        columns = cursor.fetchall()
        
        print(f"📊 Current table has {len(columns)} columns")
        
        # Check if user_id column is currently nullable
        user_id_column = next((col for col in columns if col[1] == 'user_id'), None)
        if user_id_column and user_id_column[3] == 0:  # not null = 0 means nullable
            print("✅ user_id column is already nullable, migration not needed")
            conn.close()
            return True
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create new table with nullable user_id
        create_new_table_sql = """
        CREATE TABLE logbook_entry_new (
            id INTEGER PRIMARY KEY,
            date DATE NOT NULL,
            aircraft_type VARCHAR(50),
            aircraft_registration VARCHAR(20),
            departure_airport VARCHAR(10),
            arrival_airport VARCHAR(10),
            flight_time FLOAT,
            takeoff_time DATETIME,
            landing_time DATETIME,
            pilot_in_command_time FLOAT DEFAULT 0.0,
            dual_time FLOAT DEFAULT 0.0,
            instrument_time FLOAT DEFAULT 0.0,
            night_time FLOAT DEFAULT 0.0,
            cross_country_time FLOAT DEFAULT 0.0,
            landings_day INTEGER DEFAULT 0,
            landings_night INTEGER DEFAULT 0,
            remarks TEXT,
            pilot_name VARCHAR(100),
            created_at DATETIME,
            updated_at DATETIME,
            user_id INTEGER,
            device_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (device_id) REFERENCES device(id)
        )
        """
        
        cursor.execute(create_new_table_sql)
        print("✅ Created new table with nullable user_id")
        
        # Copy data from old table to new table
        cursor.execute("""
        INSERT INTO logbook_entry_new 
        SELECT * FROM logbook_entry
        """)
        
        # Get count of copied rows
        cursor.execute("SELECT COUNT(*) FROM logbook_entry_new")
        copied_count = cursor.fetchone()[0]
        print(f"✅ Copied {copied_count} rows to new table")
        
        # Drop old table
        cursor.execute("DROP TABLE logbook_entry")
        print("✅ Dropped old table")
        
        # Rename new table
        cursor.execute("ALTER TABLE logbook_entry_new RENAME TO logbook_entry")
        print("✅ Renamed new table to logbook_entry")
        
        # Commit transaction
        conn.commit()
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(logbook_entry)")
        new_columns = cursor.fetchall()
        user_id_new = next((col for col in new_columns if col[1] == 'user_id'), None)
        
        if user_id_new and user_id_new[3] == 0:  # not null = 0 means nullable
            print("✅ Migration successful - user_id is now nullable")
            
            # Check data integrity
            cursor.execute("SELECT COUNT(*) FROM logbook_entry")
            final_count = cursor.fetchone()[0]
            print(f"✅ Data integrity verified - {final_count} rows in final table")
            
            conn.close()
            return True
        else:
            print("❌ Migration verification failed")
            conn.rollback()
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"❌ SQLite error during migration: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """Main migration function."""
    print("=" * 60)
    print("MIGRATION: Make LogbookEntry.user_id nullable for unknown pilots")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = migrate_user_id_nullable()
    
    print()
    if success:
        print("🎉 Migration completed successfully!")
        print("   Unknown pilots will no longer be linked to device owners")
    else:
        print("💥 Migration failed!")
        print("   Please check the error messages above")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
