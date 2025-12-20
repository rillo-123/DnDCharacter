import character
from weapons_manager import WeaponEntity


def test_enrich_reads_bonus_from_notes():
    item = {"name": "Dagger", "notes": "{\"bonus\": 1}", "equipped": True, "category": "Weapons"}
    enriched = character._enrich_weapon_item(item)
    assert enriched.get('bonus') == 1


def test_weaponentity_uses_notes_bonus_in_damage_and_tohit():
    # WeaponEntity should include bonus from notes in final_damage and final_tohit
    weapon_data = {"name": "Dagger", "notes": "{\"bonus\": 1, \"damage\": \"1d4\", \"damage_type\": \"piercing\"}"}
    w = WeaponEntity(weapon_data=weapon_data, character_stats={"str": 10, "dex": 10, "proficiency": 2})
    assert '+1' in w.final_damage
    assert w.final_tohit.startswith('+')
