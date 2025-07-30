#!/usr/bin/env python3
"""
Migration script to add device_id column to logbook_entry table
"""

import sqlite3
import sys
import os

def migrate_device_link():
    """Add device_id column to logbook_entry table."""
    
    db_path = 'instance/kanardiacloud.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if device_id column already exists
        cursor.execute("PRAGMA table_info(logbook_entry)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'device_id' in columns:
            print("device_id column already exists in logbook_entry table")
            conn.close()
            return True
        
        print("Adding device_id column to logbook_entry table...")
        
        # Add the device_id column
        cursor.execute("""
            ALTER TABLE logbook_entry 
            ADD COLUMN device_id INTEGER 
            REFERENCES device(id)
        """)
        
        # Commit the changes
        conn.commit()
        
        print("Successfully added device_id column")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(logbook_entry)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'device_id' in columns:
            print("Migration completed successfully")
            conn.close()
            return True
        else:
            print("ERROR: device_id column was not added properly")
            conn.close()
            return False
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == '__main__':
    success = migrate_device_link()
    sys.exit(0 if success else 1)
