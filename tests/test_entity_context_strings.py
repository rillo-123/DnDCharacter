from managers import WeaponEntity, ArmorEntity


def test_weapon_equipment_list_ctx():
    weapon_data = {"name": "Dagger", "cost": "2 gp", "weight": "1 lb."}
    w = WeaponEntity(weapon_data, {"str": 10, "dex": 10, "proficiency": 0})
    assert w.item_info_string_equipment_list_ctx() == "Dagger - 2 gp - 1 lb."


def test_weapon_skill_grid_ctx():
    weapon_data = {"name": "Longsword", "damage": "1d8", "damage_type": "slashing", "bonus": 1}
    w = WeaponEntity(weapon_data, {"str": 14, "dex": 10, "proficiency": 2})
    assert w.item_info_string_skill_grid_ctx() == "Longsword (+5 to hit, 1d8 slashing +1)"


def test_armor_equipment_list_ctx():
    armor_data = {"name": "Leather Armor", "cost": "10 gp", "weight": "10 lb."}
    a = ArmorEntity(armor_data, {"str": 10, "dex": 14, "proficiency": 0})
    assert a.item_info_string_equipment_list_ctx() == "Leather Armor - 10 gp - 10 lb."


def test_armor_character_sheet_ctx():
    armor_data = {"name": "Leather Armor", "armor_class": 11, "armor_type": "Light"}
    a = ArmorEntity(armor_data, {"dex": 14})
    assert a.item_info_string_character_sheet_ctx() == "Leather Armor (AC 13)"
