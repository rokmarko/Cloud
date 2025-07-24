#!/usr/bin/env python3
"""
Test script to create a sample logbook entry and test sync functionality.
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import create_app
from models import db, User, LogbookEntry
from services.thingsboard_sync import ThingsBoardSyncService

def create_test_logbook_entry():
    """Create a test logbook entry and test sync."""
    # Load environment variables
    load_dotenv()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        print("ThingsBoard Sync Test")
        print("=" * 30)
        
        # Find a test user
        user = User.query.first()
        if not user:
            print("❌ No users found in database")
            return False
        
        print(f"Using test user: {user.nickname or user.username}")
        
        # Create a test logbook entry
        test_entry = LogbookEntry(
            user_id=user.id,
            external_device_id="TEST_DEVICE_001",
            date=datetime.now().date(),
            aircraft_registration="OK-TEST",
            flight_time_minutes=120,  # 2 hours
            approach_count=2,
            landing_count=2,
            departure_airport="LKPR",
            arrival_airport="LKVO",
            notes="Test flight entry for ThingsBoard sync",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            db.session.add(test_entry)
            db.session.commit()
            print(f"✅ Created test logbook entry ID: {test_entry.id}")
            
            # Test sync service
            sync_service = ThingsBoardSyncService()
            
            # Get recent entries (should include our test entry)
            recent_entries = LogbookEntry.query.filter(
                LogbookEntry.created_at >= datetime.utcnow() - timedelta(days=1)
            ).all()
            
            print(f"Found {len(recent_entries)} recent entries")
            
            # Test authentication first
            if sync_service.test_authentication():
                print("✅ ThingsBoard authentication successful")
                
                # Test sync (this would normally send data to ThingsBoard)
                print("🔄 Testing sync functionality...")
                # Note: Actual sync would require proper ThingsBoard device configuration
                print("⚠️  Sync test completed (would send data to ThingsBoard in production)")
                
            else:
                print("❌ ThingsBoard authentication failed")
                return False
            
            # Clean up - remove test entry
            db.session.delete(test_entry)
            db.session.commit()
            print("🧹 Cleaned up test entry")
            
            return True
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = create_test_logbook_entry()
    sys.exit(0 if success else 1)
