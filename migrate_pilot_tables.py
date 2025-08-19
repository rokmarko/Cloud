#!/usr/bin/env python3
"""
Database migration to add Pilot table and pilot_name to LogbookEntry.

This migration:
1. Creates the Pilot table
2. Adds pilot_name column to logbook_entry table
3. Handles unique constraints
"""

import sys
import os
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrate_add_pilot_tables():
    """Add Pilot table and pilot_name column to LogbookEntry."""
    
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'kanardiacloud.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        print("🔄 Starting pilot tables migration...")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(logbook_entry)")
        columns = [column[1] for column in cursor.fetchall()]
        
        pilot_name_exists = 'pilot_name' in columns
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pilot'")
        pilot_table_exists = cursor.fetchone() is not None
        
        if pilot_table_exists and pilot_name_exists:
            print("✅ Migration already applied - Pilot table and pilot_name column exist")
            conn.close()
            return True
        
        # Create Pilot table if it doesn't exist
        if not pilot_table_exists:
            print("📝 Creating Pilot table...")
            cursor.execute("""
                CREATE TABLE pilot (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    pilot_name VARCHAR(100) NOT NULL,
                    user_id INTEGER NOT NULL,
                    device_id INTEGER NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES user (id),
                    FOREIGN KEY(device_id) REFERENCES device (id),
                    CONSTRAINT _pilot_device_uc UNIQUE (pilot_name, device_id)
                )
            """)
            print("✅ Pilot table created")
        
        # Add pilot_name column to logbook_entry if it doesn't exist
        if not pilot_name_exists:
            print("📝 Adding pilot_name column to logbook_entry...")
            cursor.execute("ALTER TABLE logbook_entry ADD COLUMN pilot_name VARCHAR(100)")
            print("✅ pilot_name column added")
        
        # Commit changes
        conn.commit()
        
        print("🎉 Migration completed successfully!")
        
        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM logbook_entry")
        total_entries = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pilot")
        pilot_mappings = cursor.fetchone()[0]
        
        print(f"📊 Current statistics:")
        print(f"   • Total logbook entries: {total_entries}")
        print(f"   • Pilot mappings: {pilot_mappings}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False


def show_help():
    """Show help information."""
    print("Pilot Tables Migration Script")
    print("=" * 30)
    print()
    print("This migration adds:")
    print("• Pilot table to map users to devices with pilot names")
    print("• pilot_name column to logbook_entry table")
    print("• Unique constraints for pilot names per device")
    print()
    print("Usage:")
    print("  python migrate_pilot_tables.py        # Run migration")
    print("  python migrate_pilot_tables.py --help # Show this help")
    print()
    print("The migration is safe to run multiple times.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
    else:
        print("🚀 Pilot Tables Migration")
        print("=" * 25)
        print()
        
        success = migrate_add_pilot_tables()
        
        if success:
            print("\n✅ Migration completed successfully!")
            print("You can now:")
            print("• Create pilot mappings for devices")
            print("• Use pilot names in logbook entries")
            print("• Link logbook entries to specific pilots")
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)
