#!/usr/bin/env python3
"""
Test script to verify the clear synced entries functionality
"""

import requests
import sys

def test_clear_synced_entries():
    """Test the clear synced entries endpoint"""
    
    # First, check if we're logged in and can access the admin area
    session = requests.Session()
    
    # Try to access the sync page (this will require login)
    response = session.get('http://localhost:5000/admin/sync')
    
    if response.status_code == 200:
        print("✅ Successfully accessed admin sync page")
        
        # Check if the page contains the clear button
        if 'Clear Synced Entries' in response.text:
            print("✅ Clear Synced Entries button found on page")
            
            # Extract synced entries count from the page
            import re
            count_match = re.search(r'Clear Synced Entries \((\d+)\)', response.text)
            if count_match:
                count = int(count_match.group(1))
                print(f"✅ Found {count} synced entries ready to be cleared")
                
                if count > 0:
                    print("⚠️  Clear button should be enabled")
                else:
                    print("ℹ️  Clear button should be disabled (no entries)")
                    
            else:
                print("❌ Could not extract synced entries count")
        else:
            print("❌ Clear Synced Entries button not found")
    else:
        print(f"❌ Failed to access admin page (status: {response.status_code})")
        print("ℹ️  This is expected if not logged in as admin")

if __name__ == "__main__":
    print("🧪 Testing Clear Synced Entries functionality...")
    test_clear_synced_entries()
