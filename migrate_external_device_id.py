#!/usr/bin/env python3
"""
Migration script to add external_device_id field to Device model
"""

import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import Device

def migrate_device_external_id():
    """Add external_device_id column to Device table if it doesn't exist."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column already exists
            inspector = db.inspect(db.engine)
            columns = [c['name'] for c in inspector.get_columns('device')]
            
            if 'external_device_id' not in columns:
                print("Adding external_device_id column to Device table...")
                
                # Add the column using raw SQL
                with db.engine.connect() as conn:
                    conn.execute(db.text(
                        "ALTER TABLE device ADD COLUMN external_device_id VARCHAR(100)"
                    ))
                    conn.commit()
                
                print("✅ Successfully added external_device_id column")
            else:
                print("✅ external_device_id column already exists")
            
            print("\n📊 Current devices:")
            devices = Device.query.all()
            if devices:
                for device in devices:
                    external_id = getattr(device, 'external_device_id', None) or 'Not set'
                    print(f"  - {device.name} (ID: {device.id}) - External ID: {external_id}")
            else:
                print("  No devices found")
                
        except Exception as e:
            print(f"❌ Error during migration: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Device external_device_id migration...")
    success = migrate_device_external_id()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
