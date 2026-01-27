"""Test CharacterManager integration with entity managers."""

import unittest
from character_models import Character
from managers import CharacterManager, initialize_character_manager, WeaponEntity, ArmorEntity


class TestCharacterManagerClass(unittest.TestCase):
    """Test CharacterManager wrapper functionality."""

    def setUp(self):
        """Create test character manager."""
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

    def test_character_manager_initialization(self):
        """CharacterManager initializes with character data."""
        mgr = CharacterManager(self.char_data)
        self.assertIsNotNone(mgr.character)
        self.assertEqual(mgr.level, 5)
        self.assertEqual(mgr.proficiency_bonus, 3)

    def test_character_manager_from_character_instance(self):
        """CharacterManager accepts Character instance."""
        char = Character(self.char_data)
        mgr = CharacterManager(char)
        self.assertEqual(mgr.character, char)
        self.assertEqual(mgr.name, "Test")

    def test_character_manager_get_stats_dict(self):
        """CharacterManager provides stats dict for managers."""
        mgr = CharacterManager(self.char_data)
        stats = mgr.get_stats_dict()
        self.assertEqual(stats["str"], 16)
        self.assertEqual(stats["dex"], 12)
        self.assertEqual(stats["proficiency"], 3)

    def test_character_manager_get_ability_modifier(self):
        """CharacterManager provides ability modifiers."""
        mgr = CharacterManager(self.char_data)
        self.assertEqual(mgr.get_ability_modifier("str"), 3)
        self.assertEqual(mgr.get_ability_modifier("dex"), 1)

    def test_character_manager_properties(self):
        """CharacterManager exposes character properties."""
        mgr = CharacterManager(self.char_data)
        self.assertEqual(mgr.name, "Test")
        self.assertEqual(mgr.class_text, "Fighter")
        self.assertEqual(mgr.race, "Human")
        self.assertEqual(mgr.level, 5)
        self.assertEqual(mgr.proficiency_bonus, 3)

    def test_initialize_character_manager_function(self):
        """initialize_character_manager creates global instance."""
        mgr = initialize_character_manager(self.char_data)
        self.assertIsNotNone(mgr)
        self.assertEqual(mgr.level, 5)

    def test_weapon_entity_with_character_manager(self):
        """WeaponEntity accepts CharacterManager."""
        mgr = CharacterManager(self.char_data)
        weapon_data = {"name": "Longsword", "damage": "1d8", "damage_type": "slashing"}
        weapon = WeaponEntity(weapon_data, mgr)
        
        # Should calculate to-hit: STR 16 (+3) + prof +3 = +6
        self.assertEqual(weapon.final_tohit, "+6")

    def test_armor_entity_with_character_manager(self):
        """ArmorEntity accepts CharacterManager."""
        mgr = CharacterManager(self.char_data)
        armor_data = {"name": "Leather Armor", "armor_class": 11, "armor_type": "Light"}
        armor = ArmorEntity(armor_data, mgr)
        
        # Should add DEX modifier: 11 + (12-10)//2 = 11 + 1 = 12
        self.assertEqual(armor.final_ac, "12")

    def test_character_manager_to_dict(self):
        """CharacterManager exports to dictionary."""
        mgr = CharacterManager(self.char_data)
        exported = mgr.to_dict()
        
        self.assertIn("identity", exported)
        self.assertIn("level", exported)
        self.assertIn("abilities", exported)
        self.assertEqual(exported["level"], 5)


class TestCharacterManagerEntityIntegration(unittest.TestCase):
    """Test CharacterManager with multiple entity managers."""

    def setUp(self):
        """Create test character manager with stats."""
        self.mgr = CharacterManager({
            "identity": {"name": "Fighter", "class": "Fighter"},
            "level": 8,
            "abilities": {
                "str": {"score": 18, "save_proficient": False},
                "dex": {"score": 14, "save_proficient": False},
                "con": {"score": 16, "save_proficient": False},
                "int": {"score": 10, "save_proficient": False},
                "wis": {"score": 12, "save_proficient": False},
                "cha": {"score": 10, "save_proficient": False},
            },
        })

    def test_multiple_weapons_with_same_manager(self):
        """Multiple weapons use same CharacterManager stats."""
        sword = WeaponEntity(
            {"name": "Longsword", "damage": "1d8", "damage_type": "slashing"},
            self.mgr
        )
        dagger = WeaponEntity(
            {"name": "Dagger", "damage": "1d4", "damage_type": "piercing"},
            self.mgr
        )
        
        # Both should use same STR mod and proficiency
        # STR 18 (+4) + prof +3 = +7
        self.assertEqual(sword.final_tohit, "+7")
        self.assertEqual(dagger.final_tohit, "+7")

    def test_multiple_armor_with_same_manager(self):
        """Multiple armor pieces use same CharacterManager stats."""
        leather = ArmorEntity(
            {"name": "Leather", "armor_class": 11, "armor_type": "Light"},
            self.mgr
        )
        shield = ArmorEntity(
            {"name": "Shield", "armor_class": 2, "armor_type": "Shield"},
            self.mgr
        )
        
        # Both should use same DEX mod (capped by type)
        # Leather: 11 + (14-10)//2 = 11 + 2 = 13
        # Shield: just +2
        self.assertEqual(leather.final_ac, "13")
        self.assertEqual(shield.final_ac, "2")


if __name__ == "__main__":
    unittest.main()
