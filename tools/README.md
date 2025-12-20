# Tools

Utility scripts for ad-hoc checks and diagnostics. Run from the repo root so relative paths (e.g., exports/...) resolve correctly.

Checks (now with CLI flags):
- checks/check_slugs.py — show prepared spell slugs
- checks/check_sources.py — show prepared spell sources
- checks/check_spellcasting.py — dump the full spellcasting block
- checks/check_domain_flag.py — show is_domain_bonus flags
- checks/check_domain_spells.py — compare domain bonus spells (default: Life, level 9)

Manual tests (run-as-scripts, not collected by pytest):
- tests/test_filter.py — simple source filter demo
- tests/test_exec_load.py — exec-based module load smoke
- tests/test_import_compat.py — import compatibility sanity
- tests/test_import_debug.py — detailed import dump
- tests/test_import_comprehensive.py — full import assertions
- tests/test_open5e_format.py — fetch and display Open5e spell format
- tests/count_spells.py — summary of authoritative vs filtered spells and domain bonuses
- tests/spell_breakdown.py — categorize prepared spells (cantrips/domain/A5E/user)

Common flags
- --file <path>: choose a specific export JSON
- --exports-dir <dir>: change where exports are read from (default: exports)
- --domain/--level: only for check_domain_spells

Examples
```bash
python tools/checks/check_slugs.py
python tools/checks/check_sources.py --file exports/Enwer.json
python tools/checks/check_domain_spells.py --domain life --level 9
```

PowerShell shim (Windows):
```powershell
pwsh tools/run_check.ps1 -Script check_slugs
pwsh tools/run_check.ps1 -Script check_domain_spells -File exports/Enwer.json -Domain life -Level 9
```
