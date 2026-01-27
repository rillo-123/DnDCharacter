# Console Logger

## Overview

The console logger captures all browser console output (log, info, warn, error, debug) and writes it to a timestamped file on disk in real-time. Each page load or hard reset creates a new log file, making it easy to track different debugging sessions.

## Features

- **Timestamped Log Files**: Each session creates a new file: `browser-console-YYYYMMDD-HHMMSS.log`
- **Real-time File Writing**: Console output written immediately to disk
- **One Active Log**: Only one log file is active at a time (new file closes the previous one)
- **Manual New Session**: Press **Ctrl+Shift+R** to start a new log file
- **Auto New Session**: Page load/reload automatically creates new log file
- **Error Tracking**: Captures uncaught errors and unhandled promise rejections
- **Timestamped Entries**: Each log entry includes an ISO timestamp

## Log File Location

```
logs/browser-console-20260127-143022.log
logs/browser-console-20260127-143156.log
logs/browser-console-20260127-144301.log
...
```

Each file is automatically created in the `logs` directory with the timestamp when it was started.

## Usage

### Automatic New Log File
- **Open page**: Automatically creates a new timestamped log file
- **Reload page (F5)**: Creates a new timestamped log file
- **Hard refresh (Ctrl+F5)**: Creates a new timestamped log file

### Manual New Log File
- **Ctrl+Shift+R**: Closes current log and starts a new timestamped file
- **Console command**: `window.startNewLogFile()`

### View Logs in VS Code
1. Open the `logs` folder
2. Sort by date to find the latest log file
3. Open `browser-console-YYYYMMDD-HHMMSS.log`
4. The file updates in real-time as the browser runs

## Log File Format

Each line in the log file follows this format:
```
[2026-01-27T12:34:56.789Z] [LEVEL] message content
```

Example session file `browser-console-20260127-143022.log`:
```
[2026-01-27T14:30:22.123Z] [INFO] === PAGE LOADED - NEW SESSION ===
[2026-01-27T14:30:22.145Z] [LOG] PySheet: Loaded 159 items from cache
[2026-01-27T14:30:22.167Z] [WARN] DEBUG: equipment_event_manager import failed
[2026-01-27T14:30:22.189Z] [ERROR] ModuleNotFoundError: No module named 'equipment_event_manager'
```

## Debugging Workflow

1. **Open page**: New timestamped log file automatically created
2. **Reproduce issue**: Perform actions that cause the problem
3. **View log**: Open the latest `browser-console-*.log` file in VS Code
4. **Analyze**: Search for ERROR, WARN, or specific function names
5. **New session**: Press Ctrl+Shift+R or reload page to start fresh log

## Managing Log Files

### File Accumulation
Log files accumulate over time. Delete old files as needed:

```powershell
# Delete log files older than 7 days
Get-ChildItem logs/browser-console-*.log | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item

# Keep only the 10 most recent log files
Get-ChildItem logs/browser-console-*.log | Sort-Object LastWriteTime -Descending | Select-Object -Skip 10 | Remove-Item
```

### Quick Cleanup
```powershell
# Delete all but the most recent 3 log files
Get-ChildItem logs/browser-console-*.log | Sort-Object LastWriteTime -Descending | Select-Object -Skip 3 | Remove-Item
```

## Technical Details

- **Backend Integration**: Browser sends logs to Flask backend via fetch API
- **Batch Writing**: Groups up to 10 log entries per write to reduce I/O
- **Async Sending**: Doesn't block the browser while writing
- **Error Resilience**: Failed writes don't crash the application
- **File Naming**: `browser-console-YYYYMMDD-HHMMSS.log` (24-hour format)
- **One Active File**: Backend tracks current log file, new sessions close previous

## Integration

The console logger is automatically loaded when you open `index.html`. No configuration required.

**Backend must be running** for logs to be written. If the backend is down, logs are lost (no buffering).

## Use Cases

### Session Comparison
Compare logs from different debugging sessions by file timestamp.

### PyScript Debugging
Captures all PyScript/Pyodide console output including module loading, HTTP fallbacks, and Python errors.

### Module Import Issues
Track which modules are loading successfully and which are falling back to HTTP.

### Performance Analysis
Review timestamps to identify slow operations or race conditions.

### Error Investigation
Capture full stack traces and error context with complete history for each session.

### Before/After Testing
Start a new log file (Ctrl+Shift+R) before each test scenario to keep sessions separate.

## Tips

- Each page reload creates a new log file - helps isolate issues by session
- Use Ctrl+Shift+R to start a new log mid-session without reloading
- Sort files by date in VS Code to find the latest log
- Delete old log files periodically to save disk space
- Compare logs from working vs. broken sessions to identify regressions
- Save important log files outside the `logs` directory for long-term reference
