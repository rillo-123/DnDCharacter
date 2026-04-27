# Progress

Last updated: 2026-04-27

## Snapshot

Status: cleric-first MVP under active refactor.

The app is a browser-first D&D 5e admin/character sheet built with HTML, CSS, native JavaScript, and a FastAPI backend for file exports, saved export serving, static serving, and browser console logs. The older Flask backend remains in place as a legacy compatibility path while the FastAPI route reaches full parity. The UI is organized around tabs for Overview, Inventory, Skills, Combat, Spells, Feats, and Manage.

The project currently has the strongest support for cleric play: domains, cleric spell progression, domain spells, spell slots, Channel Divinity persistence, armor/shield handling, equipment, and export/import have visible implementation and test coverage.

## Implemented Areas

- Browser UI in `static/index.html` with tabbed character administration.
- Core character fields for name, class, race, background, domain, alignment, player name, level, and proficiency bonus.
- Ability score, save, skill, passive perception, passive insight, and passive investigation calculations.
- Combat stats including armor class, initiative, speed, HP, temporary HP, hit dice, armor proficiencies, and weapon proficiencies.
- Inventory/equipment management with equipment library loading, custom items, currency, total weight, total cost, equip/remove flows, armor tables, and weapon attack tables.
- Armor and shield rules for base AC, Dexterity caps, shield bonuses, magic bonuses, and equipped-state behavior.
- Spell library support, spell filtering, prepared spellbook state, spell slot tracking, pact slot support, and spell cache persistence.
- Cleric-specific data in `static/assets/data/cleric_progression.json`.
- Cleric domain spell tests and integration tests.
- Channel Divinity persistence tests.
- Manage tab controls for save/load/export/import/reset-style workflows.
- FastAPI backend in `backend_fastapi.py` for serving the app, writing exports, serving saved exports, listing exports, and receiving browser console logs.
- Legacy Flask backend in `backend.py` remains available while startup scripts and docs move to FastAPI.
- Browser logger with a rolling localStorage log window.
- JavaScript controller in `static/assets/js/app.js` with local JSON data in `static/assets/data/`.
- Tests covering equipment, armor, weapons, spells, exports, autosave, HTTP serving, and manager imports.

## Cleric Coverage

Done or mostly present:

- Cleric appears in the class selector and class registry.
- Domain selector includes many cleric domains.
- Cleric progression data exists for levels 1 through 20.
- Cleric spellcasting uses Wisdom.
- Cleric full-caster spell slot progression is represented.
- Prepared spell limits and spell filtering are tested.
- Domain bonus spells are tested for integration and export/import workflows.
- Channel Divinity persistence is tested.
- Life Domain heavy armor proficiency is represented in class metadata.

Partial or still needs confirmation:

- Domain feature text and feature automation by level.
- Domain-specific mechanical effects beyond spells/proficiencies.
- Turn Undead and Destroy Undead workflows.
- Divine Intervention workflow.
- Cleric level-up guidance.
- Cleric rest behavior beyond spell slots/resources already covered.

## Non-Cleric Coverage

Present foundation:

- Class selector includes the standard core classes.
- `CLASS_REGISTRY` contains class metadata for Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, and Wizard.
- Bard and Cleric have typed specialization hooks in `class_manager.py`.
- Spellcasting progression tables include full, half, artificer-style, and warlock/pact progression.
- Generic weapons, armor, skills, saves, HP, inventory, and export systems are not cleric-only.

Known limitation:

- The app is not yet class-complete. Most classes have metadata and generic sheet behavior, but not full feature/resource/subclass automation.

## Architecture Progress

- The browser runtime has moved from PyScript to native JavaScript.
- `static/assets/js/app.js` owns browser orchestration, state collection, persistence, derived calculations, inventory rendering, spellbook behavior, and export/import calls.
- Local JSON data files under `static/assets/data/` provide equipment and spell fallback data without requiring Pyodide.
- The old PyScript startup, `py-click`, HTTP module-loading, lamp/proxy-lifecycle, and Pyodide environment tests have been replaced with native JavaScript transition checks.
- Rendered UX smoke coverage now uses Playwright/Chromium in `tests/test_rendered_ux.py` to exercise real browser startup, tab navigation, character edits, inventory, spells, Manage controls, custom-item modal rendering, and screenshot capture.
- Legacy Python frontend modules remain in the tree for historical tests and as reference during cleanup, but they are no longer loaded by `static/index.html`.

## Test Status

Current full-suite result from 2026-04-27:

- `python -m pytest tests -q`: 883 passed, 2 skipped.
- The native JavaScript transition subset is green:
  `python -m pytest tests/test_manage_tab_button_binding.py tests/test_manage_tab_buttons.py tests/test_lamp_fix.py tests/test_lamp_integration.py tests/test_proxy_lifecycle_fix.py tests/test_pyscript_environment.py tests/test_pyscript_simulation.py tests/test_http_serving.py tests/test_http_module_loading.py -q`: 34 passed.
- The rendered UX browser subset is green:
  `python -m pytest tests/test_rendered_ux.py -q --browser chromium`: 4 passed.
- Combined native transition and rendered UX subset:
  `python -m pytest tests/test_rendered_ux.py tests/test_manage_tab_button_binding.py tests/test_manage_tab_buttons.py tests/test_lamp_fix.py tests/test_lamp_integration.py tests/test_proxy_lifecycle_fix.py tests/test_pyscript_environment.py tests/test_pyscript_simulation.py tests/test_http_serving.py tests/test_http_module_loading.py -q --browser chromium`: 38 passed.
- `python -m pip install -r requirements.txt` was run for the active Python interpreter so FastAPI/uvicorn are available to the test runner.

Previous recorded full-suite result from `logs/final_test_results.log`:

- 845 tests collected.
- 784 passed.
- 60 failed.
- 1 skipped.

Strong coverage areas:

- Armor and shield AC calculations.
- Armor persistence and categorization.
- Equipment rendering and equipped-state behavior.
- Currency persistence.
- Domain spell behavior.
- Spell filtering, spell slots, spell loading, and spell rendering.
- Manage tab button behavior and messages.
- FastAPI export API, saved-export download route, console-log routes, and HTTP/static serving.
- Legacy Flask export API and HTTP serving still covered by tests.

Focused verification on 2026-04-25:

- `python -m pytest tests/test_fastapi_backend.py -q`: 12 passed.
- `python -m pytest tests/test_flask_export_api.py tests/test_startup_health.py tests/test_export_fetch_post.py::TestFlaskBackendIntegration -q`: 45 passed.
- `python -m ruff check backend_fastapi.py tests/test_fastapi_backend.py activate-env.py`: passed.
- `python -m pip check`: no broken requirements.

Focused verification on 2026-04-27:

- Native JS transition tests listed above: 34 passed.
- Rendered UX Playwright tests: 4 passed.
- `python -m pytest tests/test_borrowed_proxy_fix_comprehensive.py tests/test_cache_problem.py tests/test_pyscript_fetch_post.py tests/test_manager_preload.py -q`: 23 passed.

Current failure clusters from the 2026-04-27 full-suite run:

- None known in the pytest suite.
- Two tests are skipped because they still require unsupported/full browser module conditions.

## Known Gaps

- The docs still describe some future or intended behavior as if it already exists.
- The class model has overlapping responsibility between character models and class manager/factory code.
- Browser-level JavaScript smoke coverage now exists as static/native contract tests, but true browser automation is still future work.
- FastAPI is now the preferred backend runtime, but Flask-specific tests and docs still need gradual renaming or retirement once parity is considered stable.
- Some data and UI behavior is still cleric-shaped rather than class-agnostic.
- Full class feature automation is not yet available for most classes.
- Multi-character and party/campaign admin workflows are still future work.
- Browser-level end-to-end coverage appears lighter than unit coverage.

## Next Recommended Work

1. Fix the failing character model and class factory tests first, because class expansion depends on a stable character identity model.
2. Finish FastAPI migration cleanup: rename/retire Flask-specific tests and docs after parity is stable.
3. Decide how much of `static/assets/py/character.py` remains as supported rules code versus migration reference, then either repair its imports or retire tests that target removed browser behavior.
4. Finish cleric feature coverage: domain feature text, Channel Divinity workflow, Turn/Destroy Undead, Divine Intervention, and level-up prompts.
5. Extract a reusable class feature schema from the cleric implementation.
6. Complete Bard as the second fully supported class.
7. Add one non-full-caster class after Bard to prove the class framework is not spellcaster-only.

## Working Notes

- Treat the current cleric implementation as the reference vertical slice.
- Avoid broad class work until the failing model/startup/import tests are green.
- Keep old character exports loadable while changing schemas.
- Update `plan.md` and this file after each meaningful milestone or full test run.
- New backend work should target `backend_fastapi.py`; keep `backend.py` stable only until the legacy Flask path can be removed.
