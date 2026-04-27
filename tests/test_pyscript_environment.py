"""Native JavaScript environment checks replacing old PyScript diagnostics."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
INDEX_HTML = STATIC_DIR / "index.html"
APP_JS = STATIC_DIR / "assets" / "js" / "app.js"


def test_native_js_entrypoint_files_exist():
    assert INDEX_HTML.exists()
    assert APP_JS.exists()
    assert (STATIC_DIR / "assets" / "data" / "equipment.json").exists()
    assert (STATIC_DIR / "assets" / "data" / "spells.json").exists()


def test_index_is_not_a_pyscript_host_page():
    html = INDEX_HTML.read_text(encoding="utf-8")

    assert "pyscript.net" not in html
    assert "<py-config" not in html
    assert "<py-script" not in html
    assert "py-click" not in html
    assert 'src="assets/js/app.js"' in html


def test_app_js_uses_browser_native_apis():
    app_js = APP_JS.read_text(encoding="utf-8")

    assert "document.getElementById" in app_js
    assert "addEventListener" in app_js
    assert "localStorage" in app_js
    assert "fetch(" in app_js


def test_app_js_does_not_import_pyodide_or_python_modules():
    app_js = APP_JS.read_text(encoding="utf-8")

    forbidden = ("pyodide", "pyscript", "assets/py", "import character", "from character")
    for token in forbidden:
        assert token not in app_js.lower()
