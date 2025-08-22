"""
API routes for external server integration
"""

import os
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from src.app import db, csrf
from src.models import User, Device, LogbookEntry, Pilot, Airfield
from src.services.thingsboard_sync import ThingsBoardSyncService
from src.services.email_service import EmailService

api_bp = Blueprint('api', __name__)


def require_api_key(f):
    """Decorator to require API key for external server endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({
                'error': 'Missing API key',
                'message': 'X-API-Key header is required'
            }), 401
        
        # Get the API key from environment variables or app config
        expected_api_key = (current_app.config.get('EXTERNAL_API_KEY') or 
                          os.environ.get('EXTERNAL_API_KEY') or
                          'kanardia-external-api-key-2025-change-in-production')  # Default for development
        
        if not expected_api_key:
            return jsonify({
                'error': 'Server configuration error',
                'message': 'API key not configured on server'
            }), 500
        
        if api_key != expected_api_key:
            return jsonify({
                'error': 'Invalid API key',
                'message': 'The provided API key is not valid'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


@api_bp.route('/external/claim-device', methods=['POST'])
@csrf.exempt
@require_api_key
def claim_device():
    """
    External API endpoint to claim a device for a user.
    
    Expected JSON payload:
    {
        "user_email": "user@example.com",
        "device_name": "My Device",
        "device_id": "external_device_123",
        "device_type": "aircraft",
        "model": "Cessna 172",
        "serial_number": "Nesis XX-1000",
        "registration": "N123AB"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'JSON payload is required'
            }), 400
        
        # Validate required fields
        required_fields = ['user_email', 'device_name', 'device_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'message': f'The following fields are required: {", ".join(missing_fields)}',
                'required_fields': required_fields
            }), 400
        
        # Find the user by email
        user = User.query.filter_by(email=data['user_email'].lower().strip()).first()
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': f'No user found with email: {data["user_email"]}'
            }), 404
        
        if not user.is_active or not user.is_verified:
            return jsonify({
                'error': 'User account inactive',
                'message': 'User account is not active or verified'
            }), 400
        
        # Check if device with this external ID already exists for this user
        existing_device = Device.query.filter_by(
            external_device_id=data['device_id'],
        ).first()
        
        if existing_device:
            existing_user_email = "Unknown"
            if existing_device and existing_device.user_id:
                existing_user = User.query.get(existing_device.user_id)
                if existing_user:
                    existing_user_email = existing_user.email

            return jsonify({
                'error': f'Device already claimed by user {existing_user_email}',
                'message': f'Device {data["device_name"]} is already claimed by user {existing_device.user_id}',
                'device_id': existing_device.id,
                'device_name': existing_device.name
            }), 409
        
        # Create new device
        device = Device(
            name=data['device_name'],
            device_type=data.get('device_type', 'aircraft'),
            model=data.get('model'),
            serial_number=data['device_name'],
            external_device_id=data['device_id'],  # Use external device_id as serial_number
            registration=data.get('registration'),
            user_id=user.id
        )
        
        db.session.add(device)
        db.session.commit()
        
        # Send email notification to user
        try:
            email_sent = EmailService.send_device_claimed_email(
                user_email=user.email,
                user_nickname=user.nickname,
                device_name=device.name,
                device_type=device.device_type,
                device_model=device.model,
                device_registration=device.registration
            )
            
            if email_sent:
                current_app.logger.info(f"Device claimed email sent to {user.email} for device '{device.name}' (ID: {device.id})")
            else:
                current_app.logger.warning(f"Failed to send device claimed email to {user.email} for device '{device.name}' (ID: {device.id})")
                
        except Exception as email_error:
            # Don't fail the device claiming if email fails
            current_app.logger.error(f"Error sending device claimed email to {user.email}: {str(email_error)}")
        
        return jsonify({
            'success': True,
            'message': 'Device claimed successfully',
            'device': {
                'id': device.id,
                'name': device.name,
                'device_type': device.device_type,
                'model': device.model,
                'serial_number': device.serial_number,
                'registration': device.registration,
                'created_at': device.created_at.isoformat()
            },
            'user': {
                'email': user.email,
                'nickname': user.nickname
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error claiming device: {str(e)}")
        
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while claiming the device'
        }), 500


@api_bp.route('/external/device-status/<device_id>', methods=['GET'])
@csrf.exempt
@require_api_key
def get_device_status(device_id):
    """
    Get the status of a device by external device ID.
    
    Returns information about whether the device is claimed and by whom.
    """
    try:
        device = Device.query.filter_by(
            serial_number=device_id,
            is_active=True
        ).first()
        
        if not device:
            return jsonify({
                'device_id': device_id,
                'claimed': False,
                'message': 'Device not found or not claimed'
            }), 404
        
        user = User.query.get(device.user_id)
        
        if not user:
            return jsonify({
                'error': 'User not found',
                'message': 'Device owner not found'
            }), 500
        
        return jsonify({
            'device_id': device_id,
            'claimed': True,
            'device': {
                'id': device.id,
                'name': device.name,
                'device_type': device.device_type,
                'model': device.model,
                'registration': device.registration,
                'created_at': device.created_at.isoformat()
            },
            'user': {
                'email': user.email,
                'nickname': user.nickname
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting device status: {str(e)}")
        
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while checking device status'
        }), 500


@api_bp.route('/external/unclaim-device', methods=['POST'])
@csrf.exempt
@require_api_key
def unclaim_device():
    """
    Unclaim a device (soft delete - set is_active to False).
    
    Expected JSON payload:
    {
        "device_id": "external_device_123"
    }
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('device_id'):
            return jsonify({
                'error': 'Invalid request',
                'message': 'device_id is required in JSON payload'
            }), 400
        
        device = Device.query.filter_by(
            serial_number=data['device_id'],
            is_active=True
        ).first()
        
        if not device:
            return jsonify({
                'error': 'Device not found',
                'message': f'No active device found with ID: {data["device_id"]}'
            }), 404
        
        # Soft delete the device
        device.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Device unclaimed successfully',
            'device_id': data['device_id']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error unclaiming device: {str(e)}")
        
        return jsonify({
            'error': 'Internal server error',
            'message': 'An error occurred while unclaiming the device'
        }), 500


@api_bp.route('/external/health', methods=['GET'])
@csrf.exempt
def health_check():
    """Health check endpoint for external servers."""
    return jsonify({
        'status': 'healthy',
        'service': 'KanardiaCloud API',
        'version': '1.0.0'
    }), 200


@api_bp.route('/external/airfields', methods=['POST'])
@csrf.exempt
@require_api_key
def add_or_update_airfield():
    """
    Add or update airfield data in the database.
    
    Expected JSON payload:
    {
        "icao_code": "LJLJ",
        "name": "Ljubljana Airport", 
        "latitude": 46.2237,
        "longitude": 14.4576,
        "country": "Slovenia",
        "region": "Central Europe",
        "elevation_ft": 1273,
        "runway_info": {...},
        "frequencies": {...}
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'JSON payload required'
            }), 400
        
        # Validate required fields
        required_fields = ['icao_code', 'name', 'latitude', 'longitude']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'message': f'Required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Validate ICAO code format
        icao_code = data['icao_code'].upper()
        if len(icao_code) != 4 or not icao_code.isalpha():
            return jsonify({
                'error': 'Invalid ICAO code',
                'message': 'ICAO code must be 4 letters'
            }), 400
        
        # Validate coordinates
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
            
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
                
        except (ValueError, TypeError) as e:
            return jsonify({
                'error': 'Invalid coordinates',
                'message': str(e)
            }), 400
        
        # Check if airfield already exists
        existing_airfield = Airfield.query.filter_by(icao_code=icao_code).first()
        
        if existing_airfield:
            # Update existing airfield
            existing_airfield.name = data['name']
            existing_airfield.latitude = latitude
            existing_airfield.longitude = longitude
            existing_airfield.country = data.get('country')
            existing_airfield.region = data.get('region')
            existing_airfield.elevation_ft = data.get('elevation_ft')
            existing_airfield.runway_info = data.get('runway_info')
            existing_airfield.frequencies = data.get('frequencies')
            existing_airfield.is_active = data.get('is_active', True)
            
            db.session.commit()
            
            return jsonify({
                'status': 'updated',
                'message': f'Airfield {icao_code} updated successfully',
                'airfield': existing_airfield.to_dict()
            }), 200
            
        else:
            # Create new airfield
            airfield = Airfield(
                icao_code=icao_code,
                name=data['name'],
                latitude=latitude,
                longitude=longitude,
                country=data.get('country'),
                region=data.get('region'),
                elevation_ft=data.get('elevation_ft'),
                runway_info=data.get('runway_info'),
                frequencies=data.get('frequencies'),
                is_active=data.get('is_active', True)
            )
            
            db.session.add(airfield)
            db.session.commit()
            
            return jsonify({
                'status': 'created',
                'message': f'Airfield {icao_code} created successfully',
                'airfield': airfield.to_dict()
            }), 201
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error managing airfield: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to process airfield data'
        }), 500


@api_bp.route('/external/airfields/bulk', methods=['POST'])
@csrf.exempt
@require_api_key
def bulk_add_airfields():
    """
    Bulk add or update multiple airfields.
    
    Expected JSON payload:
    {
        "airfields": [
            {
                "icao_code": "LJLJ",
                "name": "Ljubljana Airport",
                "latitude": 46.2237,
                "longitude": 14.4576,
                "country": "Slovenia"
            },
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'airfields' not in data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'JSON payload with "airfields" array required'
            }), 400
        
        airfields_data = data['airfields']
        if not isinstance(airfields_data, list):
            return jsonify({
                'error': 'Invalid format',
                'message': 'airfields must be an array'
            }), 400
        
        results = {
            'created': 0,
            'updated': 0,
            'errors': []
        }
        
        for i, airfield_data in enumerate(airfields_data):
            try:
                # Validate required fields
                required_fields = ['icao_code', 'name', 'latitude', 'longitude']
                missing_fields = [field for field in required_fields if field not in airfield_data]
                
                if missing_fields:
                    results['errors'].append({
                        'index': i,
                        'icao_code': airfield_data.get('icao_code', 'unknown'),
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    })
                    continue
                
                icao_code = airfield_data['icao_code'].upper()
                
                # Validate coordinates
                latitude = float(airfield_data['latitude'])
                longitude = float(airfield_data['longitude'])
                
                # Check if airfield exists
                existing_airfield = Airfield.query.filter_by(icao_code=icao_code).first()
                
                if existing_airfield:
                    # Update existing
                    existing_airfield.name = airfield_data['name']
                    existing_airfield.latitude = latitude
                    existing_airfield.longitude = longitude
                    existing_airfield.country = airfield_data.get('country')
                    existing_airfield.region = airfield_data.get('region')
                    existing_airfield.elevation_ft = airfield_data.get('elevation_ft')
                    existing_airfield.runway_info = airfield_data.get('runway_info')
                    existing_airfield.frequencies = airfield_data.get('frequencies')
                    existing_airfield.is_active = airfield_data.get('is_active', True)
                    
                    results['updated'] += 1
                else:
                    # Create new
                    airfield = Airfield(
                        icao_code=icao_code,
                        name=airfield_data['name'],
                        latitude=latitude,
                        longitude=longitude,
                        country=airfield_data.get('country'),
                        region=airfield_data.get('region'),
                        elevation_ft=airfield_data.get('elevation_ft'),
                        runway_info=airfield_data.get('runway_info'),
                        frequencies=airfield_data.get('frequencies'),
                        is_active=airfield_data.get('is_active', True)
                    )
                    db.session.add(airfield)
                    results['created'] += 1
                    
            except (ValueError, TypeError, KeyError) as e:
                results['errors'].append({
                    'index': i,
                    'icao_code': airfield_data.get('icao_code', 'unknown'),
                    'error': str(e)
                })
                continue
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'status': 'completed',
            'message': f'Processed {len(airfields_data)} airfields',
            'results': results
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in bulk airfield operation: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to process bulk airfield data'
        }), 500


@api_bp.route('/external/airfields', methods=['GET'])
@csrf.exempt
@require_api_key
def get_airfields():
    """
    Get list of airfields with optional filtering.
    
    Query parameters:
    - country: Filter by country
    - region: Filter by region  
    - icao_code: Get specific airfield
    - lat, lon, radius_km: Find airfields near coordinates
    """
    try:
        # Get query parameters
        country = request.args.get('country')
        region = request.args.get('region')
        icao_code = request.args.get('icao_code')
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        radius_km = request.args.get('radius_km', 25.0, type=float)
        
        query = Airfield.query.filter_by(is_active=True)
        
        # Apply filters
        if icao_code:
            query = query.filter_by(icao_code=icao_code.upper())
        if country:
            query = query.filter_by(country=country)
        if region:
            query = query.filter_by(region=region)
        
        # Handle proximity search
        if lat is not None and lon is not None:
            try:
                latitude = float(lat)
                longitude = float(lon)
                
                # Use database method for proximity search
                results = Airfield.find_nearest(latitude, longitude, radius_km, limit=50)
                airfields = [airfield.to_dict() for airfield, distance in results]
                
                return jsonify({
                    'airfields': airfields,
                    'total': len(airfields),
                    'search_params': {
                        'latitude': latitude,
                        'longitude': longitude,
                        'radius_km': radius_km
                    }
                }), 200
                
            except (ValueError, TypeError):
                return jsonify({
                    'error': 'Invalid coordinates',
                    'message': 'lat and lon must be valid numbers'
                }), 400
        else:
            # Regular query
            airfields = query.all()
            
            return jsonify({
                'airfields': [airfield.to_dict() for airfield in airfields],
                'total': len(airfields)
            }), 200
            
    except Exception as e:
        current_app.logger.error(f"Error getting airfields: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to retrieve airfield data'
        }), 500


@api_bp.route('/external/geocode', methods=['POST'])
@csrf.exempt
@require_api_key
def reverse_geocode_api():
    """
    Reverse geocode coordinates using aviation database.
    
    Expected JSON payload:
    {
        "latitude": 46.2237,
        "longitude": 14.4576
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'JSON payload required'
            }), 400
        
        if 'latitude' not in data or 'longitude' not in data:
            return jsonify({
                'error': 'Missing coordinates',
                'message': 'latitude and longitude required'
            }), 400
        
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except (ValueError, TypeError):
            return jsonify({
                'error': 'Invalid coordinates',
                'message': 'latitude and longitude must be valid numbers'
            }), 400
        
        # Use the geocoding service
        from src.services.geocoding import reverse_geocode
        location = reverse_geocode(latitude, longitude)
        
        # Get nearest airfield details
        nearest_airfield = None
        try:
            results = Airfield.find_nearest(latitude, longitude, max_distance_km=50.0, limit=1)
            if results:
                airfield, distance = results[0]
                nearest_airfield = {
                    'icao_code': airfield.icao_code,
                    'name': airfield.name,
                    'distance_km': round(distance, 2),
                    'country': airfield.country,
                    'region': airfield.region
                }
        except Exception as e:
            current_app.logger.warning(f"Could not get nearest airfield: {e}")
        
        return jsonify({
            'location': location,
            'coordinates': {
                'latitude': latitude,
                'longitude': longitude
            },
            'nearest_airfield': nearest_airfield
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in reverse geocoding: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to process geocoding request'
        }), 500
