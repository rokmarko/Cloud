"""
Main application routes
"""

from flask import Blueprint, render_template, jsonify, current_app
from flask_login import current_user
import os
import sqlite3
from datetime import datetime

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    if current_user.is_authenticated:
        return render_template('main/index.html', title='Home')
    return render_template('main/landing.html', title='Welcome to KanardiaCloud')


@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring and load balancer."""
    try:
        # Check database connectivity
        db_path = os.path.join(current_app.instance_path, 'kanardiacloud.db')
        if not os.path.exists(db_path):
            raise Exception("Database file not found")
        
        # Quick database connectivity test
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'KanardiaCloud',
            'version': '1.0.0',
            'database': 'connected'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'KanardiaCloud',
            'error': str(e)
        }), 503


@main_bp.route('/health/ready')
def readiness_check():
    """Readiness check for Kubernetes/container orchestration."""
    try:
        # More comprehensive checks for readiness
        db_path = os.path.join(current_app.instance_path, 'kanardiacloud.db')
        if not os.path.exists(db_path):
            raise Exception("Database not ready")
        
        # Check if required tables exist
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            raise Exception("Database schema not ready")
        conn.close()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'KanardiaCloud'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {str(e)}")
        return jsonify({
            'status': 'not_ready',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'KanardiaCloud',
            'error': str(e)
        }), 503
