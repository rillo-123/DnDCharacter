# Rolling 60-Day Log Window Implementation

## Overview

A comprehensive browser-based logging system with automatic 60-day rolling window has been implemented in PySheet. This prevents localStorage from growing unbounded while maintaining a reasonable history of application events.

## Features

### ✓ Automatic Rolling Window
- **60-day rolling window**: Logs older than 60 days are automatically pruned on every save
- **Per-day limits**: Maximum 1000 entries per day prevents spam logging from consuming all storage
- **Zero configuration**: Works automatically—no user intervention needed

### ✓ Logger Methods

```python
LOGGER.info(message)        # Log informational messages
LOGGER.warning(message)     # Log warning messages  
LOGGER.error(message, exc)  # Log errors with exception details
LOGGER.get_stats()          # Retrieve logging statistics
```

### ✓ Statistics Available

The `LOGGER.get_stats()` method returns:

```python
{
    "total_logs": 157,                    # Total info/warning entries
    "total_errors": 8,                    # Total error entries
    "days_with_logs": 12,                 # Distinct days with logs
    "oldest_log": "2025-11-09T...",       # ISO timestamp of oldest entry
    "logs_by_date": {                     # Dict of date -> count
        "2025-11-21": 45,
        "2025-11-20": 38,
        ...
    },
    "storage_bytes": 24576                # Current size in localStorage
}
```

## Storage Details

### Storage Key
- **Key**: `"pysheet_logs_v2"`
- **Format**: JSON object with `"logs"` and `"errors"` arrays
- **Location**: Browser `localStorage`

### Log Entry Structure

**Info/Warning Log Entry:**
```json
{
    "timestamp": "2025-11-21T14:30:45.123456",
    "level": "INFO",
    "message": "Cleaned 6 log entries from storage"
}
```

**Error Log Entry:**
```json
{
    "timestamp": "2025-11-21T14:35:22.654321",
    "level": "ERROR",
    "message": "Failed to save character",
    "exception": "Storage quota exceeded"
}
```

## Automatic Pruning Process

When any log operation occurs (`info()`, `warning()`, `error()`):

1. **Load** existing logs from localStorage
2. **Filter by date**: Remove entries with timestamp < (now - 60 days)
3. **Limit per day**: If today has > 1000 entries, keep only the most recent 1000
4. **Save** cleaned logs back to localStorage
5. **Console output**: Also logs to browser console for debugging

## Usage Examples

### Basic Logging
```python
LOGGER.info("User exported character")
LOGGER.warning("Spell library fetch took 5 seconds")
LOGGER.error("Failed to parse import file", exception_obj)
```

### Checking Log Stats
```python
stats = LOGGER.get_stats()
print(f"Total logs: {stats['total_logs']}")
print(f"Oldest log: {stats['oldest_log'][:10]}")  # Just the date part
print(f"Storage used: {stats['storage_bytes'] // 1024}KB")
```

### In cleanup_exports() Function
The cleanup function now calls `LOGGER.get_stats()` to display:
- Total logs maintained
- Days covered
- Storage used
- Oldest log date
- Confirmation that 60-day rolling window is active

## Cleanup UI Update

When you click "Cleanup Old Exports" in the Manage tab, it now displays:

```
✓ Logs maintained! 157 log entries across 12 days (23KB). 
Rolling 60-day window active (oldest: ~2025-11-09). 
To delete old export files from /exports/, use your file manager.
```

## Storage Efficiency

### Before
- Manual limit of 100 entries total
- No time-based expiration
- Could accumulate indefinitely if manually managed poorly

### After
- Automatic 60-day rolling window
- Per-day limits prevent spam accumulation
- Self-maintaining—no manual cleanup needed
- Typical storage: 20-30KB for 2 months of active use

## Integration Points

The LOGGER is used throughout character.py in:

1. **Storage operations**
   - `show_storage_info()` - Logs storage check
   - `cleanup_exports()` - Uses stats for display
   - `estimate_export_cleanup()` - Logs estimation results

2. **Export/import**
   - Character save/load operations
   - Export success/failure
   - Import parsing results

3. **Spell management**
   - Spell library loading
   - Spell deduplication
   - Domain bonus spell protection

4. **Error handling**
   - All major try/except blocks
   - Permission requests
   - API failures

## Technical Details

### Class: BrowserLogger
Located at the top of `character.py` after imports.

**Key methods:**
- `_get_timestamp()`: Returns current ISO timestamp
- `_parse_date()`: Extracts YYYY-MM-DD from ISO timestamp
- `_load_logs()`: Retrieves logs from localStorage
- `_save_logs()`: Saves with automatic pruning
- `info()`, `warning()`, `error()`: Public logging methods
- `get_stats()`: Returns statistics

**Configuration constants:**
- `STORAGE_KEY = "pysheet_logs_v2"` - localStorage key
- `MAX_DAYS = 60` - Rolling window span
- `MAX_ENTRIES_PER_DAY = 1000` - Per-day limit

### Performance Impact
- **Minimal**: Pruning runs only when logs are written (info/warning/error)
- **JSON operations**: Fast for typical log sizes (20-30KB)
- **localStorage**: Native browser operation, no network latency

## Future Enhancements

Possible improvements:
- Export logs to JSON file (via download button)
- Filter logs by date range in UI
- Search logs by keyword
- Separate debug logs from user-facing logs
- Compression for older log data
- Log rotation with archival

## Troubleshooting

### Logs not appearing
1. Check browser console (F12) for JavaScript errors
2. Verify localStorage is enabled
3. Check localStorage quota not exceeded

### Storage still growing
1. Verify pruning is running (check oldest_log date)
2. Check if more than 1000 entries per day
3. Clear site data and start fresh

### Stats show old dates
1. Normal if you haven't logged for several days
2. Oldest entry might be exactly 60 days old
3. Next log write will trigger pruning of anything older

---

**Implementation Date**: November 21, 2025  
**Version**: 1.0  
**Storage Key Version**: v2 (independent from old `pysheet_logs` format)
