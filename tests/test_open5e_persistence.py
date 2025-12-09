import json
from types import SimpleNamespace

import pytest

import character
import export_management


class _FakeStorage:
    def __init__(self):
        self._store = {}

    def getItem(self, key):
        return self._store.get(key)

    def setItem(self, key, value):
        self._store[key] = value

    def removeItem(self, key):
        self._store.pop(key, None)


class _FakeDocument:
    def getElementById(self, _):  # noqa: N802 - mirror DOM API
        return None


@pytest.fixture(autouse=True)
def reset_inventory():
    character.INVENTORY_MANAGER.items = []
    yield
    character.INVENTORY_MANAGER.items = []


def test_open5e_item_persists_via_auto_export(monkeypatch):
    """Open5e import should land in localStorage so it survives a reload."""
    storage = _FakeStorage()

    monkeypatch.setattr(export_management, "localStorage", storage)
    monkeypatch.setattr(export_management, "window", SimpleNamespace(localStorage=storage))
    monkeypatch.setattr(export_management, "document", _FakeDocument())
    monkeypatch.setattr(export_management, "setTimeout", lambda fn, ms: None)
    monkeypatch.setattr(export_management, "clearTimeout", lambda tid: None)
    monkeypatch.setattr(export_management, "_AUTO_EXPORT_DISABLED", True)

    def _fake_collect_character_data():
        data = character.clone_default_state()
        data["inventory"]["items"] = list(character.INVENTORY_MANAGER.items)
        return data

    monkeypatch.setattr(character, "collect_character_data", _fake_collect_character_data)

    character.submit_open5e_item(
        name="Shield",
        cost="10 gp",
        weight="6 lb.",
        damage="",
        damage_type="",
        range_text="",
        properties="",
        ac_string="+2",
        armor_class="",
    )

    saved = storage.getItem(character.LOCAL_STORAGE_KEY)
    assert saved, "schedule_auto_export did not persist to localStorage"

    saved_data = json.loads(saved)
    rehydrated = character.InventoryManager()
    rehydrated.load_state(saved_data)

    assert any(item.get("name") == "Shield" for item in rehydrated.items), "Shield should persist after reload"
