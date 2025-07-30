#!/usr/bin/env python3
"""
Migration: Clean up corrupted logbook entry data

The migration script corrupted some data by putting time values in wrong columns.
This script will fix the data corruption.
"""

import sys
import os
import sqlite3
from datetime import datetime
import re

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

def cleanup_corrupted_data():
    """
    Clean up corrupted logbook entry data where time values ended up in wrong columns.
    """
    
    # Database path
    db_path = '/home/rok/Branch/NavSync/Protected/Cloud/instance/kanardiacloud.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"🔄 Starting cleanup of corrupted logbook entry data...")
    print(f"📁 Database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Find entries where user_id or device_id contains time patterns
        cursor.execute("""
            SELECT id, user_id, device_id 
            FROM logbook_entry 
            WHERE user_id LIKE '%:%' OR device_id LIKE '%:%'
        """)
        
        corrupted_entries = cursor.fetchall()
        print(f"📊 Found {len(corrupted_entries)} entries with corrupted data")
        
        fixed_count = 0
        for entry_id, user_id_val, device_id_val in corrupted_entries:
            print(f"🔧 Fixing entry {entry_id}: user_id='{user_id_val}', device_id='{device_id_val}'")
            
            # Extract actual user_id and device_id if they contain valid data
            actual_user_id = None
            actual_device_id = None
            
            # Check if the values are time strings or actual IDs
            time_pattern = re.compile(r'^\d{2}:\d{2}:\d{2}(\.\d+)?$')
            
            if user_id_val and not time_pattern.match(str(user_id_val)):
                try:
                    actual_user_id = int(user_id_val)
                except (ValueError, TypeError):
                    pass
            
            if device_id_val and not time_pattern.match(str(device_id_val)):
                try:
                    actual_device_id = int(device_id_val)
                except (ValueError, TypeError):
                    pass
            
            # Update the entry to fix the corruption
            cursor.execute("""
                UPDATE logbook_entry 
                SET user_id = ?, device_id = ?, takeoff_time = NULL, landing_time = NULL
                WHERE id = ?
            """, (actual_user_id, actual_device_id, entry_id))
            
            fixed_count += 1
        
        print(f"✅ Fixed {fixed_count} corrupted entries")
        
        # Also ensure all remaining time fields are NULL
        cursor.execute("""
            UPDATE logbook_entry 
            SET takeoff_time = NULL, landing_time = NULL 
            WHERE takeoff_time IS NOT NULL OR landing_time IS NOT NULL
        """)
        
        time_cleanup_count = cursor.rowcount
        print(f"✅ Cleared {time_cleanup_count} remaining time field entries")
        
        # Commit transaction
        conn.commit()
        
        # Verify the cleanup
        cursor.execute("SELECT COUNT(*) FROM logbook_entry WHERE user_id LIKE '%:%' OR device_id LIKE '%:%'")
        remaining_corrupted = cursor.fetchone()[0]
        
        if remaining_corrupted == 0:
            print("✅ Cleanup successful - no more corrupted data")
            conn.close()
            return True
        else:
            print(f"⚠️  Still {remaining_corrupted} entries with corruption - may need manual review")
            conn.close()
            return True
            
    except sqlite3.Error as e:
        print(f"❌ SQLite error during cleanup: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during cleanup: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def main():
    """Main cleanup function."""
    print("=" * 60)
    print("CLEANUP: Fix corrupted logbook entry data")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = cleanup_corrupted_data()
    
    print()
    if success:
        print("🎉 Cleanup completed successfully!")
        print("   Corrupted data has been fixed")
        print("   Admin logbook page should now work")
    else:
        print("💥 Cleanup failed!")
        print("   Please check the error messages above")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
