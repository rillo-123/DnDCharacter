# Auto-Export Contradictory Messages - Root Cause Analysis

## The Problem You Reported

You saw three contradictory console messages in sequence:

```
1. PySheet: auto-export directory selected
2. WARN: unable to open auto-export file in directory (NotFoundError...)
3. PySheet: auto-export not yet configured; will try again on next change
```

This is confusing because message #1 says the directory WAS selected, but message #3 says it's NOT configured.

## Root Cause

The issue is in the error handling in `export_management.py` lines 502-512:

```python
if _AUTO_EXPORT_DIRECTORY_HANDLE is not None:
    try:
        file_handle = await _AUTO_EXPORT_DIRECTORY_HANDLE.getFileHandle(
            proposed_filename,
            {"create": True},
        )
    except JsException as exc:
        console.warn(f"PySheet: unable to open auto-export file in directory ({exc})")
        if auto:
            _AUTO_EXPORT_DIRECTORY_HANDLE = None  # ← RESETS HANDLE!
```

### What Happens:

1. **User selects folder** → `_AUTO_EXPORT_DIRECTORY_HANDLE` is set
   - Message: "PySheet: auto-export directory selected" ✓

2. **Auto-export tries to write file** → `getFileHandle()` fails with `NotFoundError`
   - Message: "WARN: unable to open auto-export file in directory" ✓
   - **Code RESETS**: `_AUTO_EXPORT_DIRECTORY_HANDLE = None` 

3. **Export continues** → Falls through to message at line 782:
   ```python
   elif not (_AUTO_EXPORT_DIRECTORY_HANDLE or _AUTO_EXPORT_FILE_HANDLE):
       console.log("PySheet: auto-export not yet configured; will try again on next change")
   ```
   - Message: "PySheet: auto-export not yet configured" ✓

## Why `getFileHandle()` Fails with NotFoundError

The browser's File System API returns `NotFoundError` when:

1. **Permission Issue**: The browser selected a folder but doesn't have permission to create files in it
2. **Filesystem Limitation**: The folder picker gave a handle to a read-only directory
3. **Platform Difference**: Some folders (system folders, protected locations) can't be written to

## The Real Flow Should Be:

```
User selects folder
    ↓
getFileHandle() succeeds
    ↓
createWritable() succeeds
    ↓
write() succeeds
    ↓
✓ File saved!
```

## Current (Broken) Flow:

```
User selects folder
    ↓
getFileHandle() FAILS with NotFoundError
    ↓
Handle reset to None
    ↓
Falls back to browser download (lossy!)
    ↓
Next event: "not yet configured"
```

## Solution

The fix requires better state management and retry logic:

### 1. **Don't immediately reset on file creation failure**
Instead of resetting `_AUTO_EXPORT_DIRECTORY_HANDLE` on the first error, log it and retry:

```python
if _AUTO_EXPORT_DIRECTORY_HANDLE is not None:
    try:
        file_handle = await _AUTO_EXPORT_DIRECTORY_HANDLE.getFileHandle(
            proposed_filename,
            {"create": True},
        )
    except JsException as exc:
        console.warn(f"PySheet: unable to write to auto-export directory ({exc})")
        # DON'T reset immediately - let the user retry by toggling equipment
        # Only reset after N consecutive failures
        return False
```

### 2. **Add a failure counter**
Track consecutive failures and only reset after multiple attempts:

```python
_AUTO_EXPORT_CONSECUTIVE_FAILURES = 0
MAX_CONSECUTIVE_FAILURES = 3

# On failure:
_AUTO_EXPORT_CONSECUTIVE_FAILURES += 1
if _AUTO_EXPORT_CONSECUTIVE_FAILURES >= MAX_CONSECUTIVE_FAILURES:
    _AUTO_EXPORT_DIRECTORY_HANDLE = None
    console.warn("PySheet: persistent auto-export disabled - too many failures")

# On success:
_AUTO_EXPORT_CONSECUTIVE_FAILURES = 0
```

### 3. **Distinguish between states**
Be more specific in messages:

```python
# State 1: Never configured
"PySheet: auto-export not yet configured"

# State 2: Configured but temporarily unavailable
"PySheet: auto-export directory selected but currently unavailable (write failed)"

# State 3: Disabled after too many failures
"PySheet: persistent auto-export disabled - check directory permissions"
```

## Test Coverage

A comprehensive test suite has been created: `tests/test_auto_export_file_system_api.py`

### Tests Included (14 total):

✅ **Directory Selection Tests** (3 tests)
- Directory picker succeeds
- User aborts directory picker (AbortError)
- Permission denied on directory picker

✅ **File Creation Error Tests** (2 tests) ← KEY TESTS FOR YOUR ISSUE
- Directory selected → getFileHandle fails → state reset (reproduces your issue)
- Recovery after file creation fails (re-prompt scenario)

✅ **Permission Tests** (1 test)
- Permission request denied

✅ **Write Failure Tests** (2 tests)
- Write fails with NotAllowedError
- Export handles write failure gracefully

✅ **State Transition Tests** (3 tests)
- Initial state validation
- Success path: not configured → configured → exported
- Failure & recovery: error → reset → retry with new handle

✅ **Filename Tests** (2 tests)
- Filename generation includes name, class, level, timestamp
- Special character normalization

✅ **Error Message Tests** (1 test)
- Verify appropriate warnings are logged

## Running the Tests

```bash
# Run all auto-export File System API tests
python -m pytest tests/test_auto_export_file_system_api.py -v

# Run a specific test (the one that reproduces your issue)
python -m pytest tests/test_auto_export_file_system_api.py::TestFileCreationErrors::test_directory_selected_then_get_file_fails -v
```

## What You Should Do Now

1. **Reset browser permissions** for `localhost`:
   - Chrome/Edge: Settings → Privacy & Security → Site Settings → File System → Find localhost → Remove
   - Firefox: Should ask again on next use
   - Refresh the page

2. **Toggle an equipment item again** to trigger the folder picker

3. **When the folder picker appears**, ensure you:
   - See the "Allow?" permission dialog
   - Click "Allow" 
   - The folder browser dialog then opens
   - Navigate to and select the `exports` folder (must go INTO it, not select root)
   - Click "Select Folder"

4. **Check console for**:
   - ✓ "PySheet: auto-export directory selected" 
   - ✓ "PySheet: auto-exported character JSON to..." 
   - NOT "unable to open auto-export file"

If you still get "unable to open auto-export file", the selected folder may be read-only or protected. Try selecting a different folder or using a different location.
