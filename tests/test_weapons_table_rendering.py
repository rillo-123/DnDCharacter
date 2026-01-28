"""
Unit tests for weapons table rendering.
Tests that weapons are correctly added, removed, equipped, and displayed in the skills table.
"""

import unittest
import json
from unittest.mock import MagicMock, patch, Mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from managers import InventoryManager
from tooltip_values import WeaponToHitValue


class TestWeaponTableRendering(unittest.TestCase):
    """Test weapons table rendering and equipped status."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = InventoryManager()
        
        # Create test weapons
        self.longsword = {
            "id": "weapon-1",
            "name": "Longsword",
            "category": "Weapons",
            "qty": 1,
            "cost": "15 gp",
            "weight": "3 lb",
            "equipped": False,
            "notes": json.dumps({"damage": "1d8", "damage_type": "slashing", "bonus": 0})
        }
        
        self.longsword_plus1 = {
            "id": "weapon-2",
            "name": "Longsword +1",
            "category": "Weapons",
            "qty": 1,
            "cost": "500 gp",
            "weight": "3 lb",
            "equipped": False,
            "notes": json.dumps({"damage": "1d8", "damage_type": "slashing", "bonus": 1})
        }
        
        self.light_crossbow = {
            "id": "weapon-3",
            "name": "Light Crossbow",
            "category": "Weapons",
            "qty": 1,
            "cost": "25 gp",
            "weight": "5 lb",
            "equipped": False,
            "notes": json.dumps({"damage": "1d8", "damage_type": "piercing", "bonus": 0})
        }
        
        self.dagger = {
            "id": "weapon-4",
            "name": "Dagger",
            "category": "Weapons",
            "qty": 2,
            "cost": "2 gp",
            "weight": "1 lb",
            "equipped": False,
            "notes": json.dumps({"damage": "1d4", "damage_type": "piercing", "bonus": 0})
        }
    
    def test_add_single_weapon_to_inventory(self):
        """Test adding a single weapon to inventory."""
        # Add longsword
        item_id = self.manager.add_item(
            name="Longsword",
            cost="15 gp",
            weight="3 lb",
            qty=1,
            category="Weapons",
            notes=json.dumps({"damage": "1d8", "damage_type": "slashing", "bonus": 0})
        )
        
        # Verify it was added
        self.assertEqual(len(self.manager.items), 1)
        weapon = self.manager.get_item(item_id)
        self.assertEqual(weapon["name"], "Longsword")
        self.assertFalse(weapon.get("equipped"), "Weapon should not be equipped by default")
    
    def test_add_multiple_weapons(self):
        """Test adding multiple weapons to inventory."""
        id1 = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        id2 = self.manager.add_item("Longsword +1", "500 gp", "3 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "slashing", "bonus": 1}))
        id3 = self.manager.add_item("Light Crossbow", "25 gp", "5 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "piercing"}))
        
        self.assertEqual(len(self.manager.items), 3)
        names = [item["name"] for item in self.manager.items]
        self.assertIn("Longsword", names)
        self.assertIn("Longsword +1", names)
        self.assertIn("Light Crossbow", names)
    
    def test_equip_weapon(self):
        """Test equipping a weapon."""
        item_id = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                        json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        
        # Equip the weapon
        self.manager.update_item(item_id, {"equipped": True})
        
        # Verify it's equipped
        weapon = self.manager.get_item(item_id)
        self.assertTrue(weapon.get("equipped"), "Weapon should be equipped")
    
    def test_unequip_weapon(self):
        """Test unequipping a weapon."""
        item_id = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                        json.dumps({"damage": "1d8", "damage_type": "slashing"}),
                                        source="custom")
        self.manager.update_item(item_id, {"equipped": True})
        
        # Unequip the weapon
        self.manager.update_item(item_id, {"equipped": False})
        
        # Verify it's unequipped
        weapon = self.manager.get_item(item_id)
        self.assertFalse(weapon.get("equipped"), "Weapon should be unequipped")
    
    def test_multiple_equipped_weapons(self):
        """Test having multiple equipped weapons (two-weapon fighting, etc)."""
        id1 = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        id2 = self.manager.add_item("Dagger", "2 gp", "1 lb", 2, "Weapons",
                                    json.dumps({"damage": "1d4", "damage_type": "piercing"}))
        
        # Equip both
        self.manager.update_item(id1, {"equipped": True})
        self.manager.update_item(id2, {"equipped": True})
        
        # Get equipped weapons only
        equipped = [item for item in self.manager.items if item.get("equipped")]
        self.assertEqual(len(equipped), 2)
        equipped_names = [item["name"] for item in equipped]
        self.assertIn("Longsword", equipped_names)
        self.assertIn("Dagger", equipped_names)
    
    def test_remove_weapon(self):
        """Test removing a weapon from inventory."""
        id1 = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        id2 = self.manager.add_item("Light Crossbow", "25 gp", "5 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "piercing"}))
        
        # Remove longsword
        self.manager.remove_item(id1)
        
        # Verify it's gone
        self.assertEqual(len(self.manager.items), 1)
        weapon = self.manager.get_item(id1)
        self.assertIsNone(weapon)
    
    def test_remove_equipped_weapon(self):
        """Test removing an equipped weapon."""
        item_id = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                        json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        self.manager.update_item(item_id, {"equipped": True})
        
        # Remove equipped weapon
        self.manager.remove_item(item_id)
        
        # Verify it's gone
        equipped = [item for item in self.manager.items if item.get("equipped")]
        self.assertEqual(len(equipped), 0)
    
    def test_weapon_with_bonus(self):
        """Test weapon with bonus (Longsword +1)."""
        item_id = self.manager.add_item("Longsword +1", "500 gp", "3 lb", 1, "Weapons",
                                        json.dumps({"damage": "1d8", "damage_type": "slashing", "bonus": 1}))
        self.manager.update_item(item_id, {"equipped": True})
        
        weapon = self.manager.get_item(item_id)
        notes = json.loads(weapon.get("notes", "{}"))
        self.assertEqual(notes.get("bonus"), 1, "Weapon should have +1 bonus")
    
    def test_equipped_weapons_only_shown_in_table(self):
        """Test that only equipped weapons appear in the table."""
        id1 = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        id2 = self.manager.add_item("Light Crossbow", "25 gp", "5 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "piercing"}))
        id3 = self.manager.add_item("Dagger", "2 gp", "1 lb", 2, "Weapons",
                                    json.dumps({"damage": "1d4", "damage_type": "piercing"}))
        
        # Equip only longsword
        self.manager.update_item(id1, {"equipped": True})
        
        # Filter equipped weapons
        equipped_weapons = [item for item in self.manager.items 
                           if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]]
        
        self.assertEqual(len(equipped_weapons), 1)
        self.assertEqual(equipped_weapons[0]["name"], "Longsword")
    
    def test_weapon_tohit_tooltip_value(self):
        """Test WeaponToHitValue tooltip generation for a weapon."""
        # Create tooltip value for Longsword
        w2h = WeaponToHitValue(
            weapon_name="Longsword",
            ability="str",
            ability_mod=3,
            proficiency=2,
            weapon_bonus=0
        )
        
        # Verify total
        self.assertEqual(w2h.total, 5, "Longsword to-hit should be 3 (STR) + 2 (Prof) = 5")
        
        # Verify HTML generation
        html = w2h.generate_tooltip_html()
        self.assertIn("stat-tooltip", html)
        self.assertIn("STR mod", html)
        self.assertIn("Proficiency", html)
    
    def test_weapon_tohit_tooltip_with_bonus(self):
        """Test WeaponToHitValue tooltip with weapon bonus."""
        w2h = WeaponToHitValue(
            weapon_name="Longsword +1",
            ability="str",
            ability_mod=3,
            proficiency=2,
            weapon_bonus=1
        )
        
        # Verify total
        self.assertEqual(w2h.total, 6, "Longsword +1 should be 3 + 2 + 1 = 6")
        
        # Verify HTML includes weapon bonus
        html = w2h.generate_tooltip_html()
        self.assertIn("Weapon bonus", html)
        self.assertIn("+1", html)
    
    def test_ranged_weapon_uses_dex(self):
        """Test that ranged weapons use DEX modifier in tooltip."""
        w2h = WeaponToHitValue(
            weapon_name="Light Crossbow",
            ability="dex",
            ability_mod=2,
            proficiency=2,
            weapon_bonus=0
        )
        
        html = w2h.generate_tooltip_html()
        self.assertIn("DEX", html, "Crossbow tooltip should use DEX")
    
    def test_weapon_damage_in_notes(self):
        """Test that weapon damage is correctly stored and retrieved."""
        item_id = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                        json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        
        weapon = self.manager.get_item(item_id)
        notes = json.loads(weapon.get("notes", "{}"))
        
        self.assertEqual(notes.get("damage"), "1d8")
        self.assertEqual(notes.get("damage_type"), "slashing")
    
    def test_equip_unequip_cycle(self):
        """Test equipping and unequipping a weapon multiple times."""
        item_id = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                        json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        
        # Equip
        self.manager.update_item(item_id, {"equipped": True})
        self.assertTrue(self.manager.get_item(item_id).get("equipped"))
        
        # Unequip
        self.manager.update_item(item_id, {"equipped": False})
        self.assertFalse(self.manager.get_item(item_id).get("equipped"))
        
        # Equip again
        self.manager.update_item(item_id, {"equipped": True})
        self.assertTrue(self.manager.get_item(item_id).get("equipped"))
    
    def test_equipped_weapon_count(self):
        """Test counting equipped vs unequipped weapons."""
        id1 = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        id2 = self.manager.add_item("Light Crossbow", "25 gp", "5 lb", 1, "Weapons",
                                    json.dumps({"damage": "1d8", "damage_type": "piercing"}))
        id3 = self.manager.add_item("Dagger", "2 gp", "1 lb", 2, "Weapons",
                                    json.dumps({"damage": "1d4", "damage_type": "piercing"}))
        
        # Equip two
        self.manager.update_item(id1, {"equipped": True})
        self.manager.update_item(id2, {"equipped": True})
        
        equipped = [item for item in self.manager.items if item.get("equipped")]
        unequipped = [item for item in self.manager.items if not item.get("equipped")]
        
        self.assertEqual(len(equipped), 2)
        self.assertEqual(len(unequipped), 1)
    
    def test_weapon_table_render_no_duplicates(self):
        """Test that weapons don't appear twice in the table."""
        item_id = self.manager.add_item("Longsword", "15 gp", "3 lb", 1, "Weapons",
                                        json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        self.manager.update_item(item_id, {"equipped": True})
        
        # Get equipped weapons (simulating what render function does)
        equipped_weapons = [item for item in self.manager.items 
                           if item.get("equipped") and item.get("category", "").lower() in ["weapons", "weapon"]]
        
        # Count occurrences of longsword
        longsword_count = sum(1 for weapon in equipped_weapons if weapon["id"] == item_id)
        
        self.assertEqual(longsword_count, 1, "Longsword should appear exactly once in table")


if __name__ == "__main__":
    unittest.main()
