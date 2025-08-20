#!/usr/bin/env python3
"""
Test script to verify geocoding functionality for flight points.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models import db, LogbookEntry, FlightPoint, Device
from src.app import create_app
from src.services.thingsboard_sync import thingsboard_sync

def test_geocoding_functionality():
    """Test geocoding functionality for flight points."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find a logbook entry with flight points
            logbook_entry = LogbookEntry.query.join(FlightPoint).first()
            
            if not logbook_entry:
                print("No logbook entries with flight points found for testing")
                return
            
            print(f"Testing geocoding for logbook entry {logbook_entry.id}")
            print(f"Current departure: {logbook_entry.departure_airport}")
            print(f"Current arrival: {logbook_entry.arrival_airport}")
            
            # Count flight points
            points_count = FlightPoint.query.filter_by(logbook_entry_id=logbook_entry.id).count()
            print(f"Flight points available: {points_count}")
            
            if points_count == 0:
                print("No flight points available for geocoding")
                return
            
            # Get first and last points for reference
            first_point = FlightPoint.query.filter_by(
                logbook_entry_id=logbook_entry.id
            ).order_by(FlightPoint.sequence.asc()).first()
            
            last_point = FlightPoint.query.filter_by(
                logbook_entry_id=logbook_entry.id
            ).order_by(FlightPoint.sequence.desc()).first()
            
            print(f"First point: {first_point.latitude:.6f}, {first_point.longitude:.6f}")
            print(f"Last point: {last_point.latitude:.6f}, {last_point.longitude:.6f}")
            
            # Test the geocoding
            print("Running geocoding...")
            thingsboard_sync._geocode_departure_arrival_airports(logbook_entry)
            
            # Check results
            db.session.refresh(logbook_entry)
            print(f"Updated departure: {logbook_entry.departure_airport}")
            print(f"Updated arrival: {logbook_entry.arrival_airport}")
            
        except Exception as e:
            print(f"Error during geocoding test: {e}")
            raise

def create_test_flight_points():
    """Create test flight points for testing if none exist."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find a logbook entry without flight points
            logbook_entry = LogbookEntry.query.filter(
                ~LogbookEntry.id.in_(db.session.query(FlightPoint.logbook_entry_id).distinct())
            ).first()
            
            if not logbook_entry:
                print("No logbook entries available for creating test points")
                return
            
            print(f"Creating test flight points for logbook entry {logbook_entry.id}")
            
            # Create some test flight points (Ljubljana to Vienna)
            test_points = [
                # Takeoff from Ljubljana area
                {'lat': 46.224, 'lon': 14.458, 'sequence': 0, 'airspeed': 0, 'pressure': 1013.25},
                {'lat': 46.230, 'lon': 14.470, 'sequence': 1, 'airspeed': 120, 'pressure': 1000.0},
                
                # En route
                {'lat': 46.500, 'lon': 15.000, 'sequence': 2, 'airspeed': 150, 'pressure': 950.0},
                {'lat': 47.000, 'lon': 15.500, 'sequence': 3, 'airspeed': 160, 'pressure': 900.0},
                {'lat': 47.500, 'lon': 16.000, 'sequence': 4, 'airspeed': 155, 'pressure': 920.0},
                
                # Landing at Vienna area
                {'lat': 48.100, 'lon': 16.550, 'sequence': 5, 'airspeed': 100, 'pressure': 1015.0},
                {'lat': 48.110, 'lon': 16.570, 'sequence': 6, 'airspeed': 0, 'pressure': 1015.5},
            ]
            
            for point_data in test_points:
                flight_point = FlightPoint(
                    logbook_entry_id=logbook_entry.id,
                    latitude=point_data['lat'],
                    longitude=point_data['lon'],
                    sequence=point_data['sequence'],
                    timestamp_offset=point_data['sequence'] * 5,
                    airspeed=point_data['airspeed'],
                    static_pressure=point_data['pressure']
                )
                db.session.add(flight_point)
            
            db.session.commit()
            print(f"Created {len(test_points)} test flight points")
            
            # Now test geocoding
            test_geocoding_functionality()
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test points: {e}")
            raise

if __name__ == '__main__':
    print("Testing geocoding functionality...")
    test_geocoding_functionality()
    
    # If no data, create test data
    print("\nCreating test data if needed...")
    create_test_flight_points()
    
    print("Test completed!")
