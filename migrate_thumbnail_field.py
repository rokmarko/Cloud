#!/usr/bin/env python3
"""
Migration script to add thumbnail_filename field to InstrumentLayout model.
This adds support for PNG thumbnail images for instrument layouts.
"""

import sqlite3
import os

def migrate_thumbnail_field():
    """Add thumbnail_filename field to instrument_layout table."""
    
    # Get the database path
    db_path = os.path.join('instance', 'kanardiacloud.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(instrument_layout)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'thumbnail_filename' in columns:
            print("thumbnail_filename column already exists in instrument_layout table")
            return True
        
        # Add the new column
        print("Adding thumbnail_filename column to instrument_layout table...")
        cursor.execute("""
            ALTER TABLE instrument_layout 
            ADD COLUMN thumbnail_filename VARCHAR(255)
        """)
        
        # Commit changes
        conn.commit()
        print("✅ Successfully added thumbnail_filename column to instrument_layout table")
        
        # Verify the column was added
        cursor.execute("PRAGMA table_info(instrument_layout)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'thumbnail_filename' in columns:
            print("✅ Verified: thumbnail_filename column exists in instrument_layout table")
        else:
            print("❌ Error: thumbnail_filename column was not added successfully")
            return False
            
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Run the migration."""
    print("🔄 Starting thumbnail_filename field migration...")
    
    if migrate_thumbnail_field():
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        exit(1)

if __name__ == '__main__':
    main()
