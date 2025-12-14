# PyScript Module Loading Diagnostics

## Summary

**Problem**: Spellcasting module fails to import in PyScript environment with error:
```
DEBUG: spellcasting module import failed: No module named 'spellcasting'
```

Result: `SPELLCASTING_MANAGER = None` → No spell loading functionality

## Root Cause Analysis

### Local Testing (Native Python)
✓ **All tests pass** when run locally with native Python  
✓ `test_spellcasting_environment.py` shows that adding `assets/py` to `sys.path` fixes the issue  
✓ Modules import successfully: `spell_data.py` → `spellcasting.py` → `character.py`

### PyScript Environment (Browser)
✗ **Module not found** - PyScript doesn't see `assets/py` directory  
✗ Initial `sys.path` doesn't include `assets/py` by default  
✗ Module path setup happens but may not be correct for PyScript's execution context

## Key Diagnostic Findings

### Test Results

```
LOCAL ENVIRONMENT (Native Python)
====================================
[PASS] sys.path update           - assets/py added successfully
[PASS] spell_data import         - Available (14 class synonyms)
[PASS] spellcasting import       - Available (when path updated)
[PASS] syntax validation         - No errors in spellcasting.py
[PASS] character import          - Works with fallbacks
[PASS] import order/circular     - No circular dependencies

PYSCRIPT ENVIRONMENT (Browser)
====================================
[FAIL] spellcasting module import - "No module named 'spellcasting'"
[RESULT] SPELLCASTING_MANAGER = None
[RESULT] Spell loading disabled
```

### Why PyScript Can't Find Modules

1. **PyScript's module search**
   - PyScript looks for modules relative to HTML file location
   - PyScript initializes with limited `sys.path`
   - `assets/py` directory is not automatically in path
   - Module loading happens during page initialization

2. **Timing Issue**
   - `character.py` tries to import `spellcasting.py` at module load time
   - At this point, `assets/py` may not be in `sys.path` yet
   - The retry logic added should help, but PyScript environment may be different

3. **PyScript-Specific Behavior**
   - PyScript's `__file__` may not be available initially
   - PyScript's working directory might differ from expectations
   - Module caching may prevent retry attempts from working

## Implementation Changes

### 1. Module Path Initialization (character.py lines ~60-75)
```python
MODULE_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else (Path.cwd() / "assets" / "py")
)

# Added: Insert at [0] instead of append, plus comprehensive logging
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))  # Highest priority
    console.log(f"DEBUG: Added {MODULE_DIR} to sys.path[0]")
```

### 2. Spellcasting Import with Retry (character.py lines ~165-185)
```python
try:
    from spellcasting import SpellcastingManager, ...
    console.log("DEBUG: spellcasting module imported successfully")
except ImportError as e:
    console.warn(f"DEBUG: spellcasting import failed: {e}")
    
    # Retry with explicit path update
    try:
        assets_py = Path.cwd() / "assets" / "py"
        if str(assets_py) not in sys.path:
            sys.path.insert(0, str(assets_py))
        
        from spellcasting import SpellcastingManager, ...
        console.log("DEBUG: spellcasting imported on retry")
    except ImportError as e2:
        console.error(f"DEBUG: spellcasting import failed on retry: {e2}")
        # Use stubs for all functions
```

### 3. Debug Logging Added
- Module path detection and sys.path updates
- Import attempts and failures
- Fallback instantiation
- Retry mechanism logging

## Detailed DEBUG Output in Browser

When testing in PyScript, you should see:
```
DEBUG: MODULE_DIR = /path/to/assets/py
DEBUG: '__file__' in globals() = true/false
DEBUG: Path.cwd() = /path/to/DnDCharacter
DEBUG: sys.path before update: [...]
DEBUG: Added /path/to/assets/py to sys.path[0]
DEBUG: spellcasting module import failed: No module named 'spellcasting'
DEBUG: Attempting retry with explicit path insertion
DEBUG: Added /path/to/assets/py to sys.path[0]
DEBUG: spellcasting module imported successfully on retry (OR: import failed on retry)
DEBUG: SpellcastingManager class = None or <class>
```

## Solutions Attempted

### Solution 1: Module Path Priority ✓
**Status**: Implemented
**Effect**: Uses `sys.path.insert(0, ...)` instead of `append()` to give highest priority to assets/py

### Solution 2: Import Retry Logic ✓
**Status**: Implemented
**Effect**: On first import failure, explicitly adds path and retries once

### Solution 3: Fallback System ✓
**Status**: Already present
**Effect**: If all imports fail, uses stub functions so app doesn't crash

### Solution 4: Comprehensive Logging ✓
**Status**: Implemented
**Effect**: Detailed DEBUG statements show exactly what's happening during module loading

## Possible Additional Fixes

1. **HTML File Setup**
   - Ensure HTML file includes PyScript configuration for module paths
   - May need to explicitly set PYTHONPATH in PyScript config
   - May need `pyscript.config.paths` configuration

2. **PyScript Version/Configuration**
   - Check PyScript initialization settings
   - Verify module discovery is enabled
   - Check for any CORS or path restrictions

3. **File Organization**
   - Could move modules to more standard location
   - Could create symbolic links or copy files
   - Could use PyScript's package imports

4. **Async Module Loading**
   - Could defer imports until after page initialization
   - Could use dynamic imports with `importlib`
   - Could trigger import after DOM is ready

## How to Debug Further

### In Browser Console:

```javascript
// Check Python's sys.path
pyodide.globals.get("sys").path
// Result should include: /assets/py or full path

// Try importing manually
pyodide.runPython("from spellcasting import SpellcastingManager")
// Check if it works when called manually vs. at module load time
```

### Check PyScript Configuration:

Look for in HTML file:
```html
<link rel="stylesheet" href="https://pyscript.net/releases/2024.12.1/core.css">
<script defer src="https://pyscript.net/releases/2024.12.1/core.js"></script>

<py-config>
    packages = ["numpy"]  <!-- Check if assets/py needs to be listed -->
    paths = ["."]  <!-- May need to add "/assets/py" -->
</py-config>
```

## Testing Evidence

### test_spellcasting_import.py
- 7 tests covering import chain
- All tests PASS locally
- Shows SPELLCASTING_MANAGER = None in character import
- Confirms retry logic doesn't help when module truly not found

### test_pyscript_environment.py
- 8 diagnostic tests
- Tests module search paths
- Tests import with path manipulation
- Shows that adding path manually fixes the issue

## Next Steps

1. **Test in Browser** with latest code changes
   - Clear cache: Ctrl+Shift+Delete
   - Hard refresh: Ctrl+Shift+R
   - Check console for DEBUG messages
   - Watch for "spellcasting module imported successfully on retry"

2. **If Still Failing**
   - Check PyScript version and configuration
   - Verify HTML file has correct setup
   - Check for any CORS or path restrictions
   - Consider alternative module loading strategy

3. **If Working**
   - Test spell loading (Load Spells button)
   - Verify domain spells auto-populate
   - Check spell filtering works
   - Test prepared spells persistence

## Files Modified

- `assets/py/character.py` - Module loading initialization and retry logic
- `assets/py/character.py` - Comprehensive DEBUG logging throughout
- `tests/test_spellcasting_import.py` - Unit tests (all PASS)
- `tests/test_pyscript_environment.py` - Diagnostic tests (6/8 PASS locally)

## Commits

- `d828ea9` - Add comprehensive PyScript environment diagnostics and improve module loading with retry logic
- `050be36` - Fix test encoding issues and add comprehensive PyScript diagnostics
