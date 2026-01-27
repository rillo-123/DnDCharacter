# Event Listener Architecture

## Overview

Clean unidirectional data flow for all equipment/inventory events.

## Pattern

```
User Action → DOM Event → Event Listener → Manager Method → Data Update → GUI Redraw
```

## Flow Example: Changing Armor Bonus

1. **User Action**: User changes shield bonus from +0 to +1
2. **DOM Event**: `<input data-item-bonus="xyz">` fires "change" event
3. **Event Listener**: `event_listener.on_bonus_change()` extracts item_id and value
4. **Manager Method**: Calls `armor_manager.set_armor_bonus(inventory_manager, item_id, 1)`
5. **Data Update**: armor_manager calculates AC (2 + 1 = 3), updates item notes JSON
6. **GUI Redraw**: `inventory_manager.redraw_armor_items()` re-renders the display
7. **AC Calculation**: `update_calculations()` calls `generate_ac_tooltip()` which uses armor_manager as single source of truth

## Components

### equipment_event_manager.py
- Centralized event registration
- Routes events to appropriate managers
- Thin coordination layer with no business logic
- Single place to see all event handlers

### armor_manager.py
- **Setters**: `set_armor_ac()`, `set_armor_bonus()`
- Single source of truth for armor/shield AC calculations
- Handles base AC + magical bonus logic
- Updates item data (notes JSON)

### inventory_manager.py
- **Redraw**: `redraw_armor_items()` - refreshes UI after data changes
- **Handlers**: Internal methods for non-armor items (weapons, etc.)
- Manages item CRUD operations

### character.py
- **AC Calculation**: `generate_ac_tooltip()` calls `armor_manager.calculate_total_ac_from_armor_manager()`
- No longer calculates AC independently
- Delegates to armor_manager as authoritative source

## Benefits

✅ **Serializable** - Each action is a discrete method call  
✅ **No circular calls** - Linear flow prevents race conditions  
✅ **Single source of truth** - armor_manager owns AC logic  
✅ **Easy to debug** - Clear log messages at each step: `[EVENT-LISTENER]` → `[ARMOR-SET]` → `[EQUIPMENT]`  
✅ **Easy to test** - Setters can be called directly  
✅ **Maintainable** - One place to see all event handlers  
✅ **Loop-safe** - Multiple safeguards prevent infinite event loops (see [EVENT_LOOP_PREVENTION.md](EVENT_LOOP_PREVENTION.md))  

## Code Locations

- `equipment_event_manager.py`: Event registration and routing
- `armor_manager.py` lines 536-720: Setters and AC calculation
- `inventory_manager.py` line 789: `redraw_armor_items()`
- `character.py` line 1167: Event listener initialization
- `character.py` line 2089: `generate_ac_tooltip()` uses armor_manager

## Testing

Hard refresh (Ctrl+Shift+R) and watch console logs:

```javascript
[EVENT-LISTENER] on_bonus_change: item_id=xyz
[ARMOR-SET] Set bonus for Shield +1 to 1
[ARMOR-SET] Shield Shield: AC = 2 + 1 = 3
[EQUIPMENT] Redrawing armor items
[AC-CALC] Total AC from armor_manager: 18
```

Each step logged, no jumbled circular calls.
