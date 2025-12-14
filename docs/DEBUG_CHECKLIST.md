# QUICK DEBUG CHECKLIST

After **Ctrl+Shift+R** refresh and opening **F12 Console**, you should see:

## Initialization Phase (page loads)
```
[DEBUG] === PySheet initialization starting ===
[DEBUG] Calling register_event_listeners()
[DEBUG] Found X character input elements
[DEBUG] import-file element found, registering event listener
[DEBUG] Import event listener registered successfully
[DEBUG] Calling load_initial_state()
[DEBUG] Loaded character from localStorage (or "No stored character, using defaults")
[DEBUG] Calling update_calculations()
[DEBUG] Calling render_equipped_weapons()
[DEBUG] Populating spell class filter
[DEBUG] === PySheet initialization complete ===
```

## Import Phase (after clicking Import and selecting file)
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
...
[POPULATE] populate_form() COMPLETED SUCCESSFULLY
[IMPORT] populate_form() completed successfully
[IMPORT] Saving to localStorage...
[IMPORT] Saved to localStorage
[IMPORT] Scheduling auto-export...
[IMPORT] Auto-export scheduled
[IMPORT] SUCCESS: character imported from JSON
```

## What to Report If Nothing Happens

**Check for these in order:**

1. Do you see `[DEBUG] === PySheet initialization starting ===` ?
   - **NO**: Page didn't load Python code, check for errors (orange/red text)
   - **YES**: Continue to #2

2. Do you see `[DEBUG] import-file element found...` ?
   - **NO**: Import button HTML element missing
   - **YES**: Event listener is set up

3. Do you see `[IMPORT] handle_import called` when you click Import?
   - **NO**: Event listener not firing (button click not detected)
   - **YES**: Import handler is working

4. Where does it stop after you click Import and select file?
   - Look for the last `[IMPORT]` or `[POPULATE]` message
   - Copy any error messages (red text)

## Copy-Paste Steps

1. Refresh with **Ctrl+Shift+R**
2. Press **F12** to open Developer Tools
3. Click **Console** tab
4. **Scroll to the top** of the console
5. **Try to import** Enwer character
6. **Screenshot** everything you see
7. **Paste the screenshot** or **copy the text**
