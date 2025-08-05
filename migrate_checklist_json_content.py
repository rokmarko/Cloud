#!/usr/bin/env python3
"""
Database migration to add json_content field to Checklist model
"""

import sys
import os
import json

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db
from src.models import Checklist

# Default checklist template based on New.json
DEFAULT_CHECKLIST_TEMPLATE = {
    "Language": "en-us",
    "Voice": "Linda",
    "Root": {
        "Type": 0,
        "Name": "Root",
        "Children": [
            {
                "Type": 0,
                "Name": "Pre-flight",
                "Children": []
            },
            {
                "Type": 0,
                "Name": "In-flight",
                "Children": []
            },
            {
                "Type": 0,
                "Name": "Post-flight",
                "Children": []
            },
            {
                "Type": 0,
                "Name": "Emergency",
                "Children": []
            },
            {
                "Type": 0,
                "Name": "Reference",
                "Children": []
            }
        ]
    }
}

def migrate_checklist_json_content():
    """Add json_content field to existing checklists"""
    
    app = create_app()
    
    with app.app_context():
        # First, try to add the column (this might fail if it already exists)
        try:
            # Use raw SQL to add the column
            with db.engine.connect() as conn:
                conn.execute(db.text("ALTER TABLE checklist ADD COLUMN json_content TEXT"))
                conn.commit()
            print("✅ Added json_content column to checklist table")
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️  json_content column already exists")
            else:
                print(f"❌ Error adding column: {e}")
                return
        
        # Update existing checklists that don't have json_content
        checklists = Checklist.query.filter(
            (Checklist.json_content == None) | (Checklist.json_content == '')
        ).all()
        
        print(f"📋 Found {len(checklists)} checklists to update")
        
        for checklist in checklists:
            # Set default template for each checklist
            checklist.json_content = json.dumps(DEFAULT_CHECKLIST_TEMPLATE)
            print(f"  ✅ Updated checklist: {checklist.title}")
        
        # Commit the changes
        db.session.commit()
        
        print(f"🎯 Migration completed successfully!")
        print(f"   Updated {len(checklists)} checklists with default JSON content")

if __name__ == '__main__':
    migrate_checklist_json_content()
