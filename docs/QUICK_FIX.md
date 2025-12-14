# Quick Fix Guide: PyScript Module Loading

## TL;DR

**Problem**: Python modules not loading in PyScript  
**Reason**: Files not being served via HTTP  
**Fix**: Start web server from project root

## The Problem (What You're Seeing)

```
DEBUG: spellcasting module import failed: No module named 'spellcasting'
DEBUG: SpellcastingManager class is None
[Result] No spells load in the UI
```

## The Fix (3 Steps)

### Step 1: Stop Current Server
- Kill the currently running web server (Ctrl+C)

### Step 2: Start Server from Project Root
```bash
cd /path/to/DnDCharacter
python -m http.server 8000
```

**CRITICAL**: Run this command FROM the project root (where `index.html` is)

### Step 3: Test in Browser
1. Open http://localhost:8000
2. Press Ctrl+Shift+Delete (clear cache)
3. Press Ctrl+F5 (hard refresh)
4. Open F12 (Developer Tools)
5. Look for console message:
   - ✓ "DEBUG: spellcasting module imported successfully" = FIXED
   - ✗ "DEBUG: spellcasting module import failed" = Still broken

## How to Verify Your Server Is Correct

### Test 1: Can You Access index.html?
```bash
curl http://localhost:8000/index.html
```
Result should show HTML (not 404 error)

### Test 2: Can You Access Python Files?
```bash
curl http://localhost:8000/assets/py/spellcasting.py
```
Result should show Python code (not 404 error)

If Test 2 returns 404, your server isn't serving from project root.

### Test 3: Browser Network Tab
1. Open http://localhost:8000
2. F12 → Network tab
3. Refresh page
4. Filter: "spellcasting"
5. Look for request to `/assets/py/spellcasting.py`
6. Status should be **200 OK** (not 404)

## If Still Not Working

### Issue: Server started but files still 404

**Possible causes**:
1. Running server from wrong directory
2. Browser cache not cleared
3. Old server process still running

**Solution**:
```bash
# Kill all Python processes
pkill python

# Verify you're in right directory
pwd
# Should show: /path/to/DnDCharacter

# List assets directory
ls -la assets/py/
# Should show: spellcasting.py and 7 other files

# Start fresh server
python -m http.server 8000

# In browser: Ctrl+Shift+Delete to clear cache
# Then: Ctrl+F5 to reload
```

### Issue: Server running but console still shows error

**Check**:
1. Did you refresh AFTER cache clear? (Not just Ctrl+R)
2. Use Ctrl+Shift+Delete to open cache clear dialog
3. Select "Cookies and cached images and files"
4. Click "Clear Now"
5. Then reload page with Ctrl+F5

## Server Running Correctly - Signs to Look For

In console, you should see (in order):
```
DEBUG: MODULE_DIR = /home/pyodide/assets/py
DEBUG: sys.path after update: ['/home/pyodide/assets/py', ...]
DEBUG: spellcasting module imported successfully
DEBUG: SPELLCASTING_MANAGER instantiated successfully
DEBUG: Creating async task for _auto_load_weapons
DEBUG: _auto_load_weapons() started
... (more debug output)
```

If you see all of this, **server is working correctly**!

Then click "Load Spells" button and check:
- Spells load from Open5e
- Spell library shows spell count
- Spell filter works
- Can add spells to prepared list

## Running Tests to Verify

```bash
# Test 1: Check files exist locally
python tests/test_http_serving.py
# Should show all [OK]

# Test 2: Verify imports work (locally)
python tests/test_spellcasting_import.py
# Should show all [PASS]

# Test 3: Comprehensive diagnostics
python tests/test_pyscript_environment.py
# Should show 6+ tests passing
```

## Common Mistakes

### ❌ WRONG
```bash
cd assets/py
python -m http.server 8000
```
Result: http://localhost:8000/spellcasting.py works  
But: http://localhost:8000/index.html gives 404

### ✓ CORRECT
```bash
cd /path/to/DnDCharacter
python -m http.server 8000
```
Result: Both http://localhost:8000/index.html and http://localhost:8000/assets/py/spellcasting.py work

## Alternative: Using Python's http.server with specific port

If port 8000 is busy:
```bash
python -m http.server 9000
# Then open http://localhost:9000
```

## If Using Flask

Make sure Flask serves from project root:
```python
# In your Flask app file
app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/<path:filename>')
def serve_file(filename):
    return send_file(filename)
```

Then restart Flask:
```bash
python app.py
# Visit http://localhost:5000 (or your configured port)
```

## Checklist for Success

- [ ] Web server running from project root
- [ ] Can access http://localhost:PORT/index.html
- [ ] Can access http://localhost:PORT/assets/py/spellcasting.py
- [ ] Browser cache cleared (Ctrl+Shift+Delete)
- [ ] Page reloaded (Ctrl+F5)
- [ ] Console shows "spellcasting module imported successfully"
- [ ] Load Spells button works
- [ ] Spells appear in spell library

Once all checks pass, **PyScript module loading is working!**

## For Technical Details

See: [ROOT_CAUSE_ANALYSIS.md](ROOT_CAUSE_ANALYSIS.md)

This document explains:
- Why PyScript needs HTTP
- How module loading works
- What goes wrong when files aren't served
- How to verify each step

## Support

If still not working after following this guide:

1. Check [ROOT_CAUSE_ANALYSIS.md](ROOT_CAUSE_ANALYSIS.md) for detailed diagnosis
2. Run `python tests/test_http_serving.py` and check all tests
3. Use Browser Developer Tools (F12) Network tab to monitor requests
4. Look for `/assets/py/` requests with status 404 (indicates server problem)

The unit tests and diagnostics will help identify exactly where the issue is.
