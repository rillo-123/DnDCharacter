"""Manage-tab structure tests for the native JavaScript app."""

from __future__ import annotations

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).parent.parent
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"
APP_JS = PROJECT_ROOT / "static" / "assets" / "js" / "app.js"


def html_content() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def app_source() -> str:
    return APP_JS.read_text(encoding="utf-8")


def test_manage_tab_buttons_exist_without_pyscript_attributes():
    html = html_content()

    for button_id in (
        "long-rest-btn",
        "save-btn",
        "reset-btn",
        "export-btn",
        "storage-info-btn",
        "cleanup-btn",
    ):
        match = re.search(rf"<button[^>]+id=\"{button_id}\"[^>]*>", html)
        assert match, f"{button_id} button is missing"
        assert "py-click" not in match.group(0)


def test_manage_tab_native_handlers_are_defined_and_registered():
    app_js = app_source()

    expected_functions = (
        "resetSpellSlots",
        "saveCharacter",
        "resetCharacter",
        "exportCharacter",
        "showStorageInfo",
        "cleanupExports",
        "importCharacter",
        "loadSelectedExport",
    )

    for function_name in expected_functions:
        assert re.search(rf"\b(?:async\s+)?function\s+{function_name}\s*\(", app_js), (
            f"{function_name} should be a function in app.js"
        )

    expected_ids = (
        "long-rest-btn",
        "save-btn",
        "reset-btn",
        "export-btn",
        "storage-info-btn",
        "cleanup-btn",
        "character-switcher",
    )
    for element_id in expected_ids:
        assert f'$("# {element_id}")' not in app_js
        assert f'$("{"%s" % element_id}")?.addEventListener' in app_js


def test_export_and_storage_actions_use_fastapi_routes():
    app_js = app_source()

    assert 'fetch("/api/export"' in app_js
    assert 'fetch("/api/exports")' in app_js
    assert 'fetch(`/exports/${encodeURIComponent(filename)}`)' in app_js


def test_storage_cleanup_targets_browser_caches_not_python_state():
    app_js = app_source()

    assert "localStorage.removeItem(LOCAL_STORAGE_KEY)" in app_js
    assert "localStorage.removeItem(SPELL_CACHE_KEY)" in app_js
    assert "import character" not in app_js
