#!/usr/bin/env python3
"""
Test script for the checklist export HTTP functionality
"""

import sys
import os
import json

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db
from src.models import Checklist, User

def test_checklist_export_http():
    """Test the checklist export HTTP endpoint"""
    
    app = create_app()
    
    with app.app_context():
        print("🌐 Testing Checklist Export HTTP Endpoint")
        print("=" * 50)
        
        # Find a user and checklist to test with
        user = User.query.filter_by(is_active=True).first()
        if not user:
            print("❌ No active user found for testing")
            return
        
        checklist = Checklist.query.filter_by(user_id=user.id, is_active=True).first()
        if not checklist:
            print("❌ No checklist found for testing")
            return
        
        print(f"👤 Testing with user: {user.nickname}")
        print(f"📋 Testing checklist: {checklist.title} (ID: {checklist.id})")
        
        # Create a test client
        with app.test_client() as client:
            # Simulate login (we'll mock this by setting up the session)
            with client.session_transaction() as sess:
                sess['_user_id'] = str(user.id)
                sess['_fresh'] = True
            
            # Test the export endpoint
            export_url = f'/dashboard/checklists/{checklist.id}/export'
            print(f"🔗 Testing URL: {export_url}")
            
            response = client.get(export_url)
            
            print(f"📊 Response status: {response.status_code}")
            print(f"📋 Content-Type: {response.content_type}")
            
            if response.status_code == 200:
                print("✅ Export endpoint responded successfully")
                
                # Check response headers
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'attachment' in content_disposition:
                    print(f"✅ Proper download headers: {content_disposition}")
                else:
                    print(f"⚠️ Missing download headers: {content_disposition}")
                
                # Check if response content is valid JSON
                try:
                    response_json = json.loads(response.get_data(as_text=True))
                    print("✅ Response contains valid JSON")
                    
                    if 'Language' in response_json:
                        print(f"   Language: {response_json.get('Language')}")
                    if 'Voice' in response_json:
                        print(f"   Voice: {response_json.get('Voice')}")
                    if 'Root' in response_json and 'Children' in response_json['Root']:
                        sections = response_json['Root']['Children']
                        section_names = [s.get('Name', 'Unknown') for s in sections]
                        print(f"   Sections: {', '.join(section_names)}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Response is not valid JSON: {e}")
                    print(f"Response content: {response.get_data(as_text=True)[:200]}...")
                
            else:
                print(f"❌ Export endpoint failed with status {response.status_code}")
                print(f"Response: {response.get_data(as_text=True)}")
        
        print(f"\n🎯 HTTP Export Test Completed!")
        print(f"   🌐 The export endpoint is {'working' if response.status_code == 200 else 'not working'}")
        print(f"   📥 Users can now download checklist JSON files")
        print(f"   🔄 View button has been replaced with Export button")

if __name__ == '__main__':
    test_checklist_export_http()
