-- Migration script to add takeoff_time and landing_time columns to logbook_entry table

-- Add new time columns
ALTER TABLE logbook_entry ADD COLUMN takeoff_time TIME;
ALTER TABLE logbook_entry ADD COLUMN landing_time TIME;

-- Update existing entries with default times
-- For existing entries, set takeoff to 10:00 AM and calculate landing based on flight_time
UPDATE logbook_entry 
SET takeoff_time = '10:00:00',
    landing_time = time('10:00:00', '+' || CAST(flight_time AS TEXT) || ' hours')
WHERE takeoff_time IS NULL OR landing_time IS NULL;

-- Verify the migration
SELECT COUNT(*) as total_entries FROM logbook_entry;
SELECT COUNT(*) as entries_with_times FROM logbook_entry WHERE takeoff_time IS NOT NULL AND landing_time IS NOT NULL;

-- Show sample entries
SELECT id, date, aircraft_registration, takeoff_time, landing_time, flight_time 
FROM logbook_entry 
LIMIT 5;
