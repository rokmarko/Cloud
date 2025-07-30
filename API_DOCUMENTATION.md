# KanardiaCloud External API Documentation

This document describes the private API endpoints for external servers to interact with KanardiaCloud.

## Version History

### v1.2.0 (2025-07-30)
- **Device Linking**: Logbook entries now link to the syncing device via device_id
- **Device Information Priority**: Aircraft registration and type now preferentially use device information
- **Enhanced Sync Logic**: Improved duplicate detection based on device and flight details
- **Visual Indicators**: Synced entries display device information and sync badges in UI

### v1.1.0 (2025-07-30)
- **Major Update**: Enhanced logbook model with time-based flight tracking
- Added support for `takeoff_time` and `landing_time` fields
- Automatic flight duration calculation from time values
- Backward compatibility with legacy `flight_time` format
- Improved midnight crossover handling
- Enhanced time format support (multiple formats accepted)

### v1.0.0 (2025-07-22)
- Initial API release
- Device claiming and management
- Basic ThingsBoard integration
- Health check endpoints

## Table of Contents
1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [External Device Management](#external-device-management)
4. [ThingsBoard Integration](#thingsboard-integration)
5. [API Endpoints](#api-endpoints)
6. [Error Handling](#error-handling)
7. [Usage Examples](#usage-examples)
8. [Security Notes](#security-notes)

## Authentication

All API endpoints require authentication using an API key passed in the `X-API-Key` header.

```
X-API-Key: your-api-key-here
```

The API key should be configured in the server's environment as `EXTERNAL_API_KEY`.

## Base URL

All API endpoints are prefixed with `/api/external/`

Example: `https://your-domain.com/api/external/claim-device`

## External Device Management

KanardiaCloud supports linking devices to external systems (like ThingsBoard) for automatic logbook synchronization. When a device is claimed via the API, it can optionally include an `external_device_id` for integration with external IoT platforms.

## ThingsBoard Integration

### Background Sync Service

KanardiaCloud includes a background service that automatically synchronizes logbook entries from a ThingsBoard server every 5 minutes. The service:

- Queries ThingsBoard server at `aetos.kanardia.eu:8088`
- Uses RPC method `syncLog` via POST `/api/plugins/rpc/twoway/{deviceId}`
- Processes JSON array responses containing logbook entry data
- Automatically creates logbook entries for users with linked devices
- Prevents duplicate entries by checking existing records

### Required ThingsBoard Data Format

The ThingsBoard `syncLog` RPC method should return a JSON array of logbook entries:

```json
[
  {
    "date": "2025-07-24",
    "aircraft_registration": "N123AB",
    "aircraft_type": "Cessna 172",
    "departure_airport": "KJFK",
    "arrival_airport": "KLGA",
    "takeoff_time": "10:30:00",
    "landing_time": "12:00:00",
    "pilot_in_command_time": 1.5,
    "dual_time": 0,
    "instrument_time": 0.2,
    "night_time": 0,
    "cross_country_time": 0,
    "landings_day": 2,
    "landings_night": 0,
    "remarks": "Training flight"
  }
]
```

#### Field Descriptions

**Required Fields:**
- `date`: Flight date in YYYY-MM-DD format
- `aircraft_registration`: Aircraft registration/tail number
- `departure_airport`: ICAO code of departure airport
- `arrival_airport`: ICAO code of arrival airport

**Time Fields (recommended):**
- `takeoff_time`: Takeoff time in HH:MM:SS format (24-hour)
- `landing_time`: Landing time in HH:MM:SS format (24-hour)

**Legacy Support:**
- `flight_time`: Total flight duration in hours (decimal). If `takeoff_time` and `landing_time` are not provided, this field will be used with default takeoff time of 10:00:00

**Optional Fields:**
- `aircraft_type`: Aircraft make/model
- `pilot_in_command_time`: PIC time in hours (decimal)
- `dual_time`: Dual instruction time in hours (decimal)
- `instrument_time`: Instrument flight time in hours (decimal)
- `night_time`: Night flight time in hours (decimal)
- `cross_country_time`: Cross-country time in hours (decimal)
- `landings_day`: Number of day landings (integer)
- `landings_night`: Number of night landings (integer)
- `remarks`: Additional notes or comments

#### Time Calculation

Flight time is automatically calculated from `takeoff_time` and `landing_time`. The system handles:
- **Midnight crossovers**: Flights that land after midnight
- **Time zone considerations**: All times treated as local aircraft time
- **Precise duration calculations**: Results in decimal hours (e.g., 1.25 hours = 1 hour 15 minutes)
- **Multiple time formats**: Supports HH:MM:SS, HH:MM, HH.MM.SS, HH.MM, and 12-hour formats

#### Supported Time Formats

The system accepts various time formats:
- `"10:30:00"` - 24-hour with seconds (preferred)
- `"10:30"` - 24-hour without seconds  
- `"10.30.00"` - Period-separated with seconds
- `"10.30"` - Period-separated without seconds
- `"10:30:00 AM"` - 12-hour format with AM/PM

#### Legacy Compatibility

If only `flight_time` is provided (legacy format), the system will use a default takeoff time of 10:00:00 and calculate the landing time based on the flight duration. This ensures backward compatibility with existing integrations while encouraging migration to the more precise time-based format.

### Managing Device Sync

Administrators can configure ThingsBoard sync for devices via the admin panel:

1. **Configure Devices**: Navigate to **Admin** → **ThingsBoard Sync** → **Configure Devices**
2. **Set External Device ID**: Assign ThingsBoard device IDs to KanardiaCloud devices
3. **Monitor Sync Status**: View sync results and authentication status
4. **Manual Sync**: Trigger immediate sync for testing or troubleshooting

#### Sync Process Details

- **Automatic Sync**: Runs every 5 minutes for all configured devices
- **Device Linking**: All synced entries are linked to the originating device via device_id
- **Aircraft Information**: Uses device registration and model preferentially over data payload
- **Authentication**: Uses JWT tokens with automatic refresh
- **Duplicate Prevention**: Checks existing entries by device, date, airports, and times
- **Error Handling**: Logs failures and continues with other devices
- **Time Calculations**: Automatically calculates flight duration from takeoff/landing times

#### Aircraft Information Priority

For synced entries, aircraft information is determined in this order:
1. **Device Information** (preferred): Uses device.registration and device.model
2. **Payload Fallback**: Uses aircraft_registration and aircraft_type from sync data
3. **Default Values**: Uses "UNKNOWN" if neither source provides information

This ensures that device-specific information takes precedence while maintaining compatibility with external data sources.

#### Authentication Status

The admin interface shows real-time ThingsBoard authentication status:
- **Connection Status**: Connected/Disconnected
- **Last Authentication**: Timestamp of last successful auth
- **Token Expiry**: When the current JWT token expires
- **Recent Errors**: Any authentication or sync errors

#### Sync Statistics

Recent sync information includes:
- **Total Devices**: Number of devices configured for sync
- **Synced Devices**: Number successfully synced in last run
- **New Entries**: Number of new logbook entries created
- **Errors**: Any sync failures or issues

## API Endpoints

### 1. Claim Device

Claim a device for a user by their email address.

**Endpoint:** `POST /api/external/claim-device`

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "user_email": "pilot@example.com",
  "device_name": "Aircraft N123AB",
  "device_id": "external_device_123",
  "device_type": "aircraft",
  "model": "Cessna 172",
  "serial_number": "17280123",
  "registration": "N123AB"
}
```

**Required Fields:**
- `user_email`: The email address of the user to claim the device for
- `device_name`: Human-readable name for the device
- `device_id`: Unique identifier for the device from external system

**Optional Fields:**
- `device_type`: Type of device (`aircraft`, `radio`, `gps`, `transponder`, `other`)
- `model`: Device model/make
- `serial_number`: Manufacturer serial number
- `registration`: Aircraft registration (for aircraft type)

**Success Response (201):**
```json
{
  "success": true,
  "message": "Device claimed successfully",
  "device": {
    "id": 123,
    "name": "Aircraft N123AB",
    "device_type": "aircraft",
    "model": "Cessna 172",
    "serial_number": "external_device_123",
    "registration": "N123AB",
    "created_at": "2025-07-22T10:30:00"
  },
  "user": {
    "email": "pilot@example.com",
    "nickname": "John Pilot"
  }
}
```

**Error Responses:**
- `400`: Missing required fields or invalid request
- `401`: Missing API key
- `403`: Invalid API key
- `404`: User not found
- `409`: Device already exists for this user
- `500`: Internal server error

### 2. Check Device Status

Check if a device is claimed and get information about it.

**Endpoint:** `GET /api/external/device-status/{device_id}`

**Headers:**
```
X-API-Key: your-api-key-here
```

**URL Parameters:**
- `device_id`: The external device identifier

**Success Response (200):**
```json
{
  "device_id": "external_device_123",
  "claimed": true,
  "device": {
    "id": 123,
    "name": "Aircraft N123AB",
    "device_type": "aircraft",
    "model": "Cessna 172",
    "registration": "N123AB",
    "created_at": "2025-07-22T10:30:00"
  },
  "user": {
    "email": "pilot@example.com",
    "nickname": "John Pilot"
  }
}
```

**Not Found Response (404):**
```json
{
  "device_id": "external_device_123",
  "claimed": false,
  "message": "Device not found or not claimed"
}
```

### 3. Unclaim Device

Remove a device from a user (soft delete).

**Endpoint:** `POST /api/external/unclaim-device`

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "device_id": "external_device_123"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Device unclaimed successfully",
  "device_id": "external_device_123"
}
```

### 4. Health Check

Check if the API is healthy and available.

**Endpoint:** `GET /api/external/health`

**Headers:** None required (public endpoint)

**Success Response (200):**
```json
{
  "status": "healthy",
  "service": "KanardiaCloud API",
  "version": "1.0.0"
}
```

## Error Handling

All endpoints return JSON responses with consistent error formatting:

```json
{
  "error": "Error type",
  "message": "Human-readable error description"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created successfully
- `400`: Bad request (validation errors)
- `401`: Unauthorized (missing API key)
- `403`: Forbidden (invalid API key)
- `404`: Not found
- `409`: Conflict (resource already exists)
- `500`: Internal server error

## Usage Examples

### Logbook Sync Integration

#### ThingsBoard RPC Response Example

Example response from a ThingsBoard device's `syncLog` RPC method:

```json
[
  {
    "date": "2025-07-30",
    "aircraft_registration": "N123AB",
    "aircraft_type": "Cessna 172",
    "departure_airport": "KJFK",
    "arrival_airport": "KLGA", 
    "takeoff_time": "09:15:30",
    "landing_time": "10:45:15",
    "pilot_in_command_time": 1.5,
    "dual_time": 0,
    "instrument_time": 0.25,
    "night_time": 0,
    "cross_country_time": 1.5,
    "landings_day": 1,
    "landings_night": 0,
    "remarks": "Cross-country training flight"
  },
  {
    "date": "2025-07-30",
    "aircraft_registration": "N123AB", 
    "aircraft_type": "Cessna 172",
    "departure_airport": "KLGA",
    "arrival_airport": "KJFK",
    "takeoff_time": "14:30:00",
    "landing_time": "15:45:00", 
    "pilot_in_command_time": 1.25,
    "dual_time": 0,
    "instrument_time": 0,
    "night_time": 0,
    "cross_country_time": 1.25,
    "landings_day": 1,
    "landings_night": 0,
    "remarks": "Return flight"
  }
]
```

#### Legacy Format Support

For backward compatibility, the old format with `flight_time` is still supported:

```json
[
  {
    "date": "2025-07-30",
    "aircraft_registration": "N123AB",
    "aircraft_type": "Cessna 172", 
    "departure_airport": "KJFK",
    "arrival_airport": "KLGA",
    "flight_time": 1.5,
    "pilot_in_command_time": 1.5,
    "dual_time": 0,
    "instrument_time": 0.25,
    "night_time": 0,
    "cross_country_time": 1.5,
    "landings_day": 1,
    "landings_night": 0,
    "remarks": "Training flight"
  }
]
```

When using the legacy format, the system will:
- Use a default takeoff time of 10:00:00
- Calculate landing time based on the flight duration
- Preserve the exact flight time value provided

### Python Example

```python
import requests

API_KEY = "your-api-key-here"
BASE_URL = "https://your-domain.com/api/external"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Claim a device
payload = {
    "user_email": "pilot@example.com",
    "device_name": "Aircraft N123AB",
    "device_id": "external_device_123",
    "device_type": "aircraft",
    "model": "Cessna 172",
    "registration": "N123AB"
}

response = requests.post(f"{BASE_URL}/claim-device", json=payload, headers=headers)

if response.status_code == 201:
    print("Device claimed successfully!")
    print(response.json())
else:
    print(f"Error: {response.status_code}")
    print(response.json())
```

### curl Example

```bash
# Test health endpoint (no API key required)
curl -X GET "http://localhost:5000/api/external/health"

# Claim a device
curl -X POST "http://localhost:5000/api/external/claim-device" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: kanardia-external-api-key-2025-change-in-production" \
  -d '{
    "user_email": "test@example.com",
    "device_name": "Aircraft N123AB",
    "device_id": "external_device_123",
    "device_type": "aircraft",
    "model": "Cessna 172",
    "registration": "N123AB"
  }'

# Check device status
curl -X GET "http://localhost:5000/api/external/device-status/external_device_123" \
  -H "X-API-Key: kanardia-external-api-key-2025-change-in-production"

# Unclaim a device
curl -X POST "http://localhost:5000/api/external/unclaim-device" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: kanardia-external-api-key-2025-change-in-production" \
  -d '{
    "device_id": "external_device_123"
  }'
```

## Security Notes

1. **API Key Security**: Keep your API key secure and never expose it in client-side code
2. **HTTPS Required**: Always use HTTPS in production
3. **Rate Limiting**: Consider implementing rate limiting for production use
4. **Logging**: All API calls are logged for security monitoring
5. **User Validation**: Only active and verified users can have devices claimed for them

## Support

For API support or issues, contact the KanardiaCloud development team.
