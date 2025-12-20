import json
import copy
import pytest

import character
from weapons_manager import WeaponEntity


def test_enrich_weapon_item_reads_notes_in_equipment_library(monkeypatch):
    # Backup state
    original = copy.deepcopy(character.EQUIPMENT_LIBRARY_STATE)
    try:
        # Equipment entry with important fields stored in notes JSON only
        eq_notes = json.dumps({
            "damage": "1d8",
            "damage_type": "piercing",
            "range": "80/320",
            "properties": ["ammunition", "loading"]
        })
        character.EQUIPMENT_LIBRARY_STATE["equipment"] = [
            {"name": "Crossbow, light", "notes": eq_notes}
        ]

        item = {"name": "Crossbow, light"}
        enriched = character._enrich_weapon_item(item)

        assert enriched.get("damage") == "1d8"
        assert enriched.get("damage_type") == "piercing"
        # range_text is assigned to 'range_text' key
        assert enriched.get("range_text") == "80/320"
        assert "ammunition" in enriched.get("weapon_properties")
    finally:
        character.EQUIPMENT_LIBRARY_STATE.clear()
        character.EQUIPMENT_LIBRARY_STATE.update(original)


def test_weapon_entity_final_damage_and_range_reads_notes():
    notes = json.dumps({
        "damage": "1d8",
        "damage_type": "piercing",
        "range": "80/320",
        "properties": "ammunition, loading"
    })

    weapon_data = {"name": "Crossbow, light", "notes": notes}
    w = WeaponEntity(weapon_data=weapon_data, character_stats={"str": 10, "dex": 10, "proficiency": 2})

    assert "1d8" in w.final_damage
    assert "piercing" in w.final_damage
    assert "80/320" in w.final_range


def test_enrich_prefers_top_level_fields_over_notes(monkeypatch):
    original = copy.deepcopy(character.EQUIPMENT_LIBRARY_STATE)
    try:
        # equipment record has top-level damage, but notes has different damage
        eq_notes = json.dumps({"damage": "999d99", "damage_type": "weird"})
        character.EQUIPMENT_LIBRARY_STATE["equipment"] = [
            {"name": "Crossbow, light", "damage": "1d8", "damage_type": "piercing", "notes": eq_notes}
        ]

        item = {"name": "Crossbow, light"}
        enriched = character._enrich_weapon_item(item)

        assert enriched.get("damage") == "1d8"
        assert enriched.get("damage_type") == "piercing"
    finally:
        character.EQUIPMENT_LIBRARY_STATE.clear()
        character.EQUIPMENT_LIBRARY_STATE.update(original)
