"""Native JavaScript event binding checks for the Manage tab."""

from __future__ import annotations

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).parent.parent
INDEX_HTML = PROJECT_ROOT / "static" / "index.html"
APP_JS = PROJECT_ROOT / "static" / "assets" / "js" / "app.js"


def read_index() -> str:
    return INDEX_HTML.read_text(encoding="utf-8")


def read_app() -> str:
    return APP_JS.read_text(encoding="utf-8")


def extract_manage_section(html: str) -> str:
    start = html.find("<h2>Manage Data</h2>")
    assert start != -1, "Manage Data section is missing"
    end = html.find("</section>", start)
    assert end != -1, "Manage Data section is not closed"
    return html[start:end]


def test_manage_tab_uses_native_event_binding_contract():
    html = read_index()
    app_js = read_app()
    manage_section = extract_manage_section(html)

    assert "py-click" not in manage_section
    assert '<script type="module" src="assets/js/app.js"></script>' in html

    expected_bindings = {
        "save-btn": "saveCharacter",
        "reset-btn": "resetCharacter",
        "export-btn": "exportCharacter",
        "storage-info-btn": "showStorageInfo",
        "cleanup-btn": "cleanupExports",
    }

    for button_id, handler_name in expected_bindings.items():
        assert f'id="{button_id}"' in manage_section
        pattern = rf'\$\("{re.escape(button_id)}"\)\?\.addEventListener\("click",\s*(?:\(\) =>\s*)?{handler_name}\b'
        assert re.search(pattern, app_js), f"{button_id} is not bound to {handler_name}"

    assert 'id="long-rest-btn"' in html
    assert '$("long-rest-btn")?.addEventListener("click", resetSpellSlots)' in app_js


def test_import_control_is_bound_to_json_file_reader():
    html = read_index()
    app_js = read_app()

    assert 'id="import-file"' in html
    assert 'type="file"' in html
    assert 'accept="application/json"' in html
    assert '$("import-file")?.addEventListener("change"' in app_js
    assert "importCharacter(event.target.files?.[0])" in app_js


def test_manage_buttons_have_feedback_targets():
    html = read_index()
    app_js = read_app()

    assert 'id="storage-message"' in html
    assert 'id="saving-indicator"' in html
    assert "setSavingMessage(" in app_js
    assert "setStorageMessage(" in app_js
