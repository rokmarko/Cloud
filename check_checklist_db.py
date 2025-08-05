#!/usr/bin/env python3
"""
Check checklist database contents and test the load_json route.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app, db
from models import Checklist, User
import json

def check_checklists():
    """Check what checklists exist in the database."""
    app = create_app()
    
    with app.app_context():
        print("📋 Checking checklists in database...")
        
        checklists = Checklist.query.filter_by(is_active=True).all()
        print(f"📊 Found {len(checklists)} active checklists")
        
        for checklist in checklists:
            print(f"\n📄 Checklist ID: {checklist.id}")
            print(f"📝 Title: {checklist.title}")
            print(f"👤 User ID: {checklist.user_id}")
            print(f"📅 Created: {checklist.created_at}")
            
            # Check json_content
            if checklist.json_content:
                print(f"✅ Has json_content: {len(checklist.json_content)} characters")
                try:
                    parsed = json.loads(checklist.json_content)
                    print(f"✅ JSON is valid")
                    print(f"🔑 Keys: {list(parsed.keys()) if isinstance(parsed, dict) else 'Not a dict'}")
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parse error: {e}")
            else:
                print("❌ No json_content")
        
        # Also check users
        print(f"\n👥 Checking users...")
        users = User.query.all()
        for user in users:
            print(f"👤 User ID: {user.id}, Email: {user.email}, Name: {user.full_name}")

if __name__ == "__main__":
    check_checklists()
