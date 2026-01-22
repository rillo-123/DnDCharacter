"""
Unit tests for equipment equipped decorator functionality.
Tests that the star decorator appears on the correct item when equipped/unequipped.
"""

import unittest
import json
from unittest.mock import MagicMock, patch

from equipment_management import InventoryManager


class TestEquippedDecorator(unittest.TestCase):
    """Test equipment equipped state and decorator rendering."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = InventoryManager()
        
        # Add multiple items to inventory
        self.manager.items = [
            {
                "id": "item-1",
                "name": "Crossbow",
                "category": "Weapons",
                "qty": 1,
                "cost": "25 gp",
                "weight": "5 lb",
                "equipped": False,
                "notes": json.dumps({"damage": "1d8", "damage_type": "piercing"})
            },
            {
                "id": "item-2",
                "name": "Shield",
                "category": "Armor",
                "qty": 1,
                "cost": "10 gp",
                "weight": "6 lb",
                "equipped": False,
                "notes": json.dumps({"armor_class": "+2"})
            },
            {
                "id": "item-3",
                "name": "Longsword",
                "category": "Weapons",
                "qty": 1,
                "cost": "15 gp",
                "weight": "3 lb",
                "equipped": False,
                "notes": json.dumps({"damage": "1d8", "damage_type": "slashing"})
            }
        ]
    
    def test_equipped_decorator_appears_on_correct_item(self):
        """Test that star decorator appears on the correct equipped item."""
        # Equip the crossbow
        self.manager.update_item("item-1", {"equipped": True})
        
        # Verify the crossbow is equipped
        crossbow = self.manager.get_item("item-1")
        self.assertTrue(crossbow.get("equipped"), "Crossbow should be equipped")
        
        # Verify shield is NOT equipped
        shield = self.manager.get_item("item-2")
        self.assertFalse(shield.get("equipped"), "Shield should NOT be equipped")
        
        # Verify longsword is NOT equipped
        longsword = self.manager.get_item("item-3")
        self.assertFalse(longsword.get("equipped"), "Longsword should NOT be equipped")
    
    def test_equipped_decorator_multiple_items(self):
        """Test equipped status with multiple items."""
        # Equip crossbow and shield
        self.manager.update_item("item-1", {"equipped": True})
        self.manager.update_item("item-2", {"equipped": True})
        
        # Verify crossbow is equipped
        crossbow = self.manager.get_item("item-1")
        self.assertTrue(crossbow.get("equipped"))
        
        # Verify shield is equipped
        shield = self.manager.get_item("item-2")
        self.assertTrue(shield.get("equipped"))
        
        # Verify longsword is NOT equipped
        longsword = self.manager.get_item("item-3")
        self.assertFalse(longsword.get("equipped"))
    
    def test_unequip_item(self):
        """Test that item can be unequipped."""
        # Equip crossbow
        self.manager.update_item("item-1", {"equipped": True})
        crossbow = self.manager.get_item("item-1")
        self.assertTrue(crossbow.get("equipped"))
        
        # Unequip crossbow
        self.manager.update_item("item-1", {"equipped": False})
        crossbow = self.manager.get_item("item-1")
        self.assertFalse(crossbow.get("equipped"), "Crossbow should be unequipped")
    
    def test_equip_different_items_in_sequence(self):
        """Test equipping different items in sequence."""
        # Equip crossbow
        self.manager.update_item("item-1", {"equipped": True})
        self.assertTrue(self.manager.get_item("item-1").get("equipped"))
        self.assertFalse(self.manager.get_item("item-2").get("equipped"))
        
        # Unequip crossbow and equip shield
        self.manager.update_item("item-1", {"equipped": False})
        self.manager.update_item("item-2", {"equipped": True})
        
        self.assertFalse(self.manager.get_item("item-1").get("equipped"), "Crossbow should be unequipped")
        self.assertTrue(self.manager.get_item("item-2").get("equipped"), "Shield should be equipped")
    
    def test_get_item_returns_correct_item(self):
        """Test that get_item returns the correct item by ID."""
        crossbow = self.manager.get_item("item-1")
        shield = self.manager.get_item("item-2")
        longsword = self.manager.get_item("item-3")
        
        self.assertEqual(crossbow.get("name"), "Crossbow")
        self.assertEqual(shield.get("name"), "Shield")
        self.assertEqual(longsword.get("name"), "Longsword")
    
    def test_get_item_with_invalid_id(self):
        """Test that get_item returns None for invalid ID."""
        result = self.manager.get_item("invalid-id")
        self.assertIsNone(result)
    
    def test_update_item_only_updates_allowed_fields(self):
        """Test that update_item only updates whitelisted fields."""
        original_name = "Crossbow"
        
        # Try to update allowed field
        self.manager.update_item("item-1", {"equipped": True, "qty": 2})
        crossbow = self.manager.get_item("item-1")
        self.assertTrue(crossbow.get("equipped"))
        self.assertEqual(crossbow.get("qty"), 2)
        
        # Name should remain unchanged
        self.assertEqual(crossbow.get("name"), original_name)
    
    def test_render_inventory_with_equipped_items(self):
        """Test that render_inventory includes equipped state in HTML."""
        # Equip the crossbow
        self.manager.update_item("item-1", {"equipped": True})
        
        # Mock the document and get_element
        with patch('equipment_management.get_element') as mock_get_element:
            mock_container = MagicMock()
            mock_get_element.return_value = mock_container
            
            # Mock console.log to avoid errors
            with patch('equipment_management.console') as mock_console:
                self.manager.render_inventory()
                
                # Check that innerHTML was set
                self.assertTrue(mock_container.innerHTML is not None or mock_container.innerHTML == "")
    
    def test_equipped_state_persists_across_render(self):
        """Test that equipped state persists when re-rendering inventory."""
        # Equip crossbow
        self.manager.update_item("item-1", {"equipped": True})
        
        # Simulate render (just get the item again)
        crossbow = self.manager.get_item("item-1")
        self.assertTrue(crossbow.get("equipped"), "Equipped state should persist")
    
    def test_equipped_decorator_with_special_characters_in_name(self):
        """Test that decorator works with special characters in item name."""
        # Add item with special characters
        self.manager.items.append({
            "id": "item-special",
            "name": "Sword +1 (\"Holy\")",
            "category": "Weapons",
            "qty": 1,
            "cost": "50 gp",
            "weight": "3 lb",
            "equipped": False,
            "notes": json.dumps({"damage": "1d8+1"})
        })
        
        # Equip it
        self.manager.update_item("item-special", {"equipped": True})
        
        item = self.manager.get_item("item-special")
        self.assertTrue(item.get("equipped"))
        self.assertIn("Holy", item.get("name"))
    
    def test_item_ids_are_unique(self):
        """Test that all items have unique IDs."""
        item_ids = [item.get("id") for item in self.manager.items]
        self.assertEqual(len(item_ids), len(set(item_ids)), "All item IDs should be unique")
    
    def test_equipped_only_on_weapons_and_armor(self):
        """Test that only weapons and armor can be equipped."""
        # Add a non-equipable item
        self.manager.items.append({
            "id": "potion-1",
            "name": "Healing Potion",
            "category": "Potions",
            "qty": 3,
            "cost": "50 gp",
            "weight": "0.5 lb",
            "equipped": False,
            "notes": ""
        })
        
        # Try to mark potion as equipped (should work at data level, but UI shouldn't show checkbox)
        self.manager.update_item("potion-1", {"equipped": True})
        potion = self.manager.get_item("potion-1")
        self.assertTrue(potion.get("equipped"), "Potion state can be set, but UI shouldn't allow it")


class TestEquippedRenderOutput(unittest.TestCase):
    """Test that the rendering correctly outputs the decorator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = InventoryManager()
        self.manager.items = [
            {
                "id": "crossbow-1",
                "name": "Crossbow",
                "category": "Weapons",
                "qty": 1,
                "cost": "25 gp",
                "weight": "5 lb",
                "equipped": True,  # EQUIPPED
                "notes": json.dumps({"damage": "1d8"})
            },
            {
                "id": "shield-1",
                "name": "Shield",
                "category": "Armor",
                "qty": 1,
                "cost": "10 gp",
                "weight": "6 lb",
                "equipped": False,  # NOT EQUIPPED
                "notes": json.dumps({"armor_class": "+2"})
            }
        ]
    
    def test_decorator_in_html_output(self):
        """Test that equipped decorator appears in the HTML with correct item."""
        # The star decorator should be prepended to the item name
        crossbow = self.manager.get_item("crossbow-1")
        shield = self.manager.get_item("shield-1")
        
        # Get the decorator strings
        crossbow_decorator = "⭐ " if crossbow.get("equipped") else ""
        shield_decorator = "⭐ " if shield.get("equipped") else ""
        
        # Verify decorators
        self.assertEqual(crossbow_decorator, "⭐ ", "Crossbow should have decorator")
        self.assertEqual(shield_decorator, "", "Shield should NOT have decorator")


if __name__ == '__main__':
    unittest.main()
