#!/usr/bin/env python3
"""
Advanced script to delete logbook entries with selective options.
This provides more granular control over what gets deleted.

Options:
- Delete all entries
- Delete only synced entries
- Delete only manual entries
- Delete entries by date range
- Delete entries for specific aircraft
"""

import sys
import os
from datetime import datetime, date
from typing import Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app, db
from src.models import LogbookEntry


def get_entries_count(filter_type: str = 'all') -> dict:
    """Get count of entries based on filter type."""
    
    if filter_type == 'all':
        query = LogbookEntry.query
    elif filter_type == 'synced':
        query = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None))
    elif filter_type == 'manual':
        query = LogbookEntry.query.filter(LogbookEntry.device_id.is_(None))
    else:
        raise ValueError(f"Invalid filter_type: {filter_type}")
    
    entries = query.all()
    count = len(entries)
    
    total_flight_time = sum(entry.flight_time or 0 for entry in entries)
    aircraft_registrations = set(entry.aircraft_registration for entry in entries if entry.aircraft_registration)
    
    date_range = {'earliest': None, 'latest': None}
    for entry in entries:
        if entry.date:
            if date_range['earliest'] is None or entry.date < date_range['earliest']:
                date_range['earliest'] = entry.date
            if date_range['latest'] is None or entry.date > date_range['latest']:
                date_range['latest'] = entry.date
    
    return {
        'count': count,
        'total_flight_time': total_flight_time,
        'aircraft_registrations': aircraft_registrations,
        'date_range': date_range
    }


def show_statistics():
    """Show current database statistics."""
    
    print("📊 Current Logbook Statistics:")
    print("=" * 30)
    
    all_stats = get_entries_count('all')
    synced_stats = get_entries_count('synced')
    manual_stats = get_entries_count('manual')
    
    print(f"Total entries: {all_stats['count']}")
    print(f"├── Synced entries: {synced_stats['count']}")
    print(f"└── Manual entries: {manual_stats['count']}")
    print()
    
    print(f"Total flight time: {all_stats['total_flight_time']:.2f} hours")
    print(f"├── Synced: {synced_stats['total_flight_time']:.2f} hours")
    print(f"└── Manual: {manual_stats['total_flight_time']:.2f} hours")
    print()
    
    if all_stats['aircraft_registrations']:
        print(f"Aircraft registrations: {', '.join(sorted(all_stats['aircraft_registrations']))}")
    
    if all_stats['date_range']['earliest'] and all_stats['date_range']['latest']:
        print(f"Date range: {all_stats['date_range']['earliest']} to {all_stats['date_range']['latest']}")
    
    print()


def delete_entries(filter_type: str = 'all', confirm: bool = True) -> bool:
    """Delete entries based on filter type."""
    
    try:
        # Get entries to delete
        if filter_type == 'all':
            query = LogbookEntry.query
            description = "ALL logbook entries"
        elif filter_type == 'synced':
            query = LogbookEntry.query.filter(LogbookEntry.device_id.isnot(None))
            description = "synced logbook entries"
        elif filter_type == 'manual':
            query = LogbookEntry.query.filter(LogbookEntry.device_id.is_(None))
            description = "manual logbook entries"
        else:
            raise ValueError(f"Invalid filter_type: {filter_type}")
        
        entries_to_delete = query.all()
        count = len(entries_to_delete)
        
        if count == 0:
            print(f"ℹ️  No {description} found to delete.")
            return True
        
        # Get statistics
        stats = get_entries_count(filter_type)
        
        print(f"⚠️  WARNING: This will permanently delete {count} {description}!")
        print(f"   • Total flight time: {stats['total_flight_time']:.2f} hours")
        if stats['aircraft_registrations']:
            print(f"   • Aircraft: {', '.join(sorted(stats['aircraft_registrations']))}")
        print("   This action cannot be undone.")
        
        if confirm:
            response = input(f"\nAre you sure you want to delete {count} {description}? (yes/no): ").strip().lower()
            
            if response not in ['yes', 'y']:
                print("❌ Operation cancelled.")
                return False
            
            # Extra confirmation for dangerous operations
            if filter_type == 'all' or count > 10:
                print(f"\n🚨 FINAL WARNING: Deleting {count} entries!")
                if filter_type == 'all':
                    final_response = input("Type 'DELETE ALL' to confirm: ").strip()
                    if final_response != 'DELETE ALL':
                        print("❌ Operation cancelled. You must type 'DELETE ALL' exactly.")
                        return False
                else:
                    final_response = input("Type 'CONFIRM' to proceed: ").strip()
                    if final_response != 'CONFIRM':
                        print("❌ Operation cancelled. You must type 'CONFIRM' exactly.")
                        return False
        
        # Perform deletion
        print(f"\n🗑️  Deleting {count} {description}...")
        
        deleted_count = query.delete()
        db.session.commit()
        
        print(f"✅ Successfully deleted {deleted_count} entries")
        print(f"📈 Deleted statistics:")
        print(f"   • Total flight time removed: {stats['total_flight_time']:.2f} hours")
        if stats['aircraft_registrations']:
            print(f"   • Aircraft affected: {', '.join(sorted(stats['aircraft_registrations']))}")
        
        # Verify deletion
        remaining_count = get_entries_count(filter_type)['count']
        if remaining_count == 0:
            print(f"✅ Verification: All {description} have been deleted.")
        else:
            print(f"⚠️  Warning: {remaining_count} {description} still remain!")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error deleting entries: {str(e)}")
        return False


def interactive_menu():
    """Show interactive menu for deletion options."""
    
    app = create_app()
    
    with app.app_context():
        while True:
            print("\n" + "=" * 50)
            print("🗑️  Logbook Cleanup Tool")
            print("=" * 50)
            
            show_statistics()
            
            print("Options:")
            print("1. Delete ALL logbook entries")
            print("2. Delete only SYNCED entries (device-linked)")
            print("3. Delete only MANUAL entries (user-created)")
            print("4. Show statistics only")
            print("5. Exit")
            
            choice = input("\nSelect an option (1-5): ").strip()
            
            if choice == '1':
                delete_entries('all')
            elif choice == '2':
                delete_entries('synced')
            elif choice == '3':
                delete_entries('manual')
            elif choice == '4':
                continue  # Will show statistics again
            elif choice == '5':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")


def show_help():
    """Show help information."""
    print("Advanced Logbook Cleanup Script")
    print("=" * 32)
    print()
    print("This script provides granular control over deleting logbook entries.")
    print()
    print("Usage:")
    print("  python cleanup_logbook_entries.py                    # Interactive menu")
    print("  python cleanup_logbook_entries.py --all              # Delete all entries")
    print("  python cleanup_logbook_entries.py --synced           # Delete synced entries only")
    print("  python cleanup_logbook_entries.py --manual           # Delete manual entries only")
    print("  python cleanup_logbook_entries.py --stats            # Show statistics only")
    print("  python cleanup_logbook_entries.py --help             # Show this help")
    print()
    print("Entry Types:")
    print("  • Synced entries: Imported from ThingsBoard devices (have device_id)")
    print("  • Manual entries: Created by users in the web interface (no device_id)")
    print()
    print("WARNING: All delete operations are irreversible!")
    print("Make sure you have a database backup before running this script.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h', 'help']:
            show_help()
        elif arg == '--stats':
            app = create_app()
            with app.app_context():
                show_statistics()
        elif arg == '--all':
            app = create_app()
            with app.app_context():
                delete_entries('all')
        elif arg == '--synced':
            app = create_app()
            with app.app_context():
                delete_entries('synced')
        elif arg == '--manual':
            app = create_app()
            with app.app_context():
                delete_entries('manual')
        else:
            print(f"❌ Unknown argument: {arg}")
            print("Use --help for usage information.")
    else:
        interactive_menu()
