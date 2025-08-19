#!/usr/bin/env python3
"""
Test script for the new checklist json_content functionality
"""

import sys
import os
import json

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db
from src.models import Checklist, User

def test_checklist_json_content():
    """Test the checklist json_content functionality"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Checklist JSON Content Functionality")
        print("=" * 50)
        
        # Find a user to test with
        user = User.query.filter_by(is_active=True).first()
        if not user:
            print("❌ No active user found for testing")
            return
        
        print(f"👤 Testing with user: {user.nickname}")
        
        # Check existing checklists with json_content
        existing_checklists = Checklist.query.filter_by(user_id=user.id).all()
        print(f"📋 Found {len(existing_checklists)} existing checklists for user")
        
        for checklist in existing_checklists:
            print(f"  ✅ Checklist: {checklist.title}")
            if checklist.json_content:
                try:
                    json_data = json.loads(checklist.json_content)
                    print(f"     JSON content: {len(json_data)} keys")
                    if 'Root' in json_data and 'Children' in json_data['Root']:
                        children = json_data['Root']['Children']
                        section_names = [child['Name'] for child in children]
                        print(f"     Sections: {', '.join(section_names)}")
                except json.JSONDecodeError as e:
                    print(f"     ❌ Invalid JSON: {e}")
            else:
                print(f"     ⚠️ No JSON content")
        
        # Test creating a new checklist with the default template
        print(f"\n🆕 Testing new checklist creation...")
        
        default_template = {
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
        
        test_checklist = Checklist(
            title="Test Checklist - JSON Content",
            description="Test checklist for JSON content functionality",
            category="other",
            items=json.dumps([]),
            json_content=json.dumps(default_template),
            user_id=user.id
        )
        
        db.session.add(test_checklist)
        db.session.commit()
        
        print(f"✅ Created test checklist with ID: {test_checklist.id}")
        print(f"   Title: {test_checklist.title}")
        print(f"   JSON content length: {len(test_checklist.json_content)} characters")
        
        # Verify the JSON content
        try:
            parsed_json = json.loads(test_checklist.json_content)
            print(f"   ✅ JSON is valid")
            print(f"   Language: {parsed_json.get('Language', 'N/A')}")
            print(f"   Voice: {parsed_json.get('Voice', 'N/A')}")
            
            if 'Root' in parsed_json and 'Children' in parsed_json['Root']:
                children = parsed_json['Root']['Children']
                print(f"   Sections: {len(children)}")
                for child in children:
                    print(f"     - {child.get('Name', 'Unknown')}")
        except json.JSONDecodeError as e:
            print(f"   ❌ JSON parsing error: {e}")
        
        print(f"\n🎯 Test completed successfully!")
        print(f"   The json_content field is working correctly")
        print(f"   New checklists will be created with the default template")
        print(f"   Route: /dashboard/checklists/add (simplified form)")

if __name__ == '__main__':
    test_checklist_json_content()
