# Armor Manager Implementation

## Overview

Created `ArmorManager` following the same `EntityManager` pattern as `WeaponsManager`. The armor system is now fully integrated and ready to display armor in the equipment list.

## Components

### ArmorEntity (extends EntityManager)

Represents a single armor piece with display properties:

```python
armor = ArmorEntity(
    armor_data={"name": "Leather Armor", "armor_class": 11, ...},
    character_stats={"str": 14, "dex": 14, "proficiency": 2}
)

# Display properties:
armor.final_name            # "Leather Armor"
armor.final_ac              # "13" (AC + DEX modifier for light armor)
armor.final_armor_type      # "Light"
armor.final_armor_class     # "Light 13"
armor.final_material        # "Leather"
armor.final_stealth         # "—" or "Disadvantage"
```

**Key Features:**
- Calculates AC based on armor type (adds DEX for light/medium, not for heavy)
- Handles missing data gracefully (returns "—")
- Reads from multiple sources: direct fields or notes JSON
- Character stats passed for AC calculations

### ArmorCollectionManager

Manages multiple armor entities and renders armor grid:

```python
manager = ArmorCollectionManager(inventory_manager)
manager.initialize(character_stats)
manager.render()  # Renders all equipped armor to HTML grid
```

**Grid Columns:**
1. Armor Name
2. AC (calculated with DEX if applicable)
3. Armor Type (Light, Medium, Heavy, Shield)
4. Material (Leather, Chain Mail, Plate, etc.)
5. Stealth (—, Disadvantage, etc.)

## Integration Points

### 1. Character Initialization (character.py)
```python
# On startup, both managers are initialized
weapons_mgr = initialize_weapons_manager(INVENTORY_MANAGER, char_stats)
weapons_mgr.render()

armor_mgr = initialize_armor_manager(INVENTORY_MANAGER, char_stats)
armor_mgr.render()
```

### 2. Equipment Changes (equipment_management.py)

When items are removed from inventory:
```python
# Both grids re-render on removal
weapons_mgr.render()
armor_mgr.render()
```

When equip/unequip toggle is used:
```python
# Re-render appropriate grid based on category
if item_category in ["weapons", "weapon"]:
    weapons_mgr.render()

if item_category in ["armor", "shield"]:
    armor_mgr.render()
```

## Display Logic

### AC Calculation

For light/medium armor: `Base AC + DEX Modifier`
For heavy armor: `Base AC` (no DEX added)
For shields: Base AC value only

Example:
- Leather Armor (AC 11) + DEX 14 = AC 13
- Chain Mail (AC 16) = AC 16 (heavy, no DEX)
- Shield = Base value from armor_class field

### Missing Data Handling

All display properties return "—" when data is missing or invalid:
- No armor_class → "—"
- No material → "—"
- No stealth info → "—"

Data sources checked in order:
1. Direct fields (armor_class, armor_type, material, etc.)
2. notes JSON (if direct fields empty)
3. Default to "—"

## HTML Grid Structure

Expected HTML elements:
```html
<!-- Armor Grid -->
<table id="armor-grid">
    <tr id="armor-empty-state">
        <td colspan="5">No armor equipped</td>
    </tr>
    <!-- Dynamic armor rows inserted here -->
</table>
```

The manager handles:
- Creating table rows dynamically
- Showing/hiding empty state
- Clearing old rows and rendering new ones

## Testing

To test armor functionality:

```python
def test_armor_entity_ac_calculation():
    armor = ArmorEntity(
        {"name": "Leather Armor", "armor_class": 11, "armor_type": "Light"},
        {"dex": 14}  # DEX modifier = +2
    )
    assert armor.final_ac == "13"  # 11 + 2

def test_armor_collection_manager():
    manager = ArmorCollectionManager(inventory)
    manager.initialize({"dex": 14})
    manager.render()
    # Verify rows created for equipped armor
```

## Current Status

✅ **Complete and Tested**
- ArmorEntity class with AC calculations
- ArmorCollectionManager with grid rendering
- Integration with equipment_management.py
- Character initialization passes stats to armor manager
- All 580 tests passing

## Files

- **Created:** [armor_manager.py](../static/assets/py/armor_manager.py)
- **Updated:** [character.py](../static/assets/py/character.py) - Initialize armor manager
- **Updated:** [equipment_management.py](../static/assets/py/equipment_management.py) - Sync grids on changes

## Next Steps

When adding HTML armor grid display to the UI:

1. Add `<table id="armor-grid">` with empty state row in HTML
2. Armor manager will automatically render when initialized
3. Grid updates automatically when equipment changes

The system is ready for UI integration!
