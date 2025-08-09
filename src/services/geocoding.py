"""
Geocoding service for KanardiaCloud.

This module provides reverse geocoding functionality combining aviation-specific
data with external API fallbacks for comprehensive location intelligence.
"""

import logging
import math
import requests
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AviationGeocoder:
    """Aviation-focused reverse geocoder using ICAO airfield database."""
    
    # Enhanced ICAO airfields database for Central Europe
    ICAO_AIRFIELDS = {
        # Slovenia
        'LJLJ': {'name': 'Ljubljana Airport', 'lat': 46.2237, 'lon': 14.4576},
        'LJMB': {'name': 'Maribor Airport', 'lat': 46.4798, 'lon': 15.6866},
        'LJPZ': {'name': 'Portorož Airport', 'lat': 45.4733, 'lon': 13.6150},
        'LJCE': {'name': 'Celje Airport', 'lat': 46.2256, 'lon': 15.2522},
        
        # Austria
        'LOWW': {'name': 'Vienna International Airport', 'lat': 48.1103, 'lon': 16.5697},
        'LOWS': {'name': 'Salzburg Airport', 'lat': 47.7933, 'lon': 13.0042},
        'LOWI': {'name': 'Innsbruck Airport', 'lat': 47.2602, 'lon': 11.3540},
        'LOWG': {'name': 'Graz Airport', 'lat': 46.9911, 'lon': 15.4396},
        'LOWL': {'name': 'Linz Airport', 'lat': 48.2332, 'lon': 14.1875},
        'LOWK': {'name': 'Klagenfurt Airport', 'lat': 46.6425, 'lon': 14.3377},
        
        # Italy
        'LIPZ': {'name': 'Venice Marco Polo Airport', 'lat': 45.5053, 'lon': 12.3519},
        'LIPH': {'name': 'Treviso Airport', 'lat': 45.6484, 'lon': 12.1944},
        'LIPB': {'name': 'Bolzano Airport', 'lat': 46.4602, 'lon': 11.3264},
        'LIPU': {'name': 'Udine Airport', 'lat': 46.0347, 'lon': 13.1806},
        'LIMC': {'name': 'Milan Malpensa Airport', 'lat': 45.6306, 'lon': 8.7281},
        
        # Croatia
        'LDZA': {'name': 'Zagreb Airport', 'lat': 46.9981, 'lon': 16.0689},
        'LDPL': {'name': 'Pula Airport', 'lat': 44.8935, 'lon': 13.9220},
        'LDRI': {'name': 'Rijeka Airport', 'lat': 45.2169, 'lon': 14.5703},
        
        # Hungary
        'LHBP': {'name': 'Budapest Ferenc Liszt International Airport', 'lat': 47.4369, 'lon': 19.2556},
    }
    
    # Regional boundaries for fallback identification
    REGIONS = {
        'Slovenia': {'lat_range': (45.4, 46.9), 'lon_range': (13.4, 16.6)},
        'Austria': {'lat_range': (46.4, 49.0), 'lon_range': (9.5, 17.2)},
        'Italy': {'lat_range': (44.0, 47.1), 'lon_range': (6.6, 18.5)},
        'Croatia': {'lat_range': (42.4, 46.5), 'lon_range': (13.5, 19.4)},
        'Hungary': {'lat_range': (45.7, 48.6), 'lon_range': (16.1, 22.9)},
        'Germany': {'lat_range': (47.3, 55.1), 'lon_range': (5.9, 15.0)},
    }
    
    def reverse_geocode(self, lat: float, lon: float) -> str:
        """
        Get aviation-focused location description.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Human-readable location description
        """
        # Check for nearby ICAO airfields
        nearest_airfield = self._find_nearest_airfield(lat, lon)
        if nearest_airfield:
            distance_km = nearest_airfield['distance']
            if distance_km < 2.0:
                return f"{nearest_airfield['icao']} - {nearest_airfield['name']}"
            else:
                return f"Near {nearest_airfield['icao']} - {nearest_airfield['name']} ({distance_km:.1f}km)"
        
        # Fall back to region detection
        region = self._get_region_name(lat, lon)
        return f"{region} ({lat:.3f}°, {lon:.3f}°)"
    
    def _find_nearest_airfield(self, lat: float, lon: float, max_distance_km: float = 25.0) -> Optional[Dict[str, Any]]:
        """
        Find nearest ICAO airfield within specified distance.
        
        Args:
            lat: Target latitude
            lon: Target longitude
            max_distance_km: Maximum search distance in kilometers
            
        Returns:
            Dictionary with airfield info and distance, or None if none found
        """
        nearest_airfield = None
        min_distance = float('inf')
        
        for icao_code, airfield_data in self.ICAO_AIRFIELDS.items():
            distance = self._calculate_distance(
                lat, lon,
                airfield_data['lat'], airfield_data['lon']
            )
            
            if distance < min_distance and distance <= max_distance_km:
                min_distance = distance
                nearest_airfield = {
                    'icao': icao_code,
                    'name': airfield_data['name'],
                    'distance': distance,
                    'lat': airfield_data['lat'],
                    'lon': airfield_data['lon']
                }
        
        return nearest_airfield
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula.
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in kilometers
        """
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def _get_region_name(self, lat: float, lon: float) -> str:
        """
        Identify region based on coordinate boundaries.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Region name or 'Unknown Region'
        """
        for region_name, bounds in self.REGIONS.items():
            lat_min, lat_max = bounds['lat_range']
            lon_min, lon_max = bounds['lon_range']
            
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return region_name
        
        return 'Unknown Region'


class NominatimGeocoder:
    """OpenStreetMap Nominatim reverse geocoder with caching."""
    
    def __init__(self, cache_duration_hours: int = 24):
        """
        Initialize Nominatim geocoder.
        
        Args:
            cache_duration_hours: How long to cache results
        """
        self.base_url = "https://nominatim.openstreetmap.org/reverse"
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[str]:
        """
        Reverse geocode using Nominatim API with caching.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Human-readable location or None if error
        """
        # Create cache key (rounded to ~100m precision)
        cache_key = f"{lat:.4f},{lon:.4f}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if datetime.now() - cached_result['timestamp'] < self.cache_duration:
                logger.debug(f"Using cached location for {cache_key}")
                return cached_result['location']
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        # Make API request
        try:
            location = self._fetch_from_api(lat, lon)
            if location:
                # Cache the result
                self.cache[cache_key] = {
                    'location': location,
                    'timestamp': datetime.now()
                }
                logger.debug(f"Cached new location for {cache_key}: {location}")
            return location
        except Exception as e:
            logger.warning(f"Nominatim API request failed: {e}")
            return None
    
    def _fetch_from_api(self, lat: float, lon: float) -> Optional[str]:
        """
        Fetch location from Nominatim API.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Formatted location string or None
        """
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'json',
            'addressdetails': 1,
            'zoom': 14,  # City/town level
            'accept-language': 'en'
        }
        
        headers = {
            'User-Agent': 'KanardiaCloud/1.0 (aviation@kanardia.eu)'
        }
        
        response = requests.get(
            self.base_url,
            params=params,
            headers=headers,
            timeout=3  # Quick timeout for non-critical feature
        )
        response.raise_for_status()
        
        data = response.json()
        return self._parse_nominatim_response(data)
    
    def _parse_nominatim_response(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Parse Nominatim response to extract meaningful location.
        
        Args:
            data: Raw Nominatim response
            
        Returns:
            Formatted location string or None
        """
        if not data or 'address' not in data:
            return None
        
        address = data['address']
        
        # Extract location components in order of preference
        city = (address.get('city') or 
                address.get('town') or 
                address.get('village') or 
                address.get('municipality') or
                address.get('hamlet'))
        
        state = (address.get('state') or 
                 address.get('region') or
                 address.get('county'))
        
        country = address.get('country')
        
        # Build location string
        parts = []
        if city:
            parts.append(city)
        elif state:
            parts.append(state)
        
        if country:
            parts.append(country)
        
        if parts:
            return ', '.join(parts)
        
        return None


class HybridReverseGeocoder:
    """
    Hybrid reverse geocoder combining aviation database with API fallback.
    
    This class provides comprehensive location intelligence by first checking
    aviation-specific databases and falling back to external APIs when needed.
    """
    
    def __init__(self, use_nominatim_fallback: bool = True):
        """
        Initialize hybrid geocoder.
        
        Args:
            use_nominatim_fallback: Whether to use Nominatim as fallback
        """
        self.aviation_geocoder = AviationGeocoder()
        self.nominatim_geocoder = NominatimGeocoder() if use_nominatim_fallback else None
        self.use_nominatim_fallback = use_nominatim_fallback
    
    def reverse_geocode(self, lat: float, lon: float) -> str:
        """
        Get location description using hybrid approach.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Human-readable location description
        """
        # First try aviation-specific lookup
        aviation_result = self.aviation_geocoder.reverse_geocode(lat, lon)
        
        # If aviation lookup gives coordinate fallback and we have Nominatim enabled
        if (self.use_nominatim_fallback and 
            self.nominatim_geocoder and 
            "°" in aviation_result):
            
            try:
                api_result = self.nominatim_geocoder.reverse_geocode(lat, lon)
                if api_result:
                    logger.debug(f"Enhanced location via Nominatim: {api_result}")
                    return api_result
            except Exception as e:
                logger.warning(f"Nominatim fallback failed: {e}")
        
        return aviation_result
    
    def get_nearest_airfield(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Get nearest airfield information.
        
        Args:
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Airfield information or None if none nearby
        """
        return self.aviation_geocoder._find_nearest_airfield(lat, lon)


# Global geocoder instance
_geocoder_instance: Optional[HybridReverseGeocoder] = None


def get_geocoder() -> HybridReverseGeocoder:
    """
    Get singleton geocoder instance.
    
    Returns:
        HybridReverseGeocoder instance
    """
    global _geocoder_instance
    if _geocoder_instance is None:
        _geocoder_instance = HybridReverseGeocoder(use_nominatim_fallback=True)
    return _geocoder_instance


def reverse_geocode(lat: float, lon: float) -> str:
    """
    Convenience function for reverse geocoding.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Human-readable location description
    """
    geocoder = get_geocoder()
    return geocoder.reverse_geocode(lat, lon)
