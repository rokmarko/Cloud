#!/bin/bash
# Production status check script for KanardiaCloud

echo "=== KanardiaCloud Production Status Check ==="
echo "Date: $(date)"
echo

# Check service status
echo "1. Systemd Service Status:"
systemctl is-active kanardiacloud.service
echo "   Uptime: $(systemctl show -p ActiveEnterTimestamp kanardiacloud.service --value)"
echo

# Check if the application is responding
echo "2. Application Health:"
if curl -s -f http://127.0.0.1:5000/health > /dev/null; then
    echo "   ✅ Application is responding"
    curl -s http://127.0.0.1:5000/health | python3 -m json.tool
else
    echo "   ❌ Application is not responding"
fi
echo

# Check environment variables loading
echo "3. Environment Configuration:"
response=$(curl -s http://127.0.0.1:5000/health)
if echo "$response" | grep -q "healthy"; then
    echo "   ✅ Environment loaded successfully"
else
    echo "   ❌ Environment configuration issues"
fi
echo

# Check process information
echo "4. Process Information:"
ps aux | grep -E "(gunicorn|kanardiacloud)" | grep -v grep
echo

# Check resource usage
echo "5. Resource Usage:"
systemctl show kanardiacloud.service --property=MemoryCurrent,CPUUsageNSec
echo

# Check recent logs
echo "6. Recent Logs (last 10 lines):"
journalctl -u kanardiacloud.service --lines=10 --no-pager
echo

echo "=== Status Check Complete ==="
