# Device Owner Pilot Mapping Feature

## Overview

This feature allows device owners to create and manage pilot mappings for their devices directly from the dashboard, without requiring admin access. This provides better autonomy for device owners while maintaining security.

## Features

### 1. **Device Owner Access**
- Only device owners can manage pilot mappings for their devices
- Accessible through the device logbook page via "Manage Pilots" button
- Separate interface from admin pilot management

### 2. **Pilot Mapping Management**
- **Create mappings**: Link pilot names from logbook entries to user accounts
- **View mappings**: See all current pilot mappings for the device
- **Delete mappings**: Remove pilot mappings when no longer needed
- **Search functionality**: Find existing mappings by pilot name or user email

### 3. **Smart Suggestions**
- **Unmapped pilot detection**: Automatically identifies pilot names in logbook entries without user mappings
- **Quick selection**: One-click selection of unmapped pilots when creating new mappings
- **Autocomplete**: Type-ahead suggestions for pilot names based on logbook entries

### 4. **Statistics and Monitoring**
- Coverage percentage (mapped vs unmapped pilots)
- Number of logbook entries per pilot mapping
- Creation dates for tracking when mappings were established

## How to Use

### For Device Owners:

1. **Access Pilot Management**
   - Go to your device's logbook page
   - Click "Manage Pilots" button (only visible to device owners)

2. **Create a New Pilot Mapping**
   - Click "Add Pilot Mapping" button
   - Enter the pilot name exactly as it appears in logbook entries
   - Enter the email address of the user account to map to
   - Click "Create Pilot Mapping"

3. **Use Quick Selection**
   - If unmapped pilots are detected, use the quick-select buttons
   - These buttons auto-fill the pilot name field with detected names

4. **Delete Mappings**
   - Click the trash icon next to any mapping
   - Confirm deletion in the modal dialog
   - The mapping will be removed but logbook entries remain

## Technical Implementation

### Routes Added:
- `GET /dashboard/devices/<device_id>/pilots` - Pilot management page
- `POST /dashboard/devices/<device_id>/pilots/create` - Create new mapping
- `POST /dashboard/devices/<device_id>/pilots/<pilot_id>/delete` - Delete mapping
- `GET /dashboard/api/devices/<device_id>/pilots/suggestions` - Autocomplete API

### Security:
- All routes verify device ownership (`device.user_id == current_user.id`)
- CSRF protection on all forms
- Input validation and sanitization
- Proper error handling and logging

### Form:
- `DevicePilotMappingForm`: Simple form with pilot name and user email fields
- Email validation ensures valid email format
- Required field validation

### Database:
- Uses existing `Pilot` model
- Maintains referential integrity with User and Device models
- Supports soft deletes through `is_active` flag

## Benefits

1. **User Autonomy**: Device owners can manage their own pilot mappings
2. **Reduced Admin Load**: No need for admin intervention for basic pilot mapping tasks
3. **Better User Experience**: Direct access from device logbook context
4. **Improved Accuracy**: Pilot names suggested from actual logbook entries
5. **Real-time Feedback**: Immediate statistics and unmapped pilot detection

## Integration Points

### Device Logbook Template:
- Added "Manage Pilots" button for device owners
- Button only shows when `device.user_id == current_user.id`

### Existing Pilot System:
- Fully compatible with existing admin pilot management
- Uses same database models and relationships
- Maintains all existing functionality

### Access Control:
- Device owners: Can manage pilots for their own devices
- Mapped pilots: Can view device logbooks they're mapped to
- Admins: Retain full access to all pilot mappings

## Example Workflow

1. **Device owner notices unmapped pilot in logbook**
   ```
   Logbook entry shows: "John Smith" (Unknown pilot)
   ```

2. **Access pilot management**
   ```
   Device Logbook → "Manage Pilots" button
   ```

3. **Create mapping**
   ```
   Pilot Name: "John Smith" (auto-suggested)
   User Email: "john.smith@example.com"
   ```

4. **Result**
   ```
   Logbook entry now shows: "John Smith" → "john.smith@example.com"
   John can now access this device's logbook
   ```

## Future Enhancements

- **Email notifications**: Notify users when they're mapped to a device
- **Pilot invitations**: Send invites to create accounts for unmapped pilots
- **Bulk operations**: Map multiple pilots at once
- **Mapping history**: Track changes to pilot mappings over time
- **Role-based permissions**: Different levels of access for mapped pilots
