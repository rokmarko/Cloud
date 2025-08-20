#!/usr/bin/env python3
"""
Migration script to add flight_points_fetched field to LogbookEntry model.
This script adds the new column to existing logbook entries.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models import db, LogbookEntry
from src.app import create_app
from sqlalchemy import text

def migrate_flight_points_fetched_field():
    """Add flight_points_fetched field to LogbookEntry table."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('logbook_entry')]
            
            if 'flight_points_fetched' in columns:
                print("Column 'flight_points_fetched' already exists in logbook_entry table")
                return
            
            print("Adding flight_points_fetched column to logbook_entry table...")
            
            # Add the column with default value False
            with db.engine.connect() as conn:
                conn.execute(text(
                    "ALTER TABLE logbook_entry ADD COLUMN flight_points_fetched BOOLEAN DEFAULT FALSE"
                ))
                
                # Update existing entries to False (explicit)
                conn.execute(text(
                    "UPDATE logbook_entry SET flight_points_fetched = FALSE WHERE flight_points_fetched IS NULL"
                ))
                
                conn.commit()
            
            print("Successfully added flight_points_fetched column to logbook_entry table")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            raise

if __name__ == '__main__':
    migrate_flight_points_fetched_field()
    print("Migration completed successfully!")
