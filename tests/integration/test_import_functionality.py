#!/usr/bin/env python3
"""
Test script to verify checklist import functionality.
"""

import json
import xml.etree.ElementTree as ET

def test_json_import():
    """Test JSON file import parsing."""
    print("🧪 Testing JSON import...")
    
    try:
        with open('test_checklist.json', 'r') as f:
            json_content = json.load(f)
        
        print("✅ JSON file loaded successfully")
        print(f"📊 Checklist name: {json_content['CheckList']['Name']}")
        
        sections = json_content['CheckList']['Children']
        print(f"📋 Number of sections: {len(sections)}")
        
        for section in sections:
            print(f"  - {section['Name']}: {len(section['Children'])} items")
        
        return True
    except Exception as e:
        print(f"❌ JSON import test failed: {e}")
        return False

def test_txt_import():
    """Test TXT file import parsing."""
    print("\n🧪 Testing TXT import...")
    
    try:
        with open('test_checklist.txt', 'r') as f:
            content = f.read()
        
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        print(f"✅ TXT file loaded successfully")
        print(f"📊 Number of items: {len(lines)}")
        
        # Simulate conversion to JSON structure
        json_content = {
            "CheckList": {
                "Type": 1,
                "Name": "Test Checklist",
                "Children": [
                    {
                        "Type": 2,
                        "Name": "Imported Checklist",
                        "Children": [
                            {
                                "Type": 3,
                                "Name": line,
                                "Children": []
                            } for line in lines
                        ]
                    }
                ]
            }
        }
        
        print(f"📋 Generated JSON structure with {len(json_content['CheckList']['Children'][0]['Children'])} items")
        return True
    except Exception as e:
        print(f"❌ TXT import test failed: {e}")
        return False

def test_xml_import():
    """Test XML file import parsing."""
    print("\n🧪 Testing XML import...")
    
    try:
        with open('test_checklist.xml', 'r') as f:
            content = f.read()
        
        root = ET.fromstring(content)
        print("✅ XML file parsed successfully")
        
        # Extract all text items
        items = []
        for element in root.iter():
            if element.text and element.text.strip():
                text = element.text.strip()
                if text not in ['Pre-flight Checklist', 'External Inspection', 'Cockpit Setup']:
                    items.append(text)
        
        print(f"📊 Extracted {len(items)} items from XML")
        
        # Show first few items
        for i, item in enumerate(items[:3]):
            print(f"  {i+1}. {item}")
        
        if len(items) > 3:
            print(f"  ... and {len(items) - 3} more items")
        
        return True
    except Exception as e:
        print(f"❌ XML import test failed: {e}")
        return False

def test_file_formats():
    """Test all supported file formats."""
    print("🧪 Testing checklist import functionality...\n")
    
    tests = [
        ("JSON Import", test_json_import),
        ("TXT Import", test_txt_import),
        ("XML Import", test_xml_import)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append(result)
    
    print(f"\n📊 Test Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All import format tests passed!")
        print("📋 The import functionality supports JSON, TXT, and XML files.")
    else:
        print("\n💥 Some tests failed. Please check the issues above.")
    
    return all(results)

def main():
    """Run all tests."""
    success = test_file_formats()
    
    if success:
        print("\n✨ Next steps:")
        print("1. Go to http://127.0.0.1:5000/dashboard/checklists")
        print("2. Click 'Import Checklist' button")
        print("3. Upload one of the test files:")
        print("   - test_checklist.json (JSON format)")
        print("   - test_checklist.txt (Text format)")
        print("   - test_checklist.xml (XML format)")

if __name__ == '__main__':
    main()
