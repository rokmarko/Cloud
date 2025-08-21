#!/usr/bin/env python3
"""
Test script to validate checklist JSON parsing for the printable version.
"""

import json
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_checklist_parsing():
    """Test parsing the provided checklist file."""
    
    # Read the sample checklist
    checklist_file = "/home/rok/Prejemi/checklist_Roko_NG6(2).ckl"
    
    try:
        with open(checklist_file, 'r') as f:
            data = json.load(f)
        
        print("✅ Successfully loaded checklist JSON")
        print(f"Language: {data.get('Language', 'Not specified')}")
        print(f"Voice: {data.get('Voice', 'Not specified')}")
        
        root = data.get('Root', {})
        children = root.get('Children', [])
        
        print(f"\nFound {len(children)} main sections:")
        
        total_checklists = 0
        total_items = 0
        
        for i, section in enumerate(children):
            section_name = section.get('Name', 'Unnamed Section')
            section_type = section.get('Type', 'Unknown')
            section_children = section.get('Children', [])
            
            print(f"\n{i+1}. Section: '{section_name}' (Type: {section_type})")
            print(f"   Contains {len(section_children)} checklists")
            
            for j, checklist in enumerate(section_children):
                if checklist.get('Type') == 1:  # Checklist type
                    checklist_name = checklist.get('Name', 'Unnamed Checklist')
                    items = checklist.get('Items', [])
                    
                    print(f"   - {j+1}. Checklist: '{checklist_name}' ({len(items)} items)")
                    total_checklists += 1
                    total_items += len(items)
                    
                    # Show first few items as example
                    for k, item in enumerate(items[:2]):  # Show first 2 items
                        title = item.get('Title', 'No title')
                        action = item.get('Action', 'No action')
                        print(f"     • {title} → {action}")
                    
                    if len(items) > 2:
                        print(f"     • ... and {len(items) - 2} more items")
        
        print(f"\n📊 Summary:")
        print(f"   Total sections: {len(children)}")
        print(f"   Total checklists: {total_checklists}")
        print(f"   Total items: {total_items}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Checklist file not found: {checklist_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in checklist file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error processing checklist: {e}")
        return False

if __name__ == '__main__':
    success = test_checklist_parsing()
    if success:
        print("\n✅ Checklist parsing test completed successfully!")
        print("The printable checklist feature should work correctly with this format.")
    else:
        print("\n❌ Checklist parsing test failed!")
    
    sys.exit(0 if success else 1)
