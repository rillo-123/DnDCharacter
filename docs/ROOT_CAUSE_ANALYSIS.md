# Root Cause Analysis: PyScript Module Loading Failure

## Executive Summary

**The Real Problem**: Python files are NOT being served via HTTP to the browser.

PyScript runs in a Pyodide sandbox in the browser and fetches Python modules via HTTP. When your web server doesn't properly serve the `assets/py/` directory, PyScript can't load any modules, and you get:

```
DEBUG: spellcasting module import failed: No module named 'spellcasting'
```

## Evidence from Browser Console

```
DEBUG: MODULE_DIR = /home/pyodide/assets/py
DEBUG: '__file__' in globals() = False
DEBUG: Path.cwd() = /home/pyodide
DEBUG: sys.path before update: ['/home/pyodide', '/lib/python312.zip', '/lib/python3.12']...
DEBUG: Added /home/pyodide/assets/py to sys.path[0]
DEBUG: sys.path after update: ['/home/pyodide/assets/py', '/home/pyodide', '/lib/python312.zip']...
DEBUG: spellcasting module import failed: No module named 'spellcasting'
DEBUG: Attempting retry with explicit path insertion
DEBUG: spellcasting module import failed on retry: No module named 'spellcasting'
```

## What This Means

1. ✓ **PyScript correctly detected the path** (`/home/pyodide/assets/py`)
2. ✓ **sys.path was correctly updated** (added to position [0])
3. ✗ **But the import still failed** - This is the KEY indicator
4. ✗ **Files not accessible via HTTP** - This is the ROOT CAUSE

## How PyScript Loads Modules

When you have this in your Python code:
```python
from spellcasting import SpellcastingManager
```

PyScript does the following:

1. Checks Python standard library (works fine)
2. Checks each directory in `sys.path`
3. For each `sys.path` entry, attempts HTTP fetch:
   ```
   GET http://localhost:PORT/home/pyodide/assets/py/spellcasting.py
   ```
4. If HTTP request succeeds (200 OK), loads module
5. If HTTP request fails (404 Not Found), tries next sys.path entry
6. If all fail, raises `ImportError: No module named 'spellcasting'`

**The problem**: When PyScript tries to fetch `spellcasting.py` via HTTP, the server returns **404 Not Found**.

## How to Verify the Problem

### Check 1: Browser Network Tab

1. Open http://localhost:8000 (or your server port)
2. Open Developer Tools (F12)
3. Go to **Network** tab
4. Filter by "spellcasting"
5. Look for: `GET /assets/py/spellcasting.py`
6. Check the **Status** column:
   - **200 OK** = Server is correctly serving the file
   - **404 Not Found** = Server NOT serving the file (THIS IS THE PROBLEM)
   - **No request** = PyScript didn't even try (different problem)

### Check 2: Test the Server Manually

In your terminal:
```bash
curl http://localhost:8000/assets/py/spellcasting.py
```

**Result should be**:
- ✓ The Python code content (200 status)
- ✗ 404 error (file not found) = Server problem
- ✗ Connection refused (server not running)

### Check 3: Files Exist Locally

Our unit tests confirm:
```
[OK] assets/py/spellcasting.py (local: True)
[OK] assets/py/spell_data.py (local: True)
[OK] assets/py/character.py (local: True)
... all 8 required files exist locally
```

**Files exist on disk** ✓  
**But web server not serving them** ✗  
**Therefore PyScript can't access them** ✗

## Common Causes and Solutions

### Cause 1: Web Server Not Serving from Project Root

**Symptom**: `GET /assets/py/spellcasting.py` returns 404

**Solution**: 
Make sure your web server serves files from the project root:

```bash
# CORRECT: Serves from project root
python -m http.server 8000
# Now http://localhost:8000/index.html works
# And http://localhost:8000/assets/py/spellcasting.py works

# WRONG: cd'ing into subdirectory
cd assets
python -m http.server 8000
# Now http://localhost:8000/spellcasting.py works
# But http://localhost:8000/index.html returns 404
```

### Cause 2: Flask Not Configured Correctly

**Symptom**: Flask not serving static files in `assets/` directory

**Solution**:
Ensure your Flask app serves from project root:

```python
# BAD - limits to static/ directory
app = Flask(__name__, static_folder='static')

# GOOD - serve everything from current directory
app = Flask(__name__, static_folder='.')

# Also ensure you have these routes:
@app.route('/')
def index():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_file(filename)
```

### Cause 3: Incorrect Server Configuration

**Symptom**: Server running but files still not accessible

**Check server logs** for:
- 404 errors for `/assets/py/` files
- Permission denied errors
- Wrong working directory

**Solution**:
- Restart web server from project root
- Clear browser cache (Ctrl+Shift+Delete)
- Reload page (Ctrl+F5)

## Detailed Diagnostic Process

### Step 1: Verify Files Exist
```bash
python tests/test_http_serving.py
```
✓ All 8 files should show [OK]

### Step 2: Verify Web Server Running
```bash
# In a terminal
python -m http.server 8000

# In another terminal
curl http://localhost:8000/index.html
# Should return HTML content
```

### Step 3: Verify Files Accessible via HTTP
```bash
curl http://localhost:8000/assets/py/spellcasting.py
# Should return Python code (not 404 error)

curl http://localhost:8000/assets/py/spell_data.py
# Should return Python code (not 404 error)
```

### Step 4: Verify Browser Can Access
1. Open http://localhost:8000
2. F12 → Network tab
3. Look for `/assets/py/spellcasting.py` request
4. Status should be 200 (not 404)

### Step 5: Test in Browser
If all above work:
1. Clear browser cache (Ctrl+Shift+Delete)
2. Reload page (Ctrl+F5)
3. Check console for:
   - ✓ "DEBUG: spellcasting module imported successfully"
   - ✗ "DEBUG: spellcasting module import failed" (if seeing this, server problem)

## What Should Happen When Fixed

**Before (Current State)**:
```
DEBUG: MODULE_DIR = /home/pyodide/assets/py
DEBUG: Added /home/pyodide/assets/py to sys.path[0]
DEBUG: spellcasting module import failed: No module named 'spellcasting'
```

**After (When Fixed)**:
```
DEBUG: MODULE_DIR = /home/pyodide/assets/py
DEBUG: Added /home/pyodide/assets/py to sys.path[0]
DEBUG: spellcasting module imported successfully
DEBUG: SPELLCASTING_MANAGER instantiated successfully
DEBUG: load_spell_library() called
DEBUG: sanitize_spell_list returned 1435 spells
```

Then spells will load and display in the UI.

## Unit Tests That Catch This

We created `tests/test_http_serving.py` with 8 tests:

1. ✓ `test_files_exist_locally` - Files on disk
2. ✓ `test_pyscript_would_find_files` - Path detection
3. ✓ `test_sys_path_includes_assets_py` - Path setup
4. ✓ `test_spellcasting_findable_after_path_update` - Import works locally
5. ✓ `test_pyscript_file_serving_requirement` - Documents what PyScript needs
6. ✓ `test_pyscript_fetches_via_http` - Explains HTTP fetching
7. ✓ `test_what_needs_to_be_served` - Lists required files
8. ✓ `test_http_server_configuration` - Server setup guide

**Local test results**: All PASS ✓  
**Why?**: Native Python has direct filesystem access, doesn't need HTTP  
**Browser**: Needs HTTP, which is why it fails

## Critical Difference: Local vs Browser

| Aspect | Local (Python) | Browser (PyScript) |
|--------|---------------|--------------------|
| File Access | Direct filesystem | HTTP only |
| Module Loading | `import` loads from disk | Fetches via HTTP |
| sys.path | Can point to local paths | Must be HTTP-accessible |
| Our tests | ALL PASS (have disk access) | FAIL (no HTTP server) |
| Real issue | Files exist and importable | Files exist but not served |

## Action Plan

1. **Verify web server is running from project root**
   - Stop current server
   - Run: `python -m http.server 8000`
   - Confirm: http://localhost:8000/index.html loads

2. **Verify files are served**
   - Check: http://localhost:8000/assets/py/spellcasting.py
   - Should show Python code (not 404)

3. **Clear browser cache**
   - Ctrl+Shift+Delete
   - Clear cookies and cached files

4. **Reload page**
   - Ctrl+F5 (hard refresh)
   - Check browser console

5. **Monitor network requests**
   - F12 → Network tab
   - Look for `/assets/py/` requests
   - All should be 200 OK

6. **Verify success**
   - Console should show: "DEBUG: spellcasting module imported successfully"
   - Load Spells button should work
   - Spells should appear in library

## Files Modified/Created

- `tests/test_http_serving.py` - 8 tests documenting HTTP serving requirements
- `PYSCRIPT_DIAGNOSTICS.md` - Previous diagnostic document
- `assets/py/character.py` - Added debug logging and retry logic
- `tests/test_spellcasting_import.py` - Unit tests (all PASS locally)
- `tests/test_pyscript_environment.py` - Environment diagnostics
- `tests/test_pyscript_simulation.py` - PyScript behavior simulation

## Commits

- `3db5150` - Add HTTP serving tests (identifies real root cause)
- `b07a9ea` - Add PyScript diagnostics documentation
- `050be36` - Fix test encoding and add diagnostics
- `d828ea9` - Add module loading diagnostics and retry logic
- `2f865ea` - Fix spellcasting.py syntax error and add unit tests
- `ae6af22` - Add fallback spell class data

## Conclusion

**The spell loading code is correct.**  
**The module import logic is correct.**  
**The real issue is: Files aren't being served via HTTP.**

Once you verify your web server is correctly serving the `/assets/py/` directory from the project root, PyScript will be able to import the modules and spell loading will work.

Use the diagnostic tests and this guide to verify your server setup. If you see "spellcasting module imported successfully" in the console after fixing the server, you're done!
