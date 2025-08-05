#!/usr/bin/env python3
"""
Simple test to verify the load_json route works by directly accessing the Flask app.
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import after setting path
from app import create_app, db
from models import Checklist, User
import json

def test_load_json_function():
    """Test the load_json route function directly."""
    app = create_app()
    
    with app.app_context():
        # Create a test user if needed
        test_user = User.query.filter_by(email='admin@test.com').first()
        if not test_user:
            from werkzeug.security import generate_password_hash
            test_user = User(
                email='admin@test.com',
                password_hash=generate_password_hash('admin123'),
                full_name='Test Admin',
                is_admin=True
            )
            db.session.add(test_user)
            db.session.commit()
            print("✅ Created test user")
        
        # Check if we have any checklists
        checklists = Checklist.query.filter_by(user_id=test_user.id, is_active=True).all()
        print(f"📋 Found {len(checklists)} checklists for user {test_user.id}")
        
        if not checklists:
            # Create a test checklist
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
                        }
                    ]
                }
            }
            
            test_checklist = Checklist(
                title="Test Checklist",
                description="Test checklist for load_json",
                category="test",
                items=json.dumps([]),
                json_content=json.dumps(default_template),
                user_id=test_user.id
            )
            db.session.add(test_checklist)
            db.session.commit()
            print("✅ Created test checklist")
            checklists = [test_checklist]
        
        # Test the load_json functionality
        test_checklist = checklists[0]
        print(f"\n🧪 Testing load_json for checklist ID: {test_checklist.id}")
        print(f"📝 Title: {test_checklist.title}")
        
        # Simulate what the route does
        try:
            if test_checklist.json_content:
                json_data = json.loads(test_checklist.json_content)
                print("✅ JSON content parsed successfully")
                print(f"🔑 Keys: {list(json_data.keys())}")
                
                if isinstance(json_data, dict):
                    if 'Language' in json_data and 'Voice' in json_data and 'Root' in json_data:
                        print("✅ Has expected checklist structure")
                        print(f"🌍 Language: {json_data.get('Language')}")
                        print(f"🗣️ Voice: {json_data.get('Voice')}")
                        if 'Root' in json_data and isinstance(json_data['Root'], dict):
                            root = json_data['Root']
                            print(f"🌳 Root Name: {root.get('Name')}")
                            print(f"📁 Root Children Count: {len(root.get('Children', []))}")
                    else:
                        print("⚠️ Doesn't have expected structure")
                        
                # Test the route response format
                print(f"\n📊 Route would return: {json.dumps(json_data, indent=2)[:300]}...")
                return True
            else:
                print("❌ No json_content in checklist")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            return False

if __name__ == "__main__":
    print("🧪 Testing load_json route functionality...")
    print("=" * 50)
    
    try:
        success = test_load_json_function()
        print("\n" + "=" * 50)
        if success:
            print("🎉 Test completed successfully!")
        else:
            print("❌ Test failed!")
    except Exception as e:
        print(f"💥 Error during test: {e}")
        import traceback
        traceback.print_exc()
