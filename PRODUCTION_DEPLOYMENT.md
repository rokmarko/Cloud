# KanardiaCloud Production Deployment Guide

## Overview

This guide covers deploying KanardiaCloud in production using **Gunicorn + Systemd** for reliable, scalable operation.

## Architecture

```
Internet → Nginx/Apache → Gunicorn → Flask App → SQLite DB
                          (WSGI)
```

## Quick Setup

### Automated Deployment

```bash
# Run the automated deployment script
sudo ./deploy_production.sh
```

### Manual Setup

1. **Install Dependencies**
```bash
# Install system packages
sudo apt update
sudo apt install python3-venv nginx

# Install Python dependencies
pip install -r requirements.txt
pip install gunicorn
```

2. **Configure Environment**
```bash
# Copy production environment file
cp .env.production .env
# Edit configuration as needed
nano .env
```

3. **Install Systemd Service**
```bash
sudo cp kanardiacloud.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable kanardiacloud
sudo systemctl start kanardiacloud
```

## Configuration Files

### Environment Configuration (.env.production)
Production-specific settings including security headers and session configuration.

### Gunicorn Configuration (gunicorn.conf.py)
- **Workers**: CPU cores × 2 + 1
- **Bind**: 127.0.0.1:8000 (behind reverse proxy)
- **Logging**: Structured logging to /var/log/kanardiacloud/
- **Security**: Request limits and worker lifecycle management

### Systemd Service (kanardiacloud.service)
- **User**: www-data (configurable)
- **Auto-restart**: On failure with 5-second delay
- **Security**: Sandboxing and resource limits
- **Logging**: Journal integration

### WSGI Entry Point (wsgi.py)
Production-ready application entry point with:
- Path configuration
- Production logging setup
- Error handling

## Service Management

```bash
# Start/Stop/Restart
sudo systemctl start kanardiacloud
sudo systemctl stop kanardiacloud
sudo systemctl restart kanardiacloud

# Reload configuration (graceful)
sudo systemctl reload kanardiacloud

# Check status
sudo systemctl status kanardiacloud

# View logs
sudo journalctl -u kanardiacloud -f
```

## Monitoring

### Health Checks
- **Liveness**: `GET /health` - Basic service health
- **Readiness**: `GET /health/ready` - Application readiness

### Log Files
- **Access**: `/var/log/kanardiacloud/access.log`
- **Error**: `/var/log/kanardiacloud/error.log`
- **System**: `journalctl -u kanardiacloud`

### Performance Monitoring
```bash
# Check worker processes
ps aux | grep gunicorn

# Monitor resource usage
htop

# Check application metrics
curl http://127.0.0.1:8000/health
```

## Reverse Proxy Setup (Nginx)

### Install Nginx
```bash
sudo apt install nginx
```

### Configuration Example
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/rok/src/Cloud-1/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## SSL/HTTPS Setup

### Using Certbot (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### Manual Certificate
```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    # ... rest of configuration
}
```

## Security Considerations

### Application Security
- **CSRF Protection**: Enabled with secure tokens
- **Session Security**: Secure cookies, SameSite protection
- **Content Security**: Security headers configured
- **Input Validation**: Form validation and sanitization

### System Security
- **User Isolation**: Service runs as www-data
- **File Permissions**: Restricted access to application files
- **Network Security**: Bind to localhost only (behind proxy)
- **Resource Limits**: Memory and process limits configured

### Database Security
- **Access Control**: SQLite file permissions
- **Backup Encryption**: Consider encrypting backups
- **Connection Security**: Local socket connections only

## Backup Strategy

### Database Backup
```bash
# Create backup script
cat > /usr/local/bin/backup-kanardiacloud.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/kanardiacloud"
mkdir -p "$BACKUP_DIR"
cp /home/rok/src/Cloud-1/instance/kanardiacloud.db "$BACKUP_DIR/kanardiacloud_$DATE.db"
# Keep only last 30 days
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete
EOF

chmod +x /usr/local/bin/backup-kanardiacloud.sh
```

### Automated Backups (Cron)
```bash
# Add to crontab
echo "0 2 * * * /usr/local/bin/backup-kanardiacloud.sh" | sudo crontab -
```

## Troubleshooting

### Common Issues

1. **Service Won't Start**
```bash
# Check logs
sudo journalctl -u kanardiacloud --no-pager
# Check configuration
sudo -u www-data /home/rok/Branch/NavSync/Protected/Cloud/venv/bin/gunicorn --check-config gunicorn.conf.py
```

2. **Permission Errors**
```bash
# Fix ownership
sudo chown -R www-data:www-data /home/rok/src/Cloud-1/instance
sudo chown -R www-data:www-data /var/log/kanardiacloud
```

3. **Database Issues**
```bash
# Check database permissions
ls -la /home/rok/src/Cloud-1/instance/
# Test database connectivity
sqlite3 /home/rok/src/Cloud-1/instance/kanardiacloud.db "SELECT 1;"
```

4. **High Memory Usage**
```bash
# Reduce worker count in gunicorn.conf.py
workers = 2  # Instead of CPU*2+1
```

### Performance Tuning

1. **Worker Optimization**
   - Monitor CPU and memory usage
   - Adjust worker count based on load
   - Consider using async workers for high concurrency

2. **Database Optimization**
   - Regular VACUUM operations
   - Index optimization
   - Consider PostgreSQL for high load

3. **Caching**
   - Implement Redis for session storage
   - Add application-level caching
   - Use Nginx caching for static content

## Scaling Considerations

### Horizontal Scaling
- Load balancer with multiple instances
- Shared database (PostgreSQL/MySQL)
- Shared session storage (Redis)

### Vertical Scaling
- Increase worker processes
- Allocate more CPU/memory
- SSD storage for database

## Maintenance

### Updates
```bash
# Stop service
sudo systemctl stop kanardiacloud

# Update code
cd /home/rok/src/Cloud-1
git pull

# Update dependencies
pip install -r requirements.txt

# Restart service
sudo systemctl start kanardiacloud
```

### Log Rotation
Automatic log rotation is configured via logrotate. Logs are rotated daily and kept for 52 weeks.

### Health Monitoring
Set up monitoring alerts for:
- Service status
- Response time
- Error rate
- Disk usage
- Memory usage

## Support

For issues or questions:
1. Check application logs: `sudo journalctl -u kanardiacloud -f`
2. Verify configuration: `sudo systemctl status kanardiacloud`
3. Test health endpoints: `curl http://127.0.0.1:8000/health`
