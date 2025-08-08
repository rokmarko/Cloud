"""
ThingsBoard sync service for logbook entries
"""

import requests
import json
import logging
import os
from datetime import datetime, date, timedelta, time
from typing import List, Dict, Any, Optional
from src.app import db
from src.models import Device, LogbookEntry, User, Pilot, Event
from flask import current_app


logger = logging.getLogger(__name__)


class ThingsBoardSyncService:
    """Service for syncing logbook entries from ThingsBoard server."""
    
    def __init__(self):
        self.base_url = os.getenv('THINGSBOARD_URL', 'https://aetos.kanardia.eu:8088')
        self.username = os.getenv('THINGSBOARD_USERNAME', 'tenant@thingsboard.local')
        self.password = os.getenv('THINGSBOARD_PASSWORD', 'tenant')
        # self.tenant_id = os.getenv('THINGSBOARD_TENANT_ID', 'tenant')
        self.timeout = 30  # seconds
        self._jwt_token = None
        self._token_expires_at = None
        self._last_auth_check = None
        self._last_auth_error = None
    
    def _authenticate(self) -> Optional[str]:
        """
        Authenticate with ThingsBoard and get JWT token.
        
        Returns:
            JWT token string or None if authentication failed
        """
        # Check if we have a valid token that hasn't expired
        if (self._jwt_token and self._token_expires_at and 
            datetime.now() < self._token_expires_at):
            return self._jwt_token
        
        auth_url = f"{self.base_url}/api/auth/login"
        
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'KanardiaCloud/1.0'
        }
        
        try:
            logger.debug(f"Authenticating with ThingsBoard as {self.username}")
            
            # Update last check time
            self._last_auth_check = datetime.now()
            self._last_auth_error = None
            
            response = requests.post(
                url=auth_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            auth_data = response.json()
            
            # Extract JWT token
            self._jwt_token = auth_data.get('token')
            if not self._jwt_token:
                error_msg = "No JWT token received from ThingsBoard authentication"
                logger.error(error_msg)
                self._last_auth_error = error_msg
                return None
            
            # Calculate token expiration (tokens usually expire in 1 hour, but we'll refresh every 45 minutes)
            self._token_expires_at = datetime.now() + timedelta(minutes=45)
            
            logger.info("Successfully authenticated with ThingsBoard")
            return self._jwt_token
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP error during ThingsBoard authentication: {str(e)}"
            logger.error(error_msg)
            self._jwt_token = None
            self._token_expires_at = None
            self._last_auth_error = error_msg
            return None
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON response during ThingsBoard authentication: {str(e)}"
            logger.error(error_msg)
            self._jwt_token = None
            self._token_expires_at = None
            self._last_auth_error = error_msg
            return None
        except Exception as e:
            error_msg = f"Unexpected error during ThingsBoard authentication: {str(e)}"
            logger.error(error_msg)
            self._jwt_token = None
            self._token_expires_at = None
            self._last_auth_error = error_msg
            return None
    
    def test_authentication(self) -> bool:
        """
        Test if authentication with ThingsBoard is working.
        
        Returns:
            True if authentication successful, False otherwise
        """
        jwt_token = self._authenticate()
        return jwt_token is not None
    
    def get_authentication_status(self) -> Dict[str, Any]:
        """
        Get current authentication status information.
        
        Returns:
            Dictionary with authentication status details
        """
        return {
            'authenticated': self._jwt_token is not None,
            'token_expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None,
            'last_check': self._last_auth_check,
            'error': self._last_auth_error,
            'base_url': self.base_url,
            'username': self.username,
            # 'tenant_id': self.tenant_id
        }
    
    def sync_all_devices(self) -> Dict[str, Any]:
        """
        Sync logbook entries and events for all devices with external_device_id.
        
        Returns:
            Dict with sync results and statistics
        """
        results = {
            'synced_devices': 0,
            'total_devices': 0,
            'new_entries': 0,
            'total_entries': 0,
            'new_events': 0,
            'total_events': 0,
            'new_logbook_entries': 0,
            'errors': []
        }
        
        try:
            # Get all active devices with external_device_id
            devices = Device.query.filter(
                Device.is_active == True,
                Device.external_device_id.isnot(None),
                Device.external_device_id != ''
            ).all()
            
            results['total_devices'] = len(devices)
            
            for device in devices:
                try:
                    # Sync logbook entries
                    # device_result = self.sync_device(device)
                    
                    # Sync events
                    events_result = self.sync_device_events(device)
                    
                    results['synced_devices'] += 1
                    # results['new_entries'] += device_result.get('new_entries', 0)
                    # results['total_entries'] += device_result.get('total_entries', 0)
                    results['new_events'] += events_result.get('new_events', 0)
                    results['total_events'] += events_result.get('total_events', 0)
                    results['new_logbook_entries'] += events_result.get('new_logbook_entries', 0)
                    
                    # Combine errors
                    # results['errors'].extend(device_result.get('errors', []))
                    results['errors'].extend(events_result.get('errors', []))
                    
                except Exception as e:
                    error_msg = f"Failed to sync device {device.name} (ID: {device.external_device_id}): {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Sync completed: {results['synced_devices']}/{results['total_devices']} devices, "
                       f"{results['new_entries']} new entries, {results['new_events']} new events, "
                       f"{results['new_logbook_entries']} new logbook entries")
            
        except Exception as e:
            error_msg = f"Fatal error during sync: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def _is_device_active_in_thingsboard(self, device_id: str) -> bool:
        """
        Check if device is active in ThingsBoard using telemetry API.
        
        Args:
            device_id: External device ID in ThingsBoard
            
        Returns:
            True if device is active, False otherwise
        """
        # Authenticate and get JWT token
        jwt_token = self._authenticate()
        if not jwt_token:
            logger.error("Failed to authenticate with ThingsBoard for device activity check")
            return False
        
        # ThingsBoard telemetry API endpoint for device attributes
        url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{device_id}/values/attributes?keys=active"
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {jwt_token}',
            'X-Authorization': f'Bearer {jwt_token}',
            'User-Agent': 'KanardiaCloud/1.0'
        }
        
        # Add query parameter to get only the 'active' attribute
        # params = {'keys': 'active'}
        
        try:
            logger.debug(f"Checking device activity status for device {device_id}")
            
            response = requests.get(
                url=url,
                headers=headers,
                # params=params,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            data = response.json()
            
            # Check if 'active' attribute exists and is true
            if isinstance(data, list) and len(data) > 0:
                active_attr = data[0]
                if active_attr.get('key') == 'active':
                    is_active = active_attr.get('value', False)
                    logger.debug(f"Device {device_id} active status: {is_active}")
                    return is_active
            
            # If no active attribute found, log warning and assume inactive
            logger.warning(f"No 'active' attribute found for device {device_id}, assuming inactive")
            return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error checking device activity for {device_id}: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response checking device activity for {device_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking device activity for {device_id}: {str(e)}")
            return False
    
    def sync_device(self, device: Device) -> Dict[str, Any]:
        """
        Sync logbook entries for a specific device.
        
        Args:
            device: Device model instance with external_device_id
            
        Returns:
            Dict with sync results for this device
        """
        result = {
            'device_id': device.id,
            'external_device_id': device.external_device_id,
            'total_entries': 0,
            'new_entries': 0,
            'errors': []
        }
        
        try:
            # Call ThingsBoard RPC API
            logbook_data = self._call_thingsboard_api(device.external_device_id)
            
            if not logbook_data:
                logger.warning(f"No data returned for device {device.external_device_id}")
                return result
            
            result['total_entries'] = len(logbook_data)
            
            # Process each logbook entry
            for entry_data in logbook_data:
                try:
                    if self._create_logbook_entry(device, entry_data):
                        result['new_entries'] += 1
                except Exception as e:
                    error_msg = f"Failed to process entry for device {device.external_device_id}: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            # Commit all changes for this device
            db.session.commit()
            
            logger.info(f"Device {device.name}: {result['new_entries']}/{result['total_entries']} new entries")
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to sync device {device.external_device_id}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result
    
    def _call_thingsboard_api(self, device_id: str) -> Optional[List[Dict[str, Any]]]:
        """
        Call ThingsBoard RPC API to get logbook entries.
        
        Args:
            device_id: External device ID in ThingsBoard
            
        Returns:
            List of logbook entry dictionaries or None if error
        """
        # First check if device is active in ThingsBoard
        if not self._is_device_active_in_thingsboard(device_id):
            logger.info(f"Device {device_id} is not active in ThingsBoard, skipping RPC call")
            return None
        
        # Authenticate and get JWT token
        jwt_token = self._authenticate()
        if not jwt_token:
            logger.error("Failed to authenticate with ThingsBoard")
            return None
        
        url = f"{self.base_url}/api/rpc/twoway/{device_id}"
        
        payload = {
            "method": "syncLog",
            "params": { "count": 200 }  # Adjust count as needed
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {jwt_token}',
            'X-Authorization': f'Bearer {jwt_token}',
            'User-Agent': 'KanardiaCloud/1.0'
        }
        
        try:
            logger.debug(f"Calling ThingsBoard API for device {device_id}")
            
            response = requests.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            data = response.json()
            
            # Validate response format
            if not isinstance(data, list):
                logger.error(f"Expected list response from ThingsBoard, got {type(data)}")
                return None
            
            logger.debug(f"Retrieved {len(data)} entries from ThingsBoard for device {device_id}")
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling ThingsBoard API for device {device_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error calling ThingsBoard API for device {device_id}: {str(e)}")
            # If we get an authentication error, clear the token and try once more
            if hasattr(e, 'response') and e.response and e.response.status_code in [401, 403]:
                logger.info("Authentication failed, clearing token and retrying...")
                self._jwt_token = None
                self._token_expires_at = None
                # Could implement one retry here, but for now just return None
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from ThingsBoard for device {device_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling ThingsBoard API for device {device_id}: {str(e)}")
            return None
    
    def _create_logbook_entry(self, device: Device, entry_data: Dict[str, Any]) -> bool:
        """
        Create a logbook entry from ThingsBoard data.
        
        Args:
            device: Device model instance
            entry_data: Dictionary with logbook entry data from ThingsBoard
            
        Returns:
            True if new entry was created, False if it already exists
        """
        try:
            # Extract required fields with validation
            date_str = entry_data.get('date')
            if not date_str:
                raise ValueError("Missing required field: date")
            
            # Parse date (support various formats)
            entry_date = self._parse_date(date_str)
            
            # Use device information for aircraft details (preferred) or fall back to entry data
            aircraft_registration = device.registration or entry_data.get('aircraft_registration', 'UNKNOWN')
            aircraft_type = device.model or entry_data.get('aircraft_type', 'UNKNOWN')
            
            # Override with entry data if explicitly provided and device info is missing
            if not device.registration and entry_data.get('aircraft_registration'):
                aircraft_registration = entry_data.get('aircraft_registration')
            if not device.model and entry_data.get('aircraft_type'):
                aircraft_type = entry_data.get('aircraft_type')
                
            departure_airport = entry_data.get('departure_airport', 'UNKNOWN')
            arrival_airport = entry_data.get('arrival_airport', 'UNKNOWN')
            
            # Extract pilot name from entry data
            pilot_name = entry_data.get('pilot_name') or entry_data.get('pilot') or entry_data.get('pic_name')
            
            # Parse takeoff and landing times
            takeoff_time = self._parse_time(entry_data.get('takeoff_time'))
            landing_time = self._parse_time(entry_data.get('landing_time'))
            
            # Calculate flight_time for database (required field)
            flight_time = 0.0
            
            # Create datetime objects
            takeoff_datetime = None
            landing_datetime = None
            
            # If times are not provided, try to extract from flight_time (for backward compatibility)
            if not takeoff_time or not landing_time:
                flight_time = float(entry_data.get('flight_time', 0))
                if flight_time <= 0:
                    raise ValueError("Invalid flight_time or missing takeoff/landing times")
                
                # Default takeoff time to 10:00 AM if not provided
                if not takeoff_time:
                    from datetime import time
                    takeoff_time = time(10, 0)
                
                # Calculate landing time from flight duration if not provided
                if not landing_time:
                    from datetime import datetime, timedelta
                    takeoff_dt = datetime.combine(entry_date, takeoff_time)
                    landing_dt = takeoff_dt + timedelta(hours=flight_time)
                    landing_time = landing_dt.time()
                
                # Create final datetime objects
                takeoff_datetime = datetime.combine(entry_date, takeoff_time)
                landing_datetime = datetime.combine(entry_date, landing_time)
            else:
                # Calculate flight_time from takeoff and landing times
                from datetime import datetime, timedelta
                takeoff_datetime = datetime.combine(entry_date, takeoff_time)
                landing_datetime = datetime.combine(entry_date, landing_time)
                
                # Handle flights that cross midnight
                if landing_datetime < takeoff_datetime:
                    landing_datetime += timedelta(days=1)
                
                # Calculate flight duration in hours
                flight_duration = landing_datetime - takeoff_datetime
                flight_time = round(flight_duration.total_seconds() / 3600, 2)
            
            # Check if entry already exists (avoid duplicates)
            # For synced entries, check by device, takeoff/landing datetime
            existing_entry = LogbookEntry.query.filter_by(
                device_id=device.id,
                takeoff_datetime=takeoff_datetime,
                landing_datetime=landing_datetime
            ).first()
            
            if existing_entry:
                logger.debug(f"Logbook entry already exists for device {device.name} on {entry_date}")
                return False
            
            # Create new logbook entry
            # Determine user_id: use pilot mapping if available, otherwise device owner
            # But only if no pilot name is specified or pilot is mapped
            pilot_user_id = None
            if pilot_name:
                pilot_user_id = self._resolve_pilot_user(device, pilot_name)
            
            # Set user_id based on pilot resolution
            if pilot_name and pilot_user_id is None:
                # Unknown pilot - don't assign to anyone
                entry_user_id = None
            elif pilot_user_id:
                # Known pilot mapping
                entry_user_id = pilot_user_id
            else:
                # No pilot name specified - assign to device owner
                entry_user_id = device.user_id
            
            logbook_entry = LogbookEntry(
                takeoff_datetime=takeoff_datetime,
                landing_datetime=landing_datetime,
                aircraft_type=aircraft_type,
                aircraft_registration=aircraft_registration,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                flight_time=flight_time,
                pilot_in_command_time=float(entry_data.get('pilot_in_command_time', flight_time)),
                dual_time=float(entry_data.get('dual_time', 0)),
                instrument_time=float(entry_data.get('instrument_time', 0)),
                night_time=float(entry_data.get('night_time', 0)),
                cross_country_time=float(entry_data.get('cross_country_time', 0)),
                landings_day=int(entry_data.get('landings_day', 0)),
                landings_night=int(entry_data.get('landings_night', 0)),
                remarks=entry_data.get('remarks', f'Synced from ThingsBoard device {device.name}'),
                pilot_name=pilot_name,  # Add pilot name from entry data
                user_id=entry_user_id,  # Use resolved user_id (may be None for unknown pilots)
                device_id=device.id  # Link to the syncing device
            )
            
            db.session.add(logbook_entry)
            
            logger.debug(f"Created new logbook entry for device {device.name} ({aircraft_registration}) on {entry_date}"
                        f"{f' for pilot {pilot_name}' if pilot_name else ''}")
            return True
            
        except (ValueError, TypeError, KeyError) as e:
            logger.error(f"Invalid logbook entry data: {str(e)}")
            logger.debug(f"Entry data: {entry_data}")
            raise
    
    def _parse_date(self, date_str: str) -> date:
        """
        Parse date string in various formats.
        
        Args:
            date_str: Date string to parse
            
        Returns:
            Parsed date object
        """
        # Common date formats to try
        formats = [
            '%Y-%m-%d',           # 2025-07-24
            '%d.%m.%Y',           # 24.07.2025
            '%d/%m/%Y',           # 24/07/2025
            '%m/%d/%Y',           # 07/24/2025
            '%Y-%m-%d %H:%M:%S',  # 2025-07-24 10:30:00
            '%Y-%m-%dT%H:%M:%S',  # 2025-07-24T10:30:00
        ]
        
        for fmt in formats:
            try:
                parsed_datetime = datetime.strptime(date_str, fmt)
                return parsed_datetime.date()
            except ValueError:
                continue
        
        # If no format matches, try ISO format parsing
        try:
            parsed_datetime = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return parsed_datetime.date()
        except ValueError:
            pass
        
        raise ValueError(f"Unable to parse date: {date_str}")

    def _parse_time(self, time_str: Optional[str]) -> Optional[time]:
        """
        Parse time string in various formats.
        
        Args:
            time_str: Time string to parse
            
        Returns:
            Parsed time object or None if invalid
        """
        if not time_str:
            return None
        
        from datetime import time
        
        # Common time formats to try
        formats = [
            '%H:%M:%S',    # 10:30:00
            '%H:%M',       # 10:30
            '%H.%M.%S',    # 10.30.00
            '%H.%M',       # 10.30
            '%I:%M:%S %p', # 10:30:00 AM
            '%I:%M %p',    # 10:30 AM
        ]
        
        for fmt in formats:
            try:
                parsed_time = datetime.strptime(time_str, fmt).time()
                return parsed_time
            except ValueError:
                continue
        
        # Try parsing as HH:MM without AM/PM
        try:
            parts = time_str.split(':')
            if len(parts) >= 2:
                hour = int(parts[0])
                minute = int(parts[1])
                second = int(parts[2]) if len(parts) > 2 else 0
                
                if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                    return time(hour, minute, second)
        except (ValueError, IndexError):
            pass
        
        logger.warning(f"Unable to parse time: {time_str}")
        return None
    
    def _resolve_pilot_user(self, device: Device, pilot_name: str) -> Optional[int]:
        """
        Resolve pilot name to user ID, creating pilot mapping if needed.
        
        Args:
            device: Device instance
            pilot_name: Name of the pilot from logbook entry
            
        Returns:
            User ID of the pilot, or None if not resolved
        """
        try:
            # Check if pilot mapping already exists
            pilot_mapping = Pilot.query.filter_by(
                pilot_name=pilot_name,
                device_id=device.id
            ).first()
            
            if pilot_mapping:
                logger.debug(f"Found existing pilot mapping: {pilot_name} -> User {pilot_mapping.user_id}")
                return pilot_mapping.user_id
            
            # No pilot mapping found - do not fall back to device owner
            # This allows entries with unknown pilots to remain unlinked
            logger.info(f"No pilot mapping found for '{pilot_name}' on device {device.name}, entry will remain unlinked")
            return None
            
        except Exception as e:
            logger.error(f"Error resolving pilot user for '{pilot_name}': {str(e)}")
            return None  # Do not fall back to device owner

    def sync_device_events(self, device: Device) -> Dict[str, Any]:
        """
        Sync events for a specific device.
        
        Args:
            device: Device model instance with external_device_id
            
        Returns:
            Dict with sync results for device events
        """
        result = {
            'device_id': device.id,
            'external_device_id': device.external_device_id,
            'total_events': 0,
            'new_events': 0,
            'errors': []
        }
        
        try:
            # Call ThingsBoard RPC API for events
            events_data = self._call_thingsboard_events_api(device.external_device_id, device.current_logger_page or 0)
            
            events_list = []
            if events_data:
                # Extract current logger page if provided
                if isinstance(events_data, dict) and 'log_position' in events_data:
                    device.current_logger_page = events_data.get('log_position', 0)
                    device.updated_at = datetime.utcnow()
                    events_list = events_data.get('events', [])
                else:
                    events_list = events_data if isinstance(events_data, list) else []
            else:
                logger.warning(f"No events data received for device {device.name}")
            
            result['total_events'] = len(events_list)
            
            # Process each event
            for event in events_list:
                if self._process_device_event(device, event):
                    result['new_events'] += 1
            
            # Only process new logbook entries from new events (not rebuild everything)
            if result['new_events'] > 0:
                logger.info(f"Processing logbook entries from new events for device {device.name}")
                try:
                    logbook_results = self._build_logbook_entries_from_new_events(device, result['new_events'])
                    result['new_logbook_entries'] = logbook_results.get('new_entries', 0)
                    result['updated_logbook_entries'] = logbook_results.get('updated_entries', 0)
                    if logbook_results.get('errors'):
                        result['errors'].extend(logbook_results['errors'])
                    
                    logger.info(f"New logbook entries from events for device {device.name}: "
                               f"{result.get('new_logbook_entries', 0)} new entries")
                except Exception as e:
                    error_msg = f"Failed to build logbook from new events for device {device.name}: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            else:
                logger.debug(f"No new events for device {device.name}, skipping logbook generation")
            
            # Commit all changes for this device
            db.session.commit()
            
            logger.info(f"Device {device.name} events: {result['new_events']}/{result['total_events']} new events")
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to sync events for device {device.external_device_id}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result

    def _call_thingsboard_events_api(self, device_id: str, last_event: int) -> Optional[Dict[str, Any]]:
        """
        Call ThingsBoard RPC API to get device events.
        
        Args:
            device_id: External device ID in ThingsBoard
            
        Returns:
            Events data dictionary or None if error
        """
        # First check if device is active in ThingsBoard
        if not self._is_device_active_in_thingsboard(device_id):
            logger.info(f"Device {device_id} is not active in ThingsBoard, skipping events RPC call")
            return None
        
        # Authenticate and get JWT token
        jwt_token = self._authenticate()
        if not jwt_token:
            logger.error("Failed to authenticate with ThingsBoard")
            return None
        
        url = f"{self.base_url}/api/rpc/twoway/{device_id}"
        
        payload = {
            "method": "syncEvents",
            "params": { "count": 5000, "last_event": last_event }
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {jwt_token}',
            'X-Authorization': f'Bearer {jwt_token}',
            'User-Agent': 'KanardiaCloud/1.0'
        }
        
        try:
       
            logger.debug(f"Calling ThingsBoard events API for device {device_id}")
            
            response = requests.post(
                url=url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            data = response.json()

            # If the response is a dict with a single key 'data', and the value is a string, try to decompress it
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], str):
                try:
                    import base64
                    import zlib
                    compressed = base64.b64decode(data['data'])
                    # qCompress adds a 4-byte Qt header, skip it
                    decompressed = zlib.decompress(compressed[4:])
                    # Try to decode as utf-8 and parse as JSON
                    data = json.loads(decompressed.decode('utf-8'))
                    logger.debug(f"Decompressed and loaded JSON data for device {device_id}")
                except Exception as e:
                    logger.error(f"Failed to decompress or decode ThingsBoard events data for device {device_id}: {str(e)}")
                    return None
            
            logger.debug(f"Retrieved events data from ThingsBoard for device {device_id}")
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout calling ThingsBoard events API for device {device_id}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error calling ThingsBoard events API for device {device_id}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from ThingsBoard events API for device {device_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calling ThingsBoard events API for device {device_id}: {str(e)}")
            return None

    def _process_device_event(self, device: Device, event_data: Dict[str, Any]) -> bool:
        """
        Process a single device event from ThingsBoard.
        
        Args:
            device: Device instance
            event_data: Event data dictionary from ThingsBoard
            
        Returns:
            True if new event was created, False if it already exists
        """
        try:
            # Extract event fields
            date_time_str = event_data.get('date_time')
            page_address = event_data.get('page')
            total_time = event_data.get('total_time')
            bitfield = event_data.get('bits', 0)
            message = event_data.get('message')  # Optional message field
            
            # Validate required fields (non-nullable)
            if page_address is None:
                logger.warning(f"Skipping event for device {device.name}: page_address is required")
                return False
            
            if total_time is None:
                logger.warning(f"Skipping event for device {device.name}: total_time is required")
                return False
            
            # Parse date_time if provided
            event_datetime = None
            if date_time_str:
                try:
                    # Try different datetime formats
                    for fmt in ['%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                        try:
                            event_datetime = datetime.strptime(date_time_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    logger.warning(f"Could not parse date_time '{date_time_str}' for device {device.name}: {str(e)}")
            
            # Check if event already exists (by page_address and device)
            existing_event = Event.query.filter_by(
                device_id=device.id,
                page_address=page_address
            ).first()
            
            if existing_event:
                logger.debug(f"Event already exists for device {device.name} at page {page_address}")
                return False
            
            # Create new event
            event = Event(
                date_time=event_datetime,
                page_address=page_address,
                total_time=total_time,
                bitfield=int(bitfield) if bitfield is not None else 0,
                message=message,  # Include message field
                device_id=device.id
            )
            
            db.session.add(event)
           
            # Log the event creation with active event types
            active_events = event.get_active_events()
            events_str = ', '.join(active_events) if active_events else 'None'
            logger.debug(f"Created event for device {device.name}: page={page_address}, events=[{events_str}]")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event for device {device.name}: {str(e)}")
            return False
    
    def _rebuild_complete_logbook_from_events(self, device: Device) -> Dict[str, Any]:
        """
        Rebuild complete logbook from ALL events for a device.
        This clears existing event-generated entries and recreates them from all events.
        
        Args:
            device: Device instance
            
        Returns:
            Dict with results of logbook entry rebuild
        """
        result = {
            'new_entries': 0,
            'updated_entries': 0,
            'removed_entries': 0,
            'errors': []
        }
        
        try:
            # Step 1: Clear existing event-generated logbook entries for this device
            # We identify event-generated entries by checking if they have a device_id and
            # contain specific text in remarks indicating they were generated from events
            existing_event_entries = LogbookEntry.query.filter(
                LogbookEntry.device_id == device.id,
                LogbookEntry.remarks.like('%Generated from device events%')
            ).all()
            
            logger.debug(f"Found {len(existing_event_entries)} existing event-generated logbook entries for device {device.name}")
            
            # Remove existing event-generated entries
            for entry in existing_event_entries:
                db.session.delete(entry)
                result['removed_entries'] += 1
            
            if result['removed_entries'] > 0:
                logger.info(f"Removed {result['removed_entries']} existing event-generated logbook entries for device {device.name}")
            
            # Step 2: Build new logbook entries from ALL events
            logbook_results = self._build_logbook_entries_from_events(device)
            result['new_entries'] = logbook_results.get('new_entries', 0)
            result['updated_entries'] = logbook_results.get('updated_entries', 0)
            if logbook_results.get('errors'):
                result['errors'].extend(logbook_results['errors'])
            
            logger.info(f"Logbook rebuild for device {device.name}: "
                       f"removed {result['removed_entries']}, created {result['new_entries']} entries")
            
            return result
            
        except Exception as e:
            error_msg = f"Error rebuilding complete logbook from events for device {device.name}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def _build_logbook_entries_from_new_events(self, device: Device, num_new_events: int) -> Dict[str, Any]:
        """
        Build logbook entries from the latest takeoff/landing event pairs (only new events).
        This is more efficient than rebuilding the entire logbook.
        
        Args:
            device: Device instance
            num_new_events: Number of new events that were just added
            
        Returns:
            Dict with results of logbook entry creation
        """
        result = {
            'new_entries': 0,
            'updated_entries': 0,
            'errors': []
        }
        
        try:
            # Get recent events (last processed + some overlap for sequence completion)
            # We need more than just the new events to ensure we can complete flight sequences
            lookback_buffer = max(20, num_new_events * 2)  # At least 20 events or 2x new events
            
            recent_events = Event.query.filter_by(device_id=device.id)\
                .order_by(Event.total_time.desc())\
                .limit(lookback_buffer).all()
            
            if not recent_events:
                logger.debug(f"No recent events found for device {device.name}")
                return result
            
            # Reverse to get chronological order for processing
            recent_events.reverse()
            
            # Filter for takeoff and landing events in chronological order
            takeoff_events = [e for e in recent_events if e.has_event_bit('Takeoff')]
            landing_events = [e for e in recent_events if e.has_event_bit('Landing')]
            
            logger.debug(f"Processing {len(takeoff_events)} takeoff and {len(landing_events)} landing events "
                        f"from recent {len(recent_events)} events for device {device.name}")
            
            if not takeoff_events or not landing_events:
                logger.debug(f"No complete takeoff/landing pairs in recent events for device {device.name}")
                return result
            
            # Build flight sequences from recent events
            flight_sequences = self._build_flight_sequences(takeoff_events, landing_events)
            
            logger.debug(f"Built {len(flight_sequences)} flight sequences from recent events for device {device.name}")
            
            # Only create logbook entries that don't already exist
            for sequence in flight_sequences:
                try:
                    # Check if this sequence already has a logbook entry
                    takeoff_event = sequence['takeoff_event']
                    final_landing_event = sequence['landing_events'][-1]
                    
                    # Calculate expected takeoff/landing times for duplicate check
                    if takeoff_event.date_time:
                        takeoff_datetime = takeoff_event.date_time
                        flight_duration_ms = final_landing_event.total_time - takeoff_event.total_time
                        landing_datetime = takeoff_datetime + timedelta(milliseconds=flight_duration_ms)
                    else:
                        # Skip sequences without datetime info
                        continue
                    
                    # Check if logbook entry already exists for this sequence
                    existing_entry = LogbookEntry.query.filter_by(
                        device_id=device.id,
                        takeoff_datetime=takeoff_datetime,
                        landing_datetime=landing_datetime
                    ).first()
                    
                    if not existing_entry:
                        if self._create_logbook_entry_from_events(device, sequence):
                            result['new_entries'] += 1
                            logger.debug(f"Created new logbook entry from recent events for device {device.name}")
                    else:
                        logger.debug(f"Logbook entry already exists for sequence starting at {takeoff_event.total_time}ms")
                        
                except Exception as e:
                    error_msg = f"Failed to create logbook entry from recent events: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            return result
            
        except Exception as e:
            error_msg = f"Error building logbook entries from new events for device {device.name}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result

    def _build_logbook_entries_from_events(self, device: Device) -> Dict[str, Any]:
        """
        Build logbook entries from takeoff/landing event pairs.
        
        Args:
            device: Device instance
            
        Returns:
            Dict with results of logbook entry creation
        """
        result = {
            'new_entries': 0,
            'updated_entries': 0,
            'errors': []
        }
        
        try:
            # Get all takeoff and landing events for this device, ordered by total_time
            events = Event.query.filter_by(device_id=device.id).order_by(Event.total_time.asc()).all()
            
            # Filter for takeoff and landing events
            takeoff_events = [e for e in events if e.has_event_bit('Takeoff')]
            landing_events = [e for e in events if e.has_event_bit('Landing')]
            
            logger.debug(f"Found {len(takeoff_events)} takeoff events and {len(landing_events)} landing events for device {device.name}")
            
            if not takeoff_events or not landing_events:
                logger.info(f"No complete takeoff/landing pairs found for device {device.name}")
                return result
            
            # Build flight sequences from events
            flight_sequences = self._build_flight_sequences(takeoff_events, landing_events)
            
            logger.debug(f"Built {len(flight_sequences)} flight sequences for device {device.name}")
            
            # Create logbook entries from flight sequences
            for sequence in flight_sequences:
                try:
                    if self._create_logbook_entry_from_events(device, sequence):
                        result['new_entries'] += 1
                except Exception as e:
                    error_msg = f"Failed to create logbook entry from events: {str(e)}"
                    logger.error(error_msg)
                    result['errors'].append(error_msg)
            
            return result
            
        except Exception as e:
            error_msg = f"Error building logbook entries from events for device {device.name}: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
            return result
    
    def _build_flight_sequences(self, takeoff_events: List[Event], landing_events: List[Event]) -> List[Dict[str, Any]]:
        """
        Build flight sequences by pairing takeoff and landing events.
        Groups multiple landings within 120 seconds into single flights.
        
        Args:
            takeoff_events: List of takeoff events
            landing_events: List of landing events
            
        Returns:
            List of flight sequence dictionaries
        """
        sequences = []
        used_landings = set()
        
        for takeoff in takeoff_events:
            # Find landings that occur after this takeoff
            valid_landings = [
                landing for landing in landing_events 
                if landing.total_time > takeoff.total_time and landing.id not in used_landings
            ]
            
            if not valid_landings:
                continue
            
            # Sort landings by time
            valid_landings.sort(key=lambda e: e.total_time)
            
            # Start with the first landing after takeoff
            sequence_landings = [valid_landings[0]]
            used_landings.add(valid_landings[0].id)
            
            # Look for additional landings within 120 seconds
            last_landing_time = valid_landings[0].total_time
            
            for landing in valid_landings[1:]:
                time_diff_ms = landing.total_time - last_landing_time
                time_diff_seconds = time_diff_ms / 1000.0
                
                if time_diff_seconds <= 120:  # Within 120 seconds
                    sequence_landings.append(landing)
                    used_landings.add(landing.id)
                    last_landing_time = landing.total_time
                else:
                    break  # Gap too large, end this sequence
            
            # Create flight sequence
            sequence = {
                'takeoff_event': takeoff,
                'landing_events': sequence_landings,
                'takeoff_time_ms': takeoff.total_time,
                'final_landing_time_ms': sequence_landings[-1].total_time,
                'total_landings': len(sequence_landings)
            }
            
            sequences.append(sequence)
            
            logger.debug(f"Created flight sequence: takeoff at {takeoff.total_time}ms, "
                        f"{len(sequence_landings)} landings ending at {sequence_landings[-1].total_time}ms")
        
        return sequences
    
    def clear_all_events_and_reset_logger_pages(self) -> Dict[str, Any]:
        """
        Clear all events from the database and reset current_logger_page to 0 for all devices.
        
        Returns:
            Dict with results of the clearing operation
        """
        result = {
            'events_cleared': 0,
            'devices_reset': 0,
            'logbook_entries_removed': 0,
            'errors': []
        }
        
        try:
            # Clear all events
            events_count = Event.query.count()
            Event.query.delete()
            result['events_cleared'] = events_count
            logger.info(f"Cleared {events_count} events from database")
            
            # Clear all event-generated logbook entries
            event_entries = LogbookEntry.query.filter(
                LogbookEntry.remarks.like('%Generated from device events%')
            ).all()
            
            for entry in event_entries:
                db.session.delete(entry)
                result['logbook_entries_removed'] += 1
            
            logger.info(f"Cleared {result['logbook_entries_removed']} event-generated logbook entries")
            
            # Reset current_logger_page for all devices
            devices = Device.query.all()
            devices_updated = 0
            
            for device in devices:
                if device.current_logger_page != 0:
                    device.current_logger_page = 0
                    device.updated_at = datetime.utcnow()
                    devices_updated += 1
            
            result['devices_reset'] = devices_updated
            logger.info(f"Reset current_logger_page to 0 for {devices_updated} devices")
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Successfully cleared all events and reset logger pages: "
                       f"{result['events_cleared']} events, "
                       f"{result['logbook_entries_removed']} logbook entries, "
                       f"{result['devices_reset']} devices reset")
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error clearing events and resetting logger pages: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        return result

    def _clean_duplicate_link_messages(self, message: str) -> str:
        """
        Clean up duplicate link messages from an event message.
        
        Args:
            message: The original message string
            
        Returns:
            Cleaned message with duplicate link messages removed
        """
        if not message:
            return message
            
        import re
        
        # Find all unique logbook entry IDs mentioned in the message
        pattern = r'Linked to Logbook Entry (\d+)'
        matches = re.findall(pattern, message)
        unique_ids = list(set(matches))
        
        # Remove all existing link messages
        cleaned = re.sub(r'\[?Linked to Logbook Entry \d+\]?\s*', '', message).strip()
        
        # Add back unique link messages
        if unique_ids:
            link_messages = [f"[Linked to Logbook Entry {entry_id}]" for entry_id in sorted(unique_ids)]
            if cleaned:
                cleaned = f"{cleaned} {' '.join(link_messages)}"
            else:
                cleaned = ' '.join(link_messages)
        
        return cleaned

    def _create_logbook_entry_from_events(self, device: Device, flight_sequence: Dict[str, Any]) -> bool:
        """
        Create a logbook entry from a flight sequence (takeoff + landings).
        
        Args:
            device: Device instance
            flight_sequence: Flight sequence dictionary from _build_flight_sequences
            
        Returns:
            True if new entry was created, False if it already exists
        """
        try:
            takeoff_event = flight_sequence['takeoff_event']
            landing_events = flight_sequence['landing_events']
            final_landing_event = landing_events[-1]
            
            # Calculate flight duration
            flight_duration_ms = final_landing_event.total_time - takeoff_event.total_time
            flight_duration_hours = flight_duration_ms / (1000 * 60 * 60)  # Convert to hours
            
            # Create takeoff and landing datetime objects
            if takeoff_event.date_time:
                takeoff_datetime = takeoff_event.date_time
                
                # Calculate landing datetime
                landing_datetime = takeoff_event.date_time + timedelta(milliseconds=flight_duration_ms)
            else:
                # Fallback to current date if no timestamp available
                current_date = datetime.utcnow().date()
                takeoff_datetime = datetime.combine(current_date, time(10, 0))  # Default 10:00 AM
                
                # Calculate landing datetime from duration
                landing_datetime = takeoff_datetime + timedelta(hours=flight_duration_hours)
            
            # Check if logbook entry already exists for this event sequence
            existing_entry = LogbookEntry.query.filter_by(
                device_id=device.id,
                takeoff_datetime=takeoff_datetime,
                landing_datetime=landing_datetime
            ).first()
            
            if existing_entry:
                logger.debug(f"Logbook entry already exists for flight sequence starting at {takeoff_event.total_time}ms")
                return False
            
            # Create logbook entry - always create entries, even for unmapped pilots
            logbook_entry = LogbookEntry(
                takeoff_datetime=takeoff_datetime,
                landing_datetime=landing_datetime,
                aircraft_type=device.model or 'UNKNOWN',
                aircraft_registration=device.registration or 'UNKNOWN',
                departure_airport='UNKNOWN',  # Could be enhanced with location data
                arrival_airport='UNKNOWN',    # Could be enhanced with location data
                flight_time=round(flight_duration_hours, 2),
                pilot_in_command_time=round(flight_duration_hours, 2),
                dual_time=0.0,
                instrument_time=0.0,
                night_time=0.0,
                cross_country_time=0.0,
                landings_day=len(landing_events),  # Total number of landings in sequence
                landings_night=0,
                remarks=f'Generated from device events - Takeoff: {takeoff_event.format_log_time()}, '
                       f'Final Landing: {final_landing_event.format_log_time()}, '
                       f'Total Landings: {len(landing_events)}',
                pilot_name=None,  # Could be enhanced with pilot detection from events
                user_id=None,  # Don't assign to any specific user - will be visible in device logbook
                device_id=device.id  # Always link to device for visibility
            )
            
            db.session.add(logbook_entry)
            
            # Link events to logbook entry (we need to flush to get the ID)
            db.session.flush()
            
            # Update events with logbook entry reference if the model supports it
            # For now, we'll add this information to the remarks of existing events
            try:
                # Update takeoff event
                link_message = f"Linked to Logbook Entry {logbook_entry.id}"
                if takeoff_event.message:
                    # Clean up any existing duplicate link messages first
                    cleaned_message = self._clean_duplicate_link_messages(takeoff_event.message)
                    # Check if this specific link message is already present
                    if link_message not in cleaned_message:
                        takeoff_event.message = f"{cleaned_message} [{link_message}]"
                    else:
                        takeoff_event.message = cleaned_message
                else:
                    takeoff_event.message = link_message
                
                # Update landing events
                for landing_event in landing_events:
                    if landing_event.message:
                        # Clean up any existing duplicate link messages first
                        cleaned_message = self._clean_duplicate_link_messages(landing_event.message)
                        # Check if this specific link message is already present
                        if link_message not in cleaned_message:
                            landing_event.message = f"{cleaned_message} [{link_message}]"
                        else:
                            landing_event.message = cleaned_message
                    else:
                        landing_event.message = link_message
                
            except Exception as e:
                logger.warning(f"Could not link events to logbook entry: {str(e)}")
            
            logger.info(f"Created logbook entry from events: {flight_duration_hours:.2f}h flight "
                       f"with {len(landing_events)} landings for device {device.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating logbook entry from events: {str(e)}")
            logger.debug(f"Flight sequence data: {flight_sequence}")
            raise


# Create singleton instance
thingsboard_sync = ThingsBoardSyncService()
