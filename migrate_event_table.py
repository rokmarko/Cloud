#!/usr/bin/env python3
"""
Migration: Create Event table for device events

This migration creates the Event table to store events synced from ThingsBoard devices.
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

def create_event_table():
    """
    Create the Event table for storing device events.
    """
    
    # Database path
    db_path = '/home/rok/Branch/NavSync/Protected/Cloud/instance/kanardiacloud.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"🔄 Creating Event table for device events...")
    print(f"📁 Database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if Event table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event'")
        if cursor.fetchone():
            print("⚠️  Event table already exists, skipping creation")
            conn.close()
            return True
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create Event table
        create_table_sql = """
        CREATE TABLE event (
            id INTEGER PRIMARY KEY,
            date_time DATETIME,
            page_address BIGINT,
            total_time INTEGER,
            bitfield INTEGER NOT NULL DEFAULT 0,
            current_logger_page BIGINT,
            created_at DATETIME,
            updated_at DATETIME,
            device_id INTEGER NOT NULL,
            FOREIGN KEY (device_id) REFERENCES device(id)
        )
        """
        
        cursor.execute(create_table_sql)
        print("✅ Created Event table")
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_event_device_id ON event(device_id)")
        cursor.execute("CREATE INDEX idx_event_date_time ON event(date_time)")
        cursor.execute("CREATE INDEX idx_event_page_address ON event(page_address)")
        cursor.execute("CREATE INDEX idx_event_bitfield ON event(bitfield)")
        print("✅ Created indexes on Event table")
        
        # Commit transaction
        conn.commit()
        
        # Verify table creation
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='event'")
        if cursor.fetchone():
            print("✅ Event table created successfully")
            
            # Check table structure
            cursor.execute("PRAGMA table_info(event)")
            columns = cursor.fetchall()
            print(f"✅ Event table has {len(columns)} columns")
            
            conn.close()
            return True
        else:
            print("❌ Event table creation verification failed")
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
    print("MIGRATION: Create Event table for device events")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = create_event_table()
    
    print()
    if success:
        print("🎉 Migration completed successfully!")
        print("   Event table created for storing device events")
        print("   Ready to sync events from ThingsBoard devices")
    else:
        print("💥 Migration failed!")
        print("   Please check the error messages above")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
