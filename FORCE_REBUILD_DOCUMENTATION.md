# Force Rebuild Logbook Feature

## Overview

The Force Rebuild Logbook feature has been added to the admin section under devices. This feature allows administrators to completely rebuild the logbook for a specific device from scratch.

## What it does

1. **Clears event messages**: Removes all stored event messages for the selected device from the database
2. **Removes existing logbook entries**: Deletes all event-generated logbook entries for the device (identified by the "Generated from device events" marker in remarks)
3. **Rebuilds from events**: Recreates logbook entries by processing all events from ThingsBoard
4. **Universal visibility**: New entries are created with `user_id=None` making them visible to all users including unmapped pilots

## How to use

1. Navigate to the Admin section (`/admin/devices`)
2. Find the device you want to rebuild the logbook for
3. Click the dropdown menu (three dots) in the actions column
4. Select "Force Rebuild Logbook" (displayed with a refresh icon and warning color)
5. Confirm the action in the warning dialog

## Warning Dialog

The system will show a comprehensive warning explaining:
- This action clears all event messages for the device
- Removes all existing event-generated logbook entries  
- Recreates logbook entries from all events
- The process cannot be undone

## Backend Implementation

### Route
```
POST /admin/devices/<device_id>/force-rebuild-logbook
```

### Process
1. Authenticates admin user
2. Clears Event messages for the device
3. Calls `thingsboard_sync._rebuild_complete_logbook_from_events(device)`
4. Returns JSON response with success/failure status and detailed message

### Database Changes
- Deletes records from `Event` table where `device_id` matches
- Deletes logbook entries with device_id and "Generated from device events" in remarks
- Creates new logbook entries with optimized sync process

## Frontend Implementation

### UI Elements
- Dropdown menu item with warning color (`text-warning`)
- Material Icons refresh symbol
- Confirmation dialog with detailed warning
- Success/error alert messages
- Loading indicator during processing

### JavaScript Function
```javascript
forceRebuildLogbook(deviceId, deviceName)
```

## Error Handling

- Database rollback on errors
- Comprehensive error logging
- User-friendly error messages
- JSON response format for AJAX handling

## Logging

All force rebuild operations are logged with:
- Device information
- Number of cleared event messages
- Number of removed old entries
- Number of created new entries
- Any errors encountered

## Security

- Requires admin authentication
- CSRF token protection
- Input validation for device_id
- Error handling prevents information disclosure

## Performance Considerations

- Processing time depends on number of events
- Loading indicator shows during processing
- Longer timeout for info messages (10 seconds vs 5 seconds)
- Background processing recommended for large datasets

## Related Features

This feature works in conjunction with:
- Optimized sync system (incremental processing)
- Universal logbook visibility (user_id=None)
- Pilot access control for device logbooks
- Event message management
