"""
API routes for external server integration
"""

import os
from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from src.app import db, csrf
from src.models import User, Device

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
        "device_name": "Aircraft N123AB",
        "device_id": "external_device_123",
        "device_type": "aircraft",
        "model": "Cessna 172",
        "serial_number": "17280123",
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
            user_id=user.id,
            serial_number=data['device_id']
        ).first()
        
        if existing_device:
            return jsonify({
                'error': 'Device already exists',
                'message': f'Device with ID {data["device_id"]} is already claimed by this user',
                'device_id': existing_device.id,
                'device_name': existing_device.name
            }), 409
        
        # Create new device
        device = Device(
            name=data['device_name'],
            device_type=data.get('device_type', 'other'),
            model=data.get('model'),
            serial_number=data['device_id'],  # Use external device_id as serial_number
            registration=data.get('registration'),
            user_id=user.id
        )
        
        db.session.add(device)
        db.session.commit()
        
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
