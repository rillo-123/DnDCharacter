"""HTTP serving checks for the native JavaScript app assets."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend_fastapi import app


def test_root_serves_native_javascript_shell():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "assets/js/app.js" in response.text
    assert "pyscript.net" not in response.text
    assert "py-click" not in response.text


def test_static_javascript_module_is_served():
    with TestClient(app) as client:
        response = client.get("/assets/js/app.js")

    assert response.status_code == 200
    assert "function init()" in response.text
    assert "document.addEventListener" in response.text
    assert "create_proxy" not in response.text


def test_local_json_data_assets_are_served():
    with TestClient(app) as client:
        equipment = client.get("/assets/data/equipment.json")
        spells = client.get("/assets/data/spells.json")

    assert equipment.status_code == 200
    assert spells.status_code == 200
    assert isinstance(equipment.json(), dict)
    assert isinstance(spells.json(), dict)
    assert isinstance(spells.json().get("LOCAL_SPELLS_FALLBACK"), list)


def test_old_pyscript_asset_route_is_legacy_only_not_entrypoint():
    with TestClient(app) as client:
        html = client.get("/").text
        legacy_python = client.get("/assets/py/character.py")

    assert "/assets/py/character.py" not in html
    assert legacy_python.status_code in {200, 404}
