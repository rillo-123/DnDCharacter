# IMPORT DEBUGGING GUIDE

## How to Use the Debug Logs

The import process now has comprehensive logging at every step. Follow these instructions to debug the import issue:

### Step 1: Open Browser Developer Tools
1. Press **F12** to open Developer Tools
2. Click the **Console** tab
3. **Keep this open while doing the import**

### Step 2: Try to Import Enwer Character
1. In the app, click the **"Import JSON"** button
2. Select the **Enwer JSON file** from the exports folder
3. Watch the console for debug output

### Step 3: Look for Log Messages

You should see a sequence of log messages starting with `[IMPORT]` and `[POPULATE]`:

```
[IMPORT] handle_import called
[IMPORT] file_list: ..., length: 1
[IMPORT] Selected file: Enwer_Cleric_lvl9_20251126_2147.json, size: XXXXX bytes
[IMPORT] Starting to read file...
[IMPORT] FileReader.onload triggered
[IMPORT] File read successfully, payload size: XXXXX chars
[IMPORT] JSON parsed successfully
[IMPORT] Character: Enwer (Cleric)
[IMPORT] Importing populate_form and schedule_auto_export...
[IMPORT] Calling populate_form()...
[POPULATE] populate_form() called
[POPULATE] Auto-export suppression enabled
[POPULATE] Creating character from dict...
[POPULATE] Character created: Enwer (Cleric)
[POPULATE] Character normalized
[POPULATE] Setting identity fields...
[POPULATE] Identity set, domain: Life
[POPULATE] Basic stats set
[POPULATE] Setting ability scores...
[POPULATE] Ability scores set
[POPULATE] Setting skills...
[POPULATE] Skills set
[POPULATE] Setting combat data...
[POPULATE] Notes set
[POPULATE] Setting spell fields...
[POPULATE] Loading spellcasting state...
[POPULATE] Spellcasting state loaded
[POPULATE] Loading inventory...
[POPULATE] Inventory loaded and rendered
[POPULATE] Updating calculations...
[POPULATE] Calculations updated
[POPULATE] Setting currency...
[POPULATE] Currency set
[POPULATE] populate_form() COMPLETED SUCCESSFULLY
[POPULATE] Restoring auto-export suppression
[IMPORT] populate_form() completed successfully
[IMPORT] Saving to localStorage...
[IMPORT] Saved to localStorage
[IMPORT] Scheduling auto-export...
[IMPORT] Auto-export scheduled
[IMPORT] SUCCESS: character imported from JSON
```

### Step 4: Look for Errors

If an error occurs, you should see a message like:
```
[IMPORT] ERROR XXXX
```

or

```
[POPULATE] ERROR in populate_form: XXXX
```

Copy the exact error message and paste it here.

### Step 5: Check Console for Python Stack Traces

If there's an error, the console will also show a Python stack trace. Copy the entire error message including the traceback.

## What to Report

When you see the import not working, please:

1. Take a screenshot of the console showing:
   - Where the [IMPORT] logs stop
   - Any error messages (red text)
   - Any Python traceback

2. Or copy-paste the console output

This will tell us exactly where the import is failing.
