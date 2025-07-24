#!/usr/bin/env python3
"""
Script to grant admin privileges to a user
"""

import sys
from src.app import create_app, db
from src.models import User

def make_admin(email):
    """Grant admin privileges to a user by email"""
    
    app = create_app()
    
    with app.app_context():
        user = User.query.filter_by(email=email.lower().strip()).first()
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
        
        if user.is_admin:
            print(f"✅ User '{user.nickname}' ({email}) is already an admin")
            return True
        
        user.is_admin = True
        db.session.commit()
        
        print(f"✅ Admin privileges granted to '{user.nickname}' ({email})")
        return True

def list_admins():
    """List all admin users"""
    
    app = create_app()
    
    with app.app_context():
        admins = User.query.filter_by(is_admin=True, is_active=True).all()
        
        if not admins:
            print("No admin users found")
            return
        
        print("Admin users:")
        for admin in admins:
            print(f"  - {admin.nickname} ({admin.email})")

if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] == '--list':
            list_admins()
        else:
            make_admin(sys.argv[1])
    else:
        print("Usage:")
        print(f"  {sys.argv[0]} <email>     # Grant admin privileges to user")
        print(f"  {sys.argv[0]} --list      # List all admin users")
        print("")
        print("Example:")
        print(f"  {sys.argv[0]} admin@example.com")
