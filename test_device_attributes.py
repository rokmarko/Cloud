#!/usr/bin/env python3
"""
Test script to verify Device model attributes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import LogbookEntry, Device

def test_device_attributes():
    """Test that Device model has the correct attributes"""
    app = create_app()
    
    with app.app_context():
        # Get a synced entry
        synced_entry = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None)).first()
        
        if synced_entry:
            print(f"✅ Found synced entry ID: {synced_entry.id}")
            
            if synced_entry.device:
                print(f"✅ Device found: {synced_entry.device}")
                print(f"✅ Device name: {synced_entry.device.name}")
                print(f"✅ Device registration: {synced_entry.device.registration}")
                print(f"✅ Device type: {synced_entry.device.device_type}")
                
                # Test the logic used in clear function
                device_name = synced_entry.device.name if synced_entry.device else f"Device ID {synced_entry.device_id}"
                print(f"✅ Device name for logging: {device_name}")
                
            else:
                print(f"❌ No device found for entry {synced_entry.id}")
        else:
            print("ℹ️  No synced entries found to test")

if __name__ == "__main__":
    print("🧪 Testing Device model attributes...")
    test_device_attributes()
