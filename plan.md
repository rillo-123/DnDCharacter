# Project Plan

Last updated: 2026-04-25

## North Star

Build a table-ready D&D 5e admin app that helps manage characters during play. The project currently behaves like a browser-first character sheet with strong cleric support; the long-term direction is a class-agnostic character, party, and campaign administration tool.

## Product Principles

- Keep the app useful at the table: fast edits, clear totals, reliable save/export, and no fragile workflows.
- Treat the cleric implementation as the first complete vertical slice, then extract reusable class patterns from it.
- Preserve existing character exports and localStorage data whenever the data model changes.
- Prefer structured game data over hard-coded UI logic.
- Use FastAPI as the preferred backend path; keep the native JavaScript browser app working while backend APIs grow.
- Add tests around rules behavior, persistence, and browser startup paths before large refactors.

## Current MVP Boundary

The near-term MVP is a polished cleric-first character admin flow:

- Character identity, race, class, background, domain, alignment, level, and proficiency.
- Ability scores, saves, skills, passive scores, combat stats, and hit point controls.
- Cleric spell preparation, domain spells, spell slots, and long-rest recovery.
- Channel Divinity and custom resource tracking.
- Inventory, equipment, currency, armor class, shields, weapons, and carried weight.
- Character import/export, autosave, localStorage persistence, and export cleanup.
- Manage tab operations for saving, loading, resetting, exporting, and maintenance.

## Milestones

### 1. Stabilize The Cleric Slice

Goal: make one class feel dependable from level 1 to 20 before broadening the class system.

Deliverables:

- Cleric progression remains a source-of-truth data file, not scattered UI assumptions.
- Domain spells are automatically included, persisted, and restored without duplicate entries.
- Channel Divinity uses, spell slots, HP, hit dice, and custom resources survive save/export/import.
- Cleric domains have visible feature text and clear level gating.
- Armor, shield, weapon, and spell calculations match D&D 5e rules for the supported cases.
- Manage tab buttons provide clear success/error feedback.
- Browser startup/import/proxy lifecycle issues are fixed and covered by tests.
- FastAPI serves the current static/export/logging contract before additional rules APIs are added.

Exit criteria:

- A cleric can be created, leveled, equipped, prepared, exported, imported, and resumed without manual data repair.
- Full test suite has no known cleric, persistence, equipment, or startup regressions.
- `docs/SPECIFICATIONS.md`, `plan.md`, and `progress.md` match the implemented behavior.
- FastAPI route parity is proven for current export, saved-export, static, and console-log workflows.

### 2. Turn Cleric Logic Into A Reusable Class Framework

Goal: make the second and third classes cheaper to implement than the first.

Deliverables:

- A canonical class schema for hit dice, proficiencies, spellcasting progression, resources, features, subclasses, and rest recovery.
- One class manager path for all class metadata and typed character creation.
- A class feature renderer that works from data, not class-specific HTML branches.
- A consistent subclass model using `domain`, `college`, `oath`, `patron`, etc. as labels over the same underlying field.
- Bard becomes the second supported class because partial Bard specialization already exists.
- Wizard or Fighter becomes the third supported class to prove both caster-heavy and non-caster paths.

Exit criteria:

- Adding a class means adding data plus small targeted handlers, not copying cleric-specific code.
- Class feature tests can run without browser APIs.

### 3. Build Character Admin Workflows

Goal: make character management feel like an admin app, not just a single sheet.

Deliverables:

- Multi-character roster with quick switching and character summaries.
- Level-up workflow that shows new proficiencies, spell slots, features, ASI/feat choices, and HP changes.
- Conditions, concentration, death saves, exhaustion, inspiration, and temporary effects.
- Better rest workflows for short rest, long rest, and class-resource recovery.
- Character notes, campaign notes, and session log fields.
- Print-friendly and share-friendly character views.

Exit criteria:

- A player can manage multiple characters and common session events without touching JSON.
- Important state changes are visible, undoable where practical, and saved.

### 4. Expand Toward Party And Campaign Admin

Goal: support the DM/player admin tasks around the character sheet.

Deliverables:

- Party dashboard with HP, AC, passive scores, conditions, concentration, and resources.
- FastAPI-backed rules endpoints for derived character state, equipment calculations, spell filtering, and class features.
- NPC/monster quick records.
- Encounter tracker with initiative, rounds, conditions, and notes.
- Loot, shared inventory, shops, item handoff, and currency transactions.
- Session notes linked to characters and exports.

Exit criteria:

- The app can run a small party session from one browser tab.

### 5. Improve Data And Source Management

Goal: make game data trustworthy, searchable, and extensible.

Deliverables:

- Versioned local data schema with migration tests.
- Source tags for SRD, Open5e, D&D 5e API, custom, and homebrew content.
- Local cache controls for spells and equipment.
- Homebrew editor for equipment, spells, feats, and class features.
- Import validation with useful error messages.

Exit criteria:

- Bad or old data cannot silently corrupt a character.
- Users can distinguish official/SRD/imported/custom content at a glance.

### 6. Release Quality

Goal: make the app easy to run, test, and recover.

Deliverables:

- One documented startup path for local development.
- FastAPI/uvicorn is the documented backend startup path.
- Focused unit tests for rules and data transforms.
- Browser-level smoke tests for startup, tab navigation, save/load, spell add/remove, and equipment equip/remove.
- CI-friendly scripts for lint, tests, coverage, and security checks.
- Recovery guidance for localStorage/export issues.

Exit criteria:

- A clean checkout can be installed, tested, and started from documented commands.
- A failing rule or persistence change is caught by automated tests before manual playtesting.

## Prioritized Backlog

### P0 - Stabilize Current App

- Fix the current failing test clusters around character models, export round-trips, stale PyScript-era tests, spellcasting imports, tooltip values, total AC, and weapon rendering.
- Decide whether `character_models.py` or `managers/class_manager.py` owns character factory behavior, then remove conflicting paths.
- Retire stale PyScript proxy lifecycle tests and replace them with JavaScript event-flow coverage.
- Confirm cleric domain spell persistence and Channel Divinity persistence through export/import.
- Verify weapon to-hit, weapon damage, armor AC, shield AC, and magic item bonus behavior in one coherent rules layer.

### P1 - Make Class Support Real

- Convert cleric progression and class metadata into a reusable schema.
- Add data-driven class feature rendering.
- Complete Bard support as the next class.
- Add Wizard or Fighter as a contrasting third class.
- Add tests for class-specific spellcasting, resources, and level-gated features.

### P2 - Better Admin Experience

- Add a level-up flow.
- Add conditions and concentration tracking.
- Add party dashboard.
- Add campaign/session notes.
- Add import validation and migration UI.

## Technical Direction

- Keep managers focused: character, class, race, inventory, armor, weapons, equipment events, spellcasting, export, and entities.
- Prefer plain data files for rules tables and progression data.
- Keep UI rendering separated from rule calculations where practical.
- Use backward-compatible adapters while old exports are still in circulation.
- Treat `static/assets/js/app.js` as the browser orchestration layer and continue moving rules/data behavior into focused JavaScript modules as the port matures.
- Treat `backend_fastapi.py` as the primary backend entrypoint and `backend.py` as temporary Flask legacy compatibility.

## Definition Of Done

A feature is done when:

- It is usable from the browser UI.
- It persists through autosave, manual save, export, import, and reload where applicable.
- It has focused tests for rules behavior and serialization.
- It handles old or partial data safely.
- It is documented in the relevant project docs.
- It does not increase cleric-specific branching unless the feature is truly cleric-only.
