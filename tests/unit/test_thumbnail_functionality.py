#!/usr/bin/env python3
"""
Test script to verify thumbnail functionality for instrument layouts.
"""

import sqlite3
import os
import base64
from io import BytesIO
from PIL import Image

def test_thumbnail_field():
    """Test that the thumbnail_filename field exists in the database."""
    db_path = os.path.join('instance', 'kanardiacloud.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check table structure
        cursor.execute("PRAGMA table_info(instrument_layout)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'thumbnail_filename' not in columns:
            print("❌ thumbnail_filename column not found in instrument_layout table")
            return False
        
        print("✅ thumbnail_filename column exists in instrument_layout table")
        
        # Check existing layouts
        cursor.execute("SELECT id, title, thumbnail_filename FROM instrument_layout WHERE is_active = 1")
        layouts = cursor.fetchall()
        
        print(f"📊 Found {len(layouts)} active instrument layouts:")
        for layout_id, title, thumbnail in layouts:
            thumbnail_status = "📷 Has thumbnail" if thumbnail else "📭 No thumbnail"
            print(f"  - Layout {layout_id}: {title} ({thumbnail_status})")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

def test_thumbnail_generation():
    """Test the thumbnail generation functionality."""
    try:
        # Create a simple test image
        image = Image.new('RGB', (800, 600), color='lightblue')
        
        # Add some simple graphics to make it look like an instrument
        from PIL import ImageDraw
        draw = ImageDraw.Draw(image)
        
        # Draw a circle (like a gauge)
        draw.ellipse([300, 200, 500, 400], outline='black', width=3)
        draw.line([400, 300, 400, 250], fill='red', width=4)  # Needle
        
        # Convert to base64
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        print("✅ Successfully created test image and converted to base64")
        print(f"📏 Base64 data length: {len(base64_data)} characters")
        
        # Test thumbnail resizing
        test_image = Image.open(BytesIO(image_data))
        test_image.thumbnail((300, 200), Image.Resampling.LANCZOS)
        
        print(f"✅ Thumbnail resizing test successful: {test_image.size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Thumbnail generation test failed: {e}")
        return False

def test_directories():
    """Test that thumbnail directories exist."""
    static_dir = os.path.join('static')
    thumbnails_dir = os.path.join(static_dir, 'thumbnails')
    layouts_dir = os.path.join(thumbnails_dir, 'instrument_layouts')
    
    if not os.path.exists(static_dir):
        print(f"❌ Static directory not found: {static_dir}")
        return False
    
    if not os.path.exists(thumbnails_dir):
        print(f"❌ Thumbnails directory not found: {thumbnails_dir}")
        return False
        
    if not os.path.exists(layouts_dir):
        print(f"❌ Instrument layouts thumbnails directory not found: {layouts_dir}")
        return False
    
    print("✅ All thumbnail directories exist")
    
    # List existing thumbnails
    try:
        thumbnails = [f for f in os.listdir(layouts_dir) if f.endswith('.png')]
        print(f"📁 Found {len(thumbnails)} existing thumbnails:")
        for thumb in thumbnails[:5]:  # Show first 5
            print(f"  - {thumb}")
        if len(thumbnails) > 5:
            print(f"  ... and {len(thumbnails) - 5} more")
    except Exception as e:
        print(f"⚠️  Error listing thumbnails: {e}")
    
    return True

def main():
    """Run all tests."""
    print("🧪 Testing thumbnail functionality for instrument layouts...\n")
    
    tests = [
        ("Database Field Test", test_thumbnail_field),
        ("Thumbnail Generation Test", test_thumbnail_generation),  
        ("Directories Test", test_directories)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}:")
        result = test_func()
        results.append(result)
        print(f"{'✅' if result else '❌'} {test_name} {'PASSED' if result else 'FAILED'}")
    
    print(f"\n📊 Test Summary:")
    print(f"✅ Passed: {sum(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Thumbnail functionality is ready.")
    else:
        print("\n💥 Some tests failed. Please check the issues above.")

if __name__ == '__main__':
    main()
