# Modular Architecture - PySheet D&D Character Sheet

## Overview
The codebase is being progressively refactored from a monolithic `character.py` (~7,800 lines) into focused, reusable modules. This improves maintainability, testability, and allows incremental feature development.

## Current Module Structure

### Core Modules (Extracted)

#### `entities.py` (280 lines)
**Purpose:** Universal entity system for representing any displayable game object  
**Classes:**
- `Entity` - Base class with dynamic properties, serialization
- `Spell(Entity)` - D&D 5e spell representation with level, school, components, etc.
- `Ability(Entity)` - Class features, feats, special abilities
- `Resource(Entity)` - Trackable resources (Ki, Rage, Channel Divinity) with use/restore methods
- `Equipment(Entity)` - Base for all equipment items
- `Weapon(Equipment)` - Melee/ranged weapons with damage, range, properties
- `Armor(Equipment)` - Armor pieces with AC values
- `Shield(Equipment)` - Shields with AC bonuses

**Key Features:**
- Dynamic property storage (`.add_property()`, `.get_property()`)
- Fluent API (methods return self for chaining)
- Full serialization: `.to_dict()` and `.from_dict()` for JSON round-tripping
- Factory pattern in `from_dict()` detects subtype and creates appropriate class

**Status:** ✅ Complete and tested

---

#### `browser_logger.py` (85 lines)
**Purpose:** Browser-based logging with automatic data pruning  
**Classes:**
- `BrowserLogger` - Static logger for client-side debugging

**Features:**
- Local storage persistence
- Automatic 60-day rolling window
- Log statistics tracking
- Separate error logging channel

**Status:** ✅ Complete (ported from character.py)

---

### Modules Pending Extraction

#### `spellcasting.py` (~ 1,050 lines)
**To extract from character.py:**
- `SpellcastingManager` - Spell slot management, preparation tracking
- Spell library management functions
- Spell data tables and progression logic
- Spell correction/normalization

**Benefits:** Isolated spell logic, easier testing, reusable for spell UI features

---

#### `equipment.py` (~ 800 lines)
**To extract from character.py:**
- `InventoryManager` - Item management and equipment rendering
- Equipment rendering functions (HTML generation)
- Item library management
- Fallback equipment lists

**Benefits:** Independent equipment UI, testable item rendering, item search/filtering

---

#### `export.py` (~ 600 lines)
**To extract from character.py:**
- Export/import logic (character JSON serialization)
- Auto-export configuration and scheduling
- File management (browser-based export)
- Directory handle management

**Benefits:** Standalone export feature, easier to enhance with new formats

---

#### `spell_data.py` (~ 300 lines)
**To extract from character.py:**
- Spell library data (LOCAL_SPELLS_FALLBACK)
- Spell corrections and synonyms
- Class-to-spell-list mappings
- Spell source authoritative lists

**Benefits:** Data separate from logic, easier to update spell lists, external tool compatibility

---

### Main Module (Remains)

#### `character.py` (~ 7,800 → ~5,500 lines target)
**Purpose:** PyScript driver + UI coordination  
**Responsibilities:**
- PyScript initialization and browser API integration
- Main UI event handlers (click, change events)
- High-level workflow orchestration
- Import statements from modular files

**Will contain after refactoring:**
- Browser imports (`from js import ...`)
- Module imports from extracted files
- Top-level UI event handlers
- Character sheet rendering logic
- Main execution entry points

**Status:** 🔄 In progress (currently has duplicate definitions for backward compatibility)

---

## Import Strategy

### Current Approach (Backward Compatible)
```python
# character.py imports modular files
try:
    from entities import Entity, Spell, Ability, Resource, Equipment, Weapon, Armor, Shield
except ImportError:
    # Fallback - definitions also exist inline in character.py
    pass

try:
    from browser_logger import BrowserLogger
except ImportError:
    # Fallback - BrowserLogger defined in character.py
    pass
```

### Why This Works
1. **PyScript execution:** Browser loads `character.py` directly, has all classes available
2. **Python testing:** Can import from individual modules without loading PyScript dependencies
3. **Gradual migration:** Can move logic module-by-module without breaking PyScript

### Future: Clean Imports
Once all modules are extracted and PyScript setup is finalized:
```python
# Pure imports from modular files
from entities import Entity, Spell, Ability, Resource, Equipment, Weapon, Armor, Shield
from browser_logger import BrowserLogger
from spellcasting import SpellcastingManager
from inventory import InventoryManager
from export import ExportManager
```

---

## Module Dependencies Map

```
browser_logger.py
  └─ (no internal dependencies)

entities.py
  └─ (no internal dependencies)

character.py (main driver)
  ├─ browser_logger.py
  ├─ entities.py
  ├─ character_models.py (external)
  ├─ (future) spellcasting.py
  ├─ (future) equipment.py
  ├─ (future) export.py
  └─ (future) spell_data.py

spellcasting.py (planned)
  ├─ entities.py (for Spell class)
  └─ character_models.py (for class info)

equipment.py (planned)
  ├─ entities.py (for Equipment, Weapon, Armor, Shield)
  └─ spell_data.py (for authoritative sources)

export.py (planned)
  └─ browser_logger.py (for logging)

spell_data.py (planned)
  └─ (no internal dependencies)
```

---

## Testing Strategy

### Current Test Coverage
- ✅ 25 tests: `test_character_models.py` - Character system
- ✅ 17 tests: `test_character_export.py` - Export/import
- ✅ 54 tests: `test_equipment_*.py` - Equipment rendering and management

### New Module Tests (To Create)
- `test_entities.py` - Entity hierarchy, serialization
- `test_browser_logger.py` - Logger functionality
- `test_spellcasting.py` - Spell management (enhancement of existing)
- `test_equipment_manager.py` - Inventory logic
- `test_export_manager.py` - Export functionality

---

## Extraction Roadmap

### Phase 1 ✅ (Complete)
- [x] Extract `entities.py` - Entity base system
- [x] Extract `browser_logger.py` - Logging system
- [x] Set up import compatibility layer
- [x] Verify tests still pass (95 passing)

### Phase 2 (Next)
- [ ] Extract `spell_data.py` - Spell library data
- [ ] Extract `spellcasting.py` - Spell management logic
- [ ] Create `test_entities.py` - Entity system tests
- [ ] Update existing spell tests

### Phase 3
- [ ] Extract `equipment.py` - Item management
- [ ] Extract `inventory.py` - Inventory logic
- [ ] Create `test_equipment_manager.py`

### Phase 4
- [ ] Extract `export.py` - Export/import system
- [ ] Create `test_export_manager.py`
- [ ] Create `test_logger.py`

### Phase 5
- [ ] Clean up character.py - Remove inline definitions
- [ ] Final test run - all 95+ tests passing
- [ ] Merge feature branch to main
- [ ] Documentation update

---

## Benefits of Modular Architecture

### Code Organization
- ✅ Clear separation of concerns
- ✅ Each module has single responsibility
- ✅ Easier to locate and modify features

### Testing
- ✅ Test individual modules without PyScript
- ✅ Faster test runs
- ✅ Better test isolation

### Maintenance
- ✅ Smaller, focused files (~300-1000 lines each)
- ✅ Reduced cognitive load
- ✅ Easier code review

### Reusability
- ✅ Modules can be imported into other projects
- ✅ Spell system usable standalone
- ✅ Equipment system testable independently

### Future Features
- ✅ Easy to add new entity types
- ✅ Simple to extend logging
- ✅ Export format plugins possible

---

## Current File Sizes

| Module | Lines | Status |
|--------|-------|--------|
| `character.py` | 7,817 | 🔄 Refactoring (was 8,260) |
| `entities.py` | 280 | ✅ Extracted |
| `browser_logger.py` | 85 | ✅ Extracted |
| `character_models.py` | 380 | ⏸️ No changes (external) |
| **Total Extracted** | **~365** | **✅ Done** |
| **Target Reduction** | **-2,500** | **🎯 In progress** |

---

## Next Steps

1. **Phase 2 start:** Extract `spell_data.py` first (data-only module, no dependencies)
2. **Verify:** Run tests after each extraction
3. **Document:** Add docstrings to extracted modules
4. **Review:** Compare line counts and code quality improvements
5. **Commit:** Clean commit message per extraction

---

*Last Updated: Dec 2, 2025*  
*Status: Active Refactoring (Phase 1 Complete)*
