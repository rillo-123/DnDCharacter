"""Test CharacterManager integration with entity managers.

Verifies that:
1. Character instances can be passed to WeaponEntity and ArmorEntity
2. Character stats are properly normalized to dict format
3. Character is the single source of truth for stats
"""

import unittest
from character_models import Character
from managers import WeaponEntity, ArmorEntity


class TestCharacterManagerIntegration(unittest.TestCase):
    """Test Character instance integration with entity managers."""

    def setUp(self):
        """Create a test character with known stats."""
        self.char_data = {
            "identity": {"name": "Test", "class": "Fighter", "race": "Human"},
            "level": 5,
            "abilities": {
                "str": {"score": 16, "save_proficient": False},
                "dex": {"score": 12, "save_proficient": False},
                "con": {"score": 14, "save_proficient": False},
                "int": {"score": 10, "save_proficient": False},
                "wis": {"score": 13, "save_proficient": False},
                "cha": {"score": 11, "save_proficient": False},
            },
        }
        self.character = Character(self.char_data)

    def test_character_has_proficiency_bonus(self):
        """Character instance has correct proficiency bonus for level."""
        # Level 5 = +3 proficiency bonus
        self.assertEqual(self.character.proficiency_bonus, 3)

    def test_character_has_ability_modifier_method(self):
        """Character provides get_ability_modifier method."""
        # STR 16 = +3 modifier
        str_mod = self.character.get_ability_modifier("str")
        self.assertEqual(str_mod, 3)
        
        # DEX 12 = +1 modifier
        dex_mod = self.character.get_ability_modifier("dex")
        self.assertEqual(dex_mod, 1)

    def test_character_has_stats_dict(self):
        """Character provides get_stats_dict method."""
        stats_dict = self.character.get_stats_dict()
        self.assertIn("str", stats_dict)
        self.assertIn("dex", stats_dict)
        self.assertIn("proficiency", stats_dict)
        self.assertEqual(stats_dict["str"], 16)
        self.assertEqual(stats_dict["dex"], 12)
        self.assertEqual(stats_dict["proficiency"], 3)

    def test_weapon_entity_accepts_character(self):
        """WeaponEntity can accept Character instance."""
        weapon_data = {"name": "Longsword", "damage": "1d8", "damage_type": "slashing"}
        weapon = WeaponEntity(weapon_data, self.character)
        
        # Verify weapon was created successfully
        self.assertEqual(weapon.final_name, "Longsword")
        self.assertIsNotNone(weapon.final_tohit)

    def test_weapon_entity_with_character_calculates_tohit(self):
        """WeaponEntity with Character calculates correct to-hit."""
        # Fighter with STR 16 (+3), proficiency +3 = +6 to hit with proficient melee weapon
        weapon_data = {"name": "Longsword", "damage": "1d8", "damage_type": "slashing"}
        weapon = WeaponEntity(weapon_data, self.character)
        
        # final_tohit returns "+6" format
        self.assertEqual(weapon.final_tohit, "+6")

    def test_weapon_entity_with_character_and_bonus(self):
        """WeaponEntity calculates to-hit with weapon bonus."""
        # Longsword +1: STR 16 (+3) + proficiency +3 + bonus +1 = +7
        weapon_data = {
            "name": "Longsword +1",
            "damage": "1d8",
            "damage_type": "slashing",
            "bonus": 1
        }
        weapon = WeaponEntity(weapon_data, self.character)
        self.assertEqual(weapon.final_tohit, "+7")

    def test_armor_entity_accepts_character(self):
        """ArmorEntity can accept Character instance."""
        armor_data = {"name": "Plate Armor", "armor_class": 18, "armor_type": "Heavy"}
        armor = ArmorEntity(armor_data, self.character)
        
        # Verify armor was created successfully
        self.assertEqual(armor.display_name, "Plate Armor")

    def test_armor_entity_with_character_light_armor_adds_dex(self):
        """ArmorEntity with Character adds DEX modifier to light armor."""
        # Leather armor AC 11 + DEX 12 (+1) = 12
        armor_data = {"name": "Leather Armor", "armor_class": 11, "armor_type": "Light"}
        armor = ArmorEntity(armor_data, self.character)
        
        # Use final_ac which includes DEX modifiers
        self.assertEqual(armor.final_ac, "12")

    def test_armor_entity_with_character_heavy_armor_ignores_dex(self):
        """ArmorEntity with Character ignores DEX modifier for heavy armor."""
        # Plate armor AC 18, no DEX modifier regardless of score
        armor_data = {"name": "Plate Armor", "armor_class": 18, "armor_type": "Heavy"}
        armor = ArmorEntity(armor_data, self.character)
        
        # Use final_ac which includes DEX modifiers (but heavy armor ignores them)
        self.assertEqual(armor.final_ac, "18")

    def test_backward_compatibility_with_dict(self):
        """Entities still work with dict-based character stats."""
        stats_dict = {"str": 16, "dex": 12, "proficiency": 3}
        
        weapon_data = {"name": "Longsword", "damage": "1d8", "damage_type": "slashing"}
        weapon = WeaponEntity(weapon_data, stats_dict)
        
        # Should produce same result as Character instance
        self.assertEqual(weapon.final_tohit, "+6")

    def test_character_stats_dict_matches_entity_input(self):
        """Character.get_stats_dict() produces input compatible with entities."""
        stats_dict = self.character.get_stats_dict()
        
        weapon_data = {"name": "Longsword"}
        weapon_from_char = WeaponEntity(weapon_data, self.character)
        weapon_from_dict = WeaponEntity(weapon_data, stats_dict)
        
        # Both should calculate same to-hit value
        self.assertEqual(weapon_from_char.final_tohit, weapon_from_dict.final_tohit)


if __name__ == "__main__":
    unittest.main()
