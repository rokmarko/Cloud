#!/usr/bin/env python3
"""
Migration script to add is_admin field to User model
"""

from src.app import create_app, db
from src.models import User

def migrate_add_admin_field():
    """Add is_admin field to existing users"""
    
    app = create_app()
    
    with app.app_context():
        # Check if is_admin column exists by trying to query it
        try:
            db.session.execute(db.text("SELECT is_admin FROM user LIMIT 1"))
            print("✅ is_admin field already exists")
        except Exception:
            # Field doesn't exist, add it
            print("Adding is_admin field to User table...")
            db.session.execute(db.text('ALTER TABLE user ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL'))
            db.session.commit()
            print("✅ is_admin field added successfully")
        
        # Create first admin user if specified
        admin_email = input("Enter email for first admin user (or press Enter to skip): ").strip()
        if admin_email:
            user = User.query.filter_by(email=admin_email).first()
            if user:
                user.is_admin = True
                db.session.commit()
                print(f"✅ User {admin_email} has been granted admin privileges")
            else:
                print(f"❌ User {admin_email} not found")

if __name__ == '__main__':
    migrate_add_admin_field()
