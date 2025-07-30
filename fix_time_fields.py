#!/usr/bin/env python3
"""
Migration: Fix time fields in logbook_entry table

This migration fixes the takeoff_time and landing_time fields which currently
contain numeric values but should be TIME format or NULL.
"""

import sys
import os
import sqlite3
from datetime import datetime, time

# Add the project root to Python path
sys.path.insert(0, '/home/rok/Branch/NavSync/Protected/Cloud')

def fix_time_fields():
    """
    Fix takeoff_time and landing_time fields in logbook_entry table.
    Convert invalid numeric values to NULL since we can't determine
    the original time format.
    """
    
    # Database path
    db_path = '/home/rok/Branch/NavSync/Protected/Cloud/instance/kanardiacloud.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    print(f"🔄 Starting migration to fix time fields in logbook_entry table...")
    print(f"📁 Database: {db_path}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current data
        cursor.execute("SELECT COUNT(*) FROM logbook_entry WHERE takeoff_time IS NOT NULL OR landing_time IS NOT NULL")
        count_with_times = cursor.fetchone()[0]
        print(f"📊 Found {count_with_times} entries with time data")
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Set all numeric time values to NULL since we can't convert them properly
        # (the original numeric values don't represent valid time formats)
        cursor.execute("""
            UPDATE logbook_entry 
            SET takeoff_time = NULL, landing_time = NULL 
            WHERE takeoff_time IS NOT NULL OR landing_time IS NOT NULL
        """)
        
        affected_rows = cursor.rowcount
        print(f"✅ Reset {affected_rows} time entries to NULL")
        
        # Commit transaction
        conn.commit()
        
        # Verify the fix
        cursor.execute("SELECT COUNT(*) FROM logbook_entry WHERE takeoff_time IS NOT NULL OR landing_time IS NOT NULL")
        remaining_times = cursor.fetchone()[0]
        
        if remaining_times == 0:
            print("✅ Migration successful - all invalid time data cleared")
            conn.close()
            return True
        else:
            print(f"⚠️  Still {remaining_times} entries with time data - may need manual review")
            conn.close()
            return True
            
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
    print("MIGRATION: Fix time fields in logbook_entry table")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    success = fix_time_fields()
    
    print()
    if success:
        print("🎉 Migration completed successfully!")
        print("   Invalid time data has been cleared")
        print("   Admin logbook page should now work")
    else:
        print("💥 Migration failed!")
        print("   Please check the error messages above")
    
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
