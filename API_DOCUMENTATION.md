# KanardiaCloud External API Documentation

This document describes the private API endpoints for external servers to interact with KanardiaCloud.

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
    "flight_time": 1.5,
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

### Managing Device Sync

Administrators can configure ThingsBoard sync for devices via the admin panel:
1. Navigate to **Admin** → **ThingsBoard Sync** → **Configure Devices**
2. Set the external device ID for each device that should sync
3. Monitor sync status and recent entries in the sync dashboard

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
