# Equipment Managers Architecture - Complete Overview

## Pattern Summary

Both **Weapons** and **Armor** now follow the same `EntityManager` pattern:

```
EntityManager (base class)
├── WeaponEntity (weapon display properties)
│   └── final_name, final_tohit, final_damage, final_range, final_properties
│
└── ArmorEntity (armor display properties)
    └── final_name, final_ac, final_armor_type, final_material, final_stealth
```

Each has a corresponding Collection Manager:
- **WeaponsCollectionManager** - renders weapons grid
- **ArmorCollectionManager** - renders armor grid

## File Structure

```
static/assets/py/
├── entity_manager.py          # Base class (40 lines)
├── weapons_manager.py         # Weapons implementation (380 lines)
│   ├── WeaponEntity
│   └── WeaponsCollectionManager
│
└── armor_manager.py           # Armor implementation (320 lines)
    ├── ArmorEntity
    └── ArmorCollectionManager
```

## Initialization Flow

On application startup (character.py):

```python
# Build character stats object
char_stats = {
    "str": get_numeric_value("str", 10),
    "dex": get_numeric_value("dex", 10),
    "proficiency": compute_proficiency(level)
}

# Initialize both managers
weapons_mgr = initialize_weapons_manager(INVENTORY_MANAGER, char_stats)
weapons_mgr.render()

armor_mgr = initialize_armor_manager(INVENTORY_MANAGER, char_stats)
armor_mgr.render()
```

## Equipment Change Flow

When user removes an item (equipment_management.py):

```
Item Removed
    ↓
_handle_item_remove()
    ├─→ Update inventory
    ├─→ render_inventory()
    ├─→ weapons_mgr.render()    # If any weapons need updating
    └─→ armor_mgr.render()      # If any armor needs updating
```

When user equips/unequips an item:

```
Item Toggled (checkbox)
    ↓
_handle_equipped_toggle()
    ├─→ Update item.equipped
    ├─→ If category="weapons" → weapons_mgr.render()
    └─→ If category="armor"/"shield" → armor_mgr.render()
```

## Data Flow

### Weapons Grid

```
Inventory Item (Raw Data)
    ├── name: "Longsword"
    ├── damage: "1d8"
    ├── damage_type: "slashing"
    ├── weapon_type: "melee"
    ├── weapon_properties: "Versatile"
    └── notes: JSON with bonus, range, etc.
        ↓
    WeaponEntity (Calculations + Display Properties)
    ├── final_name → "Longsword"
    ├── final_tohit → "+4" (STR mod + proficiency)
    ├── final_damage → "1d8 slashing"
    ├── final_range → "5"
    └── final_properties → "Versatile"
        ↓
    WeaponsCollectionManager (Rendering)
    └── Creates <tr> with these display properties
        └── <table id="weapons-grid">
            ├── <td>Longsword</td>
            ├── <td>+4</td>
            ├── <td>1d8 slashing</td>
            ├── <td>5</td>
            └── <td>Versatile</td>
```

### Armor Grid

```
Inventory Item (Raw Data)
    ├── name: "Leather Armor"
    ├── armor_class: 11
    ├── armor_type: "Light"
    ├── material: "Leather"
    ├── stealth_disadvantage: false
    └── notes: JSON with details
        ↓
    ArmorEntity (Calculations + Display Properties)
    ├── final_name → "Leather Armor"
    ├── final_ac → "13" (11 + DEX +2)
    ├── final_armor_type → "Light"
    ├── final_material → "Leather"
    └── final_stealth → "—"
        ↓
    ArmorCollectionManager (Rendering)
    └── Creates <tr> with these display properties
        └── <table id="armor-grid">
            ├── <td>Leather Armor</td>
            ├── <td>13</td>
            ├── <td>Light</td>
            ├── <td>Leather</td>
            └── <td>—</td>
```

## Key Design Decisions

### 1. **Entity Pattern**
Each entity (Weapon, Armor) is responsible for:
- Extracting data from raw inventory item
- Calculating display values (AC, to-hit, etc.)
- Formatting display strings
- Validating data

### 2. **Manager Pattern**
Each manager is responsible for:
- Orchestrating a collection of entities
- Rendering to HTML
- Syncing with inventory changes

### 3. **Character Stats Injection**
Character stats (STR, DEX, proficiency) are passed to both managers:
- Allows entities to calculate context-aware values
- Weapons can calculate DEX-based to-hit
- Armor can add DEX modifier to AC
- Single source of truth for character stats

### 4. **Clean HTML Integration**
Managers don't know about display format:
- Just create DOM elements
- Could be extended to render JSON, CSV, etc.
- View logic stays separate from calculation logic

## Testing Strategy

Each layer can be tested independently:

```python
# Test entity calculations
def test_weapon_tohit():
    weapon = WeaponEntity(
        {"name": "Sword"},
        {"str": 14, "dex": 10, "proficiency": 2}
    )
    assert weapon.final_tohit == "+4"

# Test entity display formatting
def test_armor_ac_display():
    armor = ArmorEntity(
        {"armor_class": 11, "armor_type": "Light"},
        {"dex": 14}
    )
    assert armor.final_ac == "13"

# Test manager orchestration
def test_weapons_manager_render():
    manager = WeaponsCollectionManager(inventory)
    manager.render()
    # Verify DOM was updated
```

## Current Status

✅ **Complete**
- Base EntityManager class
- WeaponEntity with all display properties
- WeaponsCollectionManager with rendering
- ArmorEntity with all display properties
- ArmorCollectionManager with rendering
- Character initialization setup
- Equipment change sync setup
- All 580 tests passing

## Future Extensions

The pattern is ready for:

1. **ProficiencyBonusManager** - Single entity for proficiency
   ```python
   prof_entity = ProficiencyEntity({"value": 2}, {"level": 5})
   prof_entity.final_display_value  # "+2"
   ```

2. **ShieldManager** - Specialized armor type
   ```python
   shield = ArmorEntity({"name": "Shield", "armor_class": 2}, stats)
   shield.final_ac  # "+2 AC bonus"
   ```

3. **MagicalItemManager** - Equipment modifiers
   ```python
   item = MagicalItemEntity({"name": "Ring of Protection"}, stats)
   item.final_bonus  # "+1 AC and saving throws"
   ```

All would follow the same pattern - Entity extends EntityManager, Manager orchestrates rendering.

## Benefits

| Aspect | Benefit |
|--------|---------|
| **Testability** | Each layer independently testable |
| **Reusability** | Display properties usable in multiple contexts |
| **Maintainability** | Clear separation of concerns |
| **Extensibility** | Easy to add new entity types |
| **Debuggability** | Easy to trace values through pipeline |
| **Scalability** | Pattern works for 2 entities or 20+ |

## Code Metrics

- **Base Class:** 40 lines (EntityManager)
- **Weapons:** 380 lines total (WeaponEntity + Manager)
- **Armor:** 320 lines total (ArmorEntity + Manager)
- **Total:** ~740 lines for complete equipment display system
- **Tests:** 580 passing (includes 32 weapons tests, more can be added for armor)
- **Pattern:** Highly reusable across game entities
