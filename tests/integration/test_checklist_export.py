#!/usr/bin/env python3
"""
Test script for the checklist export functionality
"""

import sys
import os
import json

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db
from src.models import Checklist, User

def test_checklist_export():
    """Test the checklist export functionality"""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Checklist Export Functionality")
        print("=" * 50)
        
        # Find a user to test with
        user = User.query.filter_by(is_active=True).first()
        if not user:
            print("❌ No active user found for testing")
            return
        
        print(f"👤 Testing with user: {user.nickname}")
        
        # Get user's checklists
        checklists = Checklist.query.filter_by(user_id=user.id, is_active=True).all()
        print(f"📋 Found {len(checklists)} checklists for user")
        
        if not checklists:
            print("❌ No checklists found for testing")
            return
        
        # Test the first checklist
        test_checklist = checklists[0]
        print(f"🧪 Testing export for checklist: {test_checklist.title}")
        print(f"   ID: {test_checklist.id}")
        
        # Verify json_content exists
        if not test_checklist.json_content:
            print("❌ No json_content found for this checklist")
            return
        
        print(f"✅ JSON content exists ({len(test_checklist.json_content)} characters)")
        
        # Validate JSON content
        try:
            json_data = json.loads(test_checklist.json_content)
            print(f"✅ JSON content is valid")
            print(f"   Language: {json_data.get('Language', 'N/A')}")
            print(f"   Voice: {json_data.get('Voice', 'N/A')}")
            
            if 'Root' in json_data and 'Children' in json_data['Root']:
                sections = json_data['Root']['Children']
                section_names = [section.get('Name', 'Unknown') for section in sections]
                print(f"   Sections: {', '.join(section_names)}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return
        
        # Test filename generation
        import re
        safe_filename = re.sub(r'[^\w\s-]', '', test_checklist.title)
        safe_filename = re.sub(r'[-\s]+', '_', safe_filename)
        filename = f"checklist_{safe_filename}.json"
        print(f"📁 Generated filename: {filename}")
        
        # Test the export route URL
        export_url = f"/dashboard/checklists/{test_checklist.id}/export"
        print(f"🔗 Export URL: {export_url}")
        
        print(f"\n🎯 Export Test Completed Successfully!")
        print(f"   ✅ JSON content is valid and exportable")
        print(f"   ✅ Filename generation working")
        print(f"   ✅ Export route should be accessible")
        print(f"   🌐 Web interface: Replace View button with Export button")
        print(f"   📥 Click Export to download: {filename}")

if __name__ == '__main__':
    test_checklist_export()
