# Test Suite Summary

## Overview
The project now has a comprehensive test suite covering the FastAPI backend, legacy Flask backend, character models, equipment, spells, and more.

## Test Files Created

### `tests/test_fastapi_backend.py` (12 tests)
Tests for the FastAPI backend route parity:
- Static file serving for the JavaScript app
- Export character data to JSON files
- Serve saved exports from `/exports/{filename}`
- List exported files with metadata
- Filename sanitization (path traversal prevention)
- Console log endpoints
- Invalid request handling

### `tests/test_rendered_ux.py` (4 tests)
Rendered browser smoke tests for the native JavaScript UI:
- Starts the FastAPI app on a free local port
- Drives Chromium through Playwright
- Verifies initial render, tab navigation, character edits, and reload persistence
- Verifies inventory search/add and spell load/add workflows
- Verifies Manage tab and custom item modal rendering on a mobile viewport

Run with:
```powershell
python -m playwright install chromium
python -m pytest tests\test_rendered_ux.py -q --browser chromium
```

Screenshots are written under `test-artifacts/screenshots/` for local review and
are intentionally ignored by git.

### `tests/test_flask_export_api.py` (16 tests)
Legacy tests for the Flask `/api/export` and `/api/exports` endpoints:
- Export character data to JSON files
- List exported files with metadata
- Filename sanitization (path traversal prevention)
- Unicode character handling
- Complex character data export
- Integration workflows

### `tests/test_startup_health.py` (26 tests)
Startup and health check tests:
- Backend app initialization
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
- FastAPI backend tests: 12 tests
- Legacy Flask API tests: 16 tests
- Startup/health tests: 26 tests
- Other features: ~270 tests

## Running Tests

### All tests (recommended)
```powershell
.\run_all_tests.ps1
```

This script runs both test suites:
1. Main test suite (763 tests) - excludes equipment events to avoid mock contamination
2. Equipment events tests (28 tests) - runs separately with browser module mocking

### Main test suite only
```powershell
python -m pytest tests\ --ignore=tests\test_equipment_chooser.py --ignore=tests\test_equipment_events.py
```

### Equipment events only
```powershell
python -m pytest tests\test_equipment_events.py -v
```

### By category
```powershell
python -m pytest tests\ -k "spell" -v           # Spell-related tests
python -m pytest tests\ -k "equipment" -v       # Equipment tests
python -m pytest tests\ -k "export" -v          # Export tests
python -m pytest tests\ -k "ac_calculation" -v  # AC calculation tests
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
- Run `python -m pytest tests/test_fastapi_backend.py -v` to validate FastAPI server changes
- Run `python -m pytest tests/ -k "flask" -v` only when touching the legacy Flask path

### In CI/CD
- All 443 tests should pass
- No test should take more than 5 seconds

### Before Deployment
- Verify `python -m pytest tests/test_startup_health.py` passes
- Verify rendered UX smoke tests: `python -m pytest tests/test_rendered_ux.py -q --browser chromium`
- Verify FastAPI server starts: `python backend_fastapi.py --debug`
- Verify frontend loads: open `http://localhost:8080`

## Key Test Assertions

### Server Startup
- ✓ FastAPI app is created and configured
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
- [x] Add browser automation tests (Playwright)
- [ ] Add visual regression tests for UI
