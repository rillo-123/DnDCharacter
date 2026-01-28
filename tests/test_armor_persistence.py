"""Tests for armor bonus persistence and AC calculations.

Tests that armor +1 bonuses and other modifications persist across page reloads
by being stored in and retrieved from the notes field.
"""

import pytest
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from managers import ArmorEntity


class TestArmorBonusPersistence:
    """Test that armor bonuses persist across reloads via notes field."""
    
    def test_armor_with_ac_bonus_in_notes(self):
        """Test that AC value in notes takes priority over base armor_class."""
        # Simulate a Breastplate (base AC 14) with +1 bonus (modified AC 15)
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,  # Original definition
            "armor_type": "Medium Armor",
            "category": "armor",
            "notes": json.dumps({"armor_class": 15}),  # Modified to +1
            "equipped": True
        }
        
        character_stats = {"dex": 10}
        armor = ArmorEntity(armor_data, character_stats)
        
        # Should read from notes, not from armor_class field
        assert armor.final_ac == "15", "AC should be 15 from notes, not 14 from base"
    
    def test_armor_without_bonus_in_notes_uses_base(self):
        """Test that base armor_class is used when notes don't have armor_class."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "armor",
            "notes": json.dumps({"material": "steel"}),  # No armor_class in notes
            "equipped": True
        }
        
        character_stats = {"dex": 10}
        armor = ArmorEntity(armor_data, character_stats)
        
        assert armor.final_ac == "14", "Should use base armor_class when notes empty"
    
    def test_light_armor_with_bonus_applies_dex(self):
        """Test that DEX modifier is still applied to light armor bonuses."""
        # Leather (base AC 11) with +2 bonus (AC 13) + DEX +2 = 15
        armor_data = {
            "id": "1",
            "name": "Leather +2",
            "armor_class": 11,  # Base leather
            "armor_type": "Light Armor",
            "category": "armor",
            "notes": json.dumps({"armor_class": 13}),  # Modified to +2
            "equipped": True
        }
        
        character_stats = {"dex": 14}  # DEX +2
        armor = ArmorEntity(armor_data, character_stats)
        
        # Light armor: base 13 + DEX 2 = 15
        assert armor.final_ac == "15", "Light armor should add DEX modifier to bonus"
    
    def test_medium_armor_with_bonus_adds_dex(self):
        """Test that medium armor adds DEX modifier to bonuses (capped at +2)."""
        # Scale Mail (base AC 14) with +1 bonus (AC 15) + DEX +3 (capped at +2) = 17
        armor_data = {
            "id": "1",
            "name": "Scale Mail +1",
            "armor_class": 14,  # Base scale mail
            "armor_type": "Medium Armor",
            "category": "armor",
            "notes": json.dumps({"armor_class": 15}),  # Modified to +1
            "equipped": True
        }
        
        character_stats = {"dex": 16}  # DEX +3
        armor = ArmorEntity(armor_data, character_stats)
        
        # Medium armor: base 15 + DEX +2 (capped) = 17
        assert armor.final_ac == "17", "Medium armor should cap DEX modifier at +2"
    
    def test_heavy_armor_bonus_ignores_dex(self):
        """Test that heavy armor doesn't get DEX even with high DEX score."""
        # Plate (base AC 18) with no bonus, high DEX should not apply
        armor_data = {
            "id": "1",
            "name": "Plate",
            "armor_class": 18,
            "armor_type": "Heavy Armor",
            "category": "armor",
            "notes": json.dumps({}),  # No bonus
            "equipped": True
        }
        
        character_stats = {"dex": 20}  # High DEX, should be ignored
        armor = ArmorEntity(armor_data, character_stats)
        
        assert armor.final_ac == "18", "Heavy armor should not add DEX modifier"
    
    def test_heavy_armor_with_bonus_ignores_dex(self):
        """Test that heavy armor with bonus still doesn't get DEX."""
        # Plate (base AC 18) with +2 bonus (AC 20), high DEX should not apply
        armor_data = {
            "id": "1",
            "name": "Plate +2",
            "armor_class": 18,
            "armor_type": "Heavy Armor",
            "category": "armor",
            "notes": json.dumps({"armor_class": 20}),  # Modified to +2
            "equipped": True
        }
        
        character_stats = {"dex": 18}  # High DEX, should be ignored
        armor = ArmorEntity(armor_data, character_stats)
        
        assert armor.final_ac == "20", "Heavy armor bonus should not add DEX modifier"
    
    def test_shield_ignores_dex(self):
        """Test that shields don't get DEX modifier."""
        armor_data = {
            "id": "1",
            "name": "Shield +1",
            "armor_class": 2,  # Shield AC bonus
            "armor_type": "Shield",
            "category": "shield",
            "notes": json.dumps({"armor_class": 3}),  # Modified +1
            "equipped": True
        }
        
        character_stats = {"dex": 16}
        armor = ArmorEntity(armor_data, character_stats)
        
        assert armor.final_ac == "3", "Shield should not add DEX modifier"
    
    def test_empty_notes_returns_dash(self):
        """Test that zero or missing AC values return dash."""
        armor_data = {
            "id": "1",
            "name": "Unknown",
            "armor_class": 0,
            "armor_type": "Unknown",
            "category": "armor",
            "notes": "",
            "equipped": True
        }
        
        character_stats = {"dex": 10}
        armor = ArmorEntity(armor_data, character_stats)
        
        assert armor.final_ac == "—", "Zero AC should return dash"
    
    def test_malformed_notes_falls_back_to_base(self):
        """Test that malformed JSON in notes falls back to base armor_class."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "armor",
            "notes": "{bad json",  # Malformed
            "equipped": True
        }
        
        character_stats = {"dex": 10}
        armor = ArmorEntity(armor_data, character_stats)
        
        # Should fall back to base armor_class
        assert armor.final_ac == "14", "Should use base AC when notes JSON is malformed"
    
    def test_notes_with_multiple_properties_preserves_ac(self):
        """Test that other notes properties don't interfere with AC reading."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "armor",
            "material": "steel",
            "notes": json.dumps({
                "material": "enchanted steel",
                "armor_class": 15,
                "source": "dragon hoard"
            }),
            "equipped": True
        }
        
        character_stats = {"dex": 10}
        armor = ArmorEntity(armor_data, character_stats)
        
        # Should read armor_class from notes even with other properties
        assert armor.final_ac == "15", "Should read armor_class from complex notes"
    
    def test_negative_ac_in_notes_handled_gracefully(self):
        """Test that invalid (negative) AC values are handled."""
        armor_data = {
            "id": "1",
            "name": "Cursed Armor",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "armor",
            "notes": json.dumps({"armor_class": -5}),
            "equipped": True
        }
        
        character_stats = {"dex": 10}
        armor = ArmorEntity(armor_data, character_stats)
        
        # Negative or zero should return dash
        assert armor.final_ac == "—", "Negative AC should return dash"


class TestArmorEntityDisplay:
    """Test armor entity display properties."""
    
    def test_armor_name_display(self):
        """Test that armor name is displayed correctly."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "equipped": True
        }
        
        armor = ArmorEntity(armor_data, {})
        assert armor.final_name == "Breastplate +1"
    
    def test_armor_type_from_direct_field(self):
        """Test reading armor_type from direct field."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_type": "Medium Armor",
            "armor_class": 14,
            "equipped": True
        }
        
        armor = ArmorEntity(armor_data, {})
        assert armor.final_armor_type == "Medium Armor"
    
    def test_armor_type_from_notes(self):
        """Test reading armor_type from notes when not in direct field."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "notes": json.dumps({"armor_type": "Medium Armor"}),
            "equipped": True
        }
        
        armor = ArmorEntity(armor_data, {})
        assert armor.final_armor_type == "Medium Armor"
    
    def test_armor_class_full_description(self):
        """Test full armor class description with type and AC."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "notes": json.dumps({"armor_class": 15}),
            "equipped": True
        }
        
        character_stats = {"dex": 10}
        armor = ArmorEntity(armor_data, character_stats)
        
        # Should combine type and AC
        assert "Medium Armor" in armor.final_armor_class
        assert "15" in armor.final_armor_class


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
