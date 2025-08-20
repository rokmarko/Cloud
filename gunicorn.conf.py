"""
Gunicorn configuration file for KanardiaCloud production deployment.

This configuration optimizes the application for production use with
proper worker management, logging, and security settings.
"""
import multiprocessing
import os

# Basic settings
bind = "127.0.0.1:5000"
workers = multiprocessing.cpu_count() + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
timeout = 30
keepalive = 2

# Process naming
proc_name = 'kanardiacloud'

# User and group to run as (set these for production)
# user = "www-data"
# group = "www-data"

# Logging
accesslog = "/var/log/kanardiacloud/access.log"
errorlog = "/var/log/kanardiacloud/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# SSL (uncomment and configure for HTTPS)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Process management
pidfile = "/var/run/kanardiacloud/kanardiacloud.pid"
daemon = False  # Set to True for daemon mode

# Environment variables
raw_env = [
    'FLASK_ENV=production',
    'FLASK_DEBUG=0',
]

# Worker lifecycle
def on_starting(server):
    """Called just before the master process is initialized."""
    # Create necessary directories
    import os
    os.makedirs('/var/log/kanardiacloud', mode=0o755, exist_ok=True)
    os.makedirs('/var/run/kanardiacloud', mode=0o755, exist_ok=True)
    os.makedirs('logs', mode=0o755, exist_ok=True)
    
    server.log.info("Starting Gunicorn server for KanardiaCloud")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading KanardiaCloud application")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("KanardiaCloud server is ready. Listening on: %s", server.address)

def on_exit(server):
    """Called just before exiting."""
    server.log.info("Shutting down KanardiaCloud server")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info("Worker received SIGINT or SIGQUIT")

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
