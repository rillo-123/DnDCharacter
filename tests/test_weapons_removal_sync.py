"""
Unit tests for weapons grid synchronization with inventory removal.

Tests verify that when items are removed from the equipment inventory,
the weapons grid is automatically updated to remove those items as well.
"""

import sys
import json
sys.path.insert(0, 'static/assets/py')

import pytest
from equipment_management import InventoryManager


class TestWeaponsRemovalSync:
    """Test weapons grid sync when items are removed from inventory."""
    
    @pytest.fixture
    def inventory(self):
        """Create a fresh inventory manager for each test."""
        inv = InventoryManager()
        return inv
    
    def test_remove_equipped_weapon_disappears_from_grid(self, inventory):
        """
        When an equipped weapon is removed from inventory,
        it should no longer appear in the weapons grid.
        """
        # Setup: Add a weapon and equip it
        weapon_id = inventory.add_item(
            name="Longsword +1",
            category="Weapons",
            notes=json.dumps({
                "damage": "1d8",
                "damage_type": "slashing",
                "range": "Melee",
                "properties": "versatile"
            })
        )
        # Equip it
        inventory.update_item(weapon_id, {"equipped": True})
        
        # Verify weapon is in inventory
        assert len(inventory.items) == 1
        assert inventory.get_item(weapon_id) is not None
        
        # Get equipped weapons before removal
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 1
        assert equipped_weapons[0]["id"] == weapon_id
        
        # Action: Remove the weapon
        inventory.remove_item(weapon_id)
        
        # Verify: Weapon is removed from inventory
        assert len(inventory.items) == 0
        assert inventory.get_item(weapon_id) is None
        
        # Verify: No equipped weapons remain (weapons grid should be empty)
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 0
    
    def test_remove_unequipped_weapon_also_removed(self, inventory):
        """
        When an unequipped weapon is removed from inventory,
        it should not appear in the weapons grid (wasn't there anyway).
        """
        # Setup: Add weapon but don't equip it
        weapon_id = inventory.add_item(
            name="Dagger",
            category="Weapons",
            notes=json.dumps({
                "damage": "1d4",
                "damage_type": "piercing"
            })
        )
        
        # Verify weapon is in inventory but not equipped
        assert len(inventory.items) == 1
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 0
        
        # Action: Remove the weapon
        inventory.remove_item(weapon_id)
        
        # Verify: Weapon is removed
        assert len(inventory.items) == 0
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 0
    
    def test_remove_one_weapon_from_multiple(self, inventory):
        """
        When one weapon is removed from multiple equipped weapons,
        only that weapon should disappear from the grid.
        """
        # Setup: Add multiple equipped weapons
        weapon1_id = inventory.add_item(
            name="Longsword +1",
            category="Weapons",
            notes=json.dumps({"damage": "1d8", "damage_type": "slashing"})
        )
        weapon2_id = inventory.add_item(
            name="Crossbow, light",
            category="Weapons",
            notes=json.dumps({"damage": "1d8", "damage_type": "piercing"})
        )
        weapon3_id = inventory.add_item(
            name="Dagger",
            category="Weapons",
            notes=json.dumps({"damage": "1d4", "damage_type": "piercing"})
        )
        
        # Equip all
        inventory.update_item(weapon1_id, {"equipped": True})
        inventory.update_item(weapon2_id, {"equipped": True})
        inventory.update_item(weapon3_id, {"equipped": True})
        
        # Verify all 3 are equipped
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 3
        
        # Action: Remove one weapon
        inventory.remove_item(weapon2_id)
        
        # Verify: Only that weapon is removed
        assert len(inventory.items) == 2
        assert inventory.get_item(weapon2_id) is None
        assert inventory.get_item(weapon1_id) is not None
        assert inventory.get_item(weapon3_id) is not None
        
        # Verify: Grid should only show 2 weapons
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 2
        weapon_ids = {w["id"] for w in equipped_weapons}
        assert weapon_ids == {weapon1_id, weapon3_id}
    
    def test_remove_armor_does_not_affect_weapons_grid(self, inventory):
        """
        When armor is removed from inventory, it should not affect
        the weapons grid (armor is a different category).
        """
        # Setup: Add a weapon and armor
        weapon_id = inventory.add_item(
            name="Longsword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8", "damage_type": "slashing"})
        )
        armor_id = inventory.add_item(
            name="Plate Armor",
            category="Armor",
            notes="{}"
        )
        
        # Equip both
        inventory.update_item(weapon_id, {"equipped": True})
        inventory.update_item(armor_id, {"equipped": True})
        
        # Verify both are in inventory
        assert len(inventory.items) == 2
        
        # Verify only weapon is in weapons grid
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 1
        
        # Action: Remove the armor
        inventory.remove_item(armor_id)
        
        # Verify: Armor is removed but weapon remains
        assert len(inventory.items) == 1
        assert inventory.get_item(armor_id) is None
        assert inventory.get_item(weapon_id) is not None
        
        # Verify: Weapons grid still shows the weapon
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 1
        assert equipped_weapons[0]["id"] == weapon_id
    
    def test_remove_all_weapons_triggers_empty_state(self, inventory):
        """
        When all equipped weapons are removed, the weapons grid
        should show the empty state message.
        """
        # Setup: Add multiple weapons
        weapon_ids = []
        for i in range(3):
            weapon_id = inventory.add_item(
                name=f"Weapon {i}",
                category="Weapons",
                notes=json.dumps({"damage": "1d6"})
            )
            inventory.update_item(weapon_id, {"equipped": True})
            weapon_ids.append(weapon_id)
        
        # Verify all 3 are equipped
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 3
        
        # Action: Remove all weapons one by one
        inventory.remove_item(weapon_ids[0])
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 2
        
        inventory.remove_item(weapon_ids[1])
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 1
        
        inventory.remove_item(weapon_ids[2])
        
        # Verify: Inventory is empty
        assert len(inventory.items) == 0
        
        # Verify: No equipped weapons (empty state should be shown)
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 0
    
    def test_remove_weapon_by_different_id_formats(self, inventory):
        """
        Weapons should be properly identified and removed
        regardless of ID format (string, numeric, UUID-like).
        """
        # Setup: Add weapons (IDs will be auto-generated as "0", "1", etc)
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
        
        inventory.update_item(weapon1_id, {"equipped": True})
        inventory.update_item(weapon2_id, {"equipped": True})
        
        assert len(inventory.items) == 2
        
        # Remove by first ID
        inventory.remove_item(weapon1_id)
        assert len(inventory.items) == 1
        assert inventory.get_item(weapon1_id) is None
        assert inventory.get_item(weapon2_id) is not None
        
        # Remove by second ID
        inventory.remove_item(weapon2_id)
        assert len(inventory.items) == 0
    
    def test_remove_nonexistent_weapon_does_nothing(self, inventory):
        """
        Attempting to remove a weapon that doesn't exist
        should not cause errors.
        """
        # Setup: Add a weapon
        weapon_id = inventory.add_item(
            name="Sword",
            category="Weapons",
            notes=json.dumps({"damage": "1d8"})
        )
        inventory.update_item(weapon_id, {"equipped": True})
        assert len(inventory.items) == 1
        
        # Action: Try to remove non-existent weapon
        inventory.remove_item("999")
        
        # Verify: Original weapon still there
        assert len(inventory.items) == 1
        assert inventory.get_item(weapon_id) is not None
        
        # Verify: Weapons grid still shows the weapon
        equipped_weapons = [
            item for item in inventory.items
            if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]
        ]
        assert len(equipped_weapons) == 1
