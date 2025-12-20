import json
import copy
import character


def test_enrich_reads_range_from_properties_list():
    original = copy.deepcopy(character.EQUIPMENT_LIBRARY_STATE)
    try:
        character.EQUIPMENT_LIBRARY_STATE["equipment"] = [
            {"name": "Crossbow, light", "properties": ["ammunition (range 80/320)", "loading"]}
        ]

        item = {"name": "Crossbow, light"}
        enriched = character._enrich_weapon_item(item)

        assert enriched.get("weapon_properties") is not None
        # range_text should be extracted from the properties list
        assert enriched.get("range_text") == "80/320"
    finally:
        character.EQUIPMENT_LIBRARY_STATE.clear()
        character.EQUIPMENT_LIBRARY_STATE.update(original)
