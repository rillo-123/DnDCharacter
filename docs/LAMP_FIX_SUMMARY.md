## Saving Lamp Not Showing - Root Cause Analysis & Fix

### Problem
The saving lamp indicator was not showing at all when equipment checkboxes were toggled. This was a regression from the previous session where the PyScript proxy lifecycle issue was partially addressed.

### Root Cause
**Module Initialization Order Issue:**

When `character.py` loads, the import sequence is:
1. **Line 317**: `from equipment_management import ...`
   - equipment_management.py loads
   - At end of equipment_management.py, `initialize_module_references()` is called
   - At this point, `export_management` has NOT yet been imported
   - `sys.modules.get('export_management')` returns `None`
   - `_EXPORT_MODULE_REF = None` and `_SCHEDULE_AUTO_EXPORT_FUNC = None`

2. **Line 366**: `from export_management import ...`
   - export_management.py loads (too late!)
   - But equipment_management.py already failed to capture the reference

**Result**: When the checkbox handler calls `_SCHEDULE_AUTO_EXPORT_FUNC()`, it's `None`, so nothing happens and the lamp never shows.

### Solution: Lazy Initialization

**Implemented in**: `assets/py/equipment_management.py`

1. **Modified `initialize_module_references()` function (lines 1217-1243)**:
   - Made idempotent (can be called multiple times safely)
   - Added check `if _EXPORT_MODULE_REF is None:` before capturing
   - Added diagnostic logging when export_management not yet loaded
   - Will retry capture on next call (lazy initialization)

2. **Modified `_handle_equipped_toggle()` handler (lines 921-950)**:
   - Added call to `initialize_module_references()` at start of handler
   - This ensures references are captured (lazy) when handler first executes
   - By this time, all modules are fully loaded

### Technical Details

**Why This Works:**
- At module load time (import), export_management isn't available → lazy init logs a debug message
- When checkbox is first toggled, handler calls `initialize_module_references()` again (idempotent)
- By now, export_management IS in sys.modules → capture succeeds
- References stay alive for handler execution → lamp shows correctly

**Key Code Changes:**

```python
# Initialize function now idempotent
if _EXPORT_MODULE_REF is None:  # Only capture once
    _EXPORT_MODULE_REF = sys.modules.get('export_management')
    if _EXPORT_MODULE_REF:
        _SCHEDULE_AUTO_EXPORT_FUNC = getattr(...)
    else:
        console.log("export_management not yet in sys.modules (lazy init will retry...)")

# Handler ensures init happens before use
def _handle_equipped_toggle(self, event, item_id: str):
    try:
        # ... item update code ...
        
        # Ensure module references are initialized (lazy initialization)
        initialize_module_references()
        
        # Now _SCHEDULE_AUTO_EXPORT_FUNC is guaranteed to be set (if export_management loaded)
        if _SCHEDULE_AUTO_EXPORT_FUNC is not None:
            _SCHEDULE_AUTO_EXPORT_FUNC()
```

### Testing

**Created**: `tests/test_lamp_fix.py` with 5 comprehensive tests:

1. ✅ **test_lazy_initialization_captures_export_management**
   - Verifies that calling `initialize_module_references()` after export_management loads captures the function
   
2. ✅ **test_handler_calls_initialize_on_first_use**
   - Verifies that handler calls `initialize_module_references()` on first toggle
   
3. ✅ **test_schedule_auto_export_func_is_used_not_stub**
   - Confirms captured function is real export_management version, not equipment_management stub
   
4. ✅ **test_export_management_schedule_auto_export_accesses_indicator**
   - Mocks DOM and verifies schedule_auto_export() calls `getElementById("saving-indicator")`
   - Verifies it adds "recording" class and sets display/opacity
   
5. ✅ **test_initialize_logs_debug_messages**
   - Smoke test verifying initialization doesn't crash when called multiple times

**All 5 tests passing** ✅

### Expected Behavior After Fix

1. User clicks equipment checkbox
2. Handler calls `initialize_module_references()` (first time, captures export_management)
3. Handler calls `_UPDATE_CALCULATIONS_FUNC()` → AC updates
4. Handler calls `_SCHEDULE_AUTO_EXPORT_FUNC()` → **lamp shows** (red recording indicator)
5. After 2 seconds, export completes, lamp disappears
6. Character saved to localStorage

### Files Modified

- **assets/py/equipment_management.py**
  - Lines 1217-1243: Enhanced `initialize_module_references()` with lazy init
  - Lines 921-950: Modified `_handle_equipped_toggle()` to call initialize

### Validation

- ✅ Python syntax validated: `python -m py_compile equipment_management.py`
- ✅ 5 lamp-specific tests pass
- ✅ No breaking changes to existing tests
- ✅ Idempotent initialization (can be called multiple times safely)

### How to Test in Live App

1. Reload the PySheet app in browser
2. Go to Equipment tab
3. Check an equipment item (e.g., Shield)
4. **Expected**: Red "Saving..." lamp appears for ~2 seconds
5. **Check Console**: Should see debug logs showing module references captured

### Debugging

If lamp still doesn't show, check browser console for:

```
DEBUG: Captured schedule_auto_export function reference  // Should appear
DEBUG: Called schedule_auto_export() - checkbox handler  // Should appear on toggle
```

If these don't appear, check for errors about module references not being available.

---

**Status**: ✅ FIXED - Lazy initialization ensures export_management reference is captured when handler first executes, not at module load time.
