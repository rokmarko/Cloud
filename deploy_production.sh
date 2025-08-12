#!/bin/bash

# KanardiaCloud Production Deployment Script
# This script sets up the production environment with Gunicorn + Systemd

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="kanardiacloud"
APP_DIR="/home/rok/src/Cloud-1"
VENV_DIR="/home/rok/Branch/NavSync/Protected/Cloud/venv"
LOG_DIR="/var/log/$APP_NAME"
RUN_DIR="/var/run/$APP_NAME"
USER="www-data"
GROUP="www-data"

echo -e "${BLUE}=== KanardiaCloud Production Deployment ===${NC}"

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

print_status "Starting production deployment..."

# 1. Create necessary directories
print_status "Creating directories..."
mkdir -p "$LOG_DIR"
mkdir -p "$RUN_DIR"
chown -R $USER:$GROUP "$LOG_DIR"
chown -R $USER:$GROUP "$RUN_DIR"

# 2. Set proper permissions
print_status "Setting permissions..."
chown -R $USER:$GROUP "$APP_DIR/instance"
chmod 755 "$APP_DIR"
chmod 644 "$APP_DIR"/*.py
chmod 644 "$APP_DIR"/*.service
chmod 644 "$APP_DIR"/*.conf.py

# 3. Install Python dependencies
print_status "Installing Python dependencies..."
cd "$APP_DIR"
sudo -u $USER "$VENV_DIR/bin/pip" install -r requirements.txt
sudo -u $USER "$VENV_DIR/bin/pip" install gunicorn

# 4. Run database migrations if needed
print_status "Checking database..."
if [ -f "$APP_DIR/instance/kanardiacloud.db" ]; then
    print_status "Database exists, skipping initialization"
else
    print_warning "Database not found, you may need to initialize it"
fi

# 5. Test Gunicorn configuration
print_status "Testing Gunicorn configuration..."
sudo -u $USER "$VENV_DIR/bin/gunicorn" --check-config --config gunicorn.conf.py wsgi:app
if [ $? -eq 0 ]; then
    print_status "Gunicorn configuration is valid"
else
    print_error "Gunicorn configuration test failed"
    exit 1
fi

# 6. Install systemd service
print_status "Installing systemd service..."
cp "$APP_DIR/$APP_NAME.service" "/etc/systemd/system/"
systemctl daemon-reload

# 7. Enable and start service
print_status "Enabling and starting service..."
systemctl enable $APP_NAME
systemctl restart $APP_NAME

# 8. Check service status
sleep 3
if systemctl is-active --quiet $APP_NAME; then
    print_status "Service is running successfully!"
else
    print_error "Service failed to start. Checking logs..."
    journalctl -u $APP_NAME --no-pager -n 20
    exit 1
fi

# 9. Display service information
print_status "Deployment completed successfully!"
echo
echo -e "${BLUE}Service Information:${NC}"
echo "Status: $(systemctl is-active $APP_NAME)"
echo "Enabled: $(systemctl is-enabled $APP_NAME)"
echo "Logs: journalctl -u $APP_NAME -f"
echo "Config: /etc/systemd/system/$APP_NAME.service"
echo
echo -e "${BLUE}Management Commands:${NC}"
echo "Start:   sudo systemctl start $APP_NAME"
echo "Stop:    sudo systemctl stop $APP_NAME"
echo "Restart: sudo systemctl restart $APP_NAME"
echo "Reload:  sudo systemctl reload $APP_NAME"
echo "Status:  sudo systemctl status $APP_NAME"
echo "Logs:    sudo journalctl -u $APP_NAME -f"
echo
echo -e "${GREEN}Application should be available at: http://127.0.0.1:8000${NC}"

# 10. Setup log rotation (optional)
if command -v logrotate &> /dev/null; then
    print_status "Setting up log rotation..."
    cat > "/etc/logrotate.d/$APP_NAME" << EOF
$LOG_DIR/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 $USER $GROUP
    postrotate
        systemctl reload $APP_NAME
    endscript
}
EOF
    print_status "Log rotation configured"
fi

print_status "Production deployment completed!"
