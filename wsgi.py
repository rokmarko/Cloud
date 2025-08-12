"""
WSGI entry point for KanardiaCloud application.

This module provides the WSGI application object for production deployment
with Gunicorn or other WSGI servers.
"""
import os
import sys
from typing import Any

# Add the project root to Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Import the Flask application factory
from src.app import create_app

# Create application instance
app = create_app()

# Configure logging for production
if app.config.get('FLASK_ENV') == 'production':
    import logging
    from logging.handlers import RotatingFileHandler
    
    if not app.debug:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(PROJECT_ROOT, 'logs')
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
        
        # Setup file handler
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'kanardiacloud.log'),
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('KanardiaCloud startup')

if __name__ == "__main__":
    # This is only used for development/testing
    app.run(host='0.0.0.0', port=5000, debug=False)
