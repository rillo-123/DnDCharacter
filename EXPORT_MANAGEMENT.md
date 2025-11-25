# Export Management & Storage Cleanup

## Overview

PySheet creates timestamped JSON exports every time you click "Export JSON" or when auto-export runs. Over time, this can create many backup files in the `/exports/` directory.

This guide explains how to manage exports and keep your project clean.

---

## Storage Locations

### Browser-based (localStorage)
- Character data
- Prepared spells list
- Logs and debug info
- Cached spell library
- **These are cleaned automatically by the app**

### File System (exports/)
- JSON character backups
- Format: `charactername_YYYYMMDD_lvl_N.json`
- **These accumulate over time and need manual management**

---

## Built-in Cleanup (Browser UI)

In the **Settings** tab under "Storage & Cleanup":

### Storage Info Button
- Shows current localStorage usage (KB)
- Estimates number of export files
- Shows potential savings from cleanup
- **Example:** "Storage Usage: 125KB | Exports: ~24 | Potential savings: 15KB if cleaned"

### Cleanup Old Exports Button
- Cleans up old log entries from localStorage (keeps last 100)
- Displays remaining space after cleanup
- **Note:** This only cleans the browser's log cache, not the exported JSON files

---

## Desktop Cleanup (File System)

### Option 1: Manual File Manager
1. Open your file manager
2. Navigate to the project's `/exports/` folder
3. Sort by modified date (newest first)
4. Delete old backup files, keeping 5-10 recent ones per character
5. Typical savings: 1-5 MB for long-running projects

### Option 2: Python Cleanup Script (Cross-Platform) ⭐ **RECOMMENDED**
A cross-platform Python script is provided: `cleanup_exports.py`

Works on **Windows, macOS, and Linux** with standard Python 3.

**Preview mode (safe):**
```bash
python cleanup_exports.py
```

**With custom settings:**
```bash
python cleanup_exports.py --keep 3
```

**Actually delete files:**
```bash
python cleanup_exports.py --execute --keep 3
```

**From different directory:**
```bash
python cleanup_exports.py --dir /path/to/exports --execute
```

**What it does:**
- Scans the `/exports/` folder on any platform
- Groups files by character name
- Keeps the N newest files per character (default 5)
- Deletes all older backups
- Shows what would be deleted (dry run mode by default)
- Requires confirmation before deleting

**Example output:**
```
📁 Scanning exports directory: G:\My Drive\DnDCharacter\exports
Found 24 JSON files

Characters found: 3

📄 enwer
   Total files: 14
   Keeping: 5 newest
      ✓ enwer_20251120_lvl_9.json (3.5 KB) - 2025-11-20 14:32
      ✓ enwer_20251119_lvl_9.json (3.4 KB) - 2025-11-19 10:15
      ✓ enwer_20251118_lvl_9.json (3.2 KB) - 2025-11-18 09:22
      ✓ enwer_20251117_lvl_9.json (3.1 KB) - 2025-11-17 15:44
      ✓ enwer_20251116_lvl_9.json (2.9 KB) - 2025-11-16 12:10
   Deleting: 9 old
      ✗ enwer_20251115_lvl_8.json (2.8 KB) - 2025-11-15 08:30
      ✗ enwer_20251114_lvl_8.json (2.7 KB) - 2025-11-14 14:22
      ... (7 more files)
   Would save: 24.5 KB

📄 rillobaby
   Total files: 7
   Status: All files recent (keeping all)

📄 character
   Total files: 3
   Status: All files recent (keeping all)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary: Would delete 9 files, saving ~24.5 KB

💡 This is a DRY RUN (preview only)
   To actually delete files, run with --execute flag
   Example: python cleanup_exports.py --execute --keep 5
```

### Option 3: PowerShell Script (Windows Only)
For Windows-only environments, `cleanup-exports.ps1` is also available:

```powershell
# Preview
.\cleanup-exports.ps1 -KeepPerCharacter 5 -DryRun $true

# Execute
.\cleanup-exports.ps1 -KeepPerCharacter 3 -DryRun $false
```

Note: This script only works on Windows PowerShell.

### Option 4: Bash Script (macOS/Linux)
For Unix-like systems, use this one-liner:

```bash
cd exports/
for char in $(ls *.json 2>/dev/null | sed 's/_[0-9].*//' | sort -u); do
  ls -t ${char}*.json 2>/dev/null | tail -n +6 | xargs rm -f
done
echo "✓ Cleanup complete!"
```

This keeps the 5 most recent exports per character and deletes older ones.

Customize the number of files to keep:
```bash
# Keep 3 instead of 5
ls -t ${char}*.json 2>/dev/null | tail -n +4 | xargs rm -f
# Keep 10 instead of 5
ls -t ${char}*.json 2>/dev/null | tail -n +11 | xargs rm -f
```

### Chromebook Users
The Chromebook browser's file system is sandboxed, so:
1. Exported files are managed by the browser's download system
2. Use your Chromebook's Files app to browse Downloads
3. Delete old character JSON files manually
4. Or use "Clear browsing data" to remove all browser data (including the app)

---

## File Naming Convention

Files follow the pattern:
```
{charactername}_{YYYYMMDD}_lvl_{level}.json
```

Examples:
- `enwer_20251120_lvl_9.json` - Enwer, Level 9, exported Nov 20, 2025
- `rillobaby_20251115_lvl_3.json` - Rillobaby, Level 3, exported Nov 15, 2025

---

## Best Practices

### Keep These Files
- ✅ Last 2-3 weeks of exports (provides good backup coverage)
- ✅ Files at major milestones (level ups, major story events)
- ✅ Different character versions (multiclass experiments, etc.)

### Delete These Files
- ❌ Exports older than 1 month (unless special significance)
- ❌ Duplicate-named exports from testing
- ❌ Files with "(1)" "(2)" suffixes (old browser duplicates)

### Storage Goals
- **Daily usage:** ~50-100 KB localStorage (character + logs)
- **After cleanup:** Reduce exports folder to 20-50 files total
- **Typical savings:** 1-5 MB when going from 100+ to 20 exports

---

## Automated Export Management Ideas

Future enhancements could include:
1. **Server-side pruning** - Backend automatically archives old exports
2. **Cloud backup** - Auto-upload to Google Drive, OneDrive, etc.
3. **Compression** - Store exports as `.zip` to save space
4. **Versioning** - Git-like version control for characters
5. **Archive folder** - Auto-move files older than N days to `/archive/`

---

## Troubleshooting

### My exports folder has 1000+ files
1. Run the cleanup script with `-KeepPerCharacter 3`
2. This will delete all but the 3 newest files per character
3. Could save 50-200 MB depending on your usage

### I deleted files I needed!
1. Check your Recycle Bin (Windows)
2. Use file recovery software (if recently deleted)
3. Check Git history if you're using version control
4. The app always keeps backups in localStorage

### Script won't run (PowerShell execution policy)
```powershell
# Temporarily allow script execution
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process

# Then run the script
.\cleanup-exports.ps1

# Execution policy reverts when PowerShell closes
```

### I'm on Mac/Linux
Use the manual approach or adapt the PowerShell script:
```bash
# Show files by character, keep 5 newest per character
cd exports/
for char in $(ls *.json | sed 's/_[0-9]*.*//' | sort -u); do
  ls -t ${char}*.json | tail -n +6 | xargs rm -f
done
```

---

## Storage Impact Summary

| Scenario | Files | Size | Action |
|----------|-------|------|--------|
| Fresh install | 0 | 0 KB | N/A |
| 1 week active | 7-14 | 50-150 KB | Monitor |
| 1 month active | 20-30 | 100-300 KB | Consider cleanup |
| 6 months active | 100+ | 500+ KB | **Run cleanup** |
| After cleanup | 15-25 | 50-100 KB | ✓ Clean |

---

## Questions?

- **Where are my exports?** Check `/exports/` folder in the project directory
- **Where is my character data?** In the browser's localStorage (Settings tab shows usage)
- **Are exports backed up?** No automatic cloud backup; you must manage the exports folder
- **Can I restore deleted exports?** Only if they're in your Recycle Bin or you have backups elsewhere
- **How often should I clean up?** Monthly or when folder exceeds 100 MB

