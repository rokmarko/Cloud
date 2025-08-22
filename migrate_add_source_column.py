#!/usr/bin/env python3
"""
Database migration script to add 'source' column to Airfield model.
This script adds the source column and updates existing airfields with a default source value.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, Airfield

def migrate_airfield_source():
    """Add source column to Airfield table and set default values."""
    print("Adding 'source' column to Airfield model...")
    
    try:
        with create_app().app_context():
            # Check if column already exists
            result = db.session.execute(db.text("PRAGMA table_info(airfield);")).fetchall()
            columns = [row[1] for row in result]
            
            if 'source' not in columns:
                # Add the source column
                db.session.execute(db.text('ALTER TABLE airfield ADD COLUMN source VARCHAR(100) DEFAULT "legacy";'))
                db.session.commit()
                print("  ✓ Successfully added 'source' column to Airfield table")
            else:
                print("  ℹ️ Column 'source' already exists in the table")
            
            # Update any NULL values to 'legacy'
            result = db.session.execute(db.text("SELECT COUNT(*) FROM airfield WHERE source IS NULL;")).fetchone()
            null_count = result[0] if result else 0
            
            if null_count > 0:
                db.session.execute(db.text("UPDATE airfield SET source = 'legacy' WHERE source IS NULL;"))
                db.session.commit()
                print(f"  ✓ Updated {null_count} records with NULL source to 'legacy'")
            
            # Get total count
            result = db.session.execute(db.text("SELECT COUNT(*) FROM airfield;")).fetchone()
            total_count = result[0] if result else 0
            print(f"  ✓ Total airfields in database: {total_count}")
            
    except Exception as e:
        print(f"  ❌ Error during migration: {e}")
        db.session.rollback()
        return False
    
    return True

if __name__ == '__main__':
    migrate_airfield_source()
