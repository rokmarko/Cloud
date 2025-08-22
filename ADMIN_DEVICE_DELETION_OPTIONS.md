# Admin Device Management - New Deletion Options

## Overview
Added comprehensive device data deletion options to the admin interface for more granular control over device data cleanup.

## New Features Added

### 1. Delete All Events
**Location**: Admin > Devices > Device Actions Dropdown
**Endpoint**: `POST /admin/devices/{device_id}/delete-all-events`
**Function**: `deleteAllEvents(deviceId, deviceName)`

**What it does**:
- Deletes ALL events for the specified device
- Automatically deletes associated logbook entries (cascading)
- Removes all flight points data linked to those events
- **Most destructive operation** - removes all historical data

**Confirmation**: Requires typing "DELETE ALL EVENTS"

### 2. Delete All Logbook Entries  
**Location**: Admin > Devices > Device Actions Dropdown
**Endpoint**: `POST /admin/devices/{device_id}/delete-logbook-entries`
**Function**: `deleteAllLogbookEntries(deviceId, deviceName)`

**What it does**:
- Deletes ALL logbook entries for the specified device
- Removes flight history data
- Keeps events intact (allows for logbook reconstruction)

**Confirmation**: Requires typing "DELETE LOGBOOK"

### 3. Delete Flight Details
**Location**: Admin > Devices > Device Actions Dropdown  
**Endpoint**: `POST /admin/devices/{device_id}/delete-flight-details`
**Function**: `deleteFlightDetails(deviceId, deviceName)`

**What it does**:
- Deletes ALL flight points/tracks for the specified device
- Removes detailed flight path data
- Keeps logbook entries but removes detailed flight information
- **Least destructive** - preserves flight summaries

**Confirmation**: Requires typing "DELETE FLIGHT DETAILS"

## User Interface

### Updated Dropdown Menu
Each device now has an expanded actions dropdown with:

```
┌─ Existing Options ─────────────┐
│ 👤 Reassign to User            │
├────────────────────────────────┤
│ 🔄 Force Rebuild Logbook       │
├────────────────────────────────┤
│ 🗑️ Delete All Events          │ ← NEW
│ 🗑️ Delete All Logbook Entries │ ← NEW  
│ ✈️ Delete Flight Details       │ ← NEW
├────────────────────────────────┤
│ 🔓 Unlink Device               │
│ 🗑️ Unlink (API)                │
└────────────────────────────────┘
```

### Safety Features
- **Multi-level confirmation**: Each operation requires confirmation dialog + typed confirmation
- **Descriptive warnings**: Clear explanation of what will be deleted
- **Visual indicators**: Red text and warning icons for destructive operations
- **Loading states**: Shows progress during deletion operations
- **Success/error feedback**: Clear status messages after operations

## Technical Implementation

### Backend Routes (`src/routes/admin.py`)
```python
@admin_bp.route('/devices/<int:device_id>/delete-all-events', methods=['POST'])
@admin_bp.route('/devices/<int:device_id>/delete-logbook-entries', methods=['POST'])  
@admin_bp.route('/devices/<int:device_id>/delete-flight-details', methods=['POST'])
```

### Frontend JavaScript (`templates/admin/devices.html`)
```javascript
function deleteAllEvents(deviceId, deviceName)
function deleteAllLogbookEntries(deviceId, deviceName)
function deleteFlightDetails(deviceId, deviceName)
```

### Database Operations
- **Events deletion**: `Event.query.filter_by(device_id=device.id).delete()`
- **Logbook deletion**: `LogbookEntry.query.filter_by(device_id=device.id).delete()`
- **Flight points deletion**: `FlightPoint.query.filter_by(device_id=device.id).delete()`

## Data Relationships

```
Device
├── Events ──────────────┐
│   └── (cascade) ──────┐│
├── LogbookEntries ──────┼┼── Delete All Events removes ALL
│   └── FlightPoints ──┼┴┘
└── FlightPoints ────────┘
```

**Delete hierarchy**:
1. **Delete All Events** → Removes Events + LogbookEntries + FlightPoints
2. **Delete Logbook Entries** → Removes LogbookEntries + associated FlightPoints  
3. **Delete Flight Details** → Removes only FlightPoints

## Usage Scenarios

### 1. Complete Device Reset
Use "Delete All Events" when:
- Device data is corrupted beyond repair
- Starting fresh data collection
- Removing test data before production

### 2. Logbook Cleanup
Use "Delete All Logbook Entries" when:
- Need to rebuild logbook from events
- Logbook entries are corrupted but events are valid
- Want to reset flight statistics

### 3. Storage Optimization  
Use "Delete Flight Details" when:
- Reducing database size
- Keeping flight summaries but removing detailed tracks
- Privacy concerns about detailed location data

## Security & Safety

### Access Control
- **Admin only**: All operations require `@admin_required` decorator
- **CSRF protection**: All endpoints protected against CSRF attacks
- **User authentication**: Must be logged in as admin user

### Confirmation System
- **Double confirmation**: Dialog + typed confirmation required
- **Specific phrases**: Must type exact phrases to confirm
- **Cancel options**: Easy to cancel at any point

### Logging
- All deletion operations are logged with details
- Success and error states are tracked
- Database transaction rollback on errors

## Testing

To test the new functionality:

1. **Access**: Go to Admin > Devices
2. **Select device**: Click actions dropdown for any device  
3. **Choose operation**: Select one of the new deletion options
4. **Confirm**: Follow the confirmation prompts
5. **Verify**: Check logs and database for successful deletion

## Current Status: ✅ IMPLEMENTED

- ✅ Frontend UI updated with new dropdown options
- ✅ JavaScript functions implemented with safety confirmations
- ✅ Backend routes added with proper error handling
- ✅ Database models imported and deletion logic implemented
- ✅ CSRF protection and admin authentication in place
- ✅ Server reloaded and ready for testing

The admin device management now provides granular control over device data deletion with appropriate safety measures.
