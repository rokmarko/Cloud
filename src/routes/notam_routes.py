"""
NOTAM-related routes for KanardiaCloud dashboard.
"""

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from src.models import Notam, NotamUpdateLog
from src.services.notam_service import notam_service

notam_bp = Blueprint('notam', __name__, url_prefix='/notams')


@notam_bp.route('/')
@login_required
def notam_viewer():
    """Main NOTAM viewer page with tabs for table and map view."""
    # Get available ICAO codes from the database
    available_codes = (
        Notam.query
        .with_entities(Notam.icao_code)
        .distinct()
        .order_by(Notam.icao_code)
        .all()
    )
    
    icao_codes = [code[0] for code in available_codes]
    
    return render_template('notams/viewer.html', 
                         title='NOTAM Viewer',
                         icao_codes=icao_codes,
                         today=datetime.now(timezone.utc).strftime('%Y-%m-%d'))


@notam_bp.route('/api/notams')
@login_required
def api_get_notams():
    """API endpoint to get NOTAMs filtered by date and ICAO code."""
    try:
        # Get parameters
        icao_code = request.args.get('icao', '').upper()
        date_str = request.args.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))
        
        # Parse date
        try:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Validate ICAO code if provided
        if icao_code and icao_code not in notam_service.SUPPORTED_AREAS:
            return jsonify({'error': f'Unsupported ICAO code. Supported: {", ".join(notam_service.SUPPORTED_AREAS)}'}), 400
        
        # Get NOTAMs
        if icao_code:
            notams = notam_service.get_active_notams(icao_code, check_date)
        else:
            notams = notam_service.get_active_notams(check_date=check_date)
        
        # Convert to dict format
        notam_data = [notam.to_dict() for notam in notams]
        
        return jsonify({
            'notams': notam_data,
            'count': len(notam_data),
            'date': date_str,
            'icao_code': icao_code or 'all'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in api_get_notams: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@notam_bp.route('/api/notams/<path:notam_id>')
@login_required
def api_get_notam_detail(notam_id: str):
    """API endpoint to get detailed information for a specific NOTAM."""
    try:
        current_app.logger.info(f"Looking for NOTAM with ID: {notam_id}")
        notam = Notam.query.filter_by(notam_id=notam_id).first()
        
        if not notam:
            current_app.logger.warning(f"NOTAM {notam_id} not found in database")
            return jsonify({'error': 'NOTAM not found'}), 404
        
        current_app.logger.info(f"Found NOTAM {notam_id}, generating details")
        notam_detail = notam.to_dict()
        
        # Add additional details
        notam_detail.update({
            'raw_text': notam.raw_text,
            'fir': notam.fir,
            'lower_limit_raw': notam.lower_limit_raw,
            'upper_limit_raw': notam.upper_limit_raw,
            'source': notam.source,
            'created_time': notam.created_time.isoformat() if notam.created_time else None,
            'updated_at': notam.updated_at.isoformat() if notam.updated_at else None
        })
        
        return jsonify(notam_detail)
        
    except Exception as e:
        current_app.logger.error(f"Error in api_get_notam_detail: {str(e)}")
        import traceback
        current_app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@notam_bp.route('/api/statistics')
@login_required
def api_get_statistics():
    """API endpoint to get NOTAM statistics."""
    try:
        # Get overall statistics
        total_notams = Notam.query.count()
        active_notams = len(notam_service.get_active_notams())
        
        # Statistics by ICAO code
        icao_stats = {}
        for icao_code in notam_service.SUPPORTED_AREAS:
            total = Notam.query.filter_by(icao_code=icao_code).count()
            active = len(notam_service.get_active_notams(icao_code))
            icao_stats[icao_code] = {
                'total': total,
                'active': active
            }
        
        # Recent update logs
        recent_logs = (
            NotamUpdateLog.query
            .order_by(NotamUpdateLog.update_time.desc())
            .limit(10)
            .all()
        )
        
        log_data = []
        for log in recent_logs:
            log_data.append({
                'icao_code': log.icao_code,
                'update_time': log.update_time.isoformat(),
                'status': log.status,
                'total_notams': log.total_notams,
                'new_notams': log.new_notams,
                'updated_notams': log.updated_notams
            })
        
        return jsonify({
            'overview': {
                'total_notams': total_notams,
                'active_notams': active_notams
            },
            'by_icao': icao_stats,
            'recent_updates': log_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in api_get_statistics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@notam_bp.route('/api/fetch')
@login_required
def api_manual_fetch():
    """API endpoint for manually triggering NOTAM fetch (admin only)."""
    try:
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        
        icao_code = request.args.get('icao', '').upper()
        
        if icao_code:
            if icao_code not in notam_service.SUPPORTED_AREAS:
                return jsonify({'error': f'Unsupported ICAO code'}), 400
            
            result = notam_service.fetch_and_store_notams(icao_code)
            return jsonify({
                'success': True,
                'icao_code': icao_code,
                'result': result
            })
        else:
            results = notam_service.fetch_all_areas()
            return jsonify({
                'success': True,
                'results': results
            })
    
    except Exception as e:
        current_app.logger.error(f"Error in api_manual_fetch: {str(e)}")
        return jsonify({'error': str(e)}), 500
