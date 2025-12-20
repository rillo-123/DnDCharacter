# EntityManager Pattern - Architecture Documentation

## Overview

The EntityManager pattern is a design pattern for managing game entities (Weapons, Armor, ProfBonus, etc.) with clean separation between data and display logic.

## Pattern Components

### 1. Base EntityManager Class

Located in: [entity_manager.py](entity_manager.py)

```python
class EntityManager:
    """Base class for all entity managers."""
    
    def __init__(self, entity_data: Dict = None):
        self.entity = entity_data or {}
    
    @property
    def final_display_value(self) -> str:
        """Subclasses implement this to return the display value."""
        raise NotImplementedError
    
    def set_entity(self, entity_data: Dict):
        """Update the entity data."""
        self.entity = entity_data
    
    def get_entity(self) -> Dict:
        """Get the entity data."""
        return self.entity
    
    def is_valid(self) -> bool:
        """Subclasses can override to validate entity."""
        return bool(self.entity)
```

**Key Design Principle:** The manager has exactly one job - calculate and format display values from raw entity data.

### 2. WeaponEntity Implementation

Located in: [weapons_manager.py](weapons_manager.py)

```python
class WeaponEntity(EntityManager):
    """Represents a single weapon with display properties."""
    
    @property
    def final_display_value(self) -> str:
        return self.final_name
    
    @property
    def final_name(self) -> str:
        return self.entity.get("name", "Unknown")
    
    @property
    def final_tohit(self) -> str:
        # Returns "+3", "-1", or "—"
        to_hit = self._calculate_tohit()
        if to_hit == 0:
            return "—"
        elif to_hit > 0:
            return f"+{to_hit}"
        else:
            return str(to_hit)
    
    @property
    def final_damage(self) -> str:
        # Returns "1d8 slashing +1" format
        ...
    
    @property
    def final_range(self) -> str:
        # Returns "30/120" or "Melee" or "—"
        ...
    
    @property
    def final_properties(self) -> str:
        # Returns "Finesse, Light" or "—"
        ...
```

**Key Design Features:**
- Each property returns a formatted string ready for display
- Properties handle JSON parsing, validation, and fallbacks
- No HTML generation - just strings
- Easy to test in isolation
- Easy to reuse display properties in different contexts

### 3. WeaponsCollectionManager

The orchestrator that manages multiple weapon entities and renders them to HTML:

```python
class WeaponsCollectionManager:
    """Manages a collection of weapon entities and renders them."""
    
    def __init__(self, inventory_manager):
        self.inventory_manager = inventory_manager
        self.weapons: List[WeaponEntity] = []
    
    def render(self):
        """Render all weapons to grid."""
        self._build_weapon_entities()
        self._clear_weapon_rows()
        if self.weapons:
            self._render_weapon_rows()
        else:
            self._show_empty_state()
    
    def _create_weapon_row(self, weapon: WeaponEntity):
        """Create row using weapon display properties."""
        row = document.createElement("tr")
        
        name_td = document.createElement("td")
        name_td.textContent = weapon.final_name  # Use property
        row.appendChild(name_td)
        
        to_hit_td = document.createElement("td")
        to_hit_td.textContent = weapon.final_tohit  # Use property
        row.appendChild(to_hit_td)
        
        # ... etc for damage, range, properties
        return row
```

**Key Design Features:**
- Manager doesn't calculate display values - it reads them from entities
- Rendering becomes trivial - just map entity properties to HTML cells
- Easy to change where things render (table, JSON, API response) without changing entity logic

## Why This Pattern?

### Before (Fragmented)
```
character.py
├─ calculate_tohit()
├─ extract_damage()
├─ render_equipped_attack_grid()
└─ Multiple different functions doing similar things

equipment_management.py
├─ Duplicate damage parsing
├─ Duplicate range extraction
└─ Cross-module calls via _CHAR_MODULE_REF
```

**Problems:**
- Logic scattered across files
- Duplicate code for extracting/calculating same values
- Hard to test individual calculations
- Hard to reuse display logic in other contexts
- Cross-module dependencies fragile

### After (EntityManager Pattern)
```
entity_manager.py
└─ EntityManager (base class for all entities)

weapons_manager.py
├─ WeaponEntity (single weapon with display properties)
├─ WeaponsCollectionManager (orchestrates rendering)
└─ Properties: final_name, final_tohit, final_damage, etc.

[Future] armor_manager.py
├─ ArmorEntity (extends EntityManager)
└─ Properties: final_ac, final_defense_bonus, etc.

[Future] profbonus_manager.py
├─ ProfBonusEntity (extends EntityManager)
└─ Properties: final_bonus_value, final_category, etc.
```

**Benefits:**
- Single source of truth for weapon display logic
- Easy to test entity independently from rendering
- Easy to reuse same display properties in multiple places
- Easy to extend (add new entity types following the pattern)
- Clear separation: Entity = logic, Manager = orchestration, View = HTML

## Implementation Checklist

### Current Status ✅
- [x] Base EntityManager class created
- [x] WeaponEntity created with display properties
  - [x] final_name
  - [x] final_tohit (includes ability mod + proficiency + bonus)
  - [x] final_damage (includes damage type and bonus)
  - [x] final_range
  - [x] final_properties
- [x] WeaponsCollectionManager renders using entity properties
- [x] All 32 weapons tests passing
- [x] All 580 total tests passing
- [x] Character initialization passes character_stats to weapons manager

### Next Steps 🔄
1. Create ArmorEntity extending EntityManager
   - Properties: final_ac, final_defense_type, final_material
   - Manager: ArmorCollectionManager or single ArmorManager
2. Create ProfBonusEntity extending EntityManager
   - Property: final_display_value (the bonus value)
   - Manager: ProfBonusManager
3. Implement same pattern for other game entities as needed

## Testing Pattern

Each EntityManager subclass should have tests like:

```python
def test_weapon_entity_final_tohit():
    weapon = WeaponEntity(
        {"name": "Longsword"},
        {"str": 14, "dex": 10, "proficiency": 2}
    )
    assert weapon.final_tohit == "+4"  # (14-10)//2 + 2 = 4

def test_weapon_entity_final_damage():
    weapon = WeaponEntity(
        {"name": "Longsword", "damage": "1d8", "damage_type": "slashing"}
    )
    assert weapon.final_damage == "1d8 slashing"

def test_weapons_collection_manager_render():
    manager = WeaponsCollectionManager(inventory)
    manager.render()
    # Verify grid rows were created for each weapon
```

## Migration Path

If updating existing code to use EntityManager pattern:

1. Identify the entity type (Weapon, Armor, etc.)
2. Create EntitySubclass extending EntityManager with display properties
3. Create CollectionManager or SingleEntityManager to render
4. Update initialization to pass necessary stats (proficiency, abilities, etc.)
5. Update managers to call entity.property instead of calculating in render
6. Test thoroughly - each layer can be tested independently

## File Locations

- [entity_manager.py](entity_manager.py) - Base class (40 lines)
- [weapons_manager.py](weapons_manager.py) - Weapons implementation (380 lines)
  - WeaponEntity: 155 lines
  - WeaponsCollectionManager: 180 lines
  - Global initialization: 20 lines

Total: ~420 lines to manage all weapon display logic with clean tests and documentation.
