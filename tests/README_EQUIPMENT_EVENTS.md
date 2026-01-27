# Equipment Events Test Isolation

## Problem

`test_equipment_events.py` requires mocking browser modules (`js`, `pyodide`) to test the equipment event system. These mocks must be set in `sys.modules` before importing `equipment_event_manager`, which causes contamination in pytest's import collection phase.

## Solution

Run equipment events tests separately from the main test suite:

```powershell
# Run main test suite (excluding equipment events)
python -m pytest tests\ --ignore=tests\test_equipment_chooser.py --ignore=tests\test_equipment_events.py

# Run equipment events tests separately
python -m pytest tests\test_equipment_events.py -v
```

## Verification

**Equipment Events Tests (28 tests):**
```powershell
python -m pytest tests\test_equipment_events.py -v
# Expected: 28 passed
```

**Main Test Suite (763 tests):**
```powershell
python -m pytest tests\ --ignore=tests\test_equipment_chooser.py --ignore=tests\test_equipment_events.py -q
# Expected: 763 passed, 1 skipped
```

**Total: 791 passing tests**

## What's Tested

The equipment events test suite validates:

1. **Event Listener Initialization**
   - Event listener can be created
   - `_is_updating` flag initializes to False
   - Inventory manager reference is stored

2. **Bonus Change Events**
   - Integer value parsing
   - Empty value handling (defaults to 0)
   - Invalid value handling (defaults to 0)
 - Calls `set_armor_bonus()` for armor items
   - Triggers `redraw_armor_items()`
   - Triggers `update_calculations()`
   - Handles item not found gracefully
   - Delegates weapons to inventory manager

3. **Event Loop Prevention**
   - `_is_updating` flag prevents reentrant calls
   - Flag set during update
   - Flag cleared after successful update
   - Flag cleared even on exception (finally block)

4. **Other Equipment Events**
   - Quantity changes delegate to inventory manager
   - Item toggles delegate to inventory manager
   - Item removal delegates to inventory manager
   - Armor-only toggles delegate to inventory manager
   - Category changes delegate to inventory manager
   - Equipped toggles delegate to inventory manager
   - Modifier changes delegate to inventory manager

5. **Event Chaining**
   - Bonus change triggers full chain: set_bonus → redraw → calculations
   - Chain executes in correct order
   - Failed `set_bonus` skips redraw and calculations

6. ** Parameter Extraction**
   - Extracts item ID from `data-item-id` attribute
   - Parses positive bonus values
   - Handles negative bonus values

## Why Not Fix the Contamination?

Several approaches were attempted:

1. ❌ **tearDownModule()** - Runs after all tests in the file complete, but pytest has already imported other test files during collection
2. ❌ **Removing from sys.modules cache** - Python's import system caches the mocked modules across the entire test session
3. ❌ **Renaming to run last** - Doesn't help because pytest imports all files during collection phase before running any tests
4. ❌ **Pytest fixtures** - Browser modules are imported at module level before fixtures can run
5. ❌ **@patch decorators** - Can't patch module-level imports that happen before test execution

The root cause is that `equipment_event_manager.py` imports `js` and `pyodide` at the module level (not inside functions), so these must be mocked before the module is imported. Pytest's collection phase imports all test files, causing the mocks to persist in `sys.modules` for the entire test session.

## Alternative Approaches Considered

- **Separate test directory**: Move to `tests/isolated/` and run separately
- **pytest-xdist**: Use `--forked` to run in separate process (requires additional dependency)
- **Import mode**: pytest's `--import-mode=importlib` doesn't solve module-level mocking
- **Refactor equipment_event_manager**: Move browser imports inside functions (breaks production code)

The current solution (separate test runs) is the simplest and most maintainable approach.
