# Spell Class Chooser Unit Tests

## Overview
Comprehensive unit tests for the spell class filter/chooser functionality in the spells tab. These tests verify that the class dropdown correctly extracts available classes from spell data and generates proper HTML options.

## Test File
- **Location**: `tests/test_spell_class_chooser.py`
- **Total Tests**: 23
- **Status**: All passing ✓

## What Gets Tested

### Core Functionality Tests (12 tests)
1. **Class Extraction**
   - Extract unique classes from spell list
   - Handle empty spell lists (fallback to all classes)
   - Handle None inputs
   
2. **HTML Generation**
   - Proper structure (opening/closing tags)
   - Correct value attributes for each class
   - Proper display names (capitalization)
   - No duplicate options
   - Consistent ordering

3. **Specific Classes**
   - Wizard appears in filter
   - Sorcerer appears in filter
   - Cleric appears in filter

### Edge Cases & Validation (11 tests)
4. **Edge Case Handling**
   - Single-class spells (e.g., Warlock-only)
   - Multi-class spells (spells many classes can cast)
   - Unsupported class names filtered out
   - "Any class" option always first

5. **HTML Validity**
   - HTML escaping (special characters like &)
   - Valid and parseable HTML
   - Matching opening/closing tags

6. **Consistency**
   - Multiple calls produce identical output
   - Class options maintain consistent order
   - Respects SUPPORTED_CLASSES list

### Integration Tests (4 tests)
7. **Real-World Scenarios**
   - Wizard and Sorcerer with shared spells
   - Cleric and Paladin with shared spells
   - Warlock unique spells
   - All classes appear in fallback

## Running the Tests

```bash
# Run all spell class chooser tests
pytest tests/test_spell_class_chooser.py -v

# Run a specific test class
pytest tests/test_spell_class_chooser.py::TestSpellClassChooser -v

# Run a specific test
pytest tests/test_spell_class_chooser.py::TestSpellClassChooser::test_generate_filter_includes_wizard -v

# Run with output
pytest tests/test_spell_class_chooser.py -v -s
```

## Test Coverage

The tests verify:
- ✓ Class extraction logic from spell data
- ✓ HTML option generation
- ✓ Display name formatting
- ✓ Value attribute correctness
- ✓ Option ordering consistency
- ✓ No duplicates
- ✓ Edge cases (empty lists, None, unsupported classes)
- ✓ HTML validity and escaping
- ✓ Multi-class spell handling
- ✓ Fallback behavior

## How This Helps Debug the Chooser Issue

If the class chooser stops working:

1. **Run the tests**: `pytest tests/test_spell_class_chooser.py -v`
2. **Check for failures**: Any test failure will pinpoint the issue
3. **Review logs**: Tests print debug info showing what was generated
4. **Common failures and what they indicate**:
   - `test_generate_filter_options_structure` failure → HTML generation broken
   - `test_extract_classes_*` failure → Class extraction logic issue
   - `test_filter_options_maintain_order` failure → Ordering problem
   - `test_filter_respects_supported_classes` failure → Unsupported classes leaking in

## Key Functions Tested

The tests validate these key functions:

1. **`extract_available_classes(spells)`**
   - Extracts unique class keys from spell list
   - Returns all supported classes if none found
   - Filters out unsupported class names

2. **`generate_class_filter_options(spells)`**
   - Creates HTML `<option>` elements for class dropdown
   - Adds "Any class" option first
   - Uses display names for labels
   - Maintains consistent ordering

## Test Data

Tests use realistic spell data with:
- Cleric spells (Cure Wounds, Bless)
- Wizard/Sorcerer spells (Fireball, Magic Missile, Misty Step)
- Warlock spells (Hex, Eldritch Blast)
- Multi-class spells (Misty Step)
- Single-class spells (Warlock-only)

## Updating Tests

When modifying the class chooser code:

1. **Add a new test** if adding new functionality
2. **Run tests** to catch regressions
3. **Update test data** if supported classes change
4. **Verify display names** match SPELL_CLASS_DISPLAY_NAMES

## Example Test Output

```
tests/test_spell_class_chooser.py::TestSpellClassChooser::test_extract_classes_from_spells PASSED
tests/test_spell_class_chooser.py::TestSpellClassChooser::test_generate_filter_options_structure PASSED
tests/test_spell_class_chooser.py::TestSpellClassChooser::test_generate_filter_includes_wizard PASSED
...
======================= 23 passed in 0.68s =======================
```

## Related Code

- **Main code**: `assets/py/character.py` → `populate_spell_class_filter()` function
- **Integration**: Spells tab HTML uses this to populate the class dropdown
- **Related code**: `apply_spell_filters()` uses the selected class value

## Notes

- Tests are unit tests, not integration tests
- They mock the core logic without requiring a browser environment
- Tests are deterministic and should always pass with current code
- Tests serve as documentation for expected behavior
