# KanardiaCloud External API Documentation

This document describes the private API endpoints for external servers to interact with KanardiaCloud.

## Version History

### v1.3.0 (2025-08-22)
- **Airfield Management**: Complete airfield database management via API
- Added support for creating, updating, and querying aviation airfields with source tracking
- **Bulk Operations**: Bulk import/update multiple airfields in single request with status reporting
- **Geocoding API**: Reverse geocoding using aviation database with distance calculations
- **Proximity Search**: Find nearest airfields within specified radius (up to 500km)
- **Source Tracking**: Mandatory source field to track data origin for each airfield entry
- **Admin Interface**: Web-based airfield management interface with search, edit, and delete capabilities
- **Database Migration**: Automatic migration support for adding source tracking to existing data
- **Enhanced Validation**: Improved coordinate validation and ICAO code formatting

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
5. [Airfield Database Management](#airfield-database-management)
6. [API Endpoints](#api-endpoints)
7. [Error Handling](#error-handling)
8. [Usage Examples](#usage-examples)
9. [Security Notes](#security-notes)

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

## Airfield Database Management

KanardiaCloud includes a comprehensive airfield database management system that supports both API-based operations and web-based administration.

### Aviation Geocoding Service

The system uses a database-driven approach for aviation-specific geocoding:

- **ICAO Airfield Database**: Stores comprehensive airfield information including coordinates, elevation, runway data, and radio frequencies
- **Proximity Search**: Find nearest airfields using Haversine formula calculations within customizable radius (max 500km)
- **Reverse Geocoding**: Convert coordinates to aviation-specific location descriptions using nearest airfield
- **Data Source Tracking**: Mandatory source field tracks who or what system loaded each airfield entry
- **Automatic ICAO Formatting**: ICAO codes are automatically converted to uppercase for consistency
- **Comprehensive Validation**: Real-time validation of coordinates, ICAO codes, and required fields

### Supported Airfield Data

Each airfield entry can contain:

- **Basic Information**: ICAO code (4 characters, auto-uppercased), name, coordinates, country, region
- **Aviation Details**: Elevation in feet, runway information (JSON), radio frequencies (JSON)
- **Administrative**: Source tracking (mandatory), active status, creation/update timestamps
- **Extended Data**: JSON-formatted runway specifications and frequency tables with flexible schema
- **Geospatial**: Precise latitude/longitude coordinates with validation (-90/90, -180/180)

### Admin Interface Integration

The web-based admin interface provides:

- **Comprehensive CRUD Operations**: Create, read, update, delete airfields with full field validation
- **Advanced Search and Filtering**: Find airfields by country, region, ICAO code, or proximity with customizable radius
- **Bulk Operations**: Mass import/export capabilities with detailed status reporting and error handling
- **Real-time Data Validation**: Live validation of ICAO codes, coordinates, and data consistency
- **External Integration Links**: Quick access to Google Maps and SkyVector for verification and cross-reference
- **Source Management**: Track and display data sources for audit trails and data quality assurance
- **Delete Operations**: Secure deletion with confirmation dialogs, including bulk delete all functionality

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

### 5. Add or Update Airfield

Add a new airfield or update an existing one in the geocoding database. The system automatically handles create vs. update operations based on ICAO code uniqueness.

**Endpoint:** `POST /api/external/airfields`

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "icao_code": "LJLJ",
  "name": "Ljubljana Jože Pučnik Airport",
  "latitude": 46.2237,
  "longitude": 14.4576,
  "country": "Slovenia",
  "region": "Central Europe",
  "elevation_ft": 1273,
  "source": "OpenFlights Database 2025",
  "runway_info": {
    "runways": [
      {
        "designation": "31/13",
        "length_m": 3300,
        "width_m": 45,
        "surface": "Asphalt",
        "lighting": "High Intensity"
      }
    ]
  },
  "frequencies": {
    "tower": "118.100",
    "ground": "121.700",
    "approach": "119.100",
    "departure": "119.100",
    "atis": "126.225"
  },
  "is_active": true
}
```

**Required Fields:**
- `icao_code`: 4-letter ICAO airport code (automatically converted to uppercase, must be unique)
- `name`: Airport name (max 200 characters)
- `latitude`: Latitude in decimal degrees (range: -90.0 to 90.0)
- `longitude`: Longitude in decimal degrees (range: -180.0 to 180.0)
- `source`: Data source identifier (max 100 characters) - **Required for tracking data origin**

**Optional Fields:**
- `country`: Country name (max 50 characters)
- `region`: Geographic region (max 50 characters)
- `elevation_ft`: Elevation in feet above sea level (integer)
- `runway_info`: JSON object with runway specifications (stored as text)
- `frequencies`: JSON object with radio frequencies (stored as text)
- `is_active`: Boolean flag indicating if airfield is active (defaults to true)

**Data Processing:**
- ICAO codes are automatically converted to uppercase for consistency
- Coordinates are validated to ensure they fall within valid ranges
- Existing airfields (same ICAO code) are updated; new ones are created
- JSON fields (runway_info, frequencies) can contain any valid JSON structure
- Source field is used for audit trails and data quality management

**Success Response (201 - Created):**
```json
{
  "success": true,
  "message": "Airfield created successfully",
  "airfield": {
    "id": 123,
    "icao_code": "LJLJ",
    "name": "Ljubljana Jože Pučnik Airport",
    "latitude": 46.2237,
    "longitude": 14.4576,
    "country": "Slovenia",
    "region": "Central Europe",
    "elevation_ft": 1273,
    "source": "OpenFlights Database 2025",
    "is_active": true,
    "created_at": "2025-08-22T10:30:00",
    "updated_at": "2025-08-22T10:30:00",
    "runway_info": {
      "runways": [
        {
          "designation": "31/13",
          "length_m": 3300,
          "width_m": 45,
          "surface": "Asphalt",
          "lighting": "High Intensity"
        }
      ]
    },
    "frequencies": {
      "tower": "118.100",
      "ground": "121.700",
      "approach": "119.100",
      "departure": "119.100",
      "atis": "126.225"
    }
  }
}
```

**Success Response (200 - Updated):**
```json
{
  "success": true,
  "message": "Airfield updated successfully",
  "airfield": {
    "id": 123,
    "icao_code": "LJLJ",
    "name": "Ljubljana Jože Pučnik Airport",
    "latitude": 46.2237,
    "longitude": 14.4576,
    "country": "Slovenia",
    "region": "Central Europe",
    "elevation_ft": 1273,
    "source": "OpenFlights Database 2025",
    "is_active": true,
    "created_at": "2025-08-20T08:15:00",
    "updated_at": "2025-08-22T10:35:00",
    "runway_info": {
      "runways": [
        {
          "designation": "31/13",
          "length_m": 3300,
          "width_m": 45,
          "surface": "Asphalt",
          "lighting": "High Intensity"
        }
      ]
    },
    "frequencies": {
      "tower": "118.100",
      "ground": "121.700",
      "approach": "119.100",
      "departure": "119.100",
      "atis": "126.225"
    }
  }
}
```

**Error Response (400 - Validation Error):**
```json
{
  "error": "Validation failed",
  "message": "Missing required fields: source",
  "details": {
    "field": "source",
    "requirement": "Source field is required for tracking data origin"
  }
}
```

**Error Response (400 - Invalid Coordinates):**
```json
{
  "error": "Invalid coordinates",
  "message": "Latitude must be between -90 and 90 degrees"
}
```

### 6. Bulk Add/Update Airfields

Add or update multiple airfields in a single request with detailed processing results and error reporting.

**Endpoint:** `POST /api/external/airfields/bulk`

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "airfields": [
    {
      "icao_code": "LJLJ",
      "name": "Ljubljana Jože Pučnik Airport",
      "latitude": 46.2237,
      "longitude": 14.4576,
      "country": "Slovenia",
      "region": "Central Europe",
      "elevation_ft": 1273,
      "source": "Bulk Import OpenFlights 2025",
      "runway_info": {
        "runways": [
          {
            "designation": "31/13",
            "length_m": 3300,
            "width_m": 45,
            "surface": "Asphalt"
          }
        ]
      },
      "frequencies": {
        "tower": "118.100",
        "ground": "121.700",
        "approach": "119.100"
      }
    },
    {
      "icao_code": "LJMB",
      "name": "Maribor Edvard Rusjan Airport",
      "latitude": 46.4796,
      "longitude": 15.6861,
      "country": "Slovenia",
      "region": "Central Europe",
      "elevation_ft": 879,
      "source": "Bulk Import OpenFlights 2025"
    },
    {
      "icao_code": "LJPZ",
      "name": "Portorož Airport",
      "latitude": 45.4733,
      "longitude": 13.6150,
      "country": "Slovenia",
      "source": "Bulk Import OpenFlights 2025"
    }
  ]
}
```

**Requirements:**
- Each airfield must include the same required fields as single airfield upload
- All ICAO codes are automatically converted to uppercase
- Source field is required for each airfield entry
- Maximum recommended batch size: 100 airfields per request
- Processing is atomic per airfield (individual failures don't affect others)

**Success Response (200):**
```json
{
  "status": "completed",
  "message": "Processed 3 airfields",
  "results": {
    "created": 2,
    "updated": 1,
    "errors": []
  }
}
```

**Partial Success Response (200 - With Errors):**
```json
{
  "status": "completed",
  "message": "Processed 3 airfields",
  "results": {
    "created": 1,
    "updated": 0,
    "errors": [
      {
        "index": 1,
        "icao_code": "LJMB",
        "error": "Missing required fields: source"
      },
      {
        "index": 2,
        "icao_code": "INVALID",
        "error": "Latitude must be between -90 and 90 degrees"
      }
    ]
  }
}
```

**Error Response (400 - Invalid Format):**
```json
{
  "error": "Invalid format",
  "message": "JSON payload with 'airfields' array required"
}
```

**Bulk Operation Features:**
- **Atomic Processing**: Each airfield is processed independently
- **Detailed Error Reporting**: Specific error messages with array index and ICAO code
- **Mixed Results Support**: Successful operations proceed even if some fail
- **Comprehensive Statistics**: Count of created, updated, and failed operations
- **Source Validation**: Ensures all entries have proper source tracking
```

### 7. Query Airfields

Retrieve airfields with optional filtering and proximity search.

**Endpoint:** `GET /api/external/airfields`

**Headers:**
```
X-API-Key: your-api-key-here
```

**Query Parameters:**
- `country`: Filter by country name
- `region`: Filter by region
- `icao_code`: Get specific airfield by ICAO code
- `lat`: Latitude for proximity search (requires lon and optional radius_km)
- `lon`: Longitude for proximity search (requires lat and optional radius_km)
- `radius_km`: Search radius in kilometers (default: 25.0, max: 500.0)

**Examples:**

Get specific airfield:
```
GET /api/external/airfields?icao_code=LJLJ
```

Find airfields by country:
```
GET /api/external/airfields?country=Slovenia
```

Find nearest airfields:
```
GET /api/external/airfields?lat=46.2237&lon=14.4576&radius_km=50
```

**Success Response (200):**
```json
{
  "success": true,
  "count": 2,
  "airfields": [
    {
      "id": 123,
      "icao_code": "LJLJ",
      "name": "Ljubljana Airport",
      "latitude": 46.2237,
      "longitude": 14.4576,
      "country": "Slovenia",
      "region": "Central Europe",
      "elevation_ft": 1273,
      "source": "External API Import",
      "is_active": true,
      "distance_km": 0.0
    },
    {
      "id": 124,
      "icao_code": "LJPZ",
      "name": "Portorož Airport",
      "latitude": 45.4733,
      "longitude": 13.6150,
      "country": "Slovenia",
      "region": "Central Europe",
      "elevation_ft": 7,
      "source": "Legacy Data",
      "is_active": true,
      "distance_km": 83.2
    }
  ]
}
```

### 8. Reverse Geocoding

Convert coordinates to nearest aviation location using the airfield database.

**Endpoint:** `POST /api/external/geocode`

**Headers:**
```
Content-Type: application/json
X-API-Key: your-api-key-here
```

**Request Body:**
```json
{
  "latitude": 46.2237,
  "longitude": 14.4576
}
```

**Success Response (200):**
```json
{
  "success": true,
  "location": "LJLJ - Ljubljana Airport",
  "latitude": 46.2237,
  "longitude": 14.4576,
  "nearest_airfield": {
    "id": 123,
    "icao_code": "LJLJ",
    "name": "Ljubljana Airport",
    "latitude": 46.2237,
    "longitude": 14.4576,
    "country": "Slovenia",
    "distance_km": 0.0
  }
}
```

**Response when near (but not at) an airfield:**
```json
{
  "success": true,
  "location": "Near LJLJ - Ljubljana Airport (5.2km)",
  "latitude": 46.2700,
  "longitude": 14.5000,
  "nearest_airfield": {
    "id": 123,
    "icao_code": "LJLJ",
    "name": "Ljubljana Airport",
    "latitude": 46.2237,
    "longitude": 14.4576,
    "country": "Slovenia",
    "distance_km": 5.2
  }
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

### Airfield Database Management

#### Adding a Single Airfield

```bash
curl -X POST https://your-domain.com/api/external/airfields \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "icao_code": "LJLJ",
    "name": "Ljubljana Jože Pučnik Airport",
    "latitude": 46.2237,
    "longitude": 14.4576,
    "country": "Slovenia",
    "region": "Central Europe",
    "elevation_ft": 1273,
    "source": "OpenFlights Database Import 2025",
    "runway_info": {
      "runways": [
        {
          "designation": "31/13",
          "length_m": 3300,
          "width_m": 45,
          "surface": "Asphalt",
          "lighting": "High Intensity",
          "ils": true
        }
      ]
    },
    "frequencies": {
      "tower": "118.100",
      "ground": "121.700",
      "approach": "119.100",
      "departure": "119.100",
      "atis": "126.225"
    },
    "is_active": true
  }'
```

#### Bulk Import Multiple Airfields

```bash
curl -X POST https://your-domain.com/api/external/airfields/bulk \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "airfields": [
      {
        "icao_code": "LJLJ",
        "name": "Ljubljana Jože Pučnik Airport",
        "latitude": 46.2237,
        "longitude": 14.4576,
        "country": "Slovenia",
        "region": "Central Europe",
        "elevation_ft": 1273,
        "source": "Bulk Import Slovenia Airports 2025"
      },
      {
        "icao_code": "LJMB", 
        "name": "Maribor Edvard Rusjan Airport",
        "latitude": 46.4796,
        "longitude": 15.6861,
        "country": "Slovenia",
        "region": "Central Europe",
        "elevation_ft": 879,
        "source": "Bulk Import Slovenia Airports 2025"
      },
      {
        "icao_code": "LJPZ",
        "name": "Portorož Airport",
        "latitude": 45.4733,
        "longitude": 13.6150,
        "country": "Slovenia",
        "region": "Central Europe",
        "elevation_ft": 7,
        "source": "Bulk Import Slovenia Airports 2025"
      }
    ]
  }'
```

#### Query Airfields by Location

```bash
# Find nearest airfields within 50km
curl -X GET "https://your-domain.com/api/external/airfields?lat=46.2237&lon=14.4576&radius_km=50" \
  -H "X-API-Key: your-api-key-here"

# Get specific airfield by ICAO code
curl -X GET "https://your-domain.com/api/external/airfields?icao_code=LJLJ" \
  -H "X-API-Key: your-api-key-here"

# Get all airfields in Slovenia
curl -X GET "https://your-domain.com/api/external/airfields?country=Slovenia" \
  -H "X-API-Key: your-api-key-here"
```

#### Reverse Geocoding

```bash
curl -X POST https://your-domain.com/api/external/geocode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "latitude": 46.2237,
    "longitude": 14.4576
  }'
```
    ]
  }'
```

#### Querying Airfields by Country

```bash
curl -H "X-API-Key: your-api-key-here" \
  "https://your-domain.com/api/external/airfields?country=Slovenia"
```

#### Proximity Search for Nearest Airfields

```bash
curl -H "X-API-Key: your-api-key-here" \
  "https://your-domain.com/api/external/airfields?lat=46.2237&lon=14.4576&radius_km=50"
```

#### Reverse Geocoding Coordinates

```bash
curl -X POST https://your-domain.com/api/external/geocode \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "latitude": 46.2237,
    "longitude": 14.4576
  }'
```

**Response:**
```json
{
  "success": true,
  "location": "LJLJ - Ljubljana Airport",
  "latitude": 46.2237,
  "longitude": 14.4576,
  "nearest_airfield": {
    "id": 123,
    "icao_code": "LJLJ",
    "name": "Ljubljana Airport",
    "country": "Slovenia",
    "distance_km": 0.0
  }
}
```

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

# Add single airfield
airfield_payload = {
    "icao_code": "LJLJ",
    "name": "Ljubljana Jože Pučnik Airport",
    "latitude": 46.2237,
    "longitude": 14.4576,
    "country": "Slovenia",
    "region": "Central Europe",
    "elevation_ft": 1273,
    "source": "Python API Client 2025",
    "runway_info": {
        "runways": [
            {
                "designation": "31/13",
                "length_m": 3300,
                "width_m": 45,
                "surface": "Asphalt"
            }
        ]
    },
    "frequencies": {
        "tower": "118.100",
        "ground": "121.700",
        "approach": "119.100"
    },
    "is_active": True
}

response = requests.post(f"{BASE_URL}/airfields", json=airfield_payload, headers=headers)

if response.status_code in [200, 201]:
    print("Airfield added/updated successfully!")
    print(f"Status: {response.json().get('message')}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())

# Bulk import airfields
bulk_payload = {
    "airfields": [
        {
            "icao_code": "LJLJ",
            "name": "Ljubljana Jože Pučnik Airport",
            "latitude": 46.2237,
            "longitude": 14.4576,
            "country": "Slovenia",
            "source": "Python Bulk Import 2025"
        },
        {
            "icao_code": "LJMB",
            "name": "Maribor Edvard Rusjan Airport",
            "latitude": 46.4796,
            "longitude": 15.6861,
            "country": "Slovenia",
            "source": "Python Bulk Import 2025"
        }
    ]
}

response = requests.post(f"{BASE_URL}/airfields/bulk", json=bulk_payload, headers=headers)

if response.status_code == 200:
    results = response.json()
    print(f"Bulk import completed: {results['message']}")
    print(f"Created: {results['results']['created']}")
    print(f"Updated: {results['results']['updated']}")
    if results['results']['errors']:
        print(f"Errors: {len(results['results']['errors'])}")
        for error in results['results']['errors']:
            print(f"  - {error['icao_code']}: {error['error']}")
else:
    print(f"Error: {response.status_code}")
    print(response.json())

# Query airfields by location
response = requests.get(f"{BASE_URL}/airfields", 
                       params={"lat": 46.2237, "lon": 14.4576, "radius_km": 50},
                       headers={"X-API-Key": API_KEY})

if response.status_code == 200:
    airfields_data = response.json()
    print(f"Found {airfields_data['count']} airfields nearby:")
    for airfield in airfields_data['airfields']:
        print(f"  - {airfield['icao_code']}: {airfield['name']} ({airfield.get('distance_km', 'N/A')}km)")
else:
    print(f"Error: {response.status_code}")
    print(response.json())

# Reverse geocoding
geocode_payload = {
    "latitude": 46.2237,
    "longitude": 14.4576
}

response = requests.post(f"{BASE_URL}/geocode", json=geocode_payload, headers=headers)

if response.status_code == 200:
    location_data = response.json()
    print(f"Location: {location_data['location']}")
    if location_data['nearest_airfield']:
        airfield = location_data['nearest_airfield']
        print(f"Nearest airfield: {airfield['icao_code']} - {airfield['name']}")
        print(f"Distance: {airfield['distance_km']}km")
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

## Best Practices for Airfield Data

### Data Quality Guidelines

When importing airfield data, ensure:

- **ICAO Code Accuracy**: Use official 4-letter ICAO codes from authoritative sources
- **Coordinate Precision**: Provide coordinates with at least 4 decimal places for accuracy
- **Consistent Naming**: Use official airport names as published in aeronautical publications
- **Source Attribution**: Always specify the data source for traceability and validation

### Recommended Data Sources

**Free and Open Sources:**
- **OurAirports.com**: Comprehensive global airport database with regular updates
- **OpenFlights.org**: Open source database of airports, airlines, and routes
- **FAA NASR Data**: Official US airports and facilities data (monthly releases)
- **Wikipedia**: Airport lists by country (verify data independently)

**Official Aviation Sources:**
- **ICAO Publications**: Official aeronautical information and standards
- **National AIP**: Each country's Aeronautical Information Publication
- **EUROCONTROL**: European aviation data and statistics
- **Local Aviation Authorities**: Country-specific official airport data

### Data Validation and Import Tips

**Pre-Import Validation:**
```python
def validate_airfield_data(airfield):
    # ICAO code validation
    if not re.match(r'^[A-Z]{4}$', airfield['icao_code']):
        return False, "ICAO code must be 4 uppercase letters"
    
    # Coordinate validation
    if not (-90 <= airfield['latitude'] <= 90):
        return False, "Latitude must be between -90 and 90"
    
    if not (-180 <= airfield['longitude'] <= 180):
        return False, "Longitude must be between -180 and 180"
    
    return True, "Valid"
```

**Bulk Import Best Practices:**
- Process in batches of 50-100 airfields per request for optimal performance
- Include consistent source attribution for data lineage
- Validate data locally before uploading to minimize API errors
- Handle partial failures gracefully and retry failed items
- Monitor API response for detailed error information
- Use transaction-like processing where possible

**Common Data Issues to Avoid:**
- Duplicate ICAO codes (each must be unique globally)
- Incorrect coordinate formats (use decimal degrees, not DMS)
- Missing required fields (icao_code, name, latitude, longitude)
- Invalid JSON in optional fields (runway_info, frequencies)
- Inconsistent country/region naming

### Example Import Workflow

```python
import requests
import json

def bulk_import_airfields(airfields_data, api_key, batch_size=50):
    """Import airfields in batches with error handling."""
    base_url = "https://your-domain.com/api/external"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    results = {"success": 0, "failed": 0, "errors": []}
    
    # Process in batches
    for i in range(0, len(airfields_data), batch_size):
        batch = airfields_data[i:i+batch_size]
        
        payload = {"airfields": batch}
        response = requests.post(
            f"{base_url}/airfields/bulk", 
            headers=headers, 
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            results["success"] += result["results"]["created"]
            results["success"] += result["results"]["updated"]
            if result["results"]["errors"]:
                results["errors"].extend(result["results"]["errors"])
        else:
            results["failed"] += len(batch)
            results["errors"].append(f"Batch {i//batch_size + 1}: {response.text}")
    
    return results
```

## Security Notes

1. **API Key Security**: Keep your API key secure and never expose it in client-side code
2. **HTTPS Required**: Always use HTTPS in production
3. **Rate Limiting**: Consider implementing rate limiting for production use
4. **Logging**: All API calls are logged for security monitoring
5. **User Validation**: Only active and verified users can have devices claimed for them
6. **Source Field Security**: The source field is logged and audited for data integrity and tracking purposes

## Airfield Data Best Practices

### Data Quality Guidelines

- **ICAO Codes**: Use standard 4-letter ICAO codes (automatically converted to uppercase)
- **Coordinates**: Provide precise decimal coordinates (6+ decimal places for accuracy)
- **Source Tracking**: Always include a meaningful source field for audit trails and data management
- **Validation**: Validate coordinates are within valid ranges (-90/90 for lat, -180/180 for lon)

### Source Field Recommendations

The `source` field should be descriptive and include:
- Data source name (e.g., "OpenFlights Database")
- Version or date (e.g., "2025-08-22")
- Import method (e.g., "Bulk API Import")
- Organization (e.g., "ACME Aviation Data")

**Examples of good source values:**
- `"OpenFlights Database Import 2025-08-22"`
- `"Official AIP Slovenia 2025"`
- `"Manual Entry by ATC Tower LJLJ"`
- `"Jeppesen Database Export v25.8"`
- `"Internal Survey Team 2025-Q3"`

### JSON Field Structure

For `runway_info` and `frequencies` fields, maintain consistent structure:

**Runway Info Example:**
```json
{
  "runways": [
    {
      "designation": "09/27",
      "length_m": 2500,
      "width_m": 45,
      "surface": "Asphalt",
      "lighting": "Medium Intensity",
      "ils": false,
      "papi": true
    }
  ]
}
```

**Frequencies Example:**
```json
{
  "tower": "118.100",
  "ground": "121.700",
  "approach": "119.100",
  "departure": "119.100",
  "atis": "126.225",
  "multicom": "122.900"
}
```

### Bulk Import Optimization

- **Batch Size**: Limit bulk requests to 100 airfields per request for optimal performance
- **Error Handling**: Check the results array for individual failures and retry if needed
- **Source Consistency**: Use consistent source values for related data imports
- **Validation**: Pre-validate data locally before bulk import to minimize API errors

### Common Validation Errors

1. **Missing Source Field**: Source field is required for all airfield entries
2. **Invalid Coordinates**: Latitude/longitude outside valid ranges
3. **Duplicate ICAO Codes**: Same ICAO code within a bulk request
4. **Invalid JSON**: Malformed runway_info or frequencies JSON
5. **Character Limits**: Exceeding field length limits (name: 200, source: 100, etc.)

## Support

For API support or issues, contact the KanardiaCloud development team.
