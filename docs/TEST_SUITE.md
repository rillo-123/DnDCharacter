# Test Suite Summary

## Overview
The project now has a comprehensive test suite covering the Flask backend, character models, equipment, spells, and more.

## Test Files Created

### `tests/test_flask_export_api.py` (16 tests)
Tests for the Flask `/api/export` and `/api/exports` endpoints:
- Export character data to JSON files
- List exported files with metadata
- Filename sanitization (path traversal prevention)
- Unicode character handling
- Complex character data export
- Integration workflows

### `tests/test_startup_health.py` (26 tests)
Startup and health check tests:
- Flask app initialization
- Route registration and HTTP methods
- Endpoint availability and responses
- Error handling (404, 500, invalid JSON)
- Server configuration
- Response headers and JSON formatting
- Concurrent request handling
- Response time performance

## Test Results
✅ **791 tests passing** (99.9% pass rate)

### Test Distribution
- **Main test suite**: 763 tests passed, 1 skipped
- **Equipment events tests**: 28 tests passed (run separately)

### Test Categories
- AC calculation: 20 tests
- Armor manager properties: 10 tests
- Equipment events: 28 tests (requires browser module mocking)
- Character models: 27 tests
- Equipment: ~150 tests
- Spells: ~80 tests
- Domain spells: ~25 tests
- Spell class chooser: ~21 tests
- Export/import: ~50 tests
- Weapons: ~70 tests
- Flask API tests: 16 tests
- Startup/health tests: 26 tests
- Other features: ~270 tests

## Running Tests

### All tests (recommended)

**Windows (PowerShell):**
```powershell
.\run_all_tests.ps1
```

**Linux/Unix/macOS (Bash):**
```bash
./run_all_tests.sh
```

Both scripts run the same test suites:
1. Main test suite (763 tests) - excludes equipment events to avoid mock contamination
2. Equipment events tests (28 tests) - runs separately with browser module mocking

### Script Options

Both test runner scripts support the following options:

**Filtering tests:**
```bash
./run_all_tests.sh -f "spell"              # Filter by test name pattern
.\run_all_tests.ps1 -Filter "spell"        # PowerShell equivalent
```

**Code quality tools:**
```bash
./run_all_tests.sh --radon                 # Run complexity analysis
./run_all_tests.sh --ruff                  # Run linter
./run_all_tests.sh --mypy                  # Run type checker
./run_all_tests.sh --bandit                # Run security scanner
./run_all_tests.sh --coverage              # Run test coverage report
./run_all_tests.sh --all                   # Run all code quality tools
```

### Main test suite only
```bash
python -m pytest tests/ --ignore=tests/test_equipment_chooser.py --ignore=tests/test_equipment_events.py
```

### Equipment events only
```bash
python -m pytest tests/test_equipment_events.py -v
```

### By category
```bash
python -m pytest tests/ -k "spell" -v           # Spell-related tests
python -m pytest tests/ -k "equipment" -v       # Equipment tests
python -m pytest tests/ -k "export" -v          # Export tests
python -m pytest tests/ -k "ac_calculation" -v  # AC calculation tests
```

## Special Test: Equipment Events

The `test_equipment_events.py` test file requires special handling due to browser module mocking. See [README_EQUIPMENT_EVENTS.md](../tests/README_EQUIPMENT_EVENTS.md) for details.

**Why separate?** The equipment event tests mock browser modules (`js`, `pyodide`) at module level, which contaminates pytest's import collection phase. Running them separately prevents this contamination.

**What's tested:**
- Event listener initialization
- Bonus change event handling
- Event loop prevention (_is_updating flag)
- Event delegation to inventory manager
- Event chaining (set_bonus → redraw → calculations)
- Parameter extraction from DOM events

## Test Coverage
- ✅ Server startup and initialization
- ✅ API endpoint health and availability
- ✅ Error handling and edge cases
- ✅ Character data export and import
- ✅ Equipment management (inventory CRUD)
- ✅ **Equipment event system** (bonus changes, toggles, event chains)
- ✅ **Event loop prevention** (_is_updating flag mechanism)
- ✅ **AC calculation** (armor + shield + DEX modifier)
- ✅ **Armor manager properties** (armor_ac, shield_ac, other_ac, total_ac)
- ✅ Spell library and filtering
- ✅ Domain spells (Cleric specialization)
- ✅ Ability modifiers and calculations
- ✅ Skill proficiency tracking
- ✅ Hit point and hit dice management
- ✅ Spell slot tracking
- ✅ Weapon to-hit calculations (STR/DEX/Finesse)
- ✅ JSON export/import round-trip consistency

## What Gets Tested When

### During Development
- Run `python -m pytest tests/ -v` before committing
- Run `python -m pytest tests/ -k "flask" -v` to validate server changes

### In CI/CD
- All 443 tests should pass
- No test should take more than 5 seconds

### Before Deployment
- Verify `python -m pytest tests/test_startup_health.py` passes
- Verify Flask server starts: `python backend.py --debug`
- Verify frontend loads: open `http://localhost:8080`

## Key Test Assertions

### Server Startup
- ✓ Flask app is created and configured
- ✓ Static folder is properly set
- ✓ Export directory exists and is writable
- ✓ All routes are registered

### API Endpoints
- ✓ `GET /` returns index.html
- ✓ `POST /api/export` accepts character data
- ✓ `GET /api/exports` lists exports with metadata
- ✓ Invalid requests return appropriate error codes

### Error Handling
- ✓ Missing JSON returns 400
- ✓ Invalid JSON is handled gracefully
- ✓ Nonexistent routes return 404
- ✓ Path traversal attempts are sanitized

### Performance
- ✓ Response time < 1 second
- ✓ Server handles concurrent requests
- ✓ Multiple exports in sequence work correctly

## Future Test Improvements
- [ ] Add pytest-asyncio for async tests
- [ ] Add performance benchmarks
- [ ] Add security tests (CORS, injection)
- [ ] Add load testing
- [ ] Add browser automation tests (Selenium/Playwright)
- [ ] Add visual regression tests for UI
