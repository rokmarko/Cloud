#!/usr/bin/env python3
"""
Database migration script to add instrument_type column to instrument_layout table
"""

import sqlite3
import os
import sys

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def migrate_add_instrument_type():
    """Add instrument_type column to instrument_layout table."""
    
    # Path to the database
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'kanardiacloud.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Adding instrument_type column to instrument_layout table...")
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(instrument_layout)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'instrument_type' in columns:
            print("✅ Column instrument_type already exists!")
            return True
        
        # Add the new column with default value
        cursor.execute("""
            ALTER TABLE instrument_layout 
            ADD COLUMN instrument_type VARCHAR(50) NOT NULL DEFAULT 'digi'
        """)
        
        # Update existing records to have a proper instrument type
        cursor.execute("""
            UPDATE instrument_layout 
            SET instrument_type = 'digi' 
            WHERE instrument_type IS NULL OR instrument_type = ''
        """)
        
        conn.commit()
        print("✅ Successfully added instrument_type column to instrument_layout table")
        print("✅ Updated existing records with default instrument type 'digi'")
        
        # Verify the migration
        cursor.execute("SELECT COUNT(*) FROM instrument_layout")
        count = cursor.fetchone()[0]
        print(f"📊 Total instrument layouts in database: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, title, instrument_type FROM instrument_layout LIMIT 5")
            layouts = cursor.fetchall()
            print("📝 Sample layouts:")
            for layout in layouts:
                print(f"   - ID {layout[0]}: {layout[1]} (Type: {layout[2]})")
        
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
    """Main migration function."""
    print("🚀 Starting instrument_type column migration...")
    print("=" * 60)
    
    success = migrate_add_instrument_type()
    
    print("=" * 60)
    if success:
        print("🎉 Migration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Restart the Flask application")
        print("2. Test creating new instrument layouts with types")
        print("3. Verify existing layouts still work properly")
    else:
        print("❌ Migration failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check if the database file exists")
        print("2. Ensure no other processes are using the database")
        print("3. Check file permissions")

if __name__ == "__main__":
    main()
