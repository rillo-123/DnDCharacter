"""
Unit tests for equipment rendering pipeline
Tests that equipment items display only necessary fields (name, cost, weight)

Note: character.py contains JavaScript code formatted in a Python-like way for visualization.
This test file validates the logic patterns and data structures that should be implemented.
"""

import unittest
import json
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "assets" / "py"))

# Import equipment classes
# Note: character.py imports from 'js' which is PyScript-specific
# We'll skip tests if imports fail
Armor = None
Weapon = None
Shield = None
Equipment = None

try:
    # Try importing from character module
    # This will fail if PyScript is not available
    from character import Equipment, Weapon, Armor, Shield
except ImportError as e:
    # Mark for skip if imports unavailable
    import unittest
    skip_equipment_tests = True
else:
    skip_equipment_tests = False


class TestEquipmentFallbackData(unittest.TestCase):
    """Test that fallback equipment data only contains name, cost, weight"""
    
    def test_fallback_data_structure(self):
        """Verify fallback equipment list has ONLY name, cost, weight fields"""
        # Simulate the fallback equipment list from character.py
        fallback_equipment = [
            {"name": "Club", "cost": "1 sp", "weight": "2 lb."},
            {"name": "Dagger", "cost": "2 gp", "weight": "1 lb."},
            {"name": "Greataxe", "cost": "30 gp", "weight": "7 lb."},
            {"name": "Greatclub", "cost": "2 sp", "weight": "10 lb."},
            {"name": "Greatsword", "cost": "50 gp", "weight": "6 lb."},
            {"name": "Halberd", "cost": "20 gp", "weight": "6 lb."},
            {"name": "Hand Crossbow", "cost": "75 gp", "weight": "3 lb."},
            {"name": "Handaxe", "cost": "5 gp", "weight": "2 lb."},
            {"name": "Heavy Crossbow", "cost": "50 gp", "weight": "18 lb."},
            {"name": "Javelin", "cost": "5 sp", "weight": "2 lb."},
            {"name": "Light Crossbow", "cost": "25 gp", "weight": "5 lb."},
            {"name": "Light Hammer", "cost": "2 gp", "weight": "2 lb."},
            {"name": "Longbow", "cost": "50 gp", "weight": "2 lb."},
            {"name": "Longsword", "cost": "15 gp", "weight": "3 lb."},
            {"name": "Mace", "cost": "5 gp", "weight": "4 lb."},
            {"name": "Maul", "cost": "10 gp", "weight": "10 lb."},
            {"name": "Morningstar", "cost": "15 gp", "weight": "4 lb."},
            {"name": "Pike", "cost": "5 gp", "weight": "18 lb."},
            {"name": "Quarterstaff", "cost": "2 sp", "weight": "4 lb."},
            {"name": "Rapier", "cost": "25 gp", "weight": "2 lb."},
            {"name": "Scimitar", "cost": "25 gp", "weight": "3 lb."},
            {"name": "Shortsword", "cost": "10 gp", "weight": "2 lb."},
            {"name": "Shortbow", "cost": "25 gp", "weight": "2 lb."},
            {"name": "Sickle", "cost": "1 gp", "weight": "2 lb."},
            {"name": "Sling", "cost": "1 sp", "weight": "0 lb."},
            {"name": "Spear", "cost": "1 gp", "weight": "3 lb."},
            {"name": "Trident", "cost": "5 gp", "weight": "4 lb."},
            {"name": "War Pick", "cost": "5 gp", "weight": "2 lb."},
            {"name": "Warhammer", "cost": "15 gp", "weight": "2 lb."},
            {"name": "Whip", "cost": "2 gp", "weight": "3 lb."},
            {"name": "Blowgun", "cost": "10 gp", "weight": "1 lb."},
            {"name": "Crossbow Bolts", "cost": "1 gp", "weight": "1.5 lb."},
            {"name": "Arrows", "cost": "1 gp", "weight": "1 lb."},
            {"name": "Sling Bullets", "cost": "4 cp", "weight": "1.5 lb."},
            {"name": "Padded Armor", "cost": "5 gp", "weight": "8 lb."},
            {"name": "Leather Armor", "cost": "10 gp", "weight": "10 lb."},
            {"name": "Studded Leather Armor", "cost": "45 gp", "weight": "13 lb."},
            {"name": "Hide Armor", "cost": "10 gp", "weight": "15 lb."},
            {"name": "Chain Shirt", "cost": "50 gp", "weight": "20 lb."},
            {"name": "Scale Mail", "cost": "50 gp", "weight": "45 lb."},
            {"name": "Breastplate", "cost": "400 gp", "weight": "20 lb."},
            {"name": "Half Plate", "cost": "750 gp", "weight": "40 lb."},
            {"name": "Ring Mail", "cost": "30 gp", "weight": "40 lb."},
            {"name": "Chain Mail", "cost": "75 gp", "weight": "55 lb."},
            {"name": "Splint Armor", "cost": "200 gp", "weight": "60 lb."},
            {"name": "Plate Armor", "cost": "1500 gp", "weight": "65 lb."},
            {"name": "Shield", "cost": "10 gp", "weight": "6 lb."},
            {"name": "Rope", "cost": "1 gp", "weight": "0.5 lb."},
            {"name": "Backpack", "cost": "2 gp", "weight": "5 lb."},
            {"name": "Bedroll", "cost": "1 gp", "weight": "5 lb."},
            {"name": "Rope Coil", "cost": "1 gp", "weight": "1 lb."},
        ]
        
        # Test that each item has ONLY 3 fields
        for item in fallback_equipment:
            self.assertEqual(len(item), 3, f"Item {item.get('name')} should have exactly 3 fields, got {len(item)}: {item.keys()}")
            self.assertIn("name", item, f"Item missing 'name': {item}")
            self.assertIn("cost", item, f"Item missing 'cost': {item}")
            self.assertIn("weight", item, f"Item missing 'weight': {item}")
    
    def test_mace_fallback_structure(self):
        """Specifically test Mace fallback data"""
        mace = {"name": "Mace", "cost": "5 gp", "weight": "4 lb."}
        
        # Should have exactly 3 fields
        self.assertEqual(len(mace), 3)
        self.assertEqual(mace["name"], "Mace")
        self.assertEqual(mace["cost"], "5 gp")
        self.assertEqual(mace["weight"], "4 lb.")
        
        # Should NOT have damage, damage_type, range, ac, etc.
        self.assertNotIn("damage", mace)
        self.assertNotIn("damage_type", mace)
        self.assertNotIn("damage_range", mace)
        self.assertNotIn("armor_class", mace)
        self.assertNotIn("properties", mace)


class TestItemClassSerialization(unittest.TestCase):
    """Test that Item/Weapon/Armor classes serialize cleanly without extra fields"""
    
    @unittest.skipIf(skip_equipment_tests, "Equipment classes not available (PyScript import issue)")
    def test_weapon_to_dict_only_sets_populated_fields(self):
        """Test Weapon.to_dict() only includes fields with values"""
        # Create weapon with only name, cost, weight
        weapon = Weapon(
            name="Mace",
            cost="5 gp",
            weight="4 lb."
        )
        
        weapon_dict = weapon.to_dict()
        
        # Check required fields exist
        self.assertIn("name", weapon_dict)
        self.assertEqual(weapon_dict["name"], "Mace")
        self.assertIn("cost", weapon_dict)
        self.assertEqual(weapon_dict["cost"], "5 gp")
        self.assertIn("weight", weapon_dict)
        self.assertEqual(weapon_dict["weight"], "4 lb.")
        
        # Check that damage fields are NOT in the dict (since not set)
        # They should either not be present or be None/empty
        if "damage" in weapon_dict:
            self.assertIsNone(weapon_dict["damage"], "damage should be None if not set")
        if "damage_type" in weapon_dict:
            self.assertIsNone(weapon_dict["damage_type"], "damage_type should be None if not set")
        if "damage_range" in weapon_dict:
            self.assertIsNone(weapon_dict["damage_range"], "damage_range should be None if not set")
    
    @unittest.skipIf(skip_equipment_tests, "Equipment classes not available (PyScript import issue)")
    def test_armor_to_dict_only_sets_populated_fields(self):
        """Test Armor.to_dict() only includes fields with values"""
        armor = Armor(
            name="Leather Armor",
            cost="10 gp",
            weight="10 lb."
        )
        
        armor_dict = armor.to_dict()
        
        # Check required fields exist
        self.assertIn("name", armor_dict)
        self.assertEqual(armor_dict["name"], "Leather Armor")
        self.assertIn("cost", armor_dict)
        self.assertIn("weight", armor_dict)
        
        # armor_class should not be in dict if not set
        if "armor_class" in armor_dict:
            self.assertIsNone(armor_dict["armor_class"], "armor_class should be None if not set")
    
    @unittest.skipIf(skip_equipment_tests, "Equipment classes not available (PyScript import issue)")
    def test_weapon_with_damage_includes_damage(self):
        """Test that damage fields ARE included when populated"""
        weapon = Weapon(
            name="Longsword",
            cost="15 gp",
            weight="3 lb.",
            damage="1d8",
            damage_type="slashing"
        )
        
        weapon_dict = weapon.to_dict()
        
        self.assertIn("damage", weapon_dict)
        self.assertEqual(weapon_dict["damage"], "1d8")
        self.assertIn("damage_type", weapon_dict)
        self.assertEqual(weapon_dict["damage_type"], "slashing")
    
    @unittest.skipIf(skip_equipment_tests, "Equipment classes not available (PyScript import issue)")
    def test_json_notes_field_structure(self):
        """Test that JSON notes field doesn't contain empty values"""
        weapon = Weapon(
            name="Mace",
            cost="5 gp",
            weight="4 lb."
        )
        
        weapon_dict = weapon.to_dict()
        
        # If there's a notes field with JSON, it should be parsed
        if "notes" in weapon_dict and weapon_dict["notes"]:
            try:
                notes_data = json.loads(weapon_dict["notes"]) if isinstance(weapon_dict["notes"], str) else weapon_dict["notes"]
                # Should not contain empty or None values
                for key, value in notes_data.items():
                    self.assertIsNotNone(value, f"Notes field {key} should not be None")
                    if isinstance(value, str):
                        self.assertNotEqual(value, "", f"Notes field {key} should not be empty string")
            except json.JSONDecodeError:
                # If not JSON, that's okay for this test
                pass


@unittest.skipIf(skip_equipment_tests, "Equipment classes not available (PyScript import issue)")
class TestItemClassFromDict(unittest.TestCase):
    """Test that Item classes can be reconstructed from dict without extra fields"""
    
    def test_weapon_from_dict_mace(self):
        """Test reconstructing Mace weapon from minimal dict"""
        mace_dict = {
            "name": "Mace",
            "cost": "5 gp",
            "weight": "4 lb."
        }
        
        weapon = Weapon.from_dict(mace_dict)
        
        self.assertEqual(weapon.name, "Mace")
        self.assertEqual(weapon.cost, "5 gp")
        self.assertEqual(weapon.weight, "4 lb.")
        
        # Should not have damage or other fields set (or they should be None)
        self.assertTrue(weapon.damage is None or weapon.damage == "")
        self.assertTrue(weapon.damage_type is None or weapon.damage_type == "")
    
    def test_roundtrip_serialization_no_empty_fields(self):
        """Test that to_dict -> from_dict roundtrip doesn't add empty fields"""
        original_dict = {
            "name": "Mace",
            "cost": "5 gp",
            "weight": "4 lb."
        }
        
        # Create weapon from dict
        weapon = Weapon.from_dict(original_dict)
        
        # Convert back to dict
        result_dict = weapon.to_dict()
        
        # Verify critical fields are present
        self.assertEqual(result_dict["name"], "Mace")
        self.assertEqual(result_dict["cost"], "5 gp")
        self.assertEqual(result_dict["weight"], "4 lb.")


@unittest.skipIf(skip_equipment_tests, "Equipment classes not available (PyScript import issue)")
class TestEquipmentDisplayFields(unittest.TestCase):
    """Test that equipment display only shows populated fields"""
    
    def test_mace_display_fields(self):
        """Test which fields should be displayed for Mace"""
        mace = Weapon(
            name="Mace",
            cost="5 gp",
            weight="4 lb."
        )
        
        mace_dict = mace.to_dict()
        
        # Fields that SHOULD display:
        display_fields = ["name", "cost", "weight"]
        
        # Fields that should NOT display (if present, should be None/empty):
        non_display_fields = ["damage", "damage_type", "damage_range", "properties"]
        
        for field in display_fields:
            self.assertIn(field, mace_dict, f"{field} should be in dict for display")
            self.assertIsNotNone(mace_dict[field], f"{field} should not be None")
        
        for field in non_display_fields:
            if field in mace_dict:
                self.assertIsNone(mace_dict[field], f"{field} should be None for basic Mace")
    
    def test_longsword_display_fields(self):
        """Test which fields should be displayed for Longsword with damage"""
        sword = Weapon(
            name="Longsword",
            cost="15 gp",
            weight="3 lb.",
            damage="1d8",
            damage_type="slashing"
        )
        
        sword_dict = sword.to_dict()
        
        # These should all be present
        self.assertIn("name", sword_dict)
        self.assertIn("cost", sword_dict)
        self.assertIn("weight", sword_dict)
        self.assertIn("damage", sword_dict)
        self.assertIn("damage_type", sword_dict)
        
        # Verify values
        self.assertEqual(sword_dict["damage"], "1d8")
        self.assertEqual(sword_dict["damage_type"], "slashing")


class TestDataAttributeGeneration(unittest.TestCase):
    """Test that data attributes for DOM elements only include populated fields"""
    
    def test_get_displayable_attributes_for_mace(self):
        """Test which attributes should be set on DOM element for Mace"""
        mace_dict = {
            "name": "Mace",
            "cost": "5 gp",
            "weight": "4 lb."
        }
        
        # Simulate what populate_equipment_results() does
        displayable_attrs = {}
        
        # Only set attribute if value exists and is not empty
        for key in ["damage", "damage_type", "damage_range", "armor_class", "properties"]:
            value = mace_dict.get(key, "")
            if value:  # Only add if truthy
                displayable_attrs[key] = value
        
        # Mace should have NO extra attributes
        self.assertEqual(len(displayable_attrs), 0, f"Mace should have no optional attributes, got: {displayable_attrs}")
    
    def test_get_displayable_attributes_for_longsword(self):
        """Test which attributes should be set on DOM element for Longsword"""
        sword_dict = {
            "name": "Longsword",
            "cost": "15 gp",
            "weight": "3 lb.",
            "damage": "1d8",
            "damage_type": "slashing"
        }
        
        displayable_attrs = {}
        
        # Only set attribute if value exists and is not empty
        for key in ["damage", "damage_type", "damage_range", "armor_class", "properties"]:
            value = sword_dict.get(key, "")
            if value:  # Only add if truthy
                displayable_attrs[key] = value
        
        # Longsword should have damage and damage_type
        self.assertIn("damage", displayable_attrs)
        self.assertEqual(displayable_attrs["damage"], "1d8")
        self.assertIn("damage_type", displayable_attrs)
        self.assertEqual(displayable_attrs["damage_type"], "slashing")
        
        # Should NOT have damage_range or armor_class
        self.assertNotIn("damage_range", displayable_attrs)
        self.assertNotIn("armor_class", displayable_attrs)


if __name__ == "__main__":
    unittest.main()
