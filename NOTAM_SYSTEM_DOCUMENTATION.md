# NOTAM System Implementation Documentation

## Overview

The NOTAM (Notice to Airmen) system for KanardiaCloud provides automatic retrieval, parsing, storage, and notification of NOTAMs for supported European flight information regions (FIRs). The system fetches NOTAMs every 12 hours, detects changes, and sends email notifications to users who have configured their home area.

## Supported Areas

- **LJLA** - Ljubljana FIR (Slovenia)
- **EDMM** - München FIR (South Germany)  
- **LOVV** - Wien FIR (Austria)
- **LHCC** - Budapest FIR (Hungary)
- **LKAA** - Praha FIR (Czech Republic)

## System Components

### 1. NOTAM Parser (`src/notam.py`)

A comprehensive NOTAM parser that:
- Fetches NOTAMs from FAA website
- Parses Q-line structure (FIR, code, traffic, purpose, scope, coordinates, altitude)
- Extracts validity periods, coordinates, altitude limits
- Handles ICAO Q-codes with meanings
- Supports both permanent and temporary NOTAMs

### 2. Database Models (`src/models.py`)

#### User Model Extensions
- Added `home_area` field for NOTAM notification preferences

#### Notam Model
- Complete NOTAM information storage
- Q-line parsed components
- Geographic coordinates and radius
- Validity periods and status
- Full text storage for detailed view

#### NotamUpdateLog Model  
- Tracks update operations
- Statistics on new/updated/expired NOTAMs
- Error logging and status tracking

#### NotamNotificationSent Model
- Prevents duplicate notifications
- Tracks which users have been notified about which NOTAMs

### 3. NOTAM Service (`src/services/notam_service.py`)

Core service handling:
- Automated NOTAM fetching for all supported areas
- Change detection and database updates
- Email notification dispatch
- Data cleanup and maintenance
- Statistics and reporting

### 4. Routes (`src/routes/notam_routes.py`)

Web API endpoints:
- `/notams/` - Main NOTAM viewer interface
- `/notams/api/notams` - Get NOTAMs by area and date
- `/notams/api/notams/<id>` - Get detailed NOTAM information
- `/notams/api/statistics` - System statistics
- `/notams/api/fetch` - Manual fetch trigger (admin only)

### 5. User Interface (`templates/notams/viewer.html`)

Modern responsive interface featuring:
- Date selector for viewing NOTAMs on specific dates
- Area filter for specific FIRs
- Tab-based view (Table and Map)
- NOTAM search and filtering
- Detailed NOTAM modal with complete information
- Real-time statistics dashboard

### 6. Scheduled Tasks (`fetch_notams.py`)

Automated background process for:
- Fetching NOTAMs every 12 hours
- Processing and storing new data
- Detecting changes and sending notifications
- Cleanup of expired NOTAMs
- Comprehensive logging

## Installation & Setup

### 1. Database Migration

Run the migration script to add NOTAM tables:

```bash
python migrate_notam_tables.py
```

### 2. Configure Email (Optional)

For email notifications, ensure these environment variables are set:

```bash
MAIL_SERVER=smtp.your-server.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-password
MAIL_DEFAULT_SENDER=your-email@domain.com
```

### 3. Set Up Cron Job

Configure automatic NOTAM fetching:

```bash
# Edit crontab
crontab -e

# Add this line (update path to your installation)
0 6,18 * * * cd /path/to/KanardiaCloud && ./.venv/bin/python fetch_notams.py >> logs/notam_fetch.log 2>&1
```

### 4. Manual Testing

Test the system manually:

```bash
# Test NOTAM fetching
python fetch_notams.py

# Test for specific area
python -c "from src.services.notam_service import notam_service; from src.app import create_app; app = create_app(); app.app_context().push(); result = notam_service.fetch_and_store_notams('LJLA'); print(result)"
```

## User Configuration

### Home Area Setting

Users can configure their home area in User Settings:

1. Navigate to **User Settings** from the user menu
2. Select desired **Home Area for NOTAM Notifications**
3. Save settings

Available options:
- No NOTAM notifications (default)
- Ljubljana FIR (Slovenia) - LJLA
- München FIR (South Germany) - EDMM  
- Wien FIR (Austria) - LOVV
- Budapest FIR (Hungary) - LHCC
- Praha FIR (Czech Republic) - LKAA

### Email Notifications

When a home area is configured:
- User receives emails for new NOTAMs in their area
- Notifications include NOTAM summary and direct link to details
- Duplicate notifications are prevented
- Users can disable by setting home area to "No notifications"

## Using the NOTAM Viewer

### Accessing NOTAMs

1. Click **NOTAMs** in the sidebar navigation
2. Select area filter (optional - defaults to all areas)
3. Choose date (defaults to today)
4. View results in Table or Map view

### Table View Features

- **Search**: Filter NOTAMs by ID, type, or description
- **Sorting**: Click column headers to sort
- **Pagination**: Navigate through large result sets
- **Details**: Click any row or use View button for full details
- **Status Indicators**: Color-coded by criticality (red=critical, yellow=warning, blue=info)

### NOTAM Details

Click any NOTAM for detailed information including:
- Complete NOTAM text
- Parsed components (validity, coordinates, altitude limits)
- Q-code meaning and categorization
- Geographic information
- Altitude restrictions
- Original raw NOTAM text

### Statistics Dashboard

Top of the viewer shows:
- **Total NOTAMs**: All NOTAMs for selected filters
- **Active**: Currently valid NOTAMs
- **Critical**: Runway/airport related NOTAMs
- **Last Update**: Most recent data fetch

## NOTAM Categories

The system categorizes NOTAMs by Q-codes:

### Critical (Red Border)
- **QMR*** - Runway related (closures, damage, restrictions)
- **QNX*** - Taxiway/apron related (closures, surface issues)

### Warning (Yellow Border)  
- **QOB*** - Obstacles (cranes, wires, towers)
- **QRR***, **QRT*** - Airspace restrictions

### Informational (Blue Border)
- **QFA***, **QIL*** - Navigation aids, ILS issues
- **QLR*** - Lighting systems
- All other codes

## System Administration

### Manual NOTAM Fetch (Admin Only)

Administrators can trigger manual NOTAM updates:

1. Navigate to `/notams/api/fetch` (or use admin interface if implemented)
2. Optionally specify ICAO code: `/notams/api/fetch?icao=LJLA`
3. Returns JSON with operation results

### Monitoring and Logs

Check system health via:

```bash
# View NOTAM fetch logs
tail -f logs/notam_fetch.log

# View cron execution logs  
tail -f logs/cron.log

# Check database statistics
python -c "from src.services.notam_service import notam_service; from src.app import create_app; app = create_app(); app.app_context().push(); stats = notam_service.get_active_notams(); print(f'Active NOTAMs: {len(stats)}')"
```

### Database Maintenance

The system automatically:
- Cleans up expired NOTAMs older than 30 days (weekly)
- Logs all update operations
- Tracks notification history

Manual cleanup:
```bash
python -c "from src.services.notam_service import notam_service; from src.app import create_app; app = create_app(); app.app_context().push(); count = notam_service.cleanup_expired_notams(days_old=30); print(f'Cleaned {count} NOTAMs')"
```

## API Reference

### GET `/notams/api/notams`
Fetch NOTAMs with optional filters.

**Parameters:**
- `icao` (optional): Filter by ICAO code (LJLA, EDMM, etc.)  
- `date` (optional): Date in YYYY-MM-DD format (defaults to today)

**Response:**
```json
{
  "notams": [...],
  "count": 15,
  "date": "2025-08-24",
  "icao_code": "LJLA"
}
```

### GET `/notams/api/notams/<notam_id>`
Get detailed information for specific NOTAM.

**Response:**
```json
{
  "id": 123,
  "notam_id": "A1420/25", 
  "icao_code": "LJLA",
  "q_code": "QRTCA",
  "q_code_meaning": "Temporary reserved area active",
  "body": "TEMPORARY RESTRICTED AREA...",
  "valid_from": "2025-08-24T14:00:00Z",
  "valid_until": "2025-08-24T21:00:00Z",
  "is_active": true,
  "latitude": 45.65,
  "longitude": 14.3,
  "radius_nm": 2
}
```

### GET `/notams/api/statistics`
Get system statistics.

**Response:**
```json
{
  "overview": {
    "total_notams": 150,
    "active_notams": 45
  },
  "by_icao": {
    "LJLA": {"total": 30, "active": 8},
    "EDMM": {"total": 85, "active": 25}
  },
  "recent_updates": [...]
}
```

### POST `/notams/api/fetch` (Admin Only)
Manually trigger NOTAM fetch.

**Parameters:**
- `icao` (optional): Specific area to fetch

**Response:**
```json
{
  "success": true,
  "results": {
    "LJLA": {
      "total_fetched": 12,
      "new_notams": 3,
      "updated_notams": 1,
      "errors": []
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **No NOTAMs Loading**
   - Check internet connectivity
   - Verify FAA website accessibility
   - Check application logs for errors

2. **Email Notifications Not Sent**
   - Verify MAIL_* environment variables
   - Check user has home_area configured
   - Ensure new NOTAMs exist for that area

3. **Cron Job Not Running**
   - Check crontab: `crontab -l`
   - Verify file permissions: `ls -la fetch_notams.py`
   - Check cron logs: `tail -f /var/log/cron`

4. **Database Errors**
   - Run migration: `python migrate_notam_tables.py`
   - Check database connectivity
   - Verify table structure

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('src.notam').setLevel(logging.DEBUG)
logging.getLogger('src.services.notam_service').setLevel(logging.DEBUG)
```

## Security Considerations

- NOTAM data is fetched from public FAA website
- No sensitive information is stored
- Admin-only manual fetch endpoint prevents abuse
- Email notifications only sent to verified users
- Input validation on all API endpoints
- CSRF protection on web forms

## Performance Notes

- NOTAM fetching typically takes 30-60 seconds for all areas
- Database queries optimized with indexes
- Frontend implements pagination for large result sets
- Map view loads on-demand to reduce initial page load
- Background cleanup prevents database growth

## Future Enhancements

Potential improvements:
- Interactive map with NOTAM markers
- Push notifications for mobile users
- NOTAM filtering by severity/type
- Integration with flight planning tools
- Historical NOTAM archive
- Custom notification rules
- SMS notifications
- RESTful API for third-party integration

## Support

For issues or questions regarding the NOTAM system:

1. Check logs for error details
2. Verify configuration settings
3. Test manual NOTAM fetch
4. Review this documentation
5. Contact system administrator

## Technical Implementation Notes

The NOTAM system integrates seamlessly with the existing KanardiaCloud architecture:

- Uses existing user authentication and session management
- Follows established database patterns and relationships  
- Integrates with existing email notification system
- Maintains consistent UI/UX with material design theme
- Uses same CSRF protection and security measures
- Follows existing code organization and standards

The implementation is designed to be:
- **Reliable**: Robust error handling and logging
- **Scalable**: Efficient database queries and pagination
- **Maintainable**: Clear code structure and documentation
- **User-friendly**: Intuitive interface and helpful feedback
- **Extensible**: Modular design for future enhancements
