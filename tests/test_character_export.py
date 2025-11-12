"""Unit tests for character data export and collection logic.

These tests focus on the pure Python logic for collecting and exporting
character data, without depending on DOM/PyScript functionality.
"""

import pytest
import sys
import json
from pathlib import Path

# Add assets/py to path
sys.path.insert(0, str(Path(__file__).parent.parent / "assets" / "py"))

from character_models import (
    Character,
    Cleric,
    Bard,
    CharacterFactory,
    get_race_ability_bonuses,
    DEFAULT_ABILITY_KEYS,
)


def create_basic_character():
    """Create a basic character for testing."""
    return {
        "identity": {
            "name": "BasicChar",
            "class": "Fighter",
            "race": "Human",
            "background": "Soldier",
            "alignment": "Lawful Neutral",
            "player_name": "TestPlayer",
            "domain": "",
            "subclass": "",
        },
        "level": 1,
        "abilities": {
            ability: {"score": 10, "save_proficient": False}
            for ability in DEFAULT_ABILITY_KEYS
        },
    }


class TestCharacterExportBasics:
    """Test basic character export functionality."""

    def test_to_dict_contains_all_sections(self):
        """Exported dict should contain all required sections."""
        data = create_basic_character()
        char = Character(data)
        exported = char.to_dict()
        
        required_sections = ["identity", "level", "abilities", "inspiration"]
        for section in required_sections:
            assert section in exported, f"Missing '{section}' in exported data"

    def test_to_dict_preserves_identity(self):
        """Export should preserve all identity fields."""
        data = {
            "identity": {
                "name": "TestChar",
                "class": "Wizard",
                "race": "High Elf",
                "background": "Sage",
                "alignment": "Neutral Good",
                "player_name": "Player1",
                "domain": "Knowledge",
                "subclass": "Evocation",
            },
            "level": 5,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = Character(data)
        exported = char.to_dict()
        identity = exported["identity"]
        
        assert identity["name"] == "TestChar"
        assert identity["class"] == "Wizard"
        assert identity["race"] == "High Elf"
        assert identity["background"] == "Sage"
        assert identity["alignment"] == "Neutral Good"
        assert identity["player_name"] == "Player1"
        assert identity["domain"] == "Knowledge"
        assert identity["subclass"] == "Evocation"

    def test_to_dict_preserves_level(self):
        """Export should preserve character level."""
        for level in [1, 5, 9, 20]:
            data = create_basic_character()
            data["level"] = level
            char = Character(data)
            exported = char.to_dict()
            assert exported["level"] == level

    def test_to_dict_preserves_abilities(self):
        """Export should preserve all ability scores and proficiencies."""
        data = {
            "identity": {n: "" for n in ["name", "class", "race", "background", "alignment", "player_name", "domain", "subclass"]},
            "level": 1,
            "abilities": {
                "str": {"score": 15, "save_proficient": True},
                "dex": {"score": 10, "save_proficient": False},
                "con": {"score": 14, "save_proficient": True},
                "int": {"score": 8, "save_proficient": False},
                "wis": {"score": 12, "save_proficient": False},
                "cha": {"score": 13, "save_proficient": False},
            },
        }
        char = Character(data)
        exported = char.to_dict()
        abilities = exported["abilities"]
        
        assert abilities["str"]["score"] == 15
        assert abilities["str"]["save_proficient"] == True
        assert abilities["dex"]["score"] == 10
        assert abilities["dex"]["save_proficient"] == False
        assert abilities["con"]["score"] == 14
        assert abilities["con"]["save_proficient"] == True


class TestClericExport:
    """Test Cleric-specific export behavior."""

    def test_cleric_domain_export(self):
        """Cleric export should include domain synced with subclass."""
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
            "level": 3,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        exported = char.to_dict()
        
        # Both should be present and equal
        assert exported["identity"]["domain"] == "War"
        assert exported["identity"]["subclass"] == "War"

    def test_cleric_domain_change_in_export(self):
        """Changing Cleric domain should be reflected in export."""
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
            "level": 1,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        char = CharacterFactory.from_dict(data)
        char.domain = "Tempest"
        exported = char.to_dict()
        
        assert exported["identity"]["domain"] == "Tempest"
        assert exported["identity"]["subclass"] == "Tempest"


class TestCharacterRoundTrip:
    """Test data integrity through export and re-import."""

    def test_simple_character_round_trip(self):
        """Simple character should survive export/import."""
        original_data = {
            "identity": {
                "name": "TestChar",
                "class": "Fighter",
                "race": "Human",
                "background": "Soldier",
                "alignment": "Lawful Neutral",
                "player_name": "Player",
                "domain": "",
                "subclass": "",
            },
            "level": 5,
            "abilities": {
                "str": {"score": 16, "save_proficient": True},
                "dex": {"score": 12, "save_proficient": False},
                "con": {"score": 14, "save_proficient": False},
                "int": {"score": 10, "save_proficient": False},
                "wis": {"score": 10, "save_proficient": False},
                "cha": {"score": 8, "save_proficient": False},
            },
        }
        
        # Export and re-import
        char1 = Character(original_data)
        exported = char1.to_dict()
        char2 = Character(exported)
        
        # Verify key fields match
        assert char2.name == char1.name
        assert char2.class_text == char1.class_text
        assert char2.race == char1.race
        assert char2.level == char1.level
        for ability in DEFAULT_ABILITY_KEYS:
            assert char2.attributes[ability] == char1.attributes[ability]

    def test_cleric_round_trip(self):
        """Cleric should preserve domain through round-trip."""
        original_data = {
            "identity": {
                "name": "Holy",
                "class": "Cleric",
                "race": "Human",
                "background": "Acolyte",
                "alignment": "Lawful Good",
                "player_name": "Player",
                "domain": "Tempest",
                "subclass": "Tempest",
            },
            "level": 7,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        
        char1 = CharacterFactory.from_dict(original_data)
        exported = char1.to_dict()
        char2 = CharacterFactory.from_dict(exported)
        
        assert isinstance(char2, Cleric)
        assert char2.domain == "Tempest"
        assert exported["identity"]["domain"] == "Tempest"

    def test_bard_round_trip(self):
        """Bard should survive round-trip."""
        original_data = {
            "identity": {
                "name": "Melodious",
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
        
        char1 = CharacterFactory.from_dict(original_data)
        exported = char1.to_dict()
        char2 = CharacterFactory.from_dict(exported)
        
        assert isinstance(char2, Bard)
        assert char2.name == "Melodious"


class TestDataDetection:
    """Test detecting when character data has changed."""

    def test_json_comparison_identity_field_change(self):
        """JSON should differ when identity field changes."""
        data1 = {
            "identity": {
                "name": "Character1",
                "class": "Wizard",
                "race": "Human",
                "background": "Sage",
                "alignment": "Neutral Good",
                "player_name": "Player",
                "domain": "",
                "subclass": "",
            },
            "level": 5,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        
        data2 = dict(data1)
        data2["identity"] = dict(data1["identity"])
        data2["identity"]["name"] = "Character2"
        
        json1 = json.dumps(CharacterFactory.from_dict(data1).to_dict(), indent=2, sort_keys=True)
        json2 = json.dumps(CharacterFactory.from_dict(data2).to_dict(), indent=2, sort_keys=True)
        
        assert json1 != json2

    def test_json_comparison_level_change(self):
        """JSON should differ when level changes."""
        data1 = create_basic_character()
        data1["level"] = 5
        
        data2 = create_basic_character()
        data2["level"] = 6
        
        json1 = json.dumps(CharacterFactory.from_dict(data1).to_dict(), indent=2, sort_keys=True)
        json2 = json.dumps(CharacterFactory.from_dict(data2).to_dict(), indent=2, sort_keys=True)
        
        assert json1 != json2

    def test_json_comparison_ability_change(self):
        """JSON should differ when ability scores change."""
        data1 = create_basic_character()
        data1["abilities"]["str"]["score"] = 10
        
        data2 = create_basic_character()
        data2["abilities"]["str"]["score"] = 15
        
        json1 = json.dumps(CharacterFactory.from_dict(data1).to_dict(), indent=2, sort_keys=True)
        json2 = json.dumps(CharacterFactory.from_dict(data2).to_dict(), indent=2, sort_keys=True)
        
        assert json1 != json2

    def test_json_same_when_unchanged(self):
        """JSON should be identical for the same data."""
        data = create_basic_character()
        
        char1 = CharacterFactory.from_dict(data)
        char2 = CharacterFactory.from_dict(data)
        
        json1 = json.dumps(char1.to_dict(), indent=2, sort_keys=True)
        json2 = json.dumps(char2.to_dict(), indent=2, sort_keys=True)
        
        assert json1 == json2


class TestExportFieldSyncing:
    """Test that special field syncing works correctly in exports."""

    def test_cleric_domain_subclass_sync_on_export(self):
        """When exporting Cleric, domain and subclass should be in sync."""
        # Create Cleric with domain
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
        
        cleric = CharacterFactory.from_dict(data)
        exported = cleric.to_dict()
        
        # Both fields should have the same value
        assert exported["identity"]["domain"] == exported["identity"]["subclass"]
        assert exported["identity"]["domain"] == "Knowledge"

    def test_non_cleric_domain_not_in_subclass(self):
        """Non-Cleric characters should have separate domain/subclass."""
        data = {
            "identity": {
                "name": "Test",
                "class": "Wizard",
                "race": "Human",
                "background": "Sage",
                "alignment": "Neutral",
                "player_name": "Player",
                "domain": "SomeDomain",
                "subclass": "Evocation",
            },
            "level": 5,
            "abilities": {ability: {"score": 10, "save_proficient": False} for ability in DEFAULT_ABILITY_KEYS},
        }
        
        char = Character(data)
        exported = char.to_dict()
        
        # Both should be preserved separately
        assert exported["identity"]["domain"] == "SomeDomain"
        assert exported["identity"]["subclass"] == "Evocation"


class TestExportConsistency:
    """Test that exports are consistent and deterministic."""

    def test_multiple_exports_identical(self):
        """Multiple exports of same character should produce identical JSON."""
        data = create_basic_character()
        char = CharacterFactory.from_dict(data)
        
        json1 = json.dumps(char.to_dict(), indent=2, sort_keys=True)
        json2 = json.dumps(char.to_dict(), indent=2, sort_keys=True)
        json3 = json.dumps(char.to_dict(), indent=2, sort_keys=True)
        
        assert json1 == json2 == json3

    def test_export_then_reimport_produces_identical_json(self):
        """Export, reimport, then export again should produce identical JSON."""
        original_data = create_basic_character()
        
        char1 = CharacterFactory.from_dict(original_data)
        json1 = json.dumps(char1.to_dict(), indent=2, sort_keys=True)
        
        exported = char1.to_dict()
        char2 = CharacterFactory.from_dict(exported)
        json2 = json.dumps(char2.to_dict(), indent=2, sort_keys=True)
        
        assert json1 == json2

    def test_multiple_round_trips_preserve_data(self):
        """Data should survive multiple export/import cycles."""
        original_data = create_basic_character()
        
        current = original_data
        for _ in range(5):
            char = CharacterFactory.from_dict(current)
            current = char.to_dict()
        
        # Verify data integrity after 5 round-trips
        char_final = CharacterFactory.from_dict(current)
        assert char_final.name == original_data["identity"]["name"]
        assert char_final.level == original_data["level"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
