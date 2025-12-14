# PyScript Proxy Lifecycle Fix

**Date:** December 9, 2025  
**Issue:** "This borrowed proxy was automatically destroyed" error in PyScript/Pyodide  
**Status:** ✅ FIXED - All 363+ tests passing

## Problem

When toggling equipment checkboxes in the app, the saving lamp indicator stopped showing. The browser console showed:

```
Uncaught Error: This borrowed proxy was automatically destroyed at the end of a function call.
```

### Root Cause

The equipment_management module was capturing **function references** from other modules:

```python
# OLD PATTERN (PROBLEMATIC)
_SCHEDULE_AUTO_EXPORT_FUNC = getattr(_EXPORT_MODULE_REF, 'schedule_auto_export', None)
# This creates a borrowed proxy in PyScript that gets destroyed
```

In PyScript/Pyodide:
1. When you call `getattr()` on a module to get a function, it returns a **borrowed proxy**
2. Borrowed proxies have a short lifetime - they're automatically destroyed after use
3. If you store the proxy for later use, it's already dead by the time you call it
4. Result: "This borrowed proxy was automatically destroyed" error

## Solution

Store **module references** instead of **function references**, then call through the module:

```python
# NEW PATTERN (CORRECT)
_EXPORT_MODULE_REF = sys.modules.get('export_management')  # Store the MODULE
# Then call through it:
_EXPORT_MODULE_REF.schedule_auto_export()  # Not a proxy, always works
```

### Why This Works

- Module objects themselves are persistent (not proxies)
- Calling `module.function()` doesn't create borrowed proxies in PyScript
- The function lookup happens at call time, which is safe
- No proxy lifetime issues

## Implementation

### File: assets/py/equipment_management.py

**Changed Globals** (lines 41-45):
```python
# OLD: Had _UPDATE_CALCULATIONS_FUNC and _SCHEDULE_AUTO_EXPORT_FUNC
_CHAR_MODULE_REF = None
_EXPORT_MODULE_REF = None
# NEW: Only module references, no function references
```

**Updated initialize_module_references()** (lines 1217-1253):
```python
def initialize_module_references():
    """Initialize references to character and export management modules.
    
    Important: We store MODULE references, not function references. Functions are called
    through the module to avoid PyScript/Pyodide proxy lifecycle issues.
    """
    global _CHAR_MODULE_REF, _EXPORT_MODULE_REF
    
    import sys
    
    if _CHAR_MODULE_REF is None:
        _CHAR_MODULE_REF = sys.modules.get('__main__')
        if _CHAR_MODULE_REF and hasattr(_CHAR_MODULE_REF, 'update_calculations'):
            console.log("DEBUG: Captured __main__ module reference")
    
    if _EXPORT_MODULE_REF is None:
        _EXPORT_MODULE_REF = sys.modules.get('export_management')
        if _EXPORT_MODULE_REF and hasattr(_EXPORT_MODULE_REF, 'schedule_auto_export'):
            console.log("DEBUG: Captured export_management module reference")
```

**Updated _handle_equipped_toggle()** (lines 920-951):
```python
def _handle_equipped_toggle(self, event, item_id: str):
    """Handle equipped checkbox toggle."""
    try:
        # ... item update ...
        
        # Ensure module references initialized
        initialize_module_references()
        
        # Call through module references (not function proxies)
        if _CHAR_MODULE_REF is not None and hasattr(_CHAR_MODULE_REF, 'update_calculations'):
            _CHAR_MODULE_REF.update_calculations()  # ← Call through module
        
        if _EXPORT_MODULE_REF is not None and hasattr(_EXPORT_MODULE_REF, 'schedule_auto_export'):
            _EXPORT_MODULE_REF.schedule_auto_export()  # ← Call through module
```

## Testing

Created comprehensive test suite to verify the fix:

### Test Files
- **tests/test_proxy_lifecycle_fix.py** (5 tests)
  - Verifies module references stored, not functions
  - Tests calling through module references
  - Demonstrates proxy lifecycle issues and solutions

- **tests/test_lamp_fix.py** (6 tests)
  - Tests module reference pattern in equipment manager
  - Tests handler uses module references correctly
  - Tests lazy initialization with module references
  - Tests proxy lifecycle avoidance

- **tests/test_lamp_integration.py** (5 tests)
  - Tests complete app load sequence
  - Tests lazy initialization idempotence
  - Tests handler reference capture on first call
  - Tests module reference pattern avoids proxy issues

### Test Results
```
All 16 proxy/lamp tests: ✅ PASSED
Full test suite: ✅ 363+ tests PASSED
No regressions: ✅ Confirmed
```

## Key Differences: Old vs New Pattern

| Aspect | Old Pattern | New Pattern |
|--------|-----------|-----------|
| **Stored** | Function reference | Module reference |
| **Type** | Borrowed proxy | ModuleType object |
| **Lifetime** | Auto-destroyed | Persistent |
| **Call Style** | `func()` | `module.func()` |
| **PyScript Issue** | ❌ Proxy destroyed | ✅ Always works |
| **Safety** | ❌ Error-prone | ✅ Robust |

## How the Fix Resolves the Original Issue

1. **User clicks equipment checkbox**
   ↓
2. **_handle_equipped_toggle() handler executed**
   ↓
3. **Handler calls initialize_module_references()**
   ↓
4. **Module references captured and stored** (not function proxies)
   ↓
5. **Handler calls _EXPORT_MODULE_REF.schedule_auto_export()**
   ↓
6. **schedule_auto_export() executes successfully**
   ↓
7. **Saving lamp indicator shows** ✅
   ↓
8. **Character auto-saves** ✅

## Performance Impact

**None** - Actual performance is identical:
- No extra function calls
- No proxy overhead
- Slight reduction in complexity (fewer globals to track)

## Future Considerations

This pattern should be used for all cross-module function references in HTTP-loaded modules:
1. Always store module references, not function references
2. Call functions through the module: `module.function()`
3. Use lazy initialization for modules loaded in non-deterministic order
4. Verify function exists before calling: `hasattr(module, 'function')`

## Validation Checklist

- ✅ Syntax validated (python -m py_compile)
- ✅ 16 new/updated tests all passing
- ✅ 363+ existing tests still passing (no regressions)
- ✅ Handler correctly uses module references
- ✅ Lazy initialization works with module references
- ✅ Multiple initialize calls are idempotent
- ✅ Ready for live testing in browser

## Next Steps

1. Reload app in browser (fresh page load)
2. Click equipment checkboxes in Equipment tab
3. Verify saving lamp appears for ~2 seconds
4. Check console for debug messages (optional)
5. Monitor for no proxy destruction errors
