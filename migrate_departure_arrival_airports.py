#!/usr/bin/env python3
"""
Migration script to update departure and arrival airports for logbook entries with flight points.
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, LogbookEntry, FlightPoint
from src.services.geocoding import get_geocoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_departure_arrival_airports")

def update_departure_arrival_airports():
    geocoder = get_geocoder()
    updated = 0
    entries = LogbookEntry.query.join(FlightPoint, FlightPoint.logbook_entry_id == LogbookEntry.id).distinct().all()
    logger.info(f"Found {len(entries)} logbook entries with flight points.")
    
    for entry in entries:
        logger.info(f"Processing entry {entry.id}: current departure='{entry.departure_airport}', arrival='{entry.arrival_airport}'")
        
        first_point = FlightPoint.query.filter_by(logbook_entry_id=entry.id).order_by(FlightPoint.sequence.asc()).first()
        last_point = FlightPoint.query.filter_by(logbook_entry_id=entry.id).order_by(FlightPoint.sequence.desc()).first()
        
        if not first_point or not last_point:
            logger.warning(f"No flight points for entry {entry.id}")
            continue
            
        logger.info(f"Entry {entry.id}: first point lat={first_point.latitude}, lon={first_point.longitude}")
        logger.info(f"Entry {entry.id}: last point lat={last_point.latitude}, lon={last_point.longitude}")
        
        # Departure
        dep_loc = geocoder.get_nearest_airfield(first_point.latitude, first_point.longitude)
        if not dep_loc:
            logger.debug(f"Entry {entry.id}: trying swapped coordinates for departure")
            dep_loc = geocoder.get_nearest_airfield(first_point.longitude, first_point.latitude)
        dep_icao = dep_loc.get('icao_code', 'UNKN') if dep_loc else 'UNKN'
        logger.info(f"Entry {entry.id}: departure geocoding result: {dep_icao} (location: {dep_loc})")
        
        # Arrival
        arr_loc = geocoder.get_nearest_airfield(last_point.latitude, last_point.longitude)
        if not arr_loc:
            logger.debug(f"Entry {entry.id}: trying swapped coordinates for arrival")
            arr_loc = geocoder.get_nearest_airfield(last_point.longitude, last_point.latitude)
        arr_icao = arr_loc.get('icao_code', 'UNKN') if arr_loc else 'UNKN'
        logger.info(f"Entry {entry.id}: arrival geocoding result: {arr_icao} (location: {arr_loc})")
        
        changed = False
        
        # Check if departure airport needs updating
        should_update_dep = (
            entry.departure_airport in ['UNKN', 'UNKNOWN', None, ''] or  # Empty/unknown values
            (entry.departure_airport and len(entry.departure_airport) == 4 and entry.departure_airport.islower())  # Lowercase ICAO codes
        )
        
        if should_update_dep and dep_icao != 'UNKN':
            logger.info(f"Entry {entry.id}: updating departure from '{entry.departure_airport}' to '{dep_icao}'")
            entry.departure_airport = dep_icao
            changed = True
        else:
            logger.info(f"Entry {entry.id}: departure not updated (current: '{entry.departure_airport}', found: '{dep_icao}')")
            
        # Check if arrival airport needs updating  
        should_update_arr = (
            entry.arrival_airport in ['UNKN', 'UNKNOWN', None, ''] or  # Empty/unknown values
            (entry.arrival_airport and len(entry.arrival_airport) == 4 and entry.arrival_airport.islower())  # Lowercase ICAO codes
        )
        
        if should_update_arr and arr_icao != 'UNKN':
            logger.info(f"Entry {entry.id}: updating arrival from '{entry.arrival_airport}' to '{arr_icao}'")
            entry.arrival_airport = arr_icao
            changed = True
        else:
            logger.info(f"Entry {entry.id}: arrival not updated (current: '{entry.arrival_airport}', found: '{arr_icao}')")
        
        if changed:
            logger.info(f"Entry {entry.id}: set departure={dep_icao}, arrival={arr_icao}")
            updated += 1
            
    try:
        db.session.commit()
        logger.info(f"Committed updates for {updated} entries.")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to commit: {e}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        update_departure_arrival_airports()
