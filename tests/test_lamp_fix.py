"""Autosave indicator tests for the native JavaScript migration.

The old "lamp" tests existed to guard PyScript proxy lifetimes. The lamp is now
plain DOM state managed by app.js, so the important contract is that saves move
through one native function path and update the visible indicator.
"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"
APP_JS = PROJECT_ROOT / "static" / "assets" / "js" / "app.js"


def test_save_indicator_markup_exists():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert 'id="saving-indicator"' in html
    assert 'class="saving-text"' in html
    assert "Saving" in html or "Saved" in html


def test_save_character_updates_local_storage_and_indicator():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "function saveCharacter(" in app_js
    assert "localStorage.setItem(LOCAL_STORAGE_KEY" in app_js
    assert "setSavingMessage(" in app_js


def test_character_inputs_trigger_native_autosave():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert 'document.querySelectorAll("[data-character-input]")' in app_js
    assert 'input.addEventListener("input"' in app_js
    assert 'input.addEventListener("change"' in app_js
    assert "scheduleSave()" in app_js
    assert "saveCharacter({ quiet: true })" in app_js


def test_beforeunload_proxy_pattern_is_gone():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "create_proxy" not in app_js
    assert "pyodide" not in app_js.lower()
