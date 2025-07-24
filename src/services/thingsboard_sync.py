"""
ThingsBoard sync service for logbook entries
"""

import requests
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from src.app import db
from src.models import Device, LogbookEntry, User
from flask import current_app


logger = logging.getLogger(__name__)


class ThingsBoardSyncService:
    """Service for syncing logbook entries from ThingsBoard server."""
    
    def __init__(self):
        self.base_url = "https://aetos.kanardia.eu:8088"
        self.timeout = 30  # seconds
    
    def sync_all_devices(self) -> Dict[str, Any]:
        """
        Sync logbook entries for all devices with external_device_id.
        
        Returns:
            Dict with sync results and statistics
        """
        results = {
            'total_devices': 0,
            'synced_devices': 0,
            'total_entries': 0,
            'new_entries': 0,
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
                    device_result = self.sync_device(device)
                    results['synced_devices'] += 1
                    results['new_entries'] += device_result.get('new_entries', 0)
                    results['total_entries'] += device_result.get('total_entries', 0)
                    
                except Exception as e:
                    error_msg = f"Failed to sync device {device.name} (ID: {device.external_device_id}): {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
            
            logger.info(f"Sync completed: {results['synced_devices']}/{results['total_devices']} devices, "
                       f"{results['new_entries']} new entries")
            
        except Exception as e:
            error_msg = f"Fatal error during sync: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
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
        url = f"{self.base_url}/api/plugins/rpc/twoway/{device_id}"
        
        payload = {
            "method": "syncLog",
            "params": {}
        }
        
        headers = {
            'Content-Type': 'application/json',
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
            
            aircraft_registration = entry_data.get('aircraft_registration') or device.registration or 'UNKNOWN'
            aircraft_type = entry_data.get('aircraft_type') or device.model or 'UNKNOWN'
            departure_airport = entry_data.get('departure_airport', 'UNKNOWN')
            arrival_airport = entry_data.get('arrival_airport', 'UNKNOWN')
            
            flight_time = float(entry_data.get('flight_time', 0))
            if flight_time <= 0:
                raise ValueError("Invalid flight_time: must be positive number")
            
            # Check if entry already exists (avoid duplicates)
            existing_entry = LogbookEntry.query.filter_by(
                user_id=device.user_id,
                date=entry_date,
                aircraft_registration=aircraft_registration,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                flight_time=flight_time
            ).first()
            
            if existing_entry:
                logger.debug(f"Logbook entry already exists for {aircraft_registration} on {entry_date}")
                return False
            
            # Create new logbook entry
            logbook_entry = LogbookEntry(
                date=entry_date,
                aircraft_type=aircraft_type,
                aircraft_registration=aircraft_registration,
                departure_airport=departure_airport,
                arrival_airport=arrival_airport,
                flight_time=flight_time,
                pilot_in_command_time=float(entry_data.get('pilot_in_command_time', 0)),
                dual_time=float(entry_data.get('dual_time', 0)),
                instrument_time=float(entry_data.get('instrument_time', 0)),
                night_time=float(entry_data.get('night_time', 0)),
                cross_country_time=float(entry_data.get('cross_country_time', 0)),
                landings_day=int(entry_data.get('landings_day', 0)),
                landings_night=int(entry_data.get('landings_night', 0)),
                remarks=entry_data.get('remarks', f'Synced from ThingsBoard device {device.external_device_id}'),
                user_id=device.user_id
            )
            
            db.session.add(logbook_entry)
            
            logger.debug(f"Created new logbook entry for {aircraft_registration} on {entry_date}")
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


# Create singleton instance
thingsboard_sync = ThingsBoardSyncService()
