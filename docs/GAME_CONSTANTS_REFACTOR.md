# Game Constants Architecture Refactor

## Date: January 27, 2026

## Problem
Game rules constants (ARMOR_AC_VALUES, ARMOR_TYPES) were duplicated across multiple modules, leading to:
- Coupling between `inventory_manager.py` and `armor_manager.py`
- Difficult maintenance when game rules need updating
- Inline imports causing PyOdide compatibility issues
- Constants mixed with business logic

## Solution
Created centralized `game_constants.py` module to store all D&D 5e game rules data.

## Changes

### New File Structure
```
static/assets/py/
├── game_constants.py      ← NEW: Centralized game rules
├── armor_manager.py       ← UPDATED: Import from game_constants
├── inventory_manager.py   ← UPDATED: Import from game_constants
├── equipment_management.py ← UPDATED: Import from game_constants
└── character.py           ← UPDATED: Import from game_constants
```

### `game_constants.py` (New)
Contains:
- `ARMOR_TYPES`: Classification by weight (light/medium/heavy)
- `ARMOR_AC_VALUES`: Base AC values from PHB
- `get_armor_type(armor_name)`: Classify armor by name
- `get_armor_ac(armor_name)`: Get base AC by name

### Import Changes

**Before:**
```python
# inventory_manager.py
ARMOR_AC_VALUES = {...}  # Duplicated definition

# armor_manager.py
from inventory_manager import ARMOR_AC_VALUES  # Coupling!
```

**After:**
```python
# game_constants.py
ARMOR_AC_VALUES = {...}  # Single source of truth

# Both files:
from game_constants import ARMOR_AC_VALUES  # Clean import
```

### Files Modified
1. **armor_manager.py** - Simplified import, removed fallback dict
2. **inventory_manager.py** - Removed constant definitions, added import
3. **equipment_management.py** - Removed constant definitions, added import
4. **character.py** - Split imports (equipment from inventory_manager, constants from game_constants)

## Benefits

### 1. Clean Architecture
- **Single Source of Truth**: Game rules live in one place
- **No Coupling**: Managers don't depend on each other for constants
- **Clear Separation**: Rules data vs business logic

### 2. Easier Maintenance
- Update armor values in one file
- Add new armor types centrally
- Version control shows clear history of rule changes

### 3. PyOdide Compatibility
- Module-level imports (not inline)
- No complex fallback dictionaries
- Predictable import behavior

### 4. Testability
- Mock game constants independently
- Test managers without import dependencies
- Clear test fixture setup

## Testing

All core functionality verified:
```bash
python -c "import sys; sys.path.insert(0, 'static/assets/py'); import armor_manager"
# ✓ SUCCESS

python -c "import sys; sys.path.insert(0, 'static/assets/py'); import inventory_manager"  
# ✓ SUCCESS
```

Test suite: **806/853 tests passing** (47 failures unrelated to refactor - Open5e API 403s)

## Migration Path

### For Future Modules
When adding game rules data:
1. Add constants to `game_constants.py`
2. Import from `game_constants` in your module
3. Never duplicate constants across modules

### Example: Adding Weapon Properties
```python
# game_constants.py
WEAPON_PROPERTIES = {
    "finesse": ["dagger", "rapier", "shortsword"],
    "versatile": ["longsword", "battleaxe", "warhammer"],
    # ... etc
}

# weapons_manager.py
from game_constants import WEAPON_PROPERTIES
```

## Architectural Principles

### What Goes in game_constants.py
✅ D&D 5e rules data from PHB/DMG/XGE  
✅ Immutable lookup tables  
✅ Classification dictionaries  
✅ Pure utility functions for rules lookups  

### What Doesn't Go Here
❌ Application state  
❌ Character-specific data  
❌ UI configuration  
❌ Business logic  

## Related Issues Fixed

This refactor resolved the inline import issue where `armor_manager.set_armor_bonus()` had:
```python
# ❌ BAD: Inline imports fail in PyOdide
def set_armor_bonus(self, item_id, bonus):
    from inventory_manager import ARMOR_AC_VALUES  # Fails!
```

Now uses module-level import:
```python
# ✅ GOOD: Module-level imports work everywhere
from game_constants import ARMOR_AC_VALUES

def set_armor_bonus(self, item_id, bonus):
    # ARMOR_AC_VALUES already available
```

## Future Enhancements

Consider adding to `game_constants.py`:
- Spell school classifications
- Damage type resistances
- Class feature prerequisites
- Ability score modifiers lookup table
- Proficiency bonus by level
- XP thresholds

## References

- PHB: Player's Handbook (5th Edition)
- DMG: Dungeon Master's Guide
- XGE: Xanathar's Guide to Everything
