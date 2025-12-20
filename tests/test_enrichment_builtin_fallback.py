import copy
import character


def test_enrich_uses_builtin_when_cache_entry_missing_fields():
    original = copy.deepcopy(character.EQUIPMENT_LIBRARY_STATE)
    try:
        # Simulate cached equipment where Crossbow entry lacks details
        character.EQUIPMENT_LIBRARY_STATE["equipment"] = [
            {"name": "Crossbow, light"},
            {"name": "Mace", "damage": "1d6", "damage_type": "bludgeoning"}
        ]

        item = {"name": "Crossbow, light"}
        enriched = character._enrich_weapon_item(item)

        assert enriched.get("damage") == "1d8"
        assert enriched.get("damage_type") == "piercing"
        assert "80/320" in (enriched.get("range_text") or "")
        assert "ammunition" in (enriched.get("weapon_properties") or "")
    finally:
        character.EQUIPMENT_LIBRARY_STATE.clear()
        character.EQUIPMENT_LIBRARY_STATE.update(original)
