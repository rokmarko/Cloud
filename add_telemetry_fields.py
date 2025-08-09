#!/usr/bin/env python3
"""
Migration script to add telemetry fields to Device table
"""

import os
import sys

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db

def add_telemetry_fields():
    """Add telemetry fields to Device table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Add telemetry fields to device table
            print("Adding telemetry fields to device table...")
            
            with db.engine.connect() as connection:
                # Add new columns
                connection.execute(db.text('ALTER TABLE device ADD COLUMN last_telemetry_update DATETIME'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN fuel_quantity FLOAT'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN status VARCHAR(20)'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN status_description VARCHAR(50)'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN altitude FLOAT'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN latitude FLOAT'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN longitude FLOAT'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN speed FLOAT'))
                connection.execute(db.text('ALTER TABLE device ADD COLUMN location_description VARCHAR(200)'))
                connection.commit()
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")
            return False
    
    return True

if __name__ == '__main__':
    print("Starting migration to add telemetry fields...")
    success = add_telemetry_fields()
    
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
