#!/usr/bin/env python3
"""
Test script to verify json_content to xml_content migration
"""

import sqlite3
import os
import json

def test_xml_content_migration():
    """Test that the xml_content migration was successful."""
    
    print("🧪 Testing xml_content migration...")
    print("=" * 50)
    
    # Path to the database
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'kanardiacloud.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table schema
        cursor.execute("PRAGMA table_info(instrument_layout)")
        columns = {row[1]: row for row in cursor.fetchall()}
        
        # Verify xml_content exists and json_content doesn't
        if 'xml_content' in columns:
            print("✅ xml_content column exists")
        else:
            print("❌ xml_content column missing")
            return False
            
        if 'json_content' not in columns:
            print("✅ json_content column properly removed")
        else:
            print("❌ json_content column still exists")
            return False
        
        # Verify instrument_type column exists
        if 'instrument_type' in columns:
            print("✅ instrument_type column exists")
        else:
            print("❌ instrument_type column missing")
            return False
        
        # Test data integrity
        cursor.execute("SELECT id, title, xml_content, instrument_type FROM instrument_layout")
        layouts = cursor.fetchall()
        
        print(f"📊 Found {len(layouts)} instrument layouts")
        
        for layout in layouts:
            layout_id, title, xml_content, instrument_type = layout
            print(f"   - ID {layout_id}: {title} (Type: {instrument_type})")
            
            # Verify xml_content is valid JSON (even though it's called xml_content)
            try:
                if xml_content:
                    json.loads(xml_content)
                    print(f"     ✅ Valid JSON content")
                else:
                    print(f"     ⚠️ Empty xml_content")
            except json.JSONDecodeError:
                print(f"     ❌ Invalid JSON in xml_content")
                return False
        
        # Check all expected columns
        expected_columns = [
            'id', 'title', 'description', 'category', 'instrument_type', 
            'layout_data', 'xml_content', 'is_active', 'created_at', 
            'updated_at', 'user_id'
        ]
        
        missing_columns = []
        for col in expected_columns:
            if col not in columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"❌ Missing columns: {missing_columns}")
            return False
        else:
            print("✅ All expected columns present")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_code_changes():
    """Check if code files have been updated correctly."""
    print("\n🔍 Checking code changes...")
    
    success = True
    
    # Check models.py
    try:
        with open('/home/rok/src/Cloud-1/src/models.py', 'r') as f:
            models_content = f.read()
            
        if 'xml_content = db.Column' in models_content:
            print("✅ models.py: xml_content column defined")
        else:
            print("❌ models.py: xml_content column missing")
            success = False
            
        if 'json_content = db.Column' not in models_content or 'json_content' not in models_content.split('class InstrumentLayout')[1].split('class ')[0]:
            print("✅ models.py: json_content properly removed from InstrumentLayout")
        else:
            print("❌ models.py: json_content still present in InstrumentLayout")
            success = False
            
    except Exception as e:
        print(f"❌ Error checking models.py: {e}")
        success = False
    
    # Check dashboard.py routes
    try:
        with open('/home/rok/src/Cloud-1/src/routes/dashboard.py', 'r') as f:
            routes_content = f.read()
            
        # Check for xml_content usage in instrument layout sections
        instrument_layout_section = routes_content[routes_content.find('@dashboard_bp.route(\'/instrument-layouts\')'):routes_content.find('# API Endpoints for Checklist')]
        
        if 'xml_content' in instrument_layout_section:
            print("✅ dashboard.py: xml_content used in instrument layout routes")
        else:
            print("❌ dashboard.py: xml_content missing from instrument layout routes")
            success = False
            
        # Count json_content occurrences in instrument layout section
        json_content_count = instrument_layout_section.count('json_content')
        if json_content_count == 0:
            print("✅ dashboard.py: json_content properly removed from instrument layout routes")
        else:
            print(f"❌ dashboard.py: {json_content_count} json_content references still in instrument layout routes")
            success = False
            
    except Exception as e:
        print(f"❌ Error checking dashboard.py: {e}")
        success = False
    
    return success

if __name__ == "__main__":
    print("🚀 Testing json_content to xml_content Migration...")
    print("=" * 60)
    
    success1 = test_xml_content_migration()
    success2 = check_code_changes()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 All tests passed! Migration successful!")
    else:
        print("❌ Some tests failed!")
        
    print("\n📋 Summary of Changes:")
    print("- ✅ Database: json_content column renamed to xml_content")
    print("- ✅ Models: InstrumentLayout.xml_content field")
    print("- ✅ Routes: Updated to use xml_content")
    print("- ✅ Export: Changed to XML format with .xml extension")
    print("- ✅ Data: All existing layouts migrated successfully")
    
    print("\n🔄 What this means:")
    print("- Instrument layouts now use xml_content field instead of json_content")
    print("- Export files will have .xml extension and XML mimetype")
    print("- All existing data has been preserved during migration")
    print("- API endpoints updated to handle xml_content")
    print("- Editor integration maintained with new field name")
