"""
Test Manager List Properties

Tests the new list properties added to managers that return table-ready objects:
- WeaponsCollectionManager.equipped_weapons
- ArmorCollectionManager.equipped_armor_items, unequipped_armor_items, all_armor_items
"""

import sys
import os
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'py'))

from weapons_manager import WeaponsCollectionManager, WeaponEntity
from armor_manager import ArmorCollectionManager, ArmorEntity


class MockInventoryManager:
    """Mock inventory manager for testing."""
    
    def __init__(self, items=None):
        self.items = items or []


class TestWeaponsManagerEquippedProperty(unittest.TestCase):
    """Test WeaponsCollectionManager.equipped_weapons property."""
    
    def test_equipped_weapons_empty_when_no_inventory(self):
        """equipped_weapons returns empty list when no inventory manager."""
        manager = WeaponsCollectionManager()
        self.assertEqual(manager.equipped_weapons, [])
    
    def test_equipped_weapons_empty_when_no_items(self):
        """equipped_weapons returns empty list when no weapons in inventory."""
        inventory = MockInventoryManager(items=[])
        manager = WeaponsCollectionManager(inventory)
        self.assertEqual(manager.equipped_weapons, [])
    
    def test_equipped_weapons_returns_equipped_only(self):
        """equipped_weapons returns only equipped weapons."""
        inventory = MockInventoryManager(items=[
            {"id": "weapon1", "name": "Mace", "category": "weapons", "equipped": True},
            {"id": "weapon2", "name": "Crossbow", "category": "weapons", "equipped": True},
            {"id": "weapon3", "name": "Axe", "category": "weapons", "equipped": False},  # Not equipped
        ])
        manager = WeaponsCollectionManager(inventory)
        
        equipped = manager.equipped_weapons
        self.assertEqual(len(equipped), 2)
        weapon_names = [w.final_name for w in equipped]
        self.assertIn("Mace", weapon_names)
        self.assertIn("Crossbow", weapon_names)
        self.assertNotIn("Axe", weapon_names)
    
    def test_equipped_weapons_excludes_armor(self):
        """equipped_weapons excludes armor items even if category is weapons."""
        inventory = MockInventoryManager(items=[
            {"id": "weapon1", "name": "Mace", "category": "weapons", "equipped": True},
            {"id": "armor1", "name": "Breastplate", "category": "weapons", "equipped": True},  # Armor by name
            {"id": "armor2", "name": "Shield", "category": "weapons", "equipped": True},  # Shield by name
        ])
        manager = WeaponsCollectionManager(inventory)
        
        equipped = manager.equipped_weapons
        self.assertEqual(len(equipped), 1)
        self.assertEqual(equipped[0].final_name, "Mace")
    
    def test_equipped_weapons_returns_weapon_entities(self):
        """equipped_weapons returns WeaponEntity objects."""
        inventory = MockInventoryManager(items=[
            {"id": "weapon1", "name": "Dagger", "category": "weapons", "equipped": True},
        ])
        manager = WeaponsCollectionManager(inventory)
        
        equipped = manager.equipped_weapons
        self.assertEqual(len(equipped), 1)
        self.assertIsInstance(equipped[0], WeaponEntity)
    
    def test_equipped_weapons_filters_by_category(self):
        """equipped_weapons only returns items with weapons category."""
        inventory = MockInventoryManager(items=[
            {"id": "weapon1", "name": "Sword", "category": "weapons", "equipped": True},
            {"id": "weapon2", "name": "Spear", "category": "weapon", "equipped": True},  # Singular form
            {"id": "item1", "name": "Rope", "category": "gear", "equipped": True},  # Not a weapon
        ])
        manager = WeaponsCollectionManager(inventory)
        
        equipped = manager.equipped_weapons
        self.assertEqual(len(equipped), 2)
        weapon_names = [w.final_name for w in equipped]
        self.assertIn("Sword", weapon_names)
        self.assertIn("Spear", weapon_names)
        self.assertNotIn("Rope", weapon_names)


class TestArmorManagerListProperties(unittest.TestCase):
    """Test ArmorCollectionManager list properties."""
    
    def test_equipped_armor_items_empty_when_no_inventory(self):
        """equipped_armor_items returns empty list when no inventory manager."""
        manager = ArmorCollectionManager()
        self.assertEqual(manager.equipped_armor_items, [])
    
    def test_equipped_armor_items_returns_equipped_only(self):
        """equipped_armor_items returns only equipped armor/shields."""
        inventory = MockInventoryManager(items=[
            {"id": "armor1", "name": "Breastplate", "category": "armor", "equipped": True},
            {"id": "armor2", "name": "Shield", "category": "shield", "equipped": True},
            {"id": "armor3", "name": "Chain Mail", "category": "armor", "equipped": False},  # In backpack
        ])
        manager = ArmorCollectionManager(inventory)
        
        equipped = manager.equipped_armor_items
        self.assertEqual(len(equipped), 2)
        armor_names = [a.final_name for a in equipped]
        self.assertIn("Breastplate", armor_names)
        self.assertIn("Shield", armor_names)
        self.assertNotIn("Chain Mail", armor_names)
    
    def test_unequipped_armor_items_returns_backpack_only(self):
        """unequipped_armor_items returns only armor not equipped."""
        inventory = MockInventoryManager(items=[
            {"id": "armor1", "name": "Breastplate", "category": "armor", "equipped": True},
            {"id": "armor2", "name": "Chain Mail", "category": "armor", "equipped": False},
            {"id": "armor3", "name": "Leather Armor", "category": "armor", "equipped": False},
        ])
        manager = ArmorCollectionManager(inventory)
        
        unequipped = manager.unequipped_armor_items
        self.assertEqual(len(unequipped), 2)
        armor_names = [a.final_name for a in unequipped]
        self.assertIn("Chain Mail", armor_names)
        self.assertIn("Leather Armor", armor_names)
        self.assertNotIn("Breastplate", armor_names)
    
    def test_all_armor_items_returns_everything(self):
        """all_armor_items returns both equipped and unequipped armor."""
        inventory = MockInventoryManager(items=[
            {"id": "armor1", "name": "Breastplate", "category": "armor", "equipped": True},
            {"id": "armor2", "name": "Chain Mail", "category": "armor", "equipped": False},
            {"id": "armor3", "name": "Shield", "category": "shield", "equipped": True},
        ])
        manager = ArmorCollectionManager(inventory)
        
        all_armor = manager.all_armor_items
        self.assertEqual(len(all_armor), 3)
        armor_names = [a.final_name for a in all_armor]
        self.assertIn("Breastplate", armor_names)
        self.assertIn("Chain Mail", armor_names)
        self.assertIn("Shield", armor_names)
    
    def test_armor_properties_return_armor_entities(self):
        """All armor list properties return ArmorEntity objects."""
        inventory = MockInventoryManager(items=[
            {"id": "armor1", "name": "Breastplate", "category": "armor", "equipped": True},
            {"id": "armor2", "name": "Chain Mail", "category": "armor", "equipped": False},
        ])
        manager = ArmorCollectionManager(inventory)
        
        for armor in manager.equipped_armor_items:
            self.assertIsInstance(armor, ArmorEntity)
        
        for armor in manager.unequipped_armor_items:
            self.assertIsInstance(armor, ArmorEntity)
        
        for armor in manager.all_armor_items:
            self.assertIsInstance(armor, ArmorEntity)
    
    def test_armor_properties_filter_by_category(self):
        """Armor properties only include armor/armour/shield categories."""
        inventory = MockInventoryManager(items=[
            {"id": "armor1", "name": "Breastplate", "category": "armor", "equipped": True},
            {"id": "armor2", "name": "Chain Mail", "category": "armour", "equipped": True},  # British spelling
            {"id": "armor3", "name": "Shield", "category": "shield", "equipped": True},
            {"id": "weapon1", "name": "Mace", "category": "weapons", "equipped": True},  # Not armor
        ])
        manager = ArmorCollectionManager(inventory)
        
        equipped = manager.equipped_armor_items
        self.assertEqual(len(equipped), 3)
        armor_names = [a.final_name for a in equipped]
        self.assertNotIn("Mace", armor_names)


class TestManagerListPropertiesIntegration(unittest.TestCase):
    """Test integration scenarios with list properties."""
    
    def test_equipped_lists_dont_include_same_item(self):
        """Equipped weapons and equipped armor lists are mutually exclusive."""
        inventory = MockInventoryManager(items=[
            {"id": "weapon1", "name": "Mace", "category": "weapons", "equipped": True},
            {"id": "armor1", "name": "Breastplate", "category": "armor", "equipped": True},
        ])
        
        weapons_manager = WeaponsCollectionManager(inventory)
        armor_manager = ArmorCollectionManager(inventory)
        
        weapon_ids = [w.entity.get("id") for w in weapons_manager.equipped_weapons]
        armor_ids = [a.entity.get("id") for a in armor_manager.equipped_armor_items]
        
        # No overlap between weapons and armor
        self.assertEqual(set(weapon_ids) & set(armor_ids), set())
    
    def test_empty_lists_when_nothing_equipped(self):
        """All equipped lists are empty when nothing is equipped."""
        inventory = MockInventoryManager(items=[
            {"id": "weapon1", "name": "Mace", "category": "weapons", "equipped": False},
            {"id": "armor1", "name": "Breastplate", "category": "armor", "equipped": False},
        ])
        
        weapons_manager = WeaponsCollectionManager(inventory)
        armor_manager = ArmorCollectionManager(inventory)
        
        self.assertEqual(weapons_manager.equipped_weapons, [])
        self.assertEqual(armor_manager.equipped_armor_items, [])


if __name__ == '__main__':
    unittest.main()
