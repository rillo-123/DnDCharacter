"""Tests for the FastAPI backend route parity."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
import pytest

from backend_fastapi import EXPORT_DIR, LOG_DIR, app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def cleanup_test_exports() -> None:
    for file_path in EXPORT_DIR.glob("test_*.json"):
        try:
            file_path.unlink()
        except OSError:
            pass


def test_root_endpoint_returns_index_html(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<html" in response.text or "<head" in response.text
    assert "assets/js/app.js" in response.text
    assert "pyscript.net" not in response.text
    assert "<py-script" not in response.text


def test_static_javascript_app_is_served(client):
    response = client.get("/assets/js/app.js")

    assert response.status_code == 200
    assert "const LOCAL_STORAGE_KEY" in response.text
    assert "py-script" not in response.text


def test_favicon_returns_svg(client):
    response = client.get("/favicon.ico")

    assert response.status_code == 200
    assert "image/svg+xml" in response.headers["content-type"]


def test_nonexistent_static_path_returns_404(client):
    response = client.get("/definitely/not/here.txt")

    assert response.status_code == 404


def test_export_success_creates_file(client):
    cleanup_test_exports()
    char_data = {
        "name": "Enwer",
        "class": "Cleric",
        "level": 9,
        "abilities": {"strength": 16, "dexterity": 10},
    }

    response = client.post(
        "/api/export",
        json={"filename": "test_fastapi_enwer.json", "content": char_data},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["filename"] == "test_fastapi_enwer.json"
    assert data["path"] == "/exports/test_fastapi_enwer.json"
    assert data["size"] > 0

    file_path = EXPORT_DIR / "test_fastapi_enwer.json"
    assert file_path.exists()
    assert json.loads(file_path.read_text(encoding="utf-8")) == char_data
    cleanup_test_exports()


def test_export_file_can_be_downloaded_from_exports_route(client):
    cleanup_test_exports()
    char_data = {"name": "Download Test", "level": 3}

    response = client.post(
        "/api/export",
        json={"filename": "test_fastapi_download.json", "content": char_data},
    )
    assert response.status_code == 200

    download = client.get("/exports/test_fastapi_download.json")
    assert download.status_code == 200
    assert download.json() == char_data
    cleanup_test_exports()


def test_export_rejects_missing_or_bad_json(client):
    empty_response = client.post("/api/export", data="")
    invalid_response = client.post(
        "/api/export",
        data="not json",
        headers={"content-type": "application/json"},
    )

    assert empty_response.status_code == 400
    assert "error" in empty_response.json()
    assert invalid_response.status_code == 400
    assert "error" in invalid_response.json()


def test_export_rejects_missing_fields(client):
    missing_filename = client.post("/api/export", json={"content": {"name": "Enwer"}})
    missing_content = client.post("/api/export", json={"filename": "test.json"})

    assert missing_filename.status_code == 400
    assert "filename" in missing_filename.json()["error"]
    assert missing_content.status_code == 400
    assert "content" in missing_content.json()["error"]


def test_export_sanitizes_filename(client):
    cleanup_test_exports()

    response = client.post(
        "/api/export",
        json={"filename": "../../../test_fastapi_sanitized.json", "content": {"ok": True}},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_fastapi_sanitized.json"
    assert ".." not in data["path"]
    assert (EXPORT_DIR / "test_fastapi_sanitized.json").exists()
    cleanup_test_exports()


def test_list_exports_includes_metadata(client):
    cleanup_test_exports()
    file_path = EXPORT_DIR / "test_fastapi_metadata.json"
    file_path.write_text('{"test": true}', encoding="utf-8")

    response = client.get("/api/exports")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    export = next(item for item in data["exports"] if item["filename"] == file_path.name)
    assert export["size"] > 0
    assert "modified" in export
    cleanup_test_exports()


def test_export_endpoint_rejects_get(client):
    response = client.get("/api/export")

    assert response.status_code == 405


def test_console_log_endpoints_write_file(client):
    response = client.post("/api/console-log/new")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    log_path = LOG_DIR / data["filename"]
    assert log_path.exists()

    write_response = client.post("/api/console-log", json={"entries": ["one", "two"]})
    assert write_response.status_code == 200
    assert write_response.json()["count"] == 2
    assert "one" in log_path.read_text(encoding="utf-8")
