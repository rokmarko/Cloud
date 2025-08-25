#!/usr/bin/env python3
"""
Manual NOTAM fetch script for KanardiaCloud.
Run this script to manually fetch and parse NOTAMs into the database.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Optional

from src.app import create_app
from src.services.notam_service import notam_service


def fetch_single_area(icao_code: str):
    """Fetch NOTAMs for a single ICAO area."""
    print(f"Fetching NOTAMs for {icao_code}...")
    
    try:
        result = notam_service.fetch_and_store_notams(icao_code)
        print(f"✅ Success for {icao_code}:")
        print(f"   Total fetched: {result['total_fetched']}")
        print(f"   New NOTAMs: {result['new_notams']}")
        print(f"   Updated NOTAMs: {result['updated_notams']}")
        print(f"   Errors: {len(result['errors'])}")
        
        if result['errors']:
            print("   Error details:")
            for error in result['errors']:
                print(f"     - {error}")
                
    except Exception as e:
        print(f"❌ Error fetching {icao_code}: {str(e)}")


def fetch_all_areas():
    """Fetch NOTAMs for all supported areas."""
    print("Fetching NOTAMs for all supported areas...")
    
    try:
        results = notam_service.fetch_all_areas()
        
        print("\n📊 Summary:")
        total_new = 0
        total_updated = 0
        total_errors = 0
        
        for icao_code, result in results.items():
            if 'error' in result:
                print(f"❌ {icao_code}: {result['error']}")
                total_errors += 1
            else:
                print(f"✅ {icao_code}: {result['new_notams']} new, {result['updated_notams']} updated, {result['total_fetched']} total")
                total_new += result['new_notams']
                total_updated += result['updated_notams']
        
        print(f"\n🎯 Overall totals: {total_new} new, {total_updated} updated, {total_errors} areas with errors")
        
    except Exception as e:
        print(f"❌ Error in batch fetch: {str(e)}")


def show_active_notams(icao_code: Optional[str] = None):
    """Show currently active NOTAMs."""
    if icao_code:
        print(f"Active NOTAMs for {icao_code}:")
        notams = notam_service.get_active_notams(icao_code)
    else:
        print("All active NOTAMs:")
        notams = notam_service.get_active_notams()
    
    if not notams:
        print("   No active NOTAMs found.")
        return
    
    for notam in notams:
        status = "PERMANENT" if notam.is_permanent else f"Until {notam.valid_until}"
        print(f"   • {notam.notam_id} ({notam.icao_code}) - {notam.q_code_meaning} - {status}")
        if notam.body:
            preview = notam.body[:80] + "..." if len(notam.body) > 80 else notam.body
            print(f"     {preview}")


def cleanup_expired():
    """Clean up old expired NOTAMs."""
    print("Cleaning up expired NOTAMs...")
    try:
        count = notam_service.cleanup_expired_notams(days_old=30)
        print(f"✅ Cleaned up {count} expired NOTAMs")
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")


def main():
    """Main function with command-line interface."""
    if len(sys.argv) < 2:
        print("""
Usage: python manual_notam_fetch.py <command> [area]

Commands:
  fetch <ICAO>     - Fetch NOTAMs for specific ICAO code (e.g., LJLA)
  fetch-all        - Fetch NOTAMs for all supported areas
  show [ICAO]      - Show active NOTAMs (all or for specific area)
  cleanup          - Remove old expired NOTAMs
  
Supported ICAO codes: LJLA, EDMM, LOVV, LHCC, LKAA

Examples:
  python manual_notam_fetch.py fetch LJLA
  python manual_notam_fetch.py fetch-all
  python manual_notam_fetch.py show LJLA
  python manual_notam_fetch.py show
  python manual_notam_fetch.py cleanup
""")
        sys.exit(1)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        command = sys.argv[1].lower()
        
        if command == "fetch" and len(sys.argv) > 2:
            icao_code = sys.argv[2].upper()
            if icao_code in notam_service.SUPPORTED_AREAS:
                fetch_single_area(icao_code)
            else:
                print(f"❌ Unsupported ICAO code: {icao_code}")
                print(f"   Supported codes: {', '.join(notam_service.SUPPORTED_AREAS)}")
        
        elif command == "fetch-all":
            fetch_all_areas()
        
        elif command == "show":
            icao_code = sys.argv[2].upper() if len(sys.argv) > 2 else None
            if icao_code and icao_code not in notam_service.SUPPORTED_AREAS:
                print(f"❌ Unsupported ICAO code: {icao_code}")
            else:
                show_active_notams(icao_code)
        
        elif command == "cleanup":
            cleanup_expired()
        
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)


if __name__ == "__main__":
    main()
