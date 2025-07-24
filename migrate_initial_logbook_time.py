#!/usr/bin/env python3
"""
Migration script to add InitialLogbookTime table
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import InitialLogbookTime

def create_initial_logbook_time_table():
    """Create the InitialLogbookTime table."""
    app = create_app()
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            print("✅ InitialLogbookTime table created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            raise

if __name__ == '__main__':
    print("🔄 Creating InitialLogbookTime table...")
    create_initial_logbook_time_table()
    print("✅ Migration completed!")
