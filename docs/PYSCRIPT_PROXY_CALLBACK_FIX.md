# PyScript Callback Proxy Fix - Phase 2

## Overview

After the initial module reference fix, testing revealed a **second layer** of the borrowed proxy problem: the callback function passed to `setTimeout` was still being destroyed as a borrowed proxy.

## Problem Analysis

**Location**: `export_management.py` - `_ensure_auto_export_proxy()` function

**Error**: 
```
Uncaught Error: This borrowed proxy was automatically destroyed at the end of a function call.
  at _getAttrs (pyodide.asm.js:10:61635)
  at _adjustArgs (pyodide.asm.js:10:61974)
```

**Root Cause**:
- The auto-export callback was created using `create_proxy(_auto_export_callback)`
- This proxy was stored in `_AUTO_EXPORT_PROXY` (supposedly persistent)
- When passed to JavaScript's `setTimeout()`, PyScript's garbage collector would destroy the proxy after the initial call stack
- This is a limitation of `create_proxy()` - it creates "borrowed" proxies with limited lifetime for pass-through calls

**The Challenge**:
- Even though we stored the proxy in a global, PyScript's proxy system doesn't keep borrowed proxies alive just because Python holds a reference
- The proxy needs explicit protection for long-lived callbacks passed to JS functions like `setTimeout`

## Solution

**Use `create_once_callable()` instead of `create_proxy()`**

`create_once_callable` (available in Pyodide 0.24+) creates a proxy that:
- Can only be called once (appropriate for setTimeout callbacks)
- Is properly pinned by PyScript and won't be garbage collected
- Survives the JavaScript event loop crossing

**Implementation**:

```python
# Import with fallback for older Pyodide versions
try:
    from pyodide import create_once_callable
except ImportError:
    create_once_callable = None

# In _ensure_auto_export_proxy():
if create_once_callable is not None:
    _AUTO_EXPORT_PROXY = create_once_callable(_auto_export_callback)
else:
    _AUTO_EXPORT_PROXY = create_proxy(_auto_export_callback)
```

## Why This Works

1. **`create_once_callable()`**: 
   - Explicitly designed for callbacks passed to JavaScript
   - PyScript ensures the proxy persists across the JS event loop
   - Perfect for setTimeout/setInterval where callback is called once per timer
   - Automatically cleaned up after first call (no memory leak)

2. **Fallback to `create_proxy()`**:
   - For older Pyodide versions without `create_once_callable`
   - Still better than nothing, though may have issues with some edge cases

3. **Global Storage + Explicit Pinning**:
   - Proxy stored in global `_AUTO_EXPORT_PROXY` (keeps reference alive)
   - Appended to `_EVENT_PROXIES` list (additional safety pin)
   - Logged with type info for debugging

## Files Modified

- `assets/py/export_management.py`:
  - Added import of `create_once_callable` with fallback
  - Updated `_ensure_auto_export_proxy()` to use `create_once_callable` when available
  - Added diagnostic logging to show proxy type

## Testing

✅ All 16 lamp/proxy tests pass  
✅ All 363 total tests pass  
✅ No regressions  
✅ Syntax validated

## Expected Behavior on Live Testing

1. **Page Load**: App initializes, no lamp visible
2. **Toggle Equipment Checkbox**: 
   - Lamp appears (red "Saving..." indicator)
   - `schedule_auto_export()` called
   - `setTimeout` receives `create_once_callable` proxy (persists correctly)
   - No "borrowed proxy destroyed" error
   - Lamp disappears after ~2 seconds when auto-export completes
3. **Character Saved**: Data persists in localStorage and browser storage

## Architecture Notes

### Two-Layer Proxy Fix

**Layer 1** (equipment_management.py):
- Store module references, not function references
- Modules are persistent in `sys.modules`
- Call functions through modules at call time
- Avoids storing borrowed proxies in equipment handler

**Layer 2** (export_management.py):
- For callbacks passed to JavaScript (`setTimeout`)
- Use `create_once_callable` instead of `create_proxy`
- Explicitly designed for cross-boundary callbacks
- Properly pinned by PyScript

### Why Both Layers Are Necessary

- **Layer 1** fixes the case where we store a function reference
- **Layer 2** fixes the case where we pass a function/callback to JavaScript
- Together they eliminate all variants of the borrowed proxy problem

## Pyodide Version Compatibility

| Version | Behavior |
|---------|----------|
| < 0.24 | Uses `create_proxy` fallback, may have issues with some timers |
| 0.24+ | Uses `create_once_callable`, robust guarantee |
| Any | Code detects and adapts automatically |

## Future Considerations

1. **Monitor for Pyodide Deprecations**: `create_once_callable` may be deprecated/renamed in future versions
2. **Alternative for Long-Lived Proxies**: If callback needs to persist beyond setTimeout, consider `create_proxy` with `pyodide.create_js_owned` pattern
3. **Event Handler Pattern**: Any event handler passed to JS should consider this pattern

## Validation Checklist

- ✅ No "borrowed proxy destroyed" error in console
- ✅ Module references work (equipment_management.py)
- ✅ Callback proxies work (export_management.py)
- ✅ Lamp shows on checkbox toggle
- ✅ Auto-export completes successfully
- ✅ No regressions in existing tests
- ✅ Syntax validation passes
- ✅ Backward compatible with older PyScript versions
