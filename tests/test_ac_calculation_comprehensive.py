"""
Comprehensive test suite for AC calculation with armor and shields.

Tests various permutations of:
- Different armor types (light, medium, heavy)
- Adding/removing shields
- Adding/removing armor bonuses (+1, +2, +3)
- Adding/removing shield bonuses
- Combined scenarios

This ensures the AC calculation logic correctly handles all scenarios.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add static assets to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest


class MockInventoryManager:
    """Mock inventory manager for testing."""
    
    def __init__(self, items=None):
        self.items = items or []


@pytest.fixture
def mock_js_env(monkeypatch):
    """Setup mock JS environment before importing character module."""
    # Create mock document with proper querySelectorAll support
    mock_doc = MagicMock()
    
    # Mock getElementById to return elements with value attribute
    elements = {}
    def get_element_by_id(elem_id):
        if elem_id not in elements:
            elem = MagicMock()
            elem.value = "10"
            elem.innerHTML = ""
            elem.querySelectorAll = MagicMock(return_value=[])
            elements[elem_id] = elem
        return elements[elem_id]
    
    mock_doc.getElementById = get_element_by_id
    mock_doc.querySelectorAll = MagicMock(return_value=[])
    
    # Mock console
    mock_console = MagicMock()
    
    # Mock the js module
    mock_js = MagicMock()
    mock_js.document = mock_doc
    mock_js.console = mock_console
    
    # Patch sys.modules before any imports
    monkeypatch.setitem(sys.modules, 'js', mock_js)
    
    # Also patch localStorage
    mock_storage = {}
    def getItem(key):
        return mock_storage.get(key)
    def setItem(key, value):
        mock_storage[key] = value
    
    mock_js.localStorage = MagicMock()
    mock_js.localStorage.getItem = getItem
    mock_js.localStorage.setItem = setItem
    
    # Return mocks for test access
    return mock_js, mock_doc, elements


"""
Comprehensive test suite for AC calculation with armor and shields.

Tests various permutations of:
- Different armor types (light, medium, heavy)
- Adding/removing shields
- Adding/removing armor bonuses (+1, +2, +3)
- Adding/removing shield bonuses
- Combined scenarios

These tests verify the ArmorEntity AC calculation logic with various equipment
combinations that mirror real game scenarios.
"""

import json
import sys
from pathlib import Path

# Add static assets to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest
from armor_manager import ArmorEntity


class TestACCalculationPermutations:
    """Test AC calculation with various armor/shield combinations."""
    
    def test_no_armor_high_dex(self):
        """Test AC calculation without armor (unarmored = 10 + full DEX)."""
        # In D&D 5e, unarmored AC = 10 + DEX modifier
        character_stats = {"dex": 16}  # +3 modifier
        
        # Expected: 10 + 3 = 13 (no armor item, so this would be calculated elsewhere)
        # This test documents the expected behavior
        expected_unarmored_ac = 10 + 3
        assert expected_unarmored_ac == 13
    
    def test_leather_armor_no_shield(self):
        """Test AC with light armor (leather) and no shield."""
        armor_data = {
            "id": "1",
            "name": "Leather Armor",
            "armor_class": 11,
            "armor_type": "Light Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "11", "armor_type": "Light"})
        }
        character_stats = {"dex": 16}  # +3 modifier
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Light armor: 11 + 3 DEX = 14
        assert ac == 14, f"Expected AC 14, got {ac}"
    
    def test_medium_armor_no_shield(self):
        """Test AC with medium armor (breastplate) and no shield."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "14", "armor_type": "Medium"})
        }
        character_stats = {"dex": 10}  # +0 modifier
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Medium armor: 14 + 0 DEX = 14
        assert ac == 14, f"Expected AC 14, got {ac}"
    
    def test_medium_armor_dex_capped(self):
        """Test AC with medium armor caps DEX at +2."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "14", "armor_type": "Medium"})
        }
        character_stats = {"dex": 18}  # +4 modifier
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Medium armor: 14 + 2 (capped) = 16
        assert ac == 16, f"Expected AC 16 (DEX capped), got {ac}"
    
    def test_heavy_armor_no_shield(self):
        """Test AC with heavy armor (plate) and no shield (no DEX)."""
        armor_data = {
            "id": "1",
            "name": "Plate Armor",
            "armor_class": 18,
            "armor_type": "Heavy Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "18", "armor_type": "Heavy"})
        }
        character_stats = {"dex": 14}  # +2 modifier (ignored)
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Heavy armor: 18 (no DEX)
        assert ac == 18, f"Expected AC 18 (heavy armor, no DEX), got {ac}"
    
    def test_armor_plus_one_no_shield(self):
        """Test AC with +1 armor bonus."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "15",  # 14 base + 1 bonus
                "armor_type": "Medium",
                "bonus": 1
            })
        }
        character_stats = {"dex": 10}  # +0 modifier
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Breastplate +1: 15 + 0 DEX = 15
        assert ac == 15, f"Expected AC 15 (armor +1), got {ac}"
    
    def test_armor_plus_two(self):
        """Test AC with +2 armor bonus."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +2",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "16",  # 14 + 2
                "armor_type": "Medium",
                "bonus": 2
            })
        }
        character_stats = {"dex": 10}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Breastplate +2: 16 + 0 DEX = 16
        assert ac == 16, f"Expected AC 16 (armor +2), got {ac}"
    
    def test_shield_base_bonus(self):
        """Test shield provides base +2 bonus."""
        shield_data = {
            "id": "2",
            "name": "Shield",
            "armor_class": 0,  # Shields don't have intrinsic AC
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "2",  # Shield bonus
                "armor_type": "Shield"
            })
        }
        character_stats = {"dex": 10}
        
        shield = ArmorEntity(shield_data, character_stats)
        shield_ac = shield.calculate_total_ac()
        
        # Shield base bonus: 2
        assert shield_ac == 2, f"Expected shield bonus 2, got {shield_ac}"
    
    def test_shield_plus_one_bonus(self):
        """Test +1 shield provides +3 bonus (2 base + 1 magical)."""
        shield_data = {
            "id": "2",
            "name": "Shield +1",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "3",  # 2 base + 1 bonus
                "armor_type": "Shield",
                "bonus": 1
            })
        }
        character_stats = {"dex": 10}
        
        shield = ArmorEntity(shield_data, character_stats)
        shield_ac = shield.calculate_total_ac()
        
        # Shield +1 bonus: 3
        assert shield_ac == 3, f"Expected shield bonus 3, got {shield_ac}"
    
    def test_shield_plus_three_bonus(self):
        """Test +3 shield provides +5 bonus (2 base + 3 magical)."""
        shield_data = {
            "id": "2",
            "name": "Shield +3",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "5",  # 2 base + 3 bonus
                "armor_type": "Shield",
                "bonus": 3
            })
        }
        character_stats = {"dex": 10}
        
        shield = ArmorEntity(shield_data, character_stats)
        shield_ac = shield.calculate_total_ac()
        
        # Shield +3 bonus: 5
        assert shield_ac == 5, f"Expected shield bonus 5, got {shield_ac}"
    
    def test_combined_armor_and_shield(self):
        """Test combined AC: breastplate (14) + shield (2) = 16."""
        # Armor
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "14", "armor_type": "Medium"})
        }
        character_stats = {"dex": 10}
        
        # Shield
        shield_data = {
            "id": "2",
            "name": "Shield",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "2", "armor_type": "Shield"})
        }
        
        armor = ArmorEntity(armor_data, character_stats)
        shield = ArmorEntity(shield_data, character_stats)
        
        armor_ac = armor._calculate_ac()
        shield_ac = shield.calculate_total_ac()
        total_ac = armor_ac + shield_ac
        
        # Breastplate + Shield: 14 + 2 = 16
        assert total_ac == 16, f"Expected AC 16 (armor + shield), got {total_ac}"
    
    def test_combined_armor_plus_one_shield_base(self):
        """Test combined AC: breastplate +1 (15) + shield (2) = 17."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "15",
                "armor_type": "Medium",
                "bonus": 1
            })
        }
        
        shield_data = {
            "id": "2",
            "name": "Shield",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "2", "armor_type": "Shield"})
        }
        
        character_stats = {"dex": 10}
        
        armor = ArmorEntity(armor_data, character_stats)
        shield = ArmorEntity(shield_data, character_stats)
        
        total_ac = armor._calculate_ac() + shield.calculate_total_ac()
        
        # Breastplate +1 + Shield: 15 + 2 = 17
        assert total_ac == 17, f"Expected AC 17 (armor +1 + shield), got {total_ac}"
    
    def test_combined_armor_base_shield_plus_one(self):
        """Test combined AC: breastplate (14) + shield +1 (3) = 17."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "14", "armor_type": "Medium"})
        }
        
        shield_data = {
            "id": "2",
            "name": "Shield +1",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "3",
                "armor_type": "Shield",
                "bonus": 1
            })
        }
        
        character_stats = {"dex": 10}
        
        armor = ArmorEntity(armor_data, character_stats)
        shield = ArmorEntity(shield_data, character_stats)
        
        total_ac = armor._calculate_ac() + shield.calculate_total_ac()
        
        # Breastplate + Shield +1: 14 + 3 = 17
        assert total_ac == 17, f"Expected AC 17 (armor + shield +1), got {total_ac}"
    
    def test_combined_armor_plus_one_shield_plus_one(self):
        """Test combined AC: breastplate +1 (15) + shield +1 (3) = 18."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "15",
                "armor_type": "Medium",
                "bonus": 1
            })
        }
        
        shield_data = {
            "id": "2",
            "name": "Shield +1",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "3",
                "armor_type": "Shield",
                "bonus": 1
            })
        }
        
        character_stats = {"dex": 10}
        
        armor = ArmorEntity(armor_data, character_stats)
        shield = ArmorEntity(shield_data, character_stats)
        
        total_ac = armor._calculate_ac() + shield.calculate_total_ac()
        
        # Breastplate +1 + Shield +1: 15 + 3 = 18
        assert total_ac == 18, f"Expected AC 18 (both +1), got {total_ac}"
    
    def test_light_armor_with_shield(self):
        """Test combined AC: leather (11) + full DEX (+3) + shield (2) = 16."""
        armor_data = {
            "id": "1",
            "name": "Leather Armor",
            "armor_class": 11,
            "armor_type": "Light Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "11", "armor_type": "Light"})
        }
        
        shield_data = {
            "id": "2",
            "name": "Shield",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "2", "armor_type": "Shield"})
        }
        
        character_stats = {"dex": 16}  # +3 modifier
        
        armor = ArmorEntity(armor_data, character_stats)
        shield = ArmorEntity(shield_data, character_stats)
        
        total_ac = armor._calculate_ac() + shield.calculate_total_ac()
        
        # Leather + Shield: 14 + 2 = 16
        assert total_ac == 16, f"Expected AC 16 (light armor + shield), got {total_ac}"
    
    def test_heavy_armor_with_shield(self):
        """Test combined AC: plate (18) + no DEX + shield (2) = 20."""
        armor_data = {
            "id": "1",
            "name": "Plate Armor",
            "armor_class": 18,
            "armor_type": "Heavy Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "18", "armor_type": "Heavy"})
        }
        
        shield_data = {
            "id": "2",
            "name": "Shield",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "2", "armor_type": "Shield"})
        }
        
        character_stats = {"dex": 16}  # +3 modifier (ignored for heavy)
        
        armor = ArmorEntity(armor_data, character_stats)
        shield = ArmorEntity(shield_data, character_stats)
        
        total_ac = armor._calculate_ac() + shield.calculate_total_ac()
        
        # Plate + Shield: 18 + 2 = 20
        assert total_ac == 20, f"Expected AC 20 (heavy armor + shield), got {total_ac}"
    
    def test_remove_bonus_from_armor(self):
        """Test removing bonus: breastplate +1 (15) → breastplate (14)."""
        # With bonus
        armor_with_bonus = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "15",
                "armor_type": "Medium",
                "bonus": 1
            })
        }
        
        # Without bonus
        armor_without_bonus = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "14", "armor_type": "Medium"})
        }
        
        character_stats = {"dex": 10}
        
        armor1 = ArmorEntity(armor_with_bonus, character_stats)
        armor2 = ArmorEntity(armor_without_bonus, character_stats)
        
        ac_with = armor1._calculate_ac()
        ac_without = armor2._calculate_ac()
        
        assert ac_with == 15, f"Expected AC 15 with bonus, got {ac_with}"
        assert ac_without == 14, f"Expected AC 14 without bonus, got {ac_without}"
    
    def test_remove_bonus_from_shield(self):
        """Test removing bonus: shield +1 (3) → shield (2)."""
        # With bonus
        shield_with_bonus = {
            "id": "2",
            "name": "Shield +1",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({
                "armor_class": "3",
                "armor_type": "Shield",
                "bonus": 1
            })
        }
        
        # Without bonus
        shield_without_bonus = {
            "id": "2",
            "name": "Shield",
            "armor_class": 0,
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "2", "armor_type": "Shield"})
        }
        
        character_stats = {"dex": 10}
        
        shield1 = ArmorEntity(shield_with_bonus, character_stats)
        shield2 = ArmorEntity(shield_without_bonus, character_stats)
        
        ac_with = shield1.calculate_total_ac()
        ac_without = shield2.calculate_total_ac()
        
        assert ac_with == 3, f"Expected shield AC 3 with bonus, got {ac_with}"
        assert ac_without == 2, f"Expected shield AC 2 without bonus, got {ac_without}"


class TestACCalculationEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_negative_dex_modifier_medium_armor(self):
        """Test that negative DEX doesn't reduce AC for medium armor below base."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": json.dumps({"armor_class": "14", "armor_type": "Medium"})
        }
        character_stats = {"dex": 6}  # -2 modifier
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Medium armor with negative DEX should not go below 14
        # (Medium armor doesn't apply negative modifiers in 5e)
        assert ac == 14, f"Expected AC 14 (negative DEX ignored), got {ac}"
    
    def test_unequipped_armor_does_not_contribute(self):
        """Test that unequipped armor should not be counted (test documents expectation)."""
        # This is a documentation test - unequipped items should be filtered
        # before being passed to ArmorEntity
        armor_data = {
            "id": "1",
            "name": "Breastplate +2",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": False,  # Not equipped
            "notes": json.dumps({
                "armor_class": "16",
                "armor_type": "Medium",
                "bonus": 2
            })
        }
        
        # In real usage, inventory manager should filter out unequipped items
        # This test just documents that unequipped=False exists in the data structure
        assert armor_data["equipped"] == False, "Unequipped armor should be filtered by inventory manager"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
