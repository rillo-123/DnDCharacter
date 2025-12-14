# Live Testing Checklist - Lamp Indicator Fix

## Quick Summary of the Fix

The lamp wasn't showing because Python proxies were being destroyed by PyScript's garbage collector before JavaScript's `setTimeout` could use them. 

**The Solution:** Use Python's `asyncio.sleep()` instead of JavaScript's `setTimeout`. Everything stays in Python, no proxies cross to JavaScript, no destruction occurs.

---

## Testing Steps

### 1. Hard Refresh Page
```
Windows/Linux: Ctrl + Shift + R
Mac: Cmd + Shift + R
```
This ensures new Python code with asyncio changes is loaded.

### 2. Open Browser Console
```
F12 or Ctrl+Shift+I
Select "Console" tab
Look for any error messages
```

### 3. Navigate to Equipment Tab
- Click the "Equipment" tab at the top of the character sheet

### 4. Toggle Any Equipment Checkbox
- Find any equipment item with a checkbox (enable/disable equipment)
- Click it to toggle

### 5. Verify Lamp Behavior

#### ✅ SUCCESS Indicators:
- Red "Saving..." lamp appears **immediately** after toggle
- Lamp displays for **~2 seconds**
- Lamp fades/disappears **smoothly** after export completes
- **No console errors** - especially no "borrowed proxy" message
- Character data **persists** in localStorage on page reload
- AC calculation updates if armor equipped
- Multiple toggles work **consistently**

#### ❌ FAILURE Indicators (These should NOT occur):
- "This borrowed proxy was automatically destroyed" error in console
- "Uncaught Error" in console  
- Lamp never appears
- Lamp appears but never disappears
- Lamp repeatedly blinks
- JavaScript errors in console
- Data doesn't save to localStorage

---

## Detailed Test Scenarios

### Scenario 1: Single Equipment Toggle
**Steps:**
1. Navigate to Equipment tab
2. Toggle ONE equipment checkbox on
3. Verify lamp appears and disappears correctly

**Expected:** Lamp shows for ~2 seconds, then disappears. No errors.

---

### Scenario 2: Multiple Rapid Toggles
**Steps:**
1. Navigate to Equipment tab  
2. Rapidly toggle 5-10 equipment checkboxes
3. Let page settle for 3 seconds
4. Verify all changes saved

**Expected:** Lamp appears on first change, stays visible until all exports complete. No errors.

---

### Scenario 3: AC Calculation Update
**Steps:**
1. Navigate to Equipment tab
2. Toggle armor equip/unequip
3. Check Combat tab for AC value change
4. Verify lamp appeared while exporting

**Expected:** AC updates correctly, lamp appeared during change. Verified in Combat tab AC field.

---

### Scenario 4: Page Reload Persistence
**Steps:**
1. Make several equipment changes (toggle items on/off)
2. Wait for lamp to disappear (export complete)
3. Hard refresh page (Ctrl+Shift+R)
4. Verify all equipment states match before refresh

**Expected:** All equipment states preserved exactly as before refresh.

---

### Scenario 5: No Auto-Export Enabled
**Steps:**
1. Make equipment changes
2. Verify lamp appears (always shows for UX)
3. Close browser console if auto-export setup dialog appears

**Expected:** Lamp appears even without auto-export directory selected. Data saved to localStorage.

---

## Console Output to Expect

### Before the Fix (❌ BROKEN):
```
DEBUG: schedule_auto_export called! Event count: 1
DEBUG: Created JavaScript-owned auto-export callback wrapper
Uncaught Error: This borrowed proxy was automatically destroyed at the end of a function call.
```

### After the Fix (✅ WORKING):
```
DEBUG: schedule_auto_export called! Event count: 1
DEBUG: Scheduled auto-export with asyncio.sleep(2.0s)
[DEBUG][auto-export] saving-indicator state {...}
DEBUG: Character loaded from storage
```

Notice: No "borrowed proxy" error, asyncio.sleep mentioned instead of setTimeout.

---

## If Something Goes Wrong

### Error: "This borrowed proxy was automatically destroyed"
- This should NOT appear with the fix
- If it does, hard refresh page and try again
- Check browser cache is cleared (Ctrl+Shift+Delete)

### Lamp Doesn't Appear at All
- Check browser console for errors
- Hard refresh page
- Verify JavaScript is enabled
- Try equipment checkbox on different item

### Lamp Appears But Doesn't Disappear
- Wait 10 seconds for long export to complete
- Hard refresh page
- Try making a different change

### Data Not Saving
- Check browser console for "failed to save to localStorage" errors
- Verify browser allows localStorage (not private mode)
- Try clearing localStorage and refresh

---

## Success Criteria (ALL Must Be True)

- [ ] Lamp appears when equipment checkbox toggled
- [ ] Lamp displays red "Saving..." text
- [ ] Lamp disappears after ~2 seconds
- [ ] No "borrowed proxy" errors in console
- [ ] No other JavaScript errors in console
- [ ] AC updates correctly for armor changes
- [ ] Multiple toggles work consistently
- [ ] Data persists after page reload
- [ ] Equipment states match before/after reload

---

## Technical Details (For Debugging)

**What Changed:**
- `schedule_auto_export()` now uses `asyncio.Task` + `asyncio.sleep()`
- No more `setTimeout()` JavaScript calls
- No more `create_proxy()` proxy creation
- All timing stays in Python

**Why This Works:**
- asyncio events stay in Python
- No proxy boundary crossing
- No GC destruction of borrowed proxies
- Simple, robust, native to PyScript

**Performance:**
- Same 2-second delay as before
- No performance difference
- Actually simpler code (fewer abstractions)

---

## Contact/Issues

If the lamp still isn't showing after the fix:
1. Hard refresh page (Ctrl+Shift+R)
2. Open console (F12) and provide error messages
3. Take screenshot of console showing any errors
4. Note which checkbox triggered the issue

---

**Version:** Final (Post-asyncio Fix)  
**Date:** December 10, 2025  
**Status:** Ready for Production Testing
