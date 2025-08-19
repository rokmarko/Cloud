#!/usr/bin/env python3
"""
Script to delete all logbook entries from the database.
This is useful for testing and cleanup purposes.

WARNING: This will permanently delete ALL logbook entries!
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import LogbookEntry


def delete_all_logbook_entries():
    """Delete all logbook entries from the database."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get counts before deletion
            total_entries = LogbookEntry.query.count()
            synced_entries = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None)).count()
            manual_entries = LogbookEntry.query.filter(LogbookEntry.device_id.is_(None)).count()
            
            print(f"📊 Current logbook statistics:")
            print(f"   • Total entries: {total_entries}")
            print(f"   • Synced entries: {synced_entries}")
            print(f"   • Manual entries: {manual_entries}")
            
            if total_entries == 0:
                print("ℹ️  No logbook entries found to delete.")
                return
            
            # Confirm deletion
            print(f"\n⚠️  WARNING: This will permanently delete ALL {total_entries} logbook entries!")
            print("   This action cannot be undone.")
            
            response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("❌ Operation cancelled.")
                return
            
            # Double confirmation for safety
            print(f"\n🚨 FINAL WARNING: You are about to delete {total_entries} logbook entries!")
            final_response = input("Type 'DELETE ALL' to confirm: ").strip()
            
            if final_response != 'DELETE ALL':
                print("❌ Operation cancelled. You must type 'DELETE ALL' exactly.")
                return
            
            # Perform deletion
            print(f"\n🗑️  Deleting all logbook entries...")
            
            # Get entries for logging purposes
            entries_to_delete = LogbookEntry.query.all()
            
            # Track some statistics
            aircraft_registrations = set()
            flight_time_total = 0
            date_range = {'earliest': None, 'latest': None}
            
            for entry in entries_to_delete:
                if entry.aircraft_registration:
                    aircraft_registrations.add(entry.aircraft_registration)
                if entry.flight_time:
                    flight_time_total += entry.flight_time
                if entry.date:
                    if date_range['earliest'] is None or entry.date < date_range['earliest']:
                        date_range['earliest'] = entry.date
                    if date_range['latest'] is None or entry.date > date_range['latest']:
                        date_range['latest'] = entry.date
            
            # Delete all entries
            deleted_count = LogbookEntry.query.delete()
            db.session.commit()
            
            # Log the operation
            print(f"✅ Successfully deleted {deleted_count} logbook entries")
            print(f"📈 Statistics of deleted entries:")
            print(f"   • Total flight time: {flight_time_total:.2f} hours")
            print(f"   • Aircraft involved: {len(aircraft_registrations)} ({', '.join(sorted(aircraft_registrations)) if aircraft_registrations else 'None'})")
            if date_range['earliest'] and date_range['latest']:
                print(f"   • Date range: {date_range['earliest']} to {date_range['latest']}")
            print(f"   • Synced entries deleted: {synced_entries}")
            print(f"   • Manual entries deleted: {manual_entries}")
            
            # Verify deletion
            remaining_entries = LogbookEntry.query.count()
            if remaining_entries == 0:
                print(f"✅ Verification: All logbook entries have been deleted.")
            else:
                print(f"⚠️  Warning: {remaining_entries} entries still remain in database!")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error deleting logbook entries: {str(e)}")
            sys.exit(1)


def show_help():
    """Show help information."""
    print("Delete All Logbook Entries Script")
    print("=" * 35)
    print()
    print("This script will delete ALL logbook entries from the database.")
    print("This includes both manually created entries and synced entries.")
    print()
    print("Usage:")
    print("  python delete_all_logbook_entries.py        # Interactive mode")
    print("  python delete_all_logbook_entries.py --help # Show this help")
    print()
    print("WARNING: This operation is irreversible!")
    print("Make sure you have a database backup before running this script.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        show_help()
    else:
        print("🗑️  Logbook Cleanup Script")
        print("=" * 25)
        print()
        delete_all_logbook_entries()
