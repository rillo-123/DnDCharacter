"""
Test ArmorCollectionManager Properties

Tests the AC calculation properties that expose the manager's state:
- armor_ac: AC from equipped armor piece (with DEX modifier)
- shield_ac: AC bonus from equipped shields
- other_ac: AC from non-armor sources (currently shields)
- total_ac: Complete AC calculation
"""

import sys
import os
import unittest
import json

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'py'))

from managers import ArmorCollectionManager


class MockInventoryManager:
    """Mock inventory manager for testing."""
    
    def __init__(self, items):
        self.items = items
    
    def update_item(self, item_id, updates):
        """Mock update method."""
        for item in self.items:
            if item.get("id") == item_id:
                item.update(updates)
                return True
        return False


class TestArmorManagerProperties(unittest.TestCase):
    """Test ArmorCollectionManager AC properties."""
    
    def test_no_armor_equipped_uses_unarmored_ac(self):
        """With no armor, total_ac should be 10 + DEX modifier."""
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": False,
                "notes": json.dumps({"armor_class": 14})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 14})  # DEX 14 = +2
        
        assert manager.armor_ac == 0, "armor_ac should be 0 when no armor equipped"
        assert manager.shield_ac == 0, "shield_ac should be 0 when no shields"
        assert manager.other_ac == 0, "other_ac should be 0 when no shields"
        assert manager.total_ac == 12, "total_ac should be 10 + 2 (unarmored)"
    
    def test_armor_only_no_shield(self):
        """With armor but no shield."""
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 14, "armor_type": "Medium"})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 16})  # DEX 16 = +3
        
        # Medium armor caps DEX at +2
        assert manager.armor_ac == 16, "armor_ac should be 14 + 2 (capped DEX)"
        assert manager.shield_ac == 0, "shield_ac should be 0"
        assert manager.other_ac == 0, "other_ac should be 0"
        assert manager.total_ac == 16, "total_ac should be 16"
    
    def test_armor_plus_shield(self):
        """With armor and shield equipped."""
        items = [
            {
                "id": "1",
                "name": "Breastplate",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 14, "armor_type": "Medium"})
            },
            {
                "id": "2",
                "name": "Shield",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 2, "armor_type": "Shield"})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 14})  # DEX 14 = +2
        
        assert manager.armor_ac == 16, "armor_ac should be 14 + 2"
        assert manager.shield_ac == 2, "shield_ac should be 2"
        assert manager.other_ac == 2, "other_ac should be 2 (from shield)"
        assert manager.total_ac == 18, "total_ac should be 16 + 2 = 18"
    
    def test_breastplate_plus_one_shield_plus_one(self):
        """Breastplate +1 (15) + Shield +1 (3) = 18."""
        items = [
            {
                "id": "1",
                "name": "Breastplate +1",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 15, "armor_type": "Medium", "bonus": 1})
            },
            {
                "id": "2",
                "name": "Shield +1",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 3, "armor_type": "Shield", "bonus": 1})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 10})  # DEX 10 = +0
        
        assert manager.armor_ac == 15, "armor_ac should be 15 (Breastplate +1 with no DEX bonus)"
        assert manager.shield_ac == 3, "shield_ac should be 3 (Shield +1)"
        assert manager.other_ac == 3, "other_ac should be 3 (from Shield +1)"
        assert manager.total_ac == 18, f"total_ac should be 18, got {manager.total_ac}"
    
    def test_light_armor_full_dex_bonus(self):
        """Light armor gets full DEX modifier."""
        items = [
            {
                "id": "1",
                "name": "Leather Armor",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 11, "armor_type": "Light"})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 18})  # DEX 18 = +4
        
        assert manager.armor_ac == 15, "armor_ac should be 11 + 4 (full DEX)"
        assert manager.shield_ac == 0, "shield_ac should be 0"
        assert manager.total_ac == 15, "total_ac should be 15"
    
    def test_heavy_armor_no_dex_bonus(self):
        """Heavy armor gets no DEX modifier."""
        items = [
            {
                "id": "1",
                "name": "Plate Armor",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 18, "armor_type": "Heavy"})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 16})  # DEX 16 = +3
        
        assert manager.armor_ac == 18, "armor_ac should be 18 (no DEX bonus)"
        assert manager.shield_ac == 0, "shield_ac should be 0"
        assert manager.total_ac == 18, "total_ac should be 18"
    
    def test_shield_only_no_armor(self):
        """Shield without armor uses unarmored AC + shield bonus."""
        items = [
            {
                "id": "1",
                "name": "Shield",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 2, "armor_type": "Shield"})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 16})  # DEX 16 = +3
        
        assert manager.armor_ac == 0, "armor_ac should be 0 (shield is not armor)"
        assert manager.shield_ac == 2, "shield_ac should be 2"
        assert manager.other_ac == 2, "other_ac should be 2"
        # Unarmored: 10 + 3 (DEX) + 2 (shield) = 15
        assert manager.total_ac == 15, "total_ac should be 15 (10 + 3 + 2)"
    
    def test_multiple_shields(self):
        """Multiple equipped shields stack (for testing purposes)."""
        items = [
            {
                "id": "1",
                "name": "Shield",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 2, "armor_type": "Shield"})
            },
            {
                "id": "2",
                "name": "Magic Shield",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 3, "armor_type": "Shield"})
            }
        ]
        
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 10})  # DEX 10 = +0
        
        assert manager.armor_ac == 0, "armor_ac should be 0"
        assert manager.shield_ac == 5, "shield_ac should be 2 + 3 = 5"
        assert manager.other_ac == 5, "other_ac should be 5"
        assert manager.total_ac == 15, "total_ac should be 10 + 5 = 15"
    
    def test_no_inventory_manager(self):
        """With no inventory manager, uses unarmored AC."""
        manager = ArmorCollectionManager(None, {"dex": 14})  # DEX 14 = +2
        
        assert manager.armor_ac == 0, "armor_ac should be 0"
        assert manager.shield_ac == 0, "shield_ac should be 0"
        assert manager.other_ac == 0, "other_ac should be 0"
        assert manager.total_ac == 12, "total_ac should be 10 + 2 = 12"
    
    def test_properties_are_read_only(self):
        """Properties should be read-only (no setters)."""
        items = []
        inventory = MockInventoryManager(items)
        manager = ArmorCollectionManager(inventory, {"dex": 10})
        
        # These should raise AttributeError when trying to set
        try:
            manager.total_ac = 20
            self.fail("total_ac should be read-only")
        except AttributeError:
            pass  # Expected
        
        try:
            manager.armor_ac = 15
            self.fail("armor_ac should be read-only")
        except AttributeError:
            pass  # Expected


if __name__ == "__main__":
    unittest.main()
