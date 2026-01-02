"""
Test suite for character AC calculation with armor and shields.

Tests the calculate_armor_class() function directly.
"""

import json
import sys
from pathlib import Path

# Add static assets to path
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest


class MockInventoryManager:
    """Mock inventory manager for testing."""
    def __init__(self, items=None):
        self.items = items or []


class TestCalculateArmorClass:
    """Test the calculate_armor_class() function from character.py"""
    
    def test_no_armor_no_shield(self):
        """Base AC with no armor: 10 + DEX."""
        from character import calculate_armor_class, INVENTORY_MANAGER
        from unittest.mock import patch
        
        # Mock: no inventory
        with patch('character.INVENTORY_MANAGER', None):
            with patch('character.get_numeric_value') as mock_get:
                # DEX 10 = 0 modifier
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 10
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                assert ac == 10, f"Expected AC 10 (no armor, DEX 10), got {ac}"
    
    def test_breastplate_only(self):
        """Breastplate (14) + DEX 10 (0 mod) = 14."""
        from character import calculate_armor_class
        from unittest.mock import patch
        
        # Breastplate with AC 14
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 14})
            }
        ]
        
        mock_inv = MockInventoryManager(items)
        
        with patch('character.INVENTORY_MANAGER', mock_inv):
            with patch('character.get_numeric_value') as mock_get:
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 10  # DEX 10 = 0 modifier
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                assert ac == 14, f"Expected AC 14, got {ac}"
    
    def test_breastplate_plus_one_shield_only(self):
        """Breastplate +1 (15) + Shield (no bonus) should give 15 + 2 = 17."""
        from character import calculate_armor_class
        from unittest.mock import patch
        
        items = [
            {
                "id": "1",
                "name": "Breastplate +1",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 15, "bonus": 1})
            },
            {
                "id": "2",
                "name": "Shield",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"bonus": 0})
            }
        ]
        
        mock_inv = MockInventoryManager(items)
        
        with patch('character.INVENTORY_MANAGER', mock_inv):
            with patch('character.get_numeric_value') as mock_get:
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 10  # DEX 10 = 0 modifier
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                # Should be: 15 (armor) + 2 (shield base) = 17
                assert ac == 17, f"Expected AC 17 (15 + 2), got {ac}"
    
    def test_breastplate_plus_one_shield_plus_one(self):
        """Breastplate +1 (15) + Shield +1 (3) should give 15 + 3 = 18."""
        from character import calculate_armor_class
        from unittest.mock import patch
        
        items = [
            {
                "id": "1",
                "name": "Breastplate +1",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 15, "bonus": 1})
            },
            {
                "id": "2",
                "name": "Shield +1",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"bonus": 1})
            }
        ]
        
        mock_inv = MockInventoryManager(items)
        
        with patch('character.INVENTORY_MANAGER', mock_inv):
            with patch('character.get_numeric_value') as mock_get:
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 10  # DEX 10 = 0 modifier
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                # Should be: 15 (armor) + 2 (shield base) + 1 (shield bonus) = 18
                assert ac == 18, f"Expected AC 18 (15 + 3), got {ac}"
    
    def test_breastplate_with_low_dex(self):
        """Breastplate (14) + DEX 4 (mod -3, clamped to 0) should be 14."""
        from character import calculate_armor_class
        from unittest.mock import patch
        
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 14})
            }
        ]
        
        mock_inv = MockInventoryManager(items)
        
        with patch('character.INVENTORY_MANAGER', mock_inv):
            with patch('character.get_numeric_value') as mock_get:
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 4  # DEX 4 = -3 modifier, should be clamped to 0
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                # Medium armor: 14 + max(0, -3) = 14 + 0 = 14
                assert ac == 14, f"Expected AC 14 (no penalty for low DEX), got {ac}"
    
    def test_breastplate_with_high_dex(self):
        """Breastplate (14) + DEX 16 (mod +3, capped to +2 for medium) should be 16."""
        from character import calculate_armor_class
        from unittest.mock import patch
        
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 14})
            }
        ]
        
        mock_inv = MockInventoryManager(items)
        
        with patch('character.INVENTORY_MANAGER', mock_inv):
            with patch('character.get_numeric_value') as mock_get:
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 16  # DEX 16 = +3 modifier, capped to +2 for medium
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                # Medium armor: 14 + min(3, 2) = 14 + 2 = 16
                assert ac == 16, f"Expected AC 16 (DEX capped at +2), got {ac}"
    
    def test_shield_detection_by_name(self):
        """Shield detected by 'shield' in item name."""
        from character import calculate_armor_class
        from unittest.mock import patch
        
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 14})
            },
            {
                "id": "2",
                "name": "Wooden Shield",  # Contains "shield"
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({})
            }
        ]
        
        mock_inv = MockInventoryManager(items)
        
        with patch('character.INVENTORY_MANAGER', mock_inv):
            with patch('character.get_numeric_value') as mock_get:
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 10
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                # 14 (armor) + 2 (shield base) = 16
                assert ac == 16, f"Expected AC 16, got {ac}"
    
    def test_shield_detection_by_category(self):
        """Shield detected by category."""
        from character import calculate_armor_class
        from unittest.mock import patch
        
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 14})
            },
            {
                "id": "2",
                "name": "Kite Shield",
                "category": "shield",  # Shield category (lowercase)
                "equipped": True,
                "notes": json.dumps({})
            }
        ]
        
        mock_inv = MockInventoryManager(items)
        
        with patch('character.INVENTORY_MANAGER', mock_inv):
            with patch('character.get_numeric_value') as mock_get:
                def side_effect(element_id, default=10):
                    if "dex" in element_id:
                        return 10
                    return default
                mock_get.side_effect = side_effect
                
                ac = calculate_armor_class()
                # 14 (armor) + 2 (shield base) = 16
                assert ac == 16, f"Expected AC 16, got {ac}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
