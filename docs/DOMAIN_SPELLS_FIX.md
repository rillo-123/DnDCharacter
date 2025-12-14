# Domain Spells Fix - Complete Summary

## Problem Statement
Domain spells were not appearing for clerics when selecting a domain. The console showed:
```
PySheet: unable to add spell 'bless' – not in library
DEBUG: add_spell(bless, is_domain_bonus=True) returned: None
```

Despite domain spells being correctly defined and retrieved, they failed to add to the prepared spells list.

## Root Cause
The issue was **spell source validation**, not spell lookup:

1. **What worked**: 
   - Domain spells were defined in `spell_data.py`
   - `get_domain_bonus_spells()` correctly retrieved domain spells
   - `get_spell_by_slug()` successfully found spells in the library
   - Spells were in the `spell_map`

2. **What failed**:
   - The `add_spell()` method calls `is_spell_source_allowed()` to validate spell sources
   - All spells from `LOCAL_SPELLS_FALLBACK` had source: `"5e Core Rules"`
   - The allowed sources list only included: `PHB`, `TCE`, `XGE`, and their full names
   - **Solution**: `"5e Core Rules"` was not recognized as a valid source

## Solution
Updated `is_spell_source_allowed()` in `assets/py/spell_data.py`:

```python
# Before
authoritative_phrases = {
    "player's handbook",
    "players handbook",
    "tasha's cauldron",
    "tashas cauldron",
    "xanathar's guide",
    "xanathars guide",
    "srd",
}

# After
authoritative_phrases = {
    "player's handbook",
    "players handbook",
    "tasha's cauldron",
    "tashas cauldron",
    "xanathar's guide",
    "xanathars guide",
    "5e core",  # NEW: Matches "5e Core Rules"
    "srd",
}
```

## Files Modified

### 1. `assets/py/spell_data.py`
- **Change**: Added `"5e core"` to the `authoritative_phrases` set in `is_spell_source_allowed()`
- **Effect**: Spells with source "5e Core Rules" are now accepted
- **Lines**: ~575 in function `is_spell_source_allowed()`

### 2. `assets/py/spellcasting.py`
- **Changes**:
  - Enhanced `get_spell_by_slug()` with debug logging (lines 1026-1071)
  - Enhanced `set_spell_library_data()` with debug logging (lines 1265-1280)
- **Effect**: Better visibility into spell lookup and library loading for debugging

## Verification

### Test Results
All integration tests pass:
- ✅ Spell library loading (23 spells in fallback)
- ✅ Spell lookup via `get_spell_by_slug()`
- ✅ Domain spell addition to prepared spells
- ✅ Export/import of domain spells with `is_domain_bonus` flag preserved

### Test Files
- `tests/test_spell_library_debug.py` - Tests spell library and lookup
- `tests/test_domain_spells_integration.py` - Full workflow tests

### Domain Spells Verified (21 total)
Life domain at level 9:
- beacon-of-hope, bless, cure-wounds, death-ward, guardian-of-faith, lesser-restoration, mass-cure-wounds, raise-dead, revivify, spiritual-weapon

Plus 11 additional spells used by other domains (confusion, detect-magic, faerie-fire, guiding-bolt, healing-word, hold-person, insect-plague, prayer-of-healing, sacred-flame, shatter, vicious-mockery)

## How to Test

1. **In Python environment**:
   ```bash
   python tests/test_domain_spells_integration.py
   ```

2. **In browser** (requires server running on port 8080):
   - Set up a Level 9 Cleric character
   - Set domain to "Life"
   - Observe that domain spells are added to prepared spells
   - Check browser console for debug logs showing spell loading

## Debug Logging
The enhanced debug logging will show:
```
DEBUG set_spell_library_data: Built spell_map with 23 spells
DEBUG set_spell_library_data: Domain spells present: ['bless', 'cure-wounds', ...], missing: []
DEBUG get_spell_by_slug: Found 'bless' in spell_map (size=23, spells_list=23)
DEBUG add_spell: Found spell record for bless
DEBUG add_spell: Checking source for bless: source='5e Core Rules'
DEBUG add_spell: Successfully added bless. Total prepared: 1
```

## Impact
- **User-facing**: Domain spells now properly display when a cleric selects a domain
- **Code quality**: Added logging for better debugging of spell loading issues
- **Backward compatibility**: No breaking changes; all existing functionality preserved

## Future Improvements
- Consider making the source validation more flexible (e.g., lowercase normalization)
- Add more sources to the allowed list as needed
- Consider externalizing the allowed sources to a configuration file
