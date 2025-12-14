# IMPORT TROUBLESHOOTING CHECKLIST

## What to Check When Import Doesn't Work

### Step 1: Browser Console Logs
Open Developer Tools (F12) → Console tab:

- [ ] Do you see `[IMPORT] handle_import called` ?
  - **NO**: Import button not firing, check if file input element exists
  - **YES**: Continue to Step 2

- [ ] Do you see `[IMPORT] file_list:` ?
  - **NO**: File selection failed, check browser file dialog
  - **YES**: Continue to Step 3

- [ ] Do you see `[IMPORT] Selected file:` ?
  - **NO**: File not selected properly
  - **YES**: Continue to Step 4

- [ ] Do you see `[IMPORT] FileReader.onload triggered` ?
  - **NO**: File reading failed, may be browser permission issue
  - **YES**: Continue to Step 5

- [ ] Do you see `[IMPORT] JSON parsed successfully` ?
  - **NO**: JSON is invalid or file is corrupted
  - **YES**: Continue to Step 6

- [ ] Do you see `[POPULATE] populate_form() called` ?
  - **NO**: Import handler crashed, check earlier logs for errors
  - **YES**: Continue to Step 7

- [ ] Do you see `[POPULATE] populate_form() COMPLETED SUCCESSFULLY` ?
  - **NO**: populate_form crashed, find the last [POPULATE] message before the error
  - **YES**: Import should be working!

### Step 2: Check for Errors (Red Text)

Look for any messages in red:
- `PySheet: failed to import character - XXX`
- `[IMPORT] ERROR`
- `[POPULATE] ERROR`
- Python stack traces (multiple lines starting with "File...")

**If you see an error:**
1. Copy the entire error message
2. Copy any Python stack trace below it
3. Share it

### Step 3: Verify File is Valid

Test file manually:
```bash
python test_import_comprehensive.py
```

If this passes but import doesn't work in browser, it's a browser/PyScript issue.

### Step 4: Check HTML Elements

In browser console, run:
```javascript
document.getElementById("import-file")
```

Should return: `<input type="file" id="import-file" accept="application/json">`

If it returns `null`, the import button element doesn't exist.

### Step 5: Check Page is Fully Loaded

In browser console:
```javascript
window.localStorage
window.FileReader
```

Both should exist. If either is `undefined`, page didn't load properly.

### Step 6: Check Python is Working

In browser console:
```javascript
console.log(typeof py)
```

Should show `object`. If `undefined`, PyScript didn't load.

## Quick Summary: What to Report

When import doesn't work:

1. **Screenshot** of the browser console showing:
   - All [IMPORT] and [POPULATE] messages
   - Any error messages (red text)
   - Full Python stack trace if present

2. **OR** copy-paste the entire console output

3. **OR** describe:
   - Does any [IMPORT] message appear?
   - Do you see any error (red text)?
   - What's the last message before it stops?

This will help identify exactly where the import is failing.
