"""Integration-level startup checks for native JavaScript wiring."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"
APP_JS = PROJECT_ROOT / "static" / "assets" / "js" / "app.js"


def test_index_loads_single_native_app_module():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert html.count('src="assets/js/app.js"') == 1
    assert 'type="module"' in html
    assert "pyscript.net" not in html
    assert "<py-config" not in html
    assert "<py-script" not in html


def test_dom_content_loaded_initializes_app_once():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "function init()" in app_js
    assert 'document.addEventListener("DOMContentLoaded", init)' in app_js


def test_startup_loads_cached_state_and_refreshes_views():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "loadInitialState()" in app_js
    assert "renderAll()" in app_js
    assert "populateCharacterSwitcher()" in app_js
    assert "populateSpellClassFilter()" in app_js


def test_app_does_not_depend_on_python_module_bootstrap():
    app_js = APP_JS.read_text(encoding="utf-8")

    forbidden = ("assets/py", "py-click", "create_proxy", "pyodide", "PyScript")
    for token in forbidden:
        assert token not in app_js
