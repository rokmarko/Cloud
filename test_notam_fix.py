#!/usr/bin/env python3
"""
Test script to verify NOTAM functionality without authentication.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
from src.app import create_app
from src.services.notam_service import notam_service

def test_notam_retrieval():
    """Test NOTAM retrieval with the fixed timezone handling."""
    app = create_app()
    
    with app.app_context():
        print("Testing NOTAM retrieval...")
        
        # Test with current date
        today = datetime.now(timezone.utc).date()
        print(f"Checking NOTAMs for: {today}")
        
        # Get all active NOTAMs
        notams = notam_service.get_active_notams()
        print(f"Total active NOTAMs: {len(notams)}")
        
        if notams:
            print(f"\nFirst NOTAM:")
            notam = notams[0]
            print(f"  ID: {notam.notam_id}")
            print(f"  ICAO: {notam.icao_code}")
            print(f"  Valid from: {notam.valid_from}")
            print(f"  Valid until: {notam.valid_until}")
            print(f"  Is permanent: {notam.is_permanent}")
            print(f"  Body: {notam.body[:100]}..." if notam.body else "  Body: None")
        
        # Test with specific ICAO codes
        test_codes = ['LJLA', 'LJLJ', 'LJLY']
        for icao_code in test_codes:
            code_notams = notam_service.get_active_notams(icao_code)
            print(f"\nActive NOTAMs for {icao_code}: {len(code_notams)}")
            
        return True

if __name__ == "__main__":
    test_notam_retrieval()
