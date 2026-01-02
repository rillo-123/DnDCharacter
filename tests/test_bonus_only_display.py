import json
from weapons_manager import WeaponEntity
import character


def test_bonus_only_in_name_does_not_display_alone_in_damage():
    # Item with +1 in name but no damage fields
    item = {"name": "Dagger +1", "category": "Weapons", "equipped": True}
    enriched = character._enrich_weapon_item(item)

    # render_equipped_attack_grid uses enriched data; enrichment should provide base damage from builtin fallback
    assert enriched.get('damage') == '1d4'

    # WeaponEntity final_damage constructed from raw data (no enrichment step) should not return "+1" alone -- it should be '—'
    w = WeaponEntity(weapon_data={'name': 'Dagger +1', 'notes': ''}, character_stats={"str":10, "dex":10, "proficiency":2})
    assert w.final_damage == '—'


def test_render_damage_shows_bonus_only_when_damage_present(capsys):
    # Item with damage and bonus
    item = {"name": "Dagger +1", "category": "Weapons", "equipped": True, "damage": "1d4", "damage_type": "piercing", "bonus": 1}
    enriched = character._enrich_weapon_item(item)
    assert enriched.get('damage') == '1d4'
    # Simulate rendering logic: dmg_text should include +1
    dmg = enriched.get('damage')
    dmg_type = enriched.get('damage_type')
    dmg_bonus = enriched.get('bonus', 0) or item.get('bonus', 0)
    dmg_text = dmg
    if dmg_text and dmg_type:
        dmg_text = f"{dmg_text} {dmg_type}"
    if dmg_bonus and dmg_bonus > 0 and dmg_text:
        dmg_text = f"{dmg_text} +{dmg_bonus}"

    assert '+1' in dmg_text
