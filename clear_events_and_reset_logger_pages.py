#!/usr/bin/env ./venv/bin/python
"""
Script to clear all events and reset current_logger_page to 0 for all devices.
Usage: ./venv/bin/python clear_events_and_reset_logger_pages.py
"""

from src.app import create_app
from src.services.thingsboard_sync import thingsboard_sync

def main():
    """Main function to clear events and reset logger pages."""
    app = create_app()
    
    with app.app_context():
        print("🧹 Clearing all events and resetting logger pages...")
        
        # Call the clear function
        result = thingsboard_sync.clear_all_events_and_reset_logger_pages()
        
        # Display results
        print(f"✅ Events cleared: {result['events_cleared']}")
        print(f"✅ Event-generated logbook entries removed: {result['logbook_entries_removed']}")
        print(f"✅ Devices reset (current_logger_page → 0): {result['devices_reset']}")
        
        if result['errors']:
            print(f"❌ Errors encountered:")
            for error in result['errors']:
                print(f"   - {error}")
        else:
            print("🎉 All operations completed successfully!")

if __name__ == '__main__':
    main()
