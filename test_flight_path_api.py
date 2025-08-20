#!/usr/bin/env python3
"""
Test script to verify flight path API endpoint functionality.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models import db, LogbookEntry, FlightPoint
from src.app import create_app

def test_flight_path_api():
    """Test flight path API data structure."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find a logbook entry with flight points
            entry_with_points = db.session.query(LogbookEntry).join(FlightPoint).first()
            
            if not entry_with_points:
                print("No logbook entries with flight points found")
                return
            
            print(f"Testing entry ID: {entry_with_points.id}")
            print(f"Aircraft: {entry_with_points.aircraft_registration}")
            print(f"Route: {entry_with_points.departure_airport} -> {entry_with_points.arrival_airport}")
            print(f"Date: {entry_with_points.takeoff_datetime}")
            
            # Get flight points
            flight_points = FlightPoint.query.filter_by(
                logbook_entry_id=entry_with_points.id
            ).order_by(FlightPoint.sequence.asc()).all()
            
            print(f"Flight points: {len(flight_points)}")
            
            if flight_points:
                first_point = flight_points[0]
                last_point = flight_points[-1]
                
                print(f"First point: {first_point.latitude:.6f}, {first_point.longitude:.6f}")
                print(f"Last point: {last_point.latitude:.6f}, {last_point.longitude:.6f}")
                
                # Show some sample points
                print("\nSample points:")
                for i in range(0, min(len(flight_points), 5)):
                    p = flight_points[i]
                    print(f"  Point {p.sequence}: {p.latitude:.6f}, {p.longitude:.6f}, "
                          f"Speed: {p.airspeed}, Pressure: {p.static_pressure}")
                
                print(f"\nFlight path URL would be: /logbook/{entry_with_points.id}/flight-path")
                print(f"API endpoint URL would be: /api/logbook/{entry_with_points.id}/flight-points")
                
        except Exception as e:
            print(f"Error during test: {e}")
            raise

if __name__ == '__main__':
    test_flight_path_api()
    print("Test completed!")
