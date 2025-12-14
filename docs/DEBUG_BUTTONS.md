# Quick Debug Guide: Button Click Error

## The Error You're Seeing
```
TypeError: Cannot read properties of undefined (reading 'call')
```

This happens when PyScript tries to call a button handler that doesn't exist in the global scope.

---

## Step-by-Step Debug (In Browser Console)

### Step 1: Check If PyScript Loaded
```javascript
// Should return true after a moment
window.pyodide !== undefined

// Should show completion message
// Look for: "=== PySheet initialization complete ===" in console
```

### Step 2: Check If Python Functions Are Available
```javascript
// Test each manage tab button handler:
typeof window.reset_spell_slots        // Should be "function"
typeof window.save_character            // Should be "function"
typeof window.reset_character           // Should be "function"
typeof window.export_character          // Should be "function"
typeof window.show_storage_info         // Should be "function"
typeof window.cleanup_exports           // Should be "function"
typeof window._setup_auto_export_button_click  // Should be "function"

// If ANY of these returns "undefined", that handler won't work
```

### Step 3: Try Calling a Handler Directly
```javascript
// Test if the function actually works
window.reset_spell_slots()      // Should run without error
window.save_character()         // Should run without error
window.show_storage_info()      // Should run without error
```

### Step 4: Check the HTML Button Configuration
```javascript
// Get the button element
let btn = document.getElementById("long-rest-btn")

// Check py-click attribute
btn.getAttribute("py-click")     // Should show: "reset_spell_slots"

// Check if handler exists
window[btn.getAttribute("py-click")]  // Should be a function, not undefined
```

### Step 5: Manually Test Button Click
```javascript
// Get a button
let btn = document.getElementById("long-rest-btn")

// Try to click it
btn.click()

// Or manually call the handler
window.reset_spell_slots()

// Watch console for errors
```

---

## Common Causes & Solutions

### ❌ **Cause 1: Python Not Fully Loaded**
**Symptom:** Functions return `undefined` immediately after page load

**Solution:** 
- Wait 2-3 seconds for Python to load
- Look for "=== PySheet initialization complete ===" in console
- Then try accessing the handlers

---

### ❌ **Cause 2: Import Error in Character Module**
**Symptom:** Handlers exist but throw errors when clicked

**Check console for:**
```
DEBUG: export_management import failed: ...
DEBUG: *** EXPORT_MGMT FALLBACK TRIGGERED ***
```

**Solution:**
- Check that [assets/py/export_management.py](../assets/py/export_management.py) exists
- Run syntax check: `python -m py_compile assets/py/export_management.py`
- Hard refresh (Ctrl+Shift+R) to clear cache

---

### ❌ **Cause 3: Async Function Bound to py-click**
**Symptom:** Handler defined but py-click can't call it

**Solution:**
- py-click only works with sync functions
- For async handlers, create a sync wrapper (like `_setup_auto_export_button_click`)
- All our handlers are already sync ✅

---

### ❌ **Cause 4: Handler Name Mismatch**
**Symptom:** HTML says `py-click="handler_name"` but function is named differently

**Check:**
```html
<!-- HTML -->
<button py-click="reset_spell_slots">...</button>

<!-- Python must have this function (case-sensitive) -->
def reset_spell_slots(_event=None):
    ...
```

**Solution:**
- Handler names must match exactly (case-sensitive)
- All our handlers match ✅

---

## Window Scope Check

If handlers aren't in `window` scope, they won't be callable from HTML.

**Check all manage tab handlers:**
```javascript
let handlers = [
    'reset_spell_slots',
    'save_character',
    'reset_character',
    'export_character',
    'show_storage_info',
    'cleanup_exports',
    '_setup_auto_export_button_click'
];

handlers.forEach(h => {
    let exists = typeof window[h] === 'function';
    console.log(`${h}: ${exists ? '✅' : '❌'}`);
});
```

---

## Full Console Test Script

Copy-paste this into browser console after page fully loads:

```javascript
console.log("=== MANAGE TAB BUTTON DEBUG ===");
console.log("Checking button handlers...\n");

let handlers = [
    { name: 'reset_spell_slots', btn: 'long-rest-btn' },
    { name: 'save_character', btn: 'save-btn' },
    { name: 'reset_character', btn: 'reset-btn' },
    { name: 'export_character', btn: 'export-btn' },
    { name: 'show_storage_info', btn: 'storage-info-btn' },
    { name: 'cleanup_exports', btn: 'cleanup-btn' },
    { name: '_setup_auto_export_button_click', btn: 'setup-auto-export-btn' }
];

handlers.forEach(h => {
    let exists = typeof window[h.name] === 'function';
    let btn = document.getElementById(h.btn);
    let btnExists = btn !== null;
    let btnHandler = btn ? btn.getAttribute('py-click') : 'N/A';
    
    console.log(`✓ ${h.name}`);
    console.log(`  Function exists: ${exists ? '✅' : '❌'}`);
    console.log(`  Button exists: ${btnExists ? '✅' : '❌'}`);
    console.log(`  Button handler: ${btnHandler}`);
    console.log(`  Match: ${btnHandler === h.name ? '✅' : '❌'}\n`);
});

console.log("Try clicking a button now and check for errors above.");
```

---

## If Still Not Working

### Collect Debugging Info:
1. Screenshot of console errors
2. Output of the debug script above
3. Check [tests/MANAGE_TAB_TESTING_REPORT.md](MANAGE_TAB_TESTING_REPORT.md) - run the tests locally

### Run Tests Locally:
```bash
cd "g:\My Drive\DnDCharacter"
python -m pytest tests/test_manage_tab_buttons.py -v
python -m pytest tests/test_manage_tab_button_binding.py -v
```

If tests pass but buttons fail in browser, the issue is with PyScript initialization, not the code.

---

**Last Updated:** 2025-12-11
**Test Status:** 16/16 configuration tests passing ✅
