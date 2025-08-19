#!/usr/bin/env python3
"""
Migration script to add date_format field to existing users.
This script adds the date_format column with a default value for existing users.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import User

def migrate_user_date_format():
    """Add date_format field to existing users."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column already exists
            from sqlalchemy import text
            with db.engine.connect() as conn:
                result = conn.execute(text("PRAGMA table_info(user)")).fetchall()
                columns = [row[1] for row in result]
                
                if 'date_format' not in columns:
                    print("Adding date_format column to user table...")
                    conn.execute(text("ALTER TABLE user ADD COLUMN date_format VARCHAR(20) DEFAULT '%Y-%m-%d' NOT NULL"))
                    conn.commit()
                    print("✓ date_format column added successfully")
                else:
                    print("✓ date_format column already exists")
            
            # Update any users that might have NULL values
            users_updated = db.session.query(User).filter(User.date_format.is_(None)).update({
                User.date_format: '%Y-%m-%d'
            })
            
            if users_updated > 0:
                print(f"✓ Updated {users_updated} users with default date format")
                db.session.commit()
            else:
                print("✓ All users already have date_format set")
            
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
            return False
            
    return True

if __name__ == '__main__':
    migrate_user_date_format()
