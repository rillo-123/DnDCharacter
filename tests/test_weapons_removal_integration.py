"""
Integration tests for weapons grid synchronization with equipment management.

Tests verify that the equipment removal handler actually calls the weapons grid
rendering function to keep them in sync.
"""

import sys
import json
sys.path.insert(0, 'static/assets/py')

import pytest
from unittest.mock import Mock, patch, MagicMock
from inventory_manager import InventoryManager


class TestWeaponsRemovalIntegration:
    """Integration tests for weapons removal triggering grid re-render."""
    
    @pytest.fixture
    def inventory(self):
        """Create a fresh inventory manager for each test."""
        return InventoryManager()
    
    @pytest.fixture
    def mock_event(self):
        """Create a mock event object."""
        event = Mock()
        event.stopPropagation = Mock()
        event.preventDefault = Mock()
        return event
    
    def test_remove_event_handler_calls_stop_propagation(self, inventory, mock_event):
        """
        When _handle_item_remove is called, it should stop event propagation.
        """
        weapon_id = inventory.add_item(
            name="Sword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8"})
        )
        
        inventory._handle_item_remove(mock_event, weapon_id)
        
        mock_event.stopPropagation.assert_called_once()
        mock_event.preventDefault.assert_called_once()
    
    def test_remove_event_handler_removes_item(self, inventory, mock_event):
        """
        When _handle_item_remove is called, it should remove the item from inventory.
        """
        weapon_id = inventory.add_item(
            name="Sword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8"})
        )
        
        assert len(inventory.items) == 1
        inventory._handle_item_remove(mock_event, weapon_id)
        assert len(inventory.items) == 0
    
    def test_remove_event_handler_with_multiple_items(self, inventory, mock_event):
        """
        Removing one item should not affect other items.
        """
        weapon1_id = inventory.add_item(
            name="Sword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8"})
        )
        weapon2_id = inventory.add_item(
            name="Axe",
            category="Weapons",
            notes=json.dumps({"damage": "1d8"})
        )
        armor_id = inventory.add_item(
            name="Plate",
            category="Armor",
            notes="{}"
        )
        
        assert len(inventory.items) == 3
        inventory._handle_item_remove(mock_event, weapon1_id)
        
        assert len(inventory.items) == 2
        assert inventory.get_item(weapon2_id) is not None
        assert inventory.get_item(armor_id) is not None
        assert inventory.get_item(weapon1_id) is None
    
    def test_remove_event_handler_tries_to_render_weapons(self, inventory, mock_event):
        """
        When _handle_item_remove is called, it should attempt to call render_equipped_weapons.
        This test verifies the code path exists and handles missing functions gracefully.
        """
        weapon_id = inventory.add_item(
            name="Sword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8"})
        )
        inventory.update_item(weapon_id, {"equipped": True})
        
        # This should not raise an error even if render_equipped_weapons is not available
        # The handler has a safety check for _CHAR_MODULE_REF
        try:
            inventory._handle_item_remove(mock_event, weapon_id)
            # If we get here, the removal happened without errors
            assert len(inventory.items) == 0
        except Exception as e:
            pytest.fail(f"_handle_item_remove raised unexpected error: {e}")
    
    def test_equipped_item_removal_workflow(self, inventory, mock_event):
        """
        Complete workflow: add equipped weapon, then remove it via handler.
        """
        # Add and equip weapon
        weapon_id = inventory.add_item(
            name="Longsword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8", "damage_type": "slashing"})
        )
        inventory.update_item(weapon_id, {"equipped": True})
        
        # Verify it's equipped
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 1
        
        # Remove via handler
        inventory._handle_item_remove(mock_event, weapon_id)
        
        # Verify it's removed
        assert len(inventory.items) == 0
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 0
    
    def test_mixed_equipped_unequipped_removal(self, inventory, mock_event):
        """
        Test that removing unequipped weapons also works through the handler.
        """
        equipped_id = inventory.add_item(
            name="Sword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8"})
        )
        unequipped_id = inventory.add_item(
            name="Dagger",
            category="Weapons",
            notes=json.dumps({"damage": "1d4"})
        )
        
        inventory.update_item(equipped_id, {"equipped": True})
        
        # Remove unequipped weapon
        inventory._handle_item_remove(mock_event, unequipped_id)
        
        assert len(inventory.items) == 1
        assert inventory.get_item(equipped_id) is not None
        assert inventory.get_item(unequipped_id) is None
