#!/usr/bin/env python3
"""
Migration script to add thumbnail_base64 field to InstrumentLayout model.
This migration adds a new TEXT field to store base64-encoded PNG thumbnails directly in the database.

Run this script to update the database schema:
    python migrate_thumbnail_base64.py
"""
import os
import sys
import sqlite3
from pathlib import Path

# Add the src directory to the path so we can import the models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models import db, InstrumentLayout


def run_migration():
    """
    Add thumbnail_base64 column to instrument_layouts table.
    """
    # Database path
    db_path = os.path.join('instance', 'kanardiacloud.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(instrument_layout)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'thumbnail_base64' in columns:
            print("Migration already applied: thumbnail_base64 column already exists")
            conn.close()
            return True
        
        # Add the new column
        print("Adding thumbnail_base64 column to instrument_layout table...")
        cursor.execute("""
            ALTER TABLE instrument_layout 
            ADD COLUMN thumbnail_base64 TEXT
        """)
        
        conn.commit()
        conn.close()
        
        print("Migration completed successfully!")
        print("- Added thumbnail_base64 column to instrument_layout table")
        print("- Column type: TEXT (for storing base64-encoded PNG data)")
        print("- Existing thumbnails will continue to use file-based storage for backward compatibility")
        print("- New thumbnails will be stored as base64 data in the database")
        
        return True
        
    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
        return False
    except Exception as e:
        print(f"Error during migration: {e}")
        return False


def main():
    """Main migration function."""
    print("KanardiaCloud Database Migration: Add thumbnail_base64 field")
    print("=" * 60)
    print()
    
    success = run_migration()
    
    if success:
        print()
        print("Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Restart the application to use the new base64 thumbnail storage")
        print("2. New instrument layout thumbnails will be stored in the database")
        print("3. Existing file-based thumbnails will continue to work (backward compatibility)")
        sys.exit(0)
    else:
        print()
        print("Migration failed! Please check the error messages above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
