"""Startup simulation tests for the native JavaScript app shell."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"
APP_JS = PROJECT_ROOT / "static" / "assets" / "js" / "app.js"


def test_browser_cold_start_uses_static_js_and_json_assets():
    html = INDEX_HTML.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")

    assert 'src="assets/js/app.js"' in html
    assert 'fetch("assets/data/equipment.json")' in app_js
    assert 'fetch("assets/data/spells.json")' in app_js


def test_startup_no_longer_depends_on_python_path_discovery():
    html = INDEX_HTML.read_text(encoding="utf-8")
    app_js = APP_JS.read_text(encoding="utf-8")

    combined = f"{html}\n{app_js}".lower()
    assert "sys.path" not in combined
    assert "pyodide" not in combined
    assert "assets/py" not in combined


def test_cached_browser_state_is_restored_on_init():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "function loadInitialState()" in app_js
    assert "localStorage.getItem(LOCAL_STORAGE_KEY)" in app_js
    assert "populateForm(JSON.parse(raw))" in app_js
    assert "loadInitialState();" in app_js


def test_fallback_spell_data_is_local_json_not_python_module():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "async function loadSpellLibrary(" in app_js
    assert 'fetch("assets/data/spells.json")' in app_js
    assert "sanitizeSpells(" in app_js
