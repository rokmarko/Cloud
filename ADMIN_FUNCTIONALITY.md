# Admin Functionality Documentation

## Overview

The KanardiaCloud application now includes comprehensive admin functionality that allows designated users to manage all users and their devices across the platform.

## Features Added

### 1. Admin User Role
- Added `is_admin` boolean field to the User model
- Admin users have elevated privileges to access admin panel
- Regular users cannot access admin functionality

### 2. Admin Panel Dashboard
- **Route**: `/admin/`
- **Features**:
  - Statistics overview (total users, devices, checklists, logbook entries)
  - Recent users and devices widgets
  - Quick action buttons

### 3. User Management
- **Route**: `/admin/users`
- **Features**:
  - View all users with pagination
  - See user status (active/inactive, verified/unverified, admin/regular)
  - Toggle admin privileges for any user (except yourself)
  - Activate/deactivate user accounts
  - View device count per user

### 4. Device Management
- **Route**: `/admin/devices`
- **Features**:
  - View all devices across all users
  - See device details (name, type, owner, model, registration, serial number)
  - Unlink devices from users (soft delete)
  - Both form-based and API-based unlinking options

## Navigation Updates

### Top Navigation
- Added "Admin Panel" link in user dropdown menu (visible only to admin users)

### Sidebar Navigation
- Added "Administration" section with:
  - Admin Panel
  - Manage Users
  - All Devices

## API Endpoints

### Admin Device Management
- `DELETE /admin/api/devices/<device_id>` - Unlink device via API

## Security

### Admin-Only Access
- All admin routes are protected with `@admin_required` decorator
- Non-admin users are redirected to home page with error message
- Users cannot modify their own admin status

### CSRF Protection
- All admin forms include CSRF tokens
- AJAX requests include CSRF headers

## Database Migration

### Adding Admin Field
- Migration script: `migrate_admin_field.py`
- Adds `is_admin` BOOLEAN field to user table
- Default value: False

## Admin User Management Scripts

### Create Test Admin
```bash
python create_test_admin.py
```
Creates a test admin user:
- Email: admin@kanardia.test
- Password: admin123
- Nickname: Test Admin

### Grant Admin Privileges
```bash
python make_admin.py <email>
python make_admin.py --list
```

## Usage Examples

### Making a User Admin
1. Use the script: `python make_admin.py user@example.com`
2. Or use the admin panel: Admin Panel → Manage Users → Click dropdown → Make Admin

### Viewing All Devices
1. Login as admin user
2. Navigate to Admin Panel → All Devices
3. View devices across all users with owner information

### Unlinking a Device
1. Go to Admin Panel → All Devices
2. Find the device to unlink
3. Click dropdown → Unlink Device
4. Confirm the action

## Technical Implementation

### Models
- Added `is_admin` field to User model
- Admin check method: `current_user.is_admin`

### Routes
- Admin blueprint: `src/routes/admin.py`
- URL prefix: `/admin`
- Protection: `@login_required` + `@admin_required`

### Templates
- Admin templates in: `templates/admin/`
- Consistent Material Design styling
- Responsive design with pagination

### Permissions
- Admin users can:
  - View all users and their data
  - Grant/revoke admin privileges (except for themselves)
  - Activate/deactivate user accounts
  - View all devices across users
  - Unlink devices from users
- Regular users cannot access admin functionality

## Notes

### Soft Deletion
- Device unlinking uses soft deletion (sets `is_active = False`)
- Data is preserved for auditing purposes
- Deleted devices don't appear in user interfaces

### Self-Protection
- Admin users cannot modify their own admin status
- Admin users cannot deactivate themselves
- Prevents accidental lockout scenarios
