#!/usr/bin/env python3
"""
Migration script to add message field to Event table
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.app import create_app, db
from sqlalchemy import text

def main():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column already exists
            result = db.session.execute(text("""
                SELECT name FROM pragma_table_info('event') WHERE name='message';
            """)).fetchone()
            
            if result:
                print("Message column already exists in Event table.")
                return
            
            # Add the message column
            print("Adding message column to Event table...")
            db.session.execute(text("""
                ALTER TABLE event ADD COLUMN message VARCHAR(500);
            """))
            
            db.session.commit()
            print("Successfully added message column to Event table.")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during migration: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    main()
