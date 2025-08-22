#!/bin/bash
# Production startup script for KanardiaCloud

set -e

# Change to project directory
cd /home/rok/Cloud

# Activate virtual environment
source venv/bin/activate

# Export production environment
export FLASK_ENV=production
export FLASK_DEBUG=0

# Start Gunicorn with production configuration
exec gunicorn --config gunicorn.conf.py wsgi:app
