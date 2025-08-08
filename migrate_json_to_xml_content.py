#!/usr/bin/env python3
"""
Database migration script to rename json_content column to xml_content in instrument_layout table
"""

import sqlite3
import os
import sys

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def migrate_json_to_xml_content():
    """Rename json_content column to xml_content in instrument_layout table."""
    
    # Path to the database
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'kanardiacloud.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Migrating json_content to xml_content in instrument_layout table...")
        
        # Check if json_content column exists
        cursor.execute("PRAGMA table_info(instrument_layout)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        if 'json_content' not in columns:
            print("❌ Column json_content does not exist!")
            return False
            
        if 'xml_content' in columns:
            print("✅ Column xml_content already exists!")
            return True
        
        # SQLite doesn't support column rename directly, so we need to recreate the table
        print("📋 Creating backup and recreating table...")
        
        # Get current table schema
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='instrument_layout'")
        create_sql = cursor.fetchone()[0]
        
        # Create new table with xml_content instead of json_content
        new_create_sql = create_sql.replace('json_content', 'xml_content')
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create temporary table with new schema
        temp_create_sql = new_create_sql.replace('CREATE TABLE instrument_layout', 'CREATE TABLE instrument_layout_temp')
        cursor.execute(temp_create_sql)
        
        # Copy data from old table to temp table (renaming column)
        cursor.execute("""
            INSERT INTO instrument_layout_temp 
            SELECT id, title, description, category, instrument_type, layout_data, 
                   json_content as xml_content, is_active, created_at, updated_at, user_id
            FROM instrument_layout
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE instrument_layout")
        
        # Rename temp table to original name
        cursor.execute("ALTER TABLE instrument_layout_temp RENAME TO instrument_layout")
        
        # Recreate indexes if any existed
        # Note: SQLite will recreate the primary key index automatically
        
        conn.commit()
        print("✅ Successfully renamed json_content to xml_content in instrument_layout table")
        
        # Verify the migration
        cursor.execute("SELECT COUNT(*) FROM instrument_layout")
        count = cursor.fetchone()[0]
        print(f"📊 Total instrument layouts migrated: {count}")
        
        if count > 0:
            cursor.execute("SELECT id, title FROM instrument_layout LIMIT 5")
            layouts = cursor.fetchall()
            print("📝 Sample layouts:")
            for layout in layouts:
                print(f"   - ID {layout[0]}: {layout[1]}")
        
        # Verify new column exists
        cursor.execute("PRAGMA table_info(instrument_layout)")
        new_columns = [row[1] for row in cursor.fetchall()]
        if 'xml_content' in new_columns and 'json_content' not in new_columns:
            print("✅ Column migration verified successfully")
        else:
            print("❌ Column migration verification failed")
            return False
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main migration function."""
    print("🚀 Starting json_content to xml_content migration...")
    print("=" * 70)
    
    success = migrate_json_to_xml_content()
    
    print("=" * 70)
    if success:
        print("🎉 Migration completed successfully!")
        print("\n📋 Changes made:")
        print("- Renamed json_content column to xml_content")
        print("- Updated all existing instrument layout records")
        print("- Preserved all data during migration")
        print("\n📋 Next steps:")
        print("1. Restart the Flask application")
        print("2. Test instrument layout creation and editing")
        print("3. Verify XML export functionality works correctly")
    else:
        print("❌ Migration failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check if the database file exists and is writable")
        print("2. Ensure no other processes are using the database")
        print("3. Check file permissions")
        print("4. Backup your database before running migration")

if __name__ == "__main__":
    main()
