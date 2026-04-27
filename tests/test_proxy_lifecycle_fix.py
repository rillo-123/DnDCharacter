"""Regression tests that PyScript proxy lifecycle code is no longer required."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"
APP_JS = PROJECT_ROOT / "static" / "assets" / "js" / "app.js"


def test_index_has_no_pyscript_proxy_surface():
    html = INDEX_HTML.read_text(encoding="utf-8")

    forbidden = ("py-click", "<py-config", "<py-script", "pyscript.net", "create_proxy")
    for token in forbidden:
        assert token not in html


def test_app_uses_event_delegation_without_python_proxies():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert 'document.addEventListener("click"' in app_js
    assert 'document.addEventListener("change"' in app_js
    assert "event.target.closest(" in app_js
    assert "create_proxy" not in app_js


def test_dynamic_inventory_and_spell_buttons_have_data_actions():
    app_js = APP_JS.read_text(encoding="utf-8")

    expected_actions = (
        "data-add-equipment",
        "data-remove-item",
        "data-item-equipped",
        "data-spell-toggle",
        "data-cast-spell",
        "data-slot-delta",
    )
    for action in expected_actions:
        assert action in app_js
