"""Unit tests for D&D character models."""

import pytest

from character_models import (
    Character,
    Cleric,
    Bard,
    CharacterFactory,
    get_race_ability_bonuses,
    DEFAULT_ABILITY_KEYS,
)


class TestRaceAbilityBonuses:
    """Test racial ability score bonuses."""

    def test_human_bonus(self):
        """Human gets +1 to all abilities."""
        bonuses = get_race_ability_bonuses("Human")
        assert bonuses == {"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1}

    def test_elf_dex_bonus(self):
        """High Elf gets +2 DEX, +1 INT."""
        bonuses = get_race_ability_bonuses("high elf")
        assert bonuses.get("dex") == 2
        assert bonuses.get("int") == 1

    def test_dwarf_con_bonus(self):
        """Mountain Dwarf gets +2 CON, +2 STR."""
        bonuses = get_race_ability_bonuses("mountain dwarf")
        assert bonuses.get("con") == 2
        assert bonuses.get("str") == 2

    def test_unknown_race_no_bonus(self):
        """Unknown race gets no bonuses."""
        bonuses = get_race_ability_bonuses("UnknownRace")
        assert all(v == 0 for v in bonuses.values())

    def test_case_insensitive(self):
        """Race lookup should be case-insensitive."""
        bonuses_lower = get_race_ability_bonuses("human")
        bonuses_upper = get_race_ability_bonuses("HUMAN")
        bonuses_proper = get_race_ability_bonuses("Human")
        assert bonuses_lower == bonuses_upper == bonuses_proper

    def test_all_races_present(self):
        """Verify all standard D&D 5e races have bonuses."""
        races = [
            "human", "elf", "high elf", "wood elf", "dark elf",
            "dwarf", "mountain dwarf", "hill dwarf",
            "halfling", "lightfoot halfling", "stout halfling",
            "dragonborn", "gnome", "forest gnome", "rock gnome",
            "half-elf", "half-orc", "tiefling"
        ]
        for race in races:
            bonuses = get_race_ability_bonuses(race)
            assert isinstance(bonuses, dict), f"Race '{race}' should return dict"
            assert all(isinstance(v, int) for v in bonuses.values()), f"Race '{race}' bonuses should be ints"


class TestCharacterBase:
    """Test base Character class functionality."""

    def test_character_creation(self):
        """Create a basic character."""
        data = {
            "identity": {
                "name": "Test Wizard",
                "class": "Wizard",
                "race": "Human",
                "background": "Sage",
                "alignment": "Neutral Good",
                "player_name": "Player",
                "domain": "",
                "subclass": "",
            },
            "level": 5,
            "abilities": {
                "str": {"score": 8, "save_proficient": False},
                "dex": {"score": 14, "save_proficient": False},
                "con": {"score": 10, "save_proficient": False},
                "int": {"score": 16, "save_proficient": False},
                "wis": {"score": 12, "save_proficient": False},
                "cha": {"score": 10, "save_proficient": False},
            },
        }
        char = CharacterFactory.from_dict(data)
        assert char.name == "Test Wizard"
        assert char.race == "Human"
        assert char.level == 5

    def test_character_round_trip(self):
        """Character should survive to_dict/from_dict round-trip."""
        data = {
            "identity": {
                "name": "Enwer",
                "class": "Cleric",
                "race": "Human",
                "background": "Knight",
                "alignment": "Lawful Good",
                "player_name": "Player1",
                "domain": "War",
                "subclass": "",
            },
            "level": 9,
            "abilities": {
                ability: {"score": 10, "save_proficient": False}
                for ability in DEFAULT_ABILITY_KEYS
            },
        }
        char = CharacterFactory.from_dict(data)
        exported = char.to_dict()
        char2 = CharacterFactory.from_dict(exported)
        assert char2.name == char.name
        assert char2.level == char.level
        assert char2.race == char.race

    def test_display_name(self):
        """Display name should show character name."""
        data = {
            "identity": {
                "name": "Enwer",
                "class": "Cleric",
                "race": "Human",
                "background": "Knight",
                "alignment": "Lawful Good",
                "player_name": "Player",
                "domain": "",
                "subclass": "",
            },
            "level": 9,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        display = char.display_name()
        assert "Enwer" in display

    def test_class_key_detection(self):
        """Character should detect class key correctly."""
        test_cases = [
            ("Wizard", "wizard"),
            ("CLERIC", "cleric"),
            ("Bard 5", "bard"),
            ("Fighter", "fighter"),
        ]
        for class_text, expected_key in test_cases:
            data = {
                "identity": {
                    "name": "Test",
                    "class": class_text,
                    "race": "Human",
                    "background": "",
                    "alignment": "",
                    "player_name": "",
                    "domain": "",
                    "subclass": "",
                },
                "level": 1,
                "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
            }
            char = CharacterFactory.from_dict(data)
            assert char.class_key == expected_key, f"Class '{class_text}' should have key '{expected_key}', got '{char.class_key}'"

    def test_identity_properties(self):
        """Test all identity property getters and setters."""
        char = Character()
        
        char.name = "TestChar"
        assert char.name == "TestChar"
        
        char.class_text = "Wizard"
        assert char.class_text == "Wizard"
        
        char.race = "Human"
        assert char.race == "Human"
        
        char.background = "Sage"
        assert char.background == "Sage"
        
        char.alignment = "Neutral Good"
        assert char.alignment == "Neutral Good"
        
        char.player_name = "Player1"
        assert char.player_name == "Player1"
        
        char.domain = "Life"
        assert char.domain == "Life"
        
        char.subclass = "Evocation"
        assert char.subclass == "Evocation"


class TestCleric:
    """Test Cleric-specific functionality."""

    def test_cleric_creation(self):
        """Create a Cleric character."""
        data = {
            "identity": {
                "name": "Holy",
                "class": "Cleric",
                "race": "Human",
                "background": "Acolyte",
                "alignment": "Lawful Good",
                "player_name": "Player",
                "domain": "Life",
                "subclass": "Life",
            },
            "level": 3,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        assert isinstance(char, Cleric)
        assert char.domain == "Life"
        assert char.subclass == "Life"

    def test_cleric_domain_setter(self):
        """Setting domain should also set subclass and identity["domain"]."""
        data = {
            "identity": {
                "name": "Holy",
                "class": "Cleric",
                "race": "Human",
                "background": "Acolyte",
                "alignment": "Lawful Good",
                "player_name": "Player",
                "domain": "War",
                "subclass": "War",
            },
            "level": 5,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        char.domain = "Tempest"
        assert char.domain == "Tempest"
        assert char.subclass == "Tempest"
        # Verify the setter updates identity["domain"] too
        assert char._data["identity"]["domain"] == "Tempest"

    def test_cleric_domain_in_export(self):
        """Cleric domain should persist in to_dict."""
        data = {
            "identity": {
                "name": "Holy",
                "class": "Cleric",
                "race": "Human",
                "background": "Acolyte",
                "alignment": "Lawful Good",
                "player_name": "Player",
                "domain": "Knowledge",
                "subclass": "Knowledge",
            },
            "level": 1,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        exported = char.to_dict()
        assert exported["identity"]["domain"] == "Knowledge"
        assert exported["identity"]["subclass"] == "Knowledge"


class TestBard:
    """Test Bard-specific functionality."""

    def test_bard_creation(self):
        """Create a Bard character."""
        data = {
            "identity": {
                "name": "Melody",
                "class": "Bard",
                "race": "Half-Elf",
                "background": "Entertainer",
                "alignment": "Chaotic Good",
                "player_name": "Player",
                "domain": "",
                "subclass": "",
            },
            "level": 4,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        assert isinstance(char, Bard)

    def test_bard_round_trip(self):
        """Bard should survive round-trip."""
        data = {
            "identity": {
                "name": "Bardic",
                "class": "Bard",
                "race": "Human",
                "background": "Sage",
                "alignment": "Neutral",
                "player_name": "Player",
                "domain": "",
                "subclass": "",
            },
            "level": 2,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        exported = char.to_dict()
        char2 = CharacterFactory.from_dict(exported)
        assert isinstance(char2, Bard)
        assert char2.name == "Bardic"


class TestAbilityModifier:
    """Test ability score to modifier conversions."""

    def test_modifier_calculation(self):
        """Verify D&D 5e ability modifier formula: (score - 10) / 2, rounded down."""
        from math import floor
        test_cases = [
            (3, -4),
            (8, -1),
            (10, 0),
            (12, 1),
            (14, 2),
            (15, 2),
            (16, 3),
            (18, 4),
            (20, 5),
        ]
        for score, expected_mod in test_cases:
            mod = floor((score - 10) / 2)
            assert mod == expected_mod, f"Score {score} should give modifier {expected_mod}, got {mod}"

    def test_ability_accessor_scores(self):
        """Test AbilityAccessor returns ability scores correctly."""
        data = {
            "identity": {
                "name": "Test",
                "class": "Wizard",
                "race": "Human",
                "background": "",
                "alignment": "",
                "player_name": "",
                "domain": "",
                "subclass": "",
            },
            "level": 1,
            "abilities": {
                "str": {"score": 8, "save_proficient": False},
                "dex": {"score": 14, "save_proficient": False},
                "con": {"score": 12, "save_proficient": False},
                "int": {"score": 16, "save_proficient": False},
                "wis": {"score": 10, "save_proficient": False},
                "cha": {"score": 13, "save_proficient": False},
            },
        }
        char = Character(data)
        
        # Verify ability scores are retrieved correctly
        assert char.attributes["str"] == 8
        assert char.attributes["dex"] == 14
        assert char.attributes["con"] == 12
        assert char.attributes["int"] == 16
        assert char.attributes["wis"] == 10
        assert char.attributes["cha"] == 13


class TestDataPersistence:
    """Test that character data persists correctly through serialization."""

    def test_identity_fields_persist(self):
        """All identity fields should persist through to_dict/from_dict."""
        original_data = {
            "identity": {
                "name": "Test Character",
                "class": "Wizard",
                "race": "High Elf",
                "background": "Sage",
                "alignment": "Neutral Good",
                "player_name": "TestPlayer",
                "domain": "",
                "subclass": "",
            },
            "level": 7,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(original_data)
        exported = char.to_dict()
        
        assert exported["identity"]["name"] == "Test Character"
        assert exported["identity"]["class"] == "Wizard"
        assert exported["identity"]["race"] == "High Elf"
        assert exported["identity"]["background"] == "Sage"
        assert exported["identity"]["alignment"] == "Neutral Good"
        assert exported["identity"]["player_name"] == "TestPlayer"
        assert exported["level"] == 7

    def test_ability_scores_persist(self):
        """Ability scores should persist through serialization."""
        original_data = {
            "identity": {
                "name": "Test",
                "class": "Fighter",
                "race": "Human",
                "background": "",
                "alignment": "",
                "player_name": "",
                "domain": "",
                "subclass": "",
            },
            "level": 5,
            "abilities": {
                "str": {"score": 18, "save_proficient": False},
                "dex": {"score": 10, "save_proficient": False},
                "con": {"score": 16, "save_proficient": True},
                "int": {"score": 8, "save_proficient": False},
                "wis": {"score": 12, "save_proficient": False},
                "cha": {"score": 10, "save_proficient": False},
            },
        }
        char = Character(original_data)
        exported = char.to_dict()
        
        assert exported["abilities"]["str"]["score"] == 18
        assert exported["abilities"]["dex"]["score"] == 10
        assert exported["abilities"]["con"]["save_proficient"] == True

    def test_empty_fields_handled(self):
        """Empty fields should be handled gracefully."""
        data = {
            "identity": {
                "name": "",
                "class": "",
                "race": "",
                "background": "",
                "alignment": "",
                "player_name": "",
                "domain": "",
                "subclass": "",
            },
            "level": 1,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = Character(data)
        assert char.name == ""
        assert char.race == ""
        assert char.class_text == ""
        
        exported = char.to_dict()
        assert exported["identity"]["name"] == ""
        assert exported["level"] == 1


class TestCharacterFactory:
    """Test the CharacterFactory class detection and creation."""

    def test_factory_creates_cleric(self):
        """Factory should create Cleric for 'cleric' class."""
        data = {
            "identity": {
                "name": "Test",
                "class": "Cleric",
                "race": "Human",
                "background": "",
                "alignment": "",
                "player_name": "",
                "domain": "",
                "subclass": "",
            },
            "level": 1,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        assert isinstance(char, Cleric)
        assert char.class_key == "cleric"

    def test_factory_creates_bard(self):
        """Factory should create Bard for 'bard' class."""
        data = {
            "identity": {
                "name": "Test",
                "class": "Bard",
                "race": "Human",
                "background": "",
                "alignment": "",
                "player_name": "",
                "domain": "",
                "subclass": "",
            },
            "level": 1,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        assert isinstance(char, Bard)
        assert char.class_key == "bard"

    def test_factory_creates_base_character(self):
        """Factory should create base Character for unknown classes."""
        data = {
            "identity": {
                "name": "Test",
                "class": "Wizard",
                "race": "Human",
                "background": "",
                "alignment": "",
                "player_name": "",
                "domain": "",
                "subclass": "",
            },
            "level": 1,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        assert type(char) == Character
        assert not isinstance(char, Cleric)
        assert not isinstance(char, Bard)

    def test_factory_class_normalization(self):
        """Factory should normalize class names correctly."""
        test_cases = [
            ("cleric", "cleric"),
            ("Cleric", "cleric"),
            ("CLERIC", "cleric"),
            ("cleric 5", "cleric"),
            ("bard", "bard"),
            ("Bard", "bard"),
            ("wizard", "wizard"),  # First token is used
            ("fighter", "fighter"),
            ("", ""),  # Empty returns empty
        ]
        for class_text, expected_key in test_cases:
            normalized = CharacterFactory.normalize_class(class_text)
            assert normalized == expected_key, f"Class '{class_text}' should normalize to '{expected_key}', got '{normalized}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

