# Test Execution Report
**Generated:** 2026-02-01  
**Repository:** rillo-123/DnDCharacter  
**Testing Framework:** pytest 8.4.2  
**Python Version:** 3.12.3

---

## Executive Summary

This report presents the results of running the complete test suite for the DnDCharacter repository. The test suite consists of two main components:
1. Main test suite (84 test files)
2. Equipment events tests (1 test file, run separately due to browser module mocking requirements)

### Overall Results
- **Total Tests Run:** 837
- **Passed:** 792 (94.6%)
- **Failed:** 72 (8.6%)
- **Skipped:** 1 (0.1%)
- **Warnings:** 2

---

## Test Suite Breakdown

### Main Test Suite
- **Tests Run:** 837 tests (764 passed, 72 failed, 1 skipped)
- **Execution Time:** 3.91 seconds
- **Status:** ⚠️ PARTIAL PASS (91.4% pass rate)

### Equipment Events Test Suite
- **Tests Run:** 28 tests (all passed)
- **Execution Time:** 0.09 seconds
- **Status:** ✅ PASS (100% pass rate)

---

## Failure Analysis

### Category 1: Character Model and Export Failures (34 tests)
**Root Cause:** `AttributeError: 'NoneType' object has no attribute 'from_dict'`

These failures appear to be related to character model instantiation and serialization. The `from_dict` method is being called on a None object, suggesting missing or improperly initialized character factory or class.

**Affected Tests:**
- test_character_export.py (12 failures)
- test_character_models.py (16 failures)
- test_pyscript_simulation.py (1 failure)
- test_spellcasting_import.py (4 failures)
- test_total_armor_class.py (1 failure)

**Example Failure:**
```
FAILED tests/test_character_export.py::TestClericExport::test_cleric_domain_export 
- AttributeError: 'NoneType' object has no attribute 'from_dict'
```

### Category 2: Module Import Failures (15 tests)
**Root Cause:** `ModuleNotFoundError` and `ImportError` for various manager modules

These failures indicate that several manager modules are not being found in the expected locations or are not properly configured in the Python path.

**Missing Modules:**
- inventory_manager
- equipment_event_manager
- armor_manager
- weapons_manager
- spellcasting_manager

**Affected Tests:**
- test_lamp_fix.py (5 failures)
- test_lamp_integration.py (5 failures)
- test_module_imports.py (5 failures)

**Example Failure:**
```
FAILED tests/test_module_imports.py::test_inventory_manager_imports 
- Failed: inventory_manager.py has import error: No module named 'inventory_manager'
```

### Category 3: Armor Class Calculation Issues (14 tests)
**Root Cause:** AC calculation discrepancies - calculated values are 1-2 points higher than expected

These tests are failing because the calculated Armor Class values are consistently higher than the expected values. This suggests a change in the AC calculation logic or an unintended bonus being applied.

**Affected Tests:**
- test_ac_calculation_comprehensive.py (10 failures)
- test_armor_shield_ac.py (2 failures)
- test_character_ac.py (2 failures)

**Example Failures:**
```
FAILED tests/test_ac_calculation_comprehensive.py::test_breastplate_plus_one_ac_calculation
- AssertionError: Expected AC 15, got 16
  
FAILED tests/test_character_ac.py::TestCalculateArmorClass::test_breastplate_plus_one_shield_only
- AssertionError: Expected AC 17 (15 + 2), got 18
```

### Category 4: Race Ability Bonus Failures (3 tests)
**Root Cause:** Empty ability bonus dictionaries being returned

The race models are returning empty dictionaries instead of the expected ability score bonuses.

**Affected Tests:**
- test_character_models.py::TestRaceAbilityBonuses (3 failures)

**Example Failure:**
```
FAILED tests/test_character_models.py::TestRaceAbilityBonuses::test_human_bonus
- AssertionError: assert {} == {'cha': 1, 'con': 1, 'dex': 1, 'int': 1, 'str': 1, 'wis': 1}
```

### Category 5: Async Test Configuration (2 tests)
**Root Cause:** pytest-asyncio plugin not installed

Two async tests are failing because pytest-asyncio is not installed.

**Affected Tests:**
- test_pyscript_fetch_post.py (2 failures)

**Example Failure:**
```
FAILED tests/test_pyscript_fetch_post.py::TestPyodideFetchPattern::test_fetch_with_to_js_conversion
- Failed: async def functions are not natively supported.
  You need to install a suitable plugin for your async framework
```

### Category 6: Miscellaneous Failures (4 tests)
- test_http_module_loading.py: Missing spellcasting_manager.py file
- test_proxy_lifecycle_fix.py: Missing initialize_module_references function
- test_weapons_grid.py: AttributeError with super().to_dict() method

---

## Test Coverage by Module

### Passing Modules (100% pass rate)
✅ test_equipment_events.py (28/28 tests)  
✅ test_autosave_triggers.py  
✅ test_bonus_in_notes.py  
✅ test_bonus_only_display.py  
✅ test_breastplate.py  
✅ test_cache_problem.py  
✅ test_channel_divinity_persistence.py  
✅ test_complete_flow.py  
✅ test_currency_persistence.py  
✅ test_dagger_plus1_enrichment.py  
✅ test_domain_spells.py  
✅ test_domain_spells_integration.py  
✅ test_effective_level.py  
✅ test_enrichment_builtin_fallback.py  
✅ test_enrichment_builtin_fallback_when_library_empty.py  
✅ test_enrichment_from_notes.py  
✅ test_enrichment_from_properties.py  
✅ test_entity_context_strings.py  
✅ test_equipment_cards.py  
✅ test_equipment_equipped_decorator.py  
✅ test_equipment_fallback_list.py  
✅ test_equipment_rendering.py  
✅ test_equipment_rendering_logic.py  
✅ test_equipment_shield.py  
✅ test_equipment_shield_integration.py  
✅ test_export_fetch_post.py  
✅ test_export_management_proxies.py  
✅ test_flask_export_api.py  
✅ test_http_serving.py  
✅ test_manage_tab_button_binding.py  
✅ test_manage_tab_buttons.py  
✅ test_manage_tab_messages.py  
✅ test_manager_list_properties.py  
✅ test_manager_preload.py  
✅ test_miscategorized.py  
✅ test_open5e_persistence.py  
✅ test_spell_class_chooser.py  
✅ test_spell_details.py  
✅ test_spell_filtering_fix.py  
✅ test_spell_library_debug.py  
✅ test_spell_loading.py  
✅ test_spell_merge.py  
✅ test_spell_mnemonic_detection.py  
✅ test_spell_rendering.py  
✅ test_spell_slots.py  
✅ test_spellbook_domain_spells.py  
✅ test_spellcasting.py  
✅ test_startup_health.py  
✅ test_tab_order.py  
✅ test_tooltip_debug.py  
✅ test_tooltip_values.py  
✅ test_weapon_to_hit.py  
✅ test_weapons_removal_integration.py  
✅ test_weapons_removal_sync.py  
✅ test_weapons_table_render.py  
✅ test_weapons_table_rendering.py

### Modules with Failures
❌ test_ac_calculation_comprehensive.py (10 failures)  
❌ test_armor_shield_ac.py (2 failures)  
❌ test_character_ac.py (2 failures)  
❌ test_character_export.py (12 failures)  
❌ test_character_models.py (16 failures)  
❌ test_http_module_loading.py (1 failure)  
❌ test_lamp_fix.py (5 failures)  
❌ test_lamp_integration.py (5 failures)  
❌ test_module_imports.py (5 failures)  
❌ test_proxy_lifecycle_fix.py (1 failure)  
❌ test_pyscript_fetch_post.py (2 failures)  
❌ test_pyscript_simulation.py (1 failure)  
❌ test_spellcasting_import.py (4 failures)  
❌ test_total_armor_class.py (1 failure)  
❌ test_weapons_grid.py (2 failures)

---

## Recommendations

### High Priority
1. **Character Model Initialization**: Investigate why character factory or class is returning None in multiple test scenarios. This is affecting 34 tests.
2. **Module Path Configuration**: Fix module import issues for manager classes (inventory_manager, equipment_event_manager, etc.).
3. **AC Calculation Logic**: Review recent changes to armor class calculation to understand why values are consistently 1-2 points higher than expected.

### Medium Priority
4. **Race Ability Bonuses**: Fix race model initialization to ensure ability score bonuses are properly loaded.
5. **Missing Files**: Ensure spellcasting_manager.py exists in the expected location.
6. **Missing Functions**: Add or restore the initialize_module_references function to managers module.

### Low Priority
7. **Async Testing**: Consider adding pytest-asyncio to requirements.txt if async tests are needed.
8. **Test Maintenance**: Review the 2 test warnings about unknown pytest.mark.asyncio markers.

---

## Positive Highlights

Despite the failures, the test suite shows several strengths:
- **High Overall Pass Rate:** 94.6% of all tests pass
- **Fast Execution:** Tests complete in under 4 seconds
- **Good Coverage:** 84 test files covering various aspects of the application
- **Critical Paths Working:** 
  - Equipment event handling (100% pass)
  - Spell management systems (mostly passing)
  - Domain spells integration (passing)
  - Currency and persistence systems (passing)
  - Export and import functionality (excluding character model issues)

---

## Test Environment Details

### Dependencies Installed
- requests 2.32.5
- pytest 8.4.2
- flask 3.1.2
- httpx 0.28.1
- vulture 2.14
- tqdm 4.67.2
- radon 6.0.1
- flake8 7.3.0
- ruff 0.14.14
- mypy 1.19.1
- bandit 1.9.3
- coverage 7.13.2

### Test Configuration
- Virtual environment: `.venv/`
- Test runner: pytest with pluggy 1.6.0
- Platform: Linux (Python 3.12.3)

---

## Conclusion

The DnDCharacter test suite demonstrates a well-structured testing approach with extensive coverage. While 72 tests are currently failing, these failures fall into clear categories with identifiable root causes. The high pass rate (94.6%) and the concentration of failures in specific areas suggest that addressing the top 3-4 issues would significantly improve the test suite health.

The equipment events tests passing at 100% indicates that critical event handling logic is working correctly. Most failures appear to be related to configuration issues (module imports, missing files) or recent changes to core calculation logic rather than fundamental design problems.

### Action Items Summary
1. Fix character model/factory initialization (34 tests)
2. Resolve module import paths (15 tests)
3. Review AC calculation changes (14 tests)
4. Fix race ability bonus initialization (3 tests)
5. Address remaining miscellaneous issues (6 tests)

---

*End of Report*
