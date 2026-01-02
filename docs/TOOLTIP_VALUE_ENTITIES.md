# Tooltip Value Entities - Architecture & Usage

**Status**: ✅ 34 tests passing | Ready for integration

## Overview

The `TooltipValue` entity system provides a reusable, inheritance-based framework for calculating and rendering tooltips across the character sheet with consistent styling and structure.

**Key Benefits:**
- 🔄 **DRY Principle**: Reusable tooltip logic across all character stats
- 📊 **Consistent UX**: Uniform tooltip format and styling everywhere
- 🧪 **Testable**: Full unit test coverage (34 tests)
- 🏗️ **Extensible**: Easy to add new tooltip types via inheritance
- 📦 **Modular**: Separate module keeps character.py cleaner

## Architecture

### Class Hierarchy

```
TooltipValue (base class)
├── AbilityScoreValue      (STR, DEX, CON, INT, WIS, CHA)
├── SaveValue              (ability saves with proficiency)
├── SkillValue             (skill checks with expertise)
├── WeaponToHitValue       (weapon attack bonuses)
└── DamageValue            (weapon damage with modifiers)
```

### Base Class: `TooltipValue`

```python
class TooltipValue:
    """Base class for values that display tooltips with breakdown."""
    
    # Properties
    - label: str           # Display label (e.g., "STR", "Attack Bonus")
    - total: int           # Calculated total value
    - components: List     # List of (label, value) tuples for breakdown
    
    # Methods
    - add_component(label, value) → self  # Add tooltip row (chainable)
    - recalculate_total() → int           # Sum all components
    - format_bonus(value) → str           # Format as +3, -1, or —
    - generate_tooltip_html() → str       # Create HTML tooltip
```

### Specialized Classes

#### AbilityScoreValue
```python
asv = AbilityScoreValue(ability="str", base_score=15, race_bonus=2)
# total = 17
# components = [("Base STR", 15), ("Race bonus", 2)]
```

#### SaveValue
```python
sv = SaveValue(ability="dex", ability_mod=2, proficiency=3, 
              is_proficient=True, item_modifiers=1)
# total = 6 (2 + 3 + 1)
# components = [("Ability mod (DEX)", 2), ("Proficiency", 3), ...]
```

#### SkillValue
```python
sk = SkillValue(skill_name="Stealth", ability="dex", ability_mod=3,
               proficiency=2, is_expertise=True)
# total = 7 (3 + 2*2 expertise)
# components = [("DEX mod", 3), ("Expertise", 4)]
```

#### WeaponToHitValue
```python
w2h = WeaponToHitValue(weapon_name="Longsword +1", ability="str",
                      ability_mod=3, proficiency=2, weapon_bonus=1)
# total = 6 (3 + 2 + 1)
# components = [("STR mod", 3), ("Proficiency", 2), ("Weapon bonus", 1)]
```

#### DamageValue
```python
dmg = DamageValue(damage_dice="1d8", damage_type="slashing",
                 ability_mod=3, weapon_bonus=1)
# total = 4 (3 + 1)
# label = "1d8 slashing"
```

## HTML Output Format

All tooltips generate styled HTML using the `stat-tooltip multiline` CSS classes:

```html
<div class="stat-tooltip multiline">
    <div class="tooltip-row">
        <span class="tooltip-label">STR mod</span>
        <span class="tooltip-value">+3</span>
    </div>
    <div class="tooltip-row">
        <span class="tooltip-label">Proficiency</span>
        <span class="tooltip-value">+2</span>
    </div>
    <div class="tooltip-row">
        <span class="tooltip-label">Weapon bonus</span>
        <span class="tooltip-value">+1</span>
    </div>
</div>
```

**CSS Styling** (from styles.css):
- `.stat-tooltip`: Positioned tooltip with arrow, appears on hover
- `.tooltip-row`: Flexbox layout for label-value pairs
- `.tooltip-label`: Gray text (94a3b8)
- `.tooltip-value`: Blue bold text (60a5fa)

## Usage Examples

### Calculate Character Stats with Tooltips

```python
from tooltip_values import AbilityScoreValue, SaveValue, SkillValue

# Ability Scores
str_val = AbilityScoreValue(ability="str", base_score=15, race_bonus=2)
print(f"STR Total: {str_val.total}")        # 17
print(str_val.generate_tooltip_html())      # HTML tooltip

# Saves (with proficiency)
dex_save = SaveValue(
    ability="dex",
    ability_mod=2,
    proficiency=2,
    is_proficient=True,
    item_modifiers=0
)
print(f"DEX Save: {dex_save.format_bonus(dex_save.total)}")  # +4

# Skills (with expertise)
stealth = SkillValue(
    skill_name="Stealth",
    ability="dex",
    ability_mod=2,
    proficiency=2,
    is_expertise=True
)
print(f"Stealth Total: {stealth.total}")    # 6 (2 + 2*2)
```

### Polymorphic Rendering

```python
# All tooltip values can be used the same way
values = [
    AbilityScoreValue(ability="str", base_score=15),
    SaveValue(ability="dex", ability_mod=2, proficiency=2, is_proficient=True),
    SkillValue(skill_name="Acrobatics", ability="dex", ability_mod=3),
    WeaponToHitValue(weapon_name="Longsword", ability="str", 
                    ability_mod=3, proficiency=2),
]

for val in values:
    print(f"{val.label}: {val.format_bonus(val.total)}")
    print(val.generate_tooltip_html())
```

## Test Coverage

All 34 tests in `tests/test_tooltip_values.py`:

- ✅ Base `TooltipValue` functionality (7 tests)
- ✅ `AbilityScoreValue` with all abilities (4 tests)
- ✅ `SaveValue` with proficiency and items (4 tests)
- ✅ `SkillValue` with expertise and race bonuses (4 tests)
- ✅ `WeaponToHitValue` with bonuses (5 tests)
- ✅ `DamageValue` with modifiers (4 tests)
- ✅ `format_tooltip_html` utility (4 tests)
- ✅ Inheritance chain verification (2 tests)

**Run tests:**
```bash
pytest tests/test_tooltip_values.py -v
```

## Integration Points

### Current Integration
- **Weapons Grid**: To-hit tooltips for equipped weapons (ready for HTML tooltip upgrade)

### Future Integrations
- **Ability Scores Tab**: Refactor to use `AbilityScoreValue`
- **Saves**: Refactor to use `SaveValue`
- **Skills**: Refactor to use `SkillValue`
- **Damage Calculations**: Use `DamageValue` for spell damage, weapon damage, etc.

## Migration Guide

### Old Pattern (Simple Text Tooltip)
```python
tooltip = f"{ability_mod:+d} ({ability_name}) + {proficiency:+d} (Prof)"
element.title = tooltip
```

### New Pattern (Entity-Based)
```python
from tooltip_values import WeaponToHitValue

w2h = WeaponToHitValue(
    weapon_name="Longsword",
    ability="str",
    ability_mod=3,
    proficiency=2,
    weapon_bonus=0
)

html_tooltip = w2h.generate_tooltip_html()
element.innerHTML = html_tooltip
```

## Benefits of This Approach

1. **Single Source of Truth**: Tooltip logic centralized in one class
2. **Reusability**: Same tooltip rendering for all stats
3. **Testability**: 34 unit tests ensure correctness
4. **Extensibility**: Add new tooltip types by inheriting from `TooltipValue`
5. **Consistency**: All tooltips follow same visual pattern
6. **Maintenance**: Changes to tooltip format only need to be made once

## Next Steps

1. ✅ Implement `TooltipValue` hierarchy (DONE)
2. ✅ Add comprehensive tests (DONE)
3. ⏳ Integrate `WeaponToHitValue` into weapons grid rendering
4. ⏳ Upgrade weapon tooltips to use HTML format (not just text)
5. ⏳ Refactor ability scores to use `AbilityScoreValue`
6. ⏳ Refactor saves to use `SaveValue`
7. ⏳ Refactor skills to use `SkillValue`
