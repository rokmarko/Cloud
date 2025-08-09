#!/usr/bin/env python3
"""
Migration script to remove category fields from Checklist and InstrumentLayout tables
"""

import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db

def remove_category_fields():
    """Remove category columns from Checklist and InstrumentLayout tables."""
    app = create_app()
    
    with app.app_context():
        try:
            # Remove category column from checklist table
            print("Removing category column from checklist table...")
            with db.engine.connect() as connection:
                connection.execute(db.text('ALTER TABLE checklist DROP COLUMN category'))
                connection.commit()
            
            # Remove category column from instrument_layout table  
            print("Removing category column from instrument_layout table...")
            with db.engine.connect() as connection:
                connection.execute(db.text('ALTER TABLE instrument_layout DROP COLUMN category'))
                connection.commit()
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("Starting migration to remove category fields...")
    success = remove_category_fields()
    
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
