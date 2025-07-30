# Logbook Cleanup Scripts

This directory contains utility scripts for managing logbook entries in the KanardiaCloud database.

## Scripts

### 1. `delete_all_logbook_entries.py`
Simple script that deletes ALL logbook entries from the database.

**Usage:**
```bash
python delete_all_logbook_entries.py        # Interactive deletion
python delete_all_logbook_entries.py --help # Show help
```

**Features:**
- Shows statistics before deletion
- Requires double confirmation for safety
- Logs detailed statistics of deleted entries
- Irreversible operation

### 2. `cleanup_logbook_entries.py` (Recommended)
Advanced script with granular control over what gets deleted.

**Usage:**
```bash
python cleanup_logbook_entries.py           # Interactive menu
python cleanup_logbook_entries.py --all     # Delete all entries
python cleanup_logbook_entries.py --synced  # Delete synced entries only
python cleanup_logbook_entries.py --manual  # Delete manual entries only
python cleanup_logbook_entries.py --stats   # Show statistics only
python cleanup_logbook_entries.py --help    # Show help
```

**Features:**
- Interactive menu for easy use
- Selective deletion (all/synced/manual)
- Detailed statistics and previews
- Multiple confirmation levels
- Safe operation with rollback on errors

## Entry Types

**Synced Entries:**
- Imported from ThingsBoard devices
- Have a `device_id` foreign key
- Contain aircraft info from device settings
- Created automatically during sync operations

**Manual Entries:**
- Created by users in the web interface
- Have `device_id = NULL`
- Contain user-entered aircraft information
- Created through the dashboard interface

## Safety Features

Both scripts include multiple safety measures:

1. **Statistics Preview:** Shows what will be deleted before action
2. **Confirmation Prompts:** Requires explicit user confirmation
3. **Double Confirmation:** Critical operations need extra confirmation
4. **Transaction Safety:** Database rollback on errors
5. **Verification:** Confirms deletion was successful

## Usage Examples

**View current statistics:**
```bash
python cleanup_logbook_entries.py --stats
```

**Delete only synced entries (preserve manual entries):**
```bash
python cleanup_logbook_entries.py --synced
```

**Interactive cleanup (recommended for beginners):**
```bash
python cleanup_logbook_entries.py
```

## ⚠️ Important Warnings

- **ALL DELETION OPERATIONS ARE IRREVERSIBLE**
- **ALWAYS BACKUP YOUR DATABASE BEFORE RUNNING THESE SCRIPTS**
- Test in a development environment first
- These scripts require the Flask application environment to be properly configured

## Database Backup

Before running any cleanup scripts, create a backup:

```bash
# SQLite backup
cp instance/kanardiacloud.db instance/kanardiacloud_backup_$(date +%Y%m%d_%H%M%S).db

# Or export SQL dump
sqlite3 instance/kanardiacloud.db .dump > logbook_backup_$(date +%Y%m%d_%H%M%S).sql
```

## Recovery

If you accidentally delete entries and have a backup:

```bash
# Restore from backup
cp instance/kanardiacloud_backup_YYYYMMDD_HHMMSS.db instance/kanardiacloud.db

# Or restore from SQL dump
sqlite3 instance/kanardiacloud.db < logbook_backup_YYYYMMDD_HHMMSS.sql
```
