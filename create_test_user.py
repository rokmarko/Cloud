#!/usr/bin/env python3
"""
Create a test user for NOTAM interface testing.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, User
from werkzeug.security import generate_password_hash

def create_test_user():
    """Create a simple test user for testing the NOTAM interface."""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email='test@kanardiacloud.com').first()
        
        if existing_user:
            print(f"Test user already exists: test@kanardiacloud.com")
            return
            
        # Create new test user
        test_user = User(
            email='test@kanardiacloud.com',
            password_hash=generate_password_hash('testpass123'),
            nickname='Test User',
            is_admin=True,
            is_active=True,
            is_verified=True
        )
        
        db.session.add(test_user)
        db.session.commit()
        
        print("Test user created successfully!")
        print("Email: test@kanardiacloud.com")
        print("Password: testpass123")
        print("Admin privileges: Yes")

if __name__ == "__main__":
    create_test_user()
