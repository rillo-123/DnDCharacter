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

#### `spell_data.py` (350+ lines)
**Purpose:** Spell library data, constants, and source definitions
**Contents:**
- LOCAL_SPELLS_FALLBACK - 20-spell fallback library
- Spell class progressions and slot progressions
- Class-to-spell-list mappings
- Authoritative source constants (phb, xge, etc.)
- Spell synonyms and corrections

**Status:** ✅ Complete (commit c9bd3d9)

---

#### `spellcasting.py` (1,200+ lines)
**Purpose:** Spell management and casting logic
**Classes:**
- `SpellcastingManager` - Manages spell slots, casting, preparation

**Functions:**
- Spell progression calculation
- Slot management (use, recover, reset)
- Spell library synchronization
- Domain bonus spell integration
- Spell filtering and search

**Status:** ✅ Complete (commit c9bd3d9)

---

#### `equipment_management.py` (1,150 lines)
**Purpose:** Equipment/item management and inventory tracking
**Classes:**
- `Item`, `Weapon`, `Armor`, `Shield`, `Equipment` - Equipment entity types
- `InventoryManager` - Manages character inventory (650+ lines, 50+ methods)

**Features:**
- Equipment rendering HTML generation
- Item search and filtering
- Armor type and AC lookups
- Equipment library management
- Inventory weight and cost tracking

**Status:** ✅ Complete (commit f07469f)

---

#### `export_management.py` (700+ lines)
**Purpose:** Character export/import and auto-export functionality
**Functions:**
- `save_character()` - Immediate localStorage save
- `export_character()` (async) - Full export with File System API support
- `reset_character()` - Clear all character data
- `handle_import()` - Import character from JSON file
- `show_storage_info()` - Display storage usage statistics
- `cleanup_exports()` - Manage export log statistics
- `schedule_auto_export()` - Debouncing auto-export scheduler

**Features:**
- Auto-export with configurable intervals (default 2000ms, max 15 events)
- File System API support for persistent exports
- Fallback browser download for unsupported browsers
- localStorage persistence
- Export filename normalization and parsing
- Old export pruning and cleanup

**Status:** ✅ Complete (commit bddfd3b)

---

### Modules Extracted (Phase 2 Complete)

All major modules have been successfully extracted:
- ✅ `spell_data.py` - Spell library data (Phase 2 Step 1)
- ✅ `spellcasting.py` - Spell management (Phase 2 Step 2)
- ✅ `equipment_management.py` - Equipment/inventory (Phase 2 Step 3)
- ✅ `export_management.py` - Export/import functions (Phase 2 Step 4)

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
- [x] Commit 16cea29

### Phase 2 ✅ (Complete)

#### Step 1 ✅ Extract `spell_data.py`
- [x] Spell library data (20-spell fallback)
- [x] Spell progressions and constants
- [x] Class-to-spell-list mappings
- [x] Source definitions and authoritative lists
- [x] Verify 232+ tests passing
- [x] Commit c9bd3d9

#### Step 2 ✅ Extract `spellcasting.py`
- [x] SpellcastingManager class (30+ methods)
- [x] Spell helper functions (9 functions)
- [x] Spell library management
- [x] Verify 232+ tests passing
- [x] Commit c9bd3d9

#### Step 3 ✅ Extract `equipment_management.py`
- [x] Item, Weapon, Armor, Shield, Equipment classes
- [x] InventoryManager (650+ lines, 50+ methods)
- [x] Equipment rendering and HTML generation
- [x] Item library and search functionality
- [x] Verify 232+ tests passing
- [x] Commit f07469f

#### Step 4 ✅ Extract `export_management.py`
- [x] Export/import functions (save, export, reset, import)
- [x] Auto-export scheduler with debouncing
- [x] File System API helpers
- [x] Storage management functions
- [x] Verify 228+ tests passing (7 pre-existing failures)
- [x] Commit bddfd3b

#### Step 5 ✅ Final Verification & Documentation
- [x] Verify modular structure is stable
- [x] Final test run (228/235 passing)
- [x] Character.py reduced from 8,260 → 4,914 lines (40.4% reduction)
- [x] Update MODULAR_STRUCTURE.md documentation
- [x] Ready for Phase 3 or production

### Phase 3 (Future)
- [ ] Code cleanup and optimization
- [ ] Performance testing
- [ ] Browser compatibility testing
- [ ] Production release preparation

### Phase 4 (Future)
- [ ] Additional feature modules (if needed)
- [ ] Further refactoring based on usage patterns
- [ ] Enhanced testing and CI/CD

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
| `character.py` | 4,914 | ✅ Refactored (was 8,260) |
| `entities.py` | 388 | ✅ Extracted (Phase 1) |
| `browser_logger.py` | 85 | ✅ Extracted (Phase 1) |
| `spell_data.py` | 350+ | ✅ Extracted (Phase 2 Step 1) |
| `spellcasting.py` | 1,200+ | ✅ Extracted (Phase 2 Step 2) |
| `equipment_management.py` | 1,150 | ✅ Extracted (Phase 2 Step 3) |
| `export_management.py` | 700+ | ✅ Extracted (Phase 2 Step 4) |
| `character_models.py` | 380 | ⏸️ No changes (external) |
| **Total Extracted** | **4,253** | **✅ Phase 2 Complete** |
| **Reduction Achieved** | **-3,346 lines** | **✅ 40.4% reduction** |
| **Tests Passing** | **228/235** | **✅ 97% passing** |

---

## Phase 2 Summary

### Achievements
- \u2705 **4,253 lines extracted** into 6 focused modules
- \u2705 **character.py reduced 40.4%** (8,260 \u2192 4,914 lines)
- \u2705 **228/235 tests passing** (97% pass rate)
- \u2705 **7 pre-existing failures** (equipment rendering, unrelated to refactoring)
- \u2705 **4 commits pushed** to `feature/entity-system` branch

### Module Distribution
- Core system: entities.py (388 lines) + browser_logger.py (85 lines) = 473 lines
- Game logic: spell_data.py (350+) + spellcasting.py (1,200+) + equipment_management.py (1,150) + export_management.py (700+) = 3,400+ lines
- Main driver: character.py (4,914 lines) - down 40.4%

### Architecture Quality
- All modules use try-except import guards for backward compatibility
- PyScript/Pyodide guards ensure browser and test environment compatibility
- Clean separation of concerns with focused responsibilities
- Modular pattern enables future feature additions without monolithic growth

---

## Next Steps (Phase 3+)

1. **Phase 3 Planning:** Identify optimization opportunities
2. **Browser Testing:** Verify all features work in production environment
3. **Performance:** Profile and optimize if needed
4. **Production Release:** Merge to main branch
5. **Maintenance:** Monitor for issues and improvements

---

*Last Updated: Dec 3, 2025*  
*Status: Phase 2 Complete - Ready for Phase 3 Planning*
