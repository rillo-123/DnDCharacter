# Auto-Export Contradictory Messages - Quick Fix Guide

## The Issue You're Experiencing

Three confusing messages appear in order:
```
1. PySheet: auto-export directory selected ✓
2. WARN: unable to open auto-export file in directory ✗ 
3. PySheet: auto-export not yet configured ✗✗
```

## Why This Happens

**The folder was selected, but the browser can't write files to it.**

When line 2 fails, the code automatically resets the directory handle (line 510 in export_management.py), which triggers message 3.

## How to Fix It

### Option 1: Use Google Drive or Dropbox Folder (Recommended)

Most restrictive permissions issue appears with OneDrive. Try:

1. Open **File Explorer**
2. Navigate to a **Google Drive folder** or **Dropbox** if you use them
3. In the app, open the equipment dialog
4. Select that folder for auto-export
5. Toggle equipment to trigger auto-export

### Option 2: Reset Browser Permissions & Try Again

1. **Chrome/Edge**: Settings → Privacy & Security → Site Settings → File System
2. Find **localhost** entry
3. Click the trash icon to remove the permission
4. Refresh the page (Ctrl+Shift+R)
5. Toggle equipment again
6. When prompted: Click **Allow** → Select **exports** folder → Click **Select Folder**

### Option 3: Use the Manual Export Button

If auto-export won't work, manually export:
1. Click **Export JSON** button
2. Choose the folder manually each time
3. This bypasses the persistent folder issue

## Diagnostic Info

**The specific error: `NotFoundError`**

This appears when:
- Browser has permission to pick the folder, but NOT to create files in it
- The folder is read-only or system-protected
- OneDrive/cloud sync is interfering

**The test case that reproduces your issue:**

```python
pytest tests/test_auto_export_file_system_api.py::TestFileCreationErrors::test_directory_selected_then_get_file_fails -v
```

This test confirms the exact state transitions you're seeing.

## Next Steps

1. **Try Option 2** first (reset permissions)
2. **If that fails, use Option 1** (different folder location)
3. **If all else fails, use Option 3** (manual exports)

The root cause is a File System API permission boundary issue, not a bug in the code logic itself. The contradictory messages just mean the folder picker succeeded but file creation failed.
