"""Native asset-loading tests replacing PyScript HTTP module loading tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend_fastapi import app


def test_browser_entrypoint_loads_javascript_not_python_modules():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert 'src="assets/js/app.js"' in response.text
    assert "<py-config" not in response.text
    assert "assets/py/character.py" not in response.text


def test_app_module_can_be_loaded_over_http():
    with TestClient(app) as client:
        response = client.get("/assets/js/app.js")

    assert response.status_code == 200
    assert "function sanitizeSpells(" in response.text
    assert "async function loadEquipmentLibrary(" in response.text
    assert "async function loadSpellLibrary(" in response.text


def test_json_data_replaces_python_module_bootstrap():
    with TestClient(app) as client:
        equipment = client.get("/assets/data/equipment.json")
        spells = client.get("/assets/data/spells.json")

    assert equipment.status_code == 200
    assert spells.status_code == 200
    equipment_items = [
        item
        for section in equipment.json().values()
        if isinstance(section, list)
        for item in section
    ]
    assert any(item.get("name") == "Shield" for item in equipment_items)
    spell_items = spells.json().get("LOCAL_SPELLS_FALLBACK", [])
    assert any(spell.get("name") == "Cure Wounds" for spell in spell_items)


def test_fastapi_serves_export_routes_used_by_app_js():
    with TestClient(app) as client:
        list_response = client.get("/api/exports")
        bad_export = client.post("/api/export", json={})

    assert list_response.status_code == 200
    assert "exports" in list_response.json()
    assert bad_export.status_code == 400
