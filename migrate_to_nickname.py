#!/usr/bin/env python3
"""
Database migration script to update User model from first_name/last_name to nickname
"""

import sqlite3
import os
from src.app import create_app, db
from src.models import User

def migrate_database():
    """Migrate the database to use nickname instead of first_name/last_name."""
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        db_path = os.path.join(app.instance_path, 'kanardiacloud.db')
        
        if not os.path.exists(db_path):
            print("Database doesn't exist yet. Creating new schema with nickname field.")
            db.create_all()
            return
        
        print("Migrating existing database...")
        
        # Connect to SQLite database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if nickname column already exists
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'nickname' in columns:
                print("Nickname column already exists. Migration not needed.")
                return
            
            # Check if first_name and last_name exist
            has_names = 'first_name' in columns and 'last_name' in columns
            
            if has_names:
                print("Migrating from first_name/last_name to nickname...")
                
                # Add nickname column
                cursor.execute("ALTER TABLE user ADD COLUMN nickname VARCHAR(50)")
                
                # Migrate existing data - combine first_name and last_name into nickname
                cursor.execute("""
                    UPDATE user 
                    SET nickname = CASE 
                        WHEN first_name IS NOT NULL AND last_name IS NOT NULL 
                        THEN first_name || ' ' || last_name
                        WHEN first_name IS NOT NULL 
                        THEN first_name
                        WHEN last_name IS NOT NULL 
                        THEN last_name
                        ELSE 'User'
                    END
                """)
                
                # Make nickname NOT NULL
                cursor.execute("""
                    CREATE TABLE user_new (
                        id INTEGER PRIMARY KEY,
                        email VARCHAR(120) NOT NULL UNIQUE,
                        password_hash VARCHAR(128) NOT NULL,
                        nickname VARCHAR(50) NOT NULL,
                        is_active BOOLEAN NOT NULL DEFAULT 0,
                        is_verified BOOLEAN NOT NULL DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        last_login DATETIME
                    )
                """)
                
                # Copy data to new table
                cursor.execute("""
                    INSERT INTO user_new (id, email, password_hash, nickname, is_active, is_verified, created_at, last_login)
                    SELECT id, email, password_hash, nickname, is_active, is_verified, created_at, last_login
                    FROM user
                """)
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE user")
                cursor.execute("ALTER TABLE user_new RENAME TO user")
                
                # Recreate indexes
                cursor.execute("CREATE INDEX ix_user_email ON user (email)")
                
                print("Migration completed successfully!")
                
            else:
                print("Adding nickname column to new database...")
                # Just add the nickname column for a fresh database
                cursor.execute("ALTER TABLE user ADD COLUMN nickname VARCHAR(50) NOT NULL DEFAULT 'User'")
            
            conn.commit()
            
        except Exception as e:
            print(f"Error during migration: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

if __name__ == '__main__':
    migrate_database()
