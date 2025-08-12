#!/usr/bin/env python3
"""
Database migration script to add logbook_entry_id field to Event table.
This replaces the message-based linking approach with a proper foreign key relationship.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, Event, LogbookEntry
from sqlalchemy import text

def migrate_event_logbook_link():
    """Add logbook_entry_id field to Event table."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the column already exists
            with db.engine.connect() as connection:
                result = connection.execute(text("""
                    SELECT COUNT(*) as count
                    FROM pragma_table_info('event')
                    WHERE name = 'logbook_entry_id'
                """)).fetchone()
                
                if result.count > 0:
                    print("Column 'logbook_entry_id' already exists in 'event' table")
                    return
                
                # Add the new column
                print("Adding 'logbook_entry_id' column to 'event' table...")
                connection.execute(text("""
                    ALTER TABLE event 
                    ADD COLUMN logbook_entry_id INTEGER 
                    REFERENCES logbook_entry(id)
                """))
                
                connection.commit()
                print("Successfully added 'logbook_entry_id' column to 'event' table")
            
            # Optional: Migrate existing message-based links to the new field
            # This would parse existing event messages to extract logbook entry IDs
            migrate_existing_links()
            
        except Exception as e:
            print(f"Migration failed: {str(e)}")
            raise

def migrate_existing_links():
    """
    Migrate existing message-based links to the new logbook_entry_id field.
    This parses event messages like "Linked to Logbook Entry 123" and sets the foreign key.
    """
    try:
        import re
        
        # Find events with link messages
        events_with_links = Event.query.filter(
            Event.message.like('%Linked to Logbook Entry%')
        ).all()
        
        print(f"Found {len(events_with_links)} events with existing link messages")
        
        migrated_count = 0
        for event in events_with_links:
            if not event.message:
                continue
            
            # Extract logbook entry ID from message
            pattern = r'Linked to Logbook Entry (\d+)'
            matches = re.findall(pattern, event.message)
            
            if matches:
                # Use the first (or only) logbook entry ID found
                logbook_entry_id = int(matches[0])
                
                # Verify the logbook entry exists
                logbook_entry = LogbookEntry.query.get(logbook_entry_id)
                if logbook_entry:
                    event.logbook_entry_id = logbook_entry_id
                    migrated_count += 1
                    
                    # Clean the message by removing link references
                    cleaned_message = re.sub(r'\[?Linked to Logbook Entry \d+\]?\s*', '', event.message).strip()
                    if not cleaned_message:
                        event.message = None
                    else:
                        event.message = cleaned_message
        
        # Commit all changes
        db.session.commit()
        print(f"Successfully migrated {migrated_count} event links to new foreign key field")
        
    except Exception as e:
        db.session.rollback()
        print(f"Failed to migrate existing links: {str(e)}")
        raise

if __name__ == '__main__':
    migrate_event_logbook_link()
    print("Migration completed successfully!")
