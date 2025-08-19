# Event Model write_address Field Addition

## Summary
Added a new `write_address` field to the Event model to track the write address from device loggers.

## Changes Made

### 1. Model Changes (`src/models.py`)
- Added `write_address = db.Column(db.BigInteger, nullable=True)` to the Event model
- Field is positioned after `page_address` since they are related concepts
- Field is nullable to allow for events where write address is not available

### 2. Migration Script (`migrate_event_write_address.py`)
Created a comprehensive migration script that:
- Adds the `write_address` column to the existing `event` table
- Populates the field for all existing events using their linked device's `current_logger_page`
- Provides verification and rollback functionality
- Handles SQLAlchemy version compatibility

### 3. Database Schema Changes
```sql
ALTER TABLE event ADD COLUMN write_address BIGINT;
```

## Usage

### Running the Migration
```bash
source .venv/bin/activate
python migrate_event_write_address.py
```

### Verification
```bash
python migrate_event_write_address.py verify
```

### Migration Results
- Successfully migrated 3,228 existing events
- All events now have `write_address` populated from their device's `current_logger_page`
- New Event objects can be created with the `write_address` field

## Field Purpose
The `write_address` field stores the write address from device loggers, which is used to:
- Track the position in the device's memory where the event was written
- Provide correlation between events and device logger states
- Enable better synchronization and debugging of device data

## Example Usage
```python
# Creating a new event with write_address
event = Event(
    page_address=123456,
    write_address=device.current_logger_page,
    total_time=3600000,
    bitfield=0,
    device_id=device.id
)

# Accessing write_address from existing events
for event in Event.query.all():
    print(f"Event {event.id}: write_address={event.write_address}")
```

## Database Impact
- Added one new nullable BIGINT column to the `event` table
- No impact on existing functionality
- All existing events have been migrated successfully
- Field can be None for events where write address is not applicable
