#!/usr/bin/env python3
"""
Database migration to add NOTAM tables and home_area field to User table.
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import User, Notam, NotamUpdateLog, NotamNotificationSent

def migrate_notam_tables():
    """Create NOTAM-related tables and add home_area column to User table."""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Starting NOTAM database migration...")
            
            # Check if home_area column exists in User table
            inspector = db.inspect(db.engine)
            user_columns = [col['name'] for col in inspector.get_columns('user')]
            
            if 'home_area' not in user_columns:
                print("Adding home_area column to User table...")
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE user ADD COLUMN home_area VARCHAR(4)'))
                    conn.commit()
                print("✓ Added home_area column to User table")
            else:
                print("✓ home_area column already exists in User table")
            
            # Create all tables (will only create missing ones)
            print("Creating NOTAM tables...")
            db.create_all()
            
            # Check if tables were created successfully
            tables = inspector.get_table_names()
            notam_tables = ['notams', 'notam_update_logs', 'notam_notifications_sent']
            
            for table in notam_tables:
                if table in tables:
                    print(f"✓ Table '{table}' created/exists")
                else:
                    print(f"✗ Failed to create table '{table}'")
            
            print("\n🎉 NOTAM database migration completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            return False


if __name__ == "__main__":
    success = migrate_notam_tables()
    sys.exit(0 if success else 1)
