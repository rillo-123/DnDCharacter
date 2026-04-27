"""Rendered browser checks for the native JavaScript app.

These tests intentionally exercise the app through Chromium so the migration can
keep user-visible behavior protected while older PyScript-era tests are cleaned
up or retired.
"""

from __future__ import annotations

from pathlib import Path
import re
import socket
import subprocess
import sys
import time
from collections.abc import Generator

from playwright.sync_api import Page, expect
import pytest
import requests


PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOT_DIR = PROJECT_ROOT / "test-artifacts" / "screenshots"


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="session")
def rendered_app_url() -> Generator[str, None, None]:
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend_fastapi:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.monotonic() + 20
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError(f"FastAPI server exited early:\n{output}")
            try:
                response = requests.get(url, timeout=0.5)
                if response.status_code == 200:
                    yield url
                    return
            except requests.RequestException as exc:
                last_error = exc
            time.sleep(0.25)
        raise RuntimeError(f"FastAPI server did not start at {url}: {last_error}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture
def ux_page(page: Page) -> Generator[Page, None, None]:
    errors: list[str] = []
    page.on("pageerror", lambda exc: errors.append(str(exc)))
    page.on(
        "console",
        lambda msg: errors.append(msg.text) if msg.type == "error" else None,
    )
    yield page
    assert not errors, "Browser errors were logged:\n" + "\n".join(errors)


def screenshot(page: Page, name: str) -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=SCREENSHOT_DIR / name, full_page=True)


def open_app(page: Page, url: str) -> None:
    page.goto(url, wait_until="domcontentloaded")
    expect(page.locator("#character-header-name")).to_be_visible()
    expect(page.locator("#saving-indicator .saving-text")).to_be_visible()


def test_app_renders_and_tabs_are_navigable(ux_page: Page, rendered_app_url: str):
    open_app(ux_page, rendered_app_url)

    expected_panels = {
        "Overview": "#tab-overview",
        "Inventory": "#tab-inventory",
        "Skills": "#tab-skills",
        "Combat": "#tab-combat",
        "Spells": "#tab-spells",
        "Feats": "#tab-feats",
        "Manage": "#tab-manage",
    }

    for tab_name, panel_selector in expected_panels.items():
        ux_page.get_by_role("button", name=tab_name).click()
        expect(ux_page.locator(panel_selector)).to_have_class(re.compile(r"\bactive\b"))
        expect(ux_page.locator(panel_selector)).to_be_visible()

    screenshot(ux_page, "tabs-manage-desktop.png")


def test_character_edits_update_header_and_survive_reload(ux_page: Page, rendered_app_url: str):
    open_app(ux_page, rendered_app_url)

    ux_page.locator("#name").fill("Rendered Cleric")
    ux_page.locator("#class").select_option(label="Cleric")
    ux_page.locator("#race").select_option(label="Human")
    ux_page.locator("#level").fill("5")
    expect(ux_page.locator("#character-header-name")).to_have_text("Rendered Cleric")
    expect(ux_page.locator("#character-header-summary")).to_contain_text("Human Cleric - Level 5")
    expect(ux_page.locator("#saving-indicator .saving-text")).to_have_text("Saved", timeout=2000)

    ux_page.reload(wait_until="networkidle")
    expect(ux_page.locator("#character-header-name")).to_have_text("Rendered Cleric")
    expect(ux_page.locator("#character-header-summary")).to_contain_text("Human Cleric - Level 5")
    screenshot(ux_page, "overview-edited-desktop.png")


def test_inventory_and_spell_workflows_render(ux_page: Page, rendered_app_url: str):
    ux_page.route(
        "https://api.open5e.com/**",
        lambda route: route.fulfill(status=200, json={"results": []}),
    )
    open_app(ux_page, rendered_app_url)
    ux_page.locator("#class").select_option(label="Cleric")

    ux_page.get_by_role("button", name="Inventory").click()
    ux_page.locator("#equipment-search-input").fill("Shield")
    expect(ux_page.locator("#equipment-library-results")).to_contain_text("Shield")
    ux_page.locator("[data-add-equipment]").first.click()
    expect(ux_page.locator("#equipment-table")).to_contain_text("Shield")

    ux_page.get_by_role("button", name="Spells").click()
    ux_page.locator("#spells-load-btn").click()
    expect(ux_page.locator("#spell-library-status")).to_contain_text("spells loaded", timeout=5000)
    ux_page.locator("#spell-search").fill("Cure Wounds")
    expect(ux_page.locator("#spell-library-results")).to_contain_text("Cure Wounds")
    ux_page.locator("#spell-library-results details").first.locator("summary").click()
    ux_page.locator("#spell-library-results [data-spell-toggle]").first.click()
    expect(ux_page.locator("#spellbook-levels")).to_contain_text("Cure Wounds")

    screenshot(ux_page, "inventory-spells-desktop.png")


def test_manage_and_custom_item_surfaces_render_on_mobile(ux_page: Page, rendered_app_url: str):
    ux_page.set_viewport_size({"width": 390, "height": 844})
    open_app(ux_page, rendered_app_url)

    ux_page.get_by_role("button", name="Manage").click()
    expect(ux_page.locator("#save-btn")).to_be_visible()
    expect(ux_page.locator("#export-btn")).to_be_visible()
    expect(ux_page.locator("#storage-info-btn")).to_be_visible()
    screenshot(ux_page, "manage-mobile.png")

    ux_page.get_by_role("button", name="Inventory").click()
    ux_page.locator("#equipment-custom-btn").click()
    expect(ux_page.locator("#custom-item-modal")).to_be_visible()
    expect(ux_page.locator("#custom-item-add")).to_be_visible()
    screenshot(ux_page, "custom-item-modal-mobile.png")
