#!/usr/bin/env python3
"""
Create a test admin user for testing purposes
"""

from src.app import create_app, db
from src.models import User

def create_test_admin():
    """Create a test admin user"""
    
    app = create_app()
    
    with app.app_context():
        # Check if test admin already exists
        test_admin = User.query.filter_by(email='admin@kanardia.test').first()
        
        if test_admin:
            print("✅ Test admin user already exists")
            if not test_admin.is_admin:
                test_admin.is_admin = True
                db.session.commit()
                print("✅ Admin privileges granted to test user")
            return
        
        # Create test admin user
        test_admin = User(
            email='admin@kanardia.test',
            nickname='Test Admin',
            is_active=True,
            is_verified=True,
            is_admin=True
        )
        test_admin.set_password('admin123')
        
        db.session.add(test_admin)
        db.session.commit()
        
        print("✅ Test admin user created successfully")
        print("   Email: admin@kanardia.test")
        print("   Password: admin123")
        print("   Nickname: Test Admin")

if __name__ == '__main__':
    create_test_admin()
