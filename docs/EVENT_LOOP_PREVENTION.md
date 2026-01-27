# Event Loop Prevention

## The Problem

In event-driven UIs, there's a risk of infinite loops:

```
User changes input → Event fires → Update data → Redraw UI → Set input value → Event fires again! 🔄
```

## Our Safeguards

### 1. **DOM Replacement (Primary Defense)**

```python
container.innerHTML = "".join(sections_html)  # ← Destroys old elements & listeners
register_all_events()  # ← Attaches NEW listeners to NEW elements
```

When we rebuild HTML with `innerHTML`:
- Old DOM elements are **destroyed**
- Old event listeners are **garbage collected**
- New elements have **no listeners** until we explicitly attach them

**Result:** No risk of old listeners firing on new elements.

### 2. **"change" Events Only Fire on User Interaction**

JavaScript behavior:
```javascript
// ❌ Does NOT trigger 'change' event
input.value = "5";

// ✓ DOES trigger 'change' event  
// - User types in field and blurs
// - User selects from dropdown
// - User toggles checkbox
```

Our code sets values programmatically:
```python
# This happens during render - does NOT fire events
body_html += f'<input data-item-bonus="{item_id}" value="{bonus_val}">'
```

**Result:** Programmatic updates don't trigger event handlers.

### 3. **Flag-Based Re-entrance Prevention (Extra Safety)**

```python
class EquipmentEventListener:
    def __init__(self, inventory_manager):
        self._is_updating = False  # ← Guard flag
    
    def on_bonus_change(self, event, item_id: str):
        # Check flag first
        if self._is_updating:
            console.log("Ignoring event during update")
            return  # ← Block re-entrant calls
        
        self._is_updating = True
        try:
            # Do update work...
            set_armor_bonus(...)
            redraw_armor_items()
        finally:
            self._is_updating = False  # ← Always clear flag
```

**Result:** Even if a "change" event somehow fired during update, it's blocked.

### 4. **Proxy Cleanup (Memory Leak Prevention)**

```python
def register_all_handlers(self):
    global _EVENT_PROXIES
    
    # Clear old proxies before registering new ones
    old_count = len(_EVENT_PROXIES)
    _EVENT_PROXIES = []
    console.log(f"Cleared {old_count} old proxies")
    
    # Register new handlers...
```

**Result:** Old proxies are discarded, preventing memory leaks.

## Read-Only vs Interactive Elements

### Read-Only Display (No Events)

```python
# AC field - display only, no event listener
body_html += f'<span>{ac_val or "—"}</span>'
```

These elements:
- Show calculated values
- Have **no event listeners**
- Never fire events
- Examples: AC display, total damage, calculated modifiers

### Interactive Elements (With Events)

```python
# Bonus field - user can edit, has event listener
body_html += f'<input type="number" data-item-bonus="{item_id}" value="{bonus_val}">'
```

These elements:
- User can change values
- Have **change event listeners**
- Fire events on user interaction only
- Examples: bonus spinners, equipped checkboxes, quantity inputs

## Flow Diagram

```
User changes bonus spinner (+0 → +1)
    ↓
"change" event fires (user action only!)
    ↓
on_bonus_change() checks _is_updating flag (false, proceed)
    ↓
Set _is_updating = True (block other events)
    ↓
armor_manager.set_armor_bonus() updates data
    ↓
inventory_manager.redraw_armor_items()
    ├─ Destroys old DOM (innerHTML = "...")
    ├─ Builds new HTML with updated values
    ├─ Old listeners garbage collected
    └─ register_all_events() attaches NEW listeners
    ↓
Set _is_updating = False (allow events again)
    ↓
Done! No loop occurred ✓
```

## Why No Loops?

1. **innerHTML destroys old listeners** - They can't fire again
2. **Programmatic value setting doesn't fire "change"** - Only user input does
3. **Flag blocks re-entrance** - Even if event fired during update, it's ignored
4. **Proxies cleaned up** - No memory leaks or zombie listeners

## Testing Loop Prevention

Console logs show the protection working:

```javascript
[EVENT-LISTENER] on_bonus_change: item_id=xyz
[EVENT-LISTENER] Cleared 15 old proxies
[ARMOR-SET] Set bonus for Shield to 1
[EQUIPMENT] Redrawing armor items
[EVENT-LISTENER] Registered 15 new handlers
// ✓ No duplicate event firing!
```

If a loop were occurring, you'd see:
```javascript
[EVENT-LISTENER] on_bonus_change: item_id=xyz
[EVENT-LISTENER] on_bonus_change: item_id=xyz  // ← Duplicate!
[EVENT-LISTENER] on_bonus_change: item_id=xyz  // ← Infinite loop!
```

But our safeguards **prevent this entirely**.
