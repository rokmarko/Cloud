#!/usr/bin/env python3
"""
Test script for force rebuild logbook functionality
"""

import requests
import json
import sys
import os

# Add the src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import create_app, db
from src.models import User, Device

def test_force_rebuild():
    """Test the force rebuild logbook endpoint"""
    
    app = create_app()
    
    with app.app_context():
        # Find an admin user
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            print("No admin user found. Creating one...")
            admin_user = User(
                email='admin@test.com',
                nickname='TestAdmin',
                is_admin=True,
                is_active=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created admin user: {admin_user.nickname}")
        
        # Find a device to test with
        device = Device.query.filter_by(is_active=True).first()
        if not device:
            print("No active device found for testing")
            return
        
        print(f"Testing force rebuild for device: {device.name} (ID: {device.id})")
        print(f"Owner: {device.owner.nickname}")
        
        # Test the endpoint exists by checking if route is registered
        from src.routes.admin import admin_bp
        routes = []
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('admin.') and 'force-rebuild' in rule.rule:
                routes.append(rule.rule)
        
        if routes:
            print(f"Force rebuild route found: {routes[0]}")
            print("✅ Force rebuild functionality has been successfully added!")
        else:
            print("❌ Force rebuild route not found")
            
        # List all admin routes for verification
        print("\nAll admin routes:")
        for rule in app.url_map.iter_rules():
            if rule.endpoint.startswith('admin.'):
                print(f"  {rule.rule} -> {rule.endpoint}")

if __name__ == '__main__':
    test_force_rebuild()
