#!/usr/bin/env python3
"""
Migration script to populate airfield database from hardcoded data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import create_app
from src.models import db, Airfield

# Hardcoded airfield data to migrate
ICAO_AIRFIELDS = {
    # Slovenia
    'LJLJ': {'name': 'Ljubljana Airport', 'lat': 46.2237, 'lon': 14.4576, 'country': 'Slovenia', 'region': 'Central Europe'},
    'LJMB': {'name': 'Maribor Airport', 'lat': 46.4798, 'lon': 15.6866, 'country': 'Slovenia', 'region': 'Central Europe'},
    'LJPZ': {'name': 'Portorož Airport', 'lat': 45.4733, 'lon': 13.6150, 'country': 'Slovenia', 'region': 'Central Europe'},
    'LJCE': {'name': 'Celje Airport', 'lat': 46.2256, 'lon': 15.2522, 'country': 'Slovenia', 'region': 'Central Europe'},
    
    # Austria
    'LOWW': {'name': 'Vienna International Airport', 'lat': 48.1103, 'lon': 16.5697, 'country': 'Austria', 'region': 'Central Europe'},
    'LOWS': {'name': 'Salzburg Airport', 'lat': 47.7933, 'lon': 13.0042, 'country': 'Austria', 'region': 'Central Europe'},
    'LOWI': {'name': 'Innsbruck Airport', 'lat': 47.2602, 'lon': 11.3540, 'country': 'Austria', 'region': 'Central Europe'},
    'LOWG': {'name': 'Graz Airport', 'lat': 46.9911, 'lon': 15.4396, 'country': 'Austria', 'region': 'Central Europe'},
    'LOWL': {'name': 'Linz Airport', 'lat': 48.2332, 'lon': 14.1875, 'country': 'Austria', 'region': 'Central Europe'},
    'LOWK': {'name': 'Klagenfurt Airport', 'lat': 46.6425, 'lon': 14.3377, 'country': 'Austria', 'region': 'Central Europe'},
    
    # Italy
    'LIPZ': {'name': 'Venice Marco Polo Airport', 'lat': 45.5053, 'lon': 12.3519, 'country': 'Italy', 'region': 'Central Europe'},
    'LIPH': {'name': 'Treviso Airport', 'lat': 45.6484, 'lon': 12.1944, 'country': 'Italy', 'region': 'Central Europe'},
    'LIPB': {'name': 'Bolzano Airport', 'lat': 46.4602, 'lon': 11.3264, 'country': 'Italy', 'region': 'Central Europe'},
    'LIPU': {'name': 'Udine Airport', 'lat': 46.0347, 'lon': 13.1806, 'country': 'Italy', 'region': 'Central Europe'},
    'LIMC': {'name': 'Milan Malpensa Airport', 'lat': 45.6306, 'lon': 8.7281, 'country': 'Italy', 'region': 'Central Europe'},
    
    # Croatia
    'LDZA': {'name': 'Zagreb Airport', 'lat': 46.9981, 'lon': 16.0689, 'country': 'Croatia', 'region': 'Central Europe'},
    'LDPL': {'name': 'Pula Airport', 'lat': 44.8935, 'lon': 13.9220, 'country': 'Croatia', 'region': 'Central Europe'},
    'LDRI': {'name': 'Rijeka Airport', 'lat': 45.2169, 'lon': 14.5703, 'country': 'Croatia', 'region': 'Central Europe'},
    
    # Hungary
    'LHBP': {'name': 'Budapest Ferenc Liszt International Airport', 'lat': 47.4369, 'lon': 19.2556, 'country': 'Hungary', 'region': 'Central Europe'},
}

def migrate_airfields():
    """Migrate hardcoded airfield data to database."""
    app = create_app()
    with app.app_context():
        print("Migrating airfield data to database...")
        
        created_count = 0
        updated_count = 0
        
        for icao_code, data in ICAO_AIRFIELDS.items():
            # Check if airfield already exists
            existing_airfield = Airfield.query.filter_by(icao_code=icao_code).first()
            
            if existing_airfield:
                # Update existing airfield
                existing_airfield.name = data['name']
                existing_airfield.latitude = data['lat']
                existing_airfield.longitude = data['lon']
                existing_airfield.country = data.get('country')
                existing_airfield.region = data.get('region')
                existing_airfield.is_active = True
                updated_count += 1
                print(f"  Updated: {icao_code} - {data['name']}")
            else:
                # Create new airfield
                airfield = Airfield(
                    icao_code=icao_code,
                    name=data['name'],
                    latitude=data['lat'],
                    longitude=data['lon'],
                    country=data.get('country'),
                    region=data.get('region'),
                    is_active=True
                )
                db.session.add(airfield)
                created_count += 1
                print(f"  Created: {icao_code} - {data['name']}")
        
        # Commit changes
        db.session.commit()
        
        print(f"\nMigration completed:")
        print(f"  Created: {created_count} airfields")
        print(f"  Updated: {updated_count} airfields")
        print(f"  Total: {created_count + updated_count} airfields")

if __name__ == '__main__':
    migrate_airfields()
