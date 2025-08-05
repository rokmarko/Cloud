#!/usr/bin/env python3
"""
Migration script to add the InstrumentLayout table to the database.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app, db
from models import InstrumentLayout

def migrate_instrument_layout_table():
    """Add the InstrumentLayout table to the database."""
    app = create_app()
    
    with app.app_context():
        print("🔧 Adding InstrumentLayout table to database...")
        
        try:
            # Create the table
            db.create_all()
            print("✅ InstrumentLayout table created successfully!")
            
            # Check if table exists by trying to query it
            count = InstrumentLayout.query.count()
            print(f"📊 Current instrument layouts in database: {count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating InstrumentLayout table: {e}")
            return False

if __name__ == "__main__":
    print("🚀 Running InstrumentLayout table migration...")
    print("=" * 50)
    
    success = migrate_instrument_layout_table()
    
    print("=" * 50)
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
