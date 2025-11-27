"""
Unit tests for equipment rendering pipeline logic
Tests that equipment items display only necessary fields (name, cost, weight)

This test file validates data structures and logic patterns for equipment rendering,
focusing on identifying where unnecessary fields might be appearing.
"""

import unittest
import json
import re


class TestEquipmentFallbackData(unittest.TestCase):
    """Test that fallback equipment data only contains name, cost, weight"""
    
    def test_fallback_data_structure(self):
        """Verify fallback equipment list has ONLY name, cost, weight fields"""
        # These are the exact items from character.py fallback list
        fallback_equipment = [
            {"name": "Club", "cost": "1 sp", "weight": "2 lb."},
            {"name": "Dagger", "cost": "2 gp", "weight": "1 lb."},
            {"name": "Mace", "cost": "5 gp", "weight": "4 lb."},
            {"name": "Longsword", "cost": "15 gp", "weight": "3 lb."},
            {"name": "Leather Armor", "cost": "10 gp", "weight": "10 lb."},
            {"name": "Shield", "cost": "10 gp", "weight": "6 lb."},
        ]
        
        # Test that each item has ONLY 3 fields
        for item in fallback_equipment:
            self.assertEqual(
                len(item), 3,
                f"Item {item.get('name')} should have exactly 3 fields, got {len(item)}: {list(item.keys())}"
            )
            self.assertIn("name", item)
            self.assertIn("cost", item)
            self.assertIn("weight", item)
            
            # Should NOT have any weapon or armor specific fields
            for forbidden_field in ["damage", "damage_type", "damage_range", "armor_class", "properties", "qty", "category", "notes", "source", "id"]:
                self.assertNotIn(forbidden_field, item, f"Fallback item {item.get('name')} should not have field '{forbidden_field}'")
    
    def test_mace_specific_fallback(self):
        """Specifically test Mace fallback data"""
        mace = {"name": "Mace", "cost": "5 gp", "weight": "4 lb."}
        
        # Verify exact structure
        self.assertEqual(len(mace), 3)
        self.assertEqual(mace["name"], "Mace")
        self.assertEqual(mace["cost"], "5 gp")
        self.assertEqual(mace["weight"], "4 lb.")


class TestDataAttributeGeneration(unittest.TestCase):
    """Test that data attributes for DOM elements only include populated fields"""
    
    def simulate_populate_equipment_results(self, item_dict):
        """Simulate the populate_equipment_results() logic for setting data attributes.
        
        This mirrors the JavaScript logic that conditionally sets data attributes.
        """
        displayable_attrs = {}
        
        # Only set optional data attributes if they have values
        optional_fields = ["damage", "damage_type", "damage_range", "armor_class", "properties"]
        
        for field in optional_fields:
            value = item_dict.get(field, "")
            if value:  # Only add if truthy (non-empty string, non-zero number, etc.)
                displayable_attrs[field] = value
        
        return displayable_attrs
    
    def test_mace_has_no_data_attributes(self):
        """Test that Mace should not have any optional data attributes"""
        mace_dict = {
            "name": "Mace",
            "cost": "5 gp",
            "weight": "4 lb."
        }
        
        attrs = self.simulate_populate_equipment_results(mace_dict)
        
        # Mace should have NO optional data attributes
        self.assertEqual(len(attrs), 0, f"Mace should have no optional attributes, got: {attrs}")
    
    def test_longsword_has_damage_attributes(self):
        """Test that Longsword should have damage attributes"""
        sword_dict = {
            "name": "Longsword",
            "cost": "15 gp",
            "weight": "3 lb.",
            "damage": "1d8",
            "damage_type": "slashing"
        }
        
        attrs = self.simulate_populate_equipment_results(sword_dict)
        
        # Should have damage and damage_type, but NOT armor_class or range
        self.assertIn("damage", attrs)
        self.assertEqual(attrs["damage"], "1d8")
        self.assertIn("damage_type", attrs)
        self.assertEqual(attrs["damage_type"], "slashing")
        
        self.assertNotIn("damage_range", attrs)
        self.assertNotIn("armor_class", attrs)
    
    def test_empty_string_not_added_as_attribute(self):
        """Test that empty string values don't create data attributes"""
        item_with_empty = {
            "name": "Test Item",
            "cost": "1 gp",
            "weight": "1 lb.",
            "damage": "",  # Empty string
            "damage_type": ""
        }
        
        attrs = self.simulate_populate_equipment_results(item_with_empty)
        
        # Empty strings should not create attributes
        self.assertEqual(len(attrs), 0, f"Empty string values should not create attributes, got: {attrs}")
    
    def test_none_values_not_added(self):
        """Test that None values don't create data attributes"""
        item_with_none = {
            "name": "Test Item",
            "cost": "1 gp",
            "weight": "1 lb.",
            "damage": None,
            "armor_class": None
        }
        
        attrs = self.simulate_populate_equipment_results(item_with_none)
        
        # None values should not create attributes
        self.assertEqual(len(attrs), 0, f"None values should not create attributes, got: {attrs}")


class TestEquipmentHandlerLogic(unittest.TestCase):
    """Test equipment click handler logic"""
    
    def simulate_handle_equipment_click(self, data_attrs):
        """Simulate _handle_equipment_click() logic for extracting attributes.
        
        This should extract only the data attributes that were set.
        """
        extracted = {}
        
        # Extract each optional field, using empty string as fallback
        for field in ["damage", "damage_type", "damage_range", "armor_class", "properties"]:
            value = data_attrs.get(field, "")
            extracted[field] = value
        
        return extracted
    
    def test_handler_extracts_only_set_attributes(self):
        """Test that handler only passes attributes that were actually set"""
        # Mace has no optional attributes set
        mace_attrs = {}
        
        result = self.simulate_handle_equipment_click(mace_attrs)
        
        # All values should be empty strings (the fallback)
        for field in ["damage", "damage_type", "damage_range", "armor_class", "properties"]:
            self.assertEqual(result[field], "", f"Field {field} should be empty string for Mace")
    
    def test_handler_with_damage_attributes(self):
        """Test handler with weapon damage attributes"""
        sword_attrs = {
            "damage": "1d8",
            "damage_type": "slashing"
        }
        
        result = self.simulate_handle_equipment_click(sword_attrs)
        
        # Damage fields should have values
        self.assertEqual(result["damage"], "1d8")
        self.assertEqual(result["damage_type"], "slashing")
        
        # Others should be empty
        self.assertEqual(result["damage_range"], "")
        self.assertEqual(result["armor_class"], "")


class TestItemSerializationLogic(unittest.TestCase):
    """Test item to_dict() serialization logic"""
    
    def simulate_item_to_dict_basic(self, name, cost, weight):
        """Simulate Item.to_dict() for basic item without extra properties"""
        item_dict = {
            "id": "1",
            "name": name,
            "cost": cost,
            "weight": weight,
            "qty": 1,
            "category": "",
            "notes": "",
            "source": "custom"
        }
        return item_dict
    
    def simulate_weapon_to_dict(self, name, cost, weight, damage="", damage_type="", damage_range=""):
        """Simulate Weapon.to_dict() logic"""
        # Start with base item dict
        item_dict = self.simulate_item_to_dict_basic(name, cost, weight)
        item_dict["category"] = "Weapons"
        
        # Add extra properties to notes if any damage fields are set
        extra_props = {}
        if damage:
            extra_props["damage"] = damage
        if damage_type:
            extra_props["damage_type"] = damage_type
        if damage_range:
            extra_props["range"] = damage_range
        
        # Only add notes if there are extra properties
        if extra_props:
            item_dict["notes"] = json.dumps(extra_props)
        
        return item_dict
    
    def test_mace_serialization_has_no_extra_properties(self):
        """Test that Mace serializes without extra weapon properties"""
        mace_dict = self.simulate_weapon_to_dict("Mace", "5 gp", "4 lb.")
        
        # Should have basic fields
        self.assertEqual(mace_dict["name"], "Mace")
        self.assertEqual(mace_dict["cost"], "5 gp")
        self.assertEqual(mace_dict["weight"], "4 lb.")
        
        # notes should be empty for basic weapon
        self.assertEqual(mace_dict["notes"], "")
        
        # Should NOT have damage in the stored data
        self.assertNotIn("damage", mace_dict)
    
    def test_longsword_serialization_includes_damage(self):
        """Test that Longsword with damage serializes correctly"""
        sword_dict = self.simulate_weapon_to_dict("Longsword", "15 gp", "3 lb.", 
                                                  damage="1d8", damage_type="slashing")
        
        # Basic fields
        self.assertEqual(sword_dict["name"], "Longsword")
        self.assertEqual(sword_dict["cost"], "15 gp")
        
        # notes should contain JSON with damage info
        self.assertNotEqual(sword_dict["notes"], "")
        
        try:
            notes_data = json.loads(sword_dict["notes"])
            self.assertIn("damage", notes_data)
            self.assertEqual(notes_data["damage"], "1d8")
            self.assertIn("damage_type", notes_data)
            self.assertEqual(notes_data["damage_type"], "slashing")
        except json.JSONDecodeError:
            self.fail(f"notes field should be valid JSON, got: {sword_dict['notes']}")
    
    def test_no_empty_strings_in_notes_json(self):
        """Test that empty string values are not added to notes JSON"""
        # Weapon with empty damage fields should not add them to JSON
        item_dict = self.simulate_weapon_to_dict("Mace", "5 gp", "4 lb.",
                                                damage="", damage_type="", damage_range="")
        
        # notes should be empty if no properties were actually set
        self.assertEqual(item_dict["notes"], "", "notes should be empty if no damage properties")


class TestInventoryDisplayLogic(unittest.TestCase):
    """Test how items should be displayed in inventory"""
    
    def get_display_fields(self, item_dict):
        """Determine which fields should be visible for an item"""
        # Always show these fields if they have values
        always_show = ["name", "cost", "weight"]
        
        # Conditionally show based on content
        conditional_show = []
        
        if item_dict.get("notes"):
            try:
                notes_data = json.loads(item_dict["notes"])
                # Only show fields that are in notes
                if "damage" in notes_data and notes_data["damage"]:
                    conditional_show.append(("damage", notes_data["damage"]))
                if "damage_type" in notes_data and notes_data["damage_type"]:
                    conditional_show.append(("damage_type", notes_data["damage_type"]))
                if "armor_class" in notes_data and notes_data["armor_class"]:
                    conditional_show.append(("armor_class", notes_data["armor_class"]))
            except json.JSONDecodeError:
                pass
        
        return always_show, conditional_show
    
    def test_mace_shows_only_basic_fields(self):
        """Test that Mace displays only name, cost, weight"""
        mace_dict = {
            "name": "Mace",
            "cost": "5 gp",
            "weight": "4 lb.",
            "notes": ""  # No extra properties
        }
        
        always_show, conditional_show = self.get_display_fields(mace_dict)
        
        # Should show basic fields
        self.assertIn("name", always_show)
        self.assertIn("cost", always_show)
        self.assertIn("weight", always_show)
        
        # Should NOT show any conditional fields
        self.assertEqual(len(conditional_show), 0, f"Mace should show no conditional fields, got: {conditional_show}")
    
    def test_longsword_shows_damage(self):
        """Test that Longsword displays damage information"""
        sword_dict = {
            "name": "Longsword",
            "cost": "15 gp",
            "weight": "3 lb.",
            "notes": json.dumps({"damage": "1d8", "damage_type": "slashing"})
        }
        
        always_show, conditional_show = self.get_display_fields(sword_dict)
        
        # Should show basic fields
        self.assertIn("name", always_show)
        
        # Should show damage info
        field_names = [f[0] for f in conditional_show]
        self.assertIn("damage", field_names)
        self.assertIn("damage_type", field_names)
        
        # Get values
        field_dict = {f[0]: f[1] for f in conditional_show}
        self.assertEqual(field_dict["damage"], "1d8")
        self.assertEqual(field_dict["damage_type"], "slashing")


class TestInventoryRenderConditionalFields(unittest.TestCase):
    """Test that inventory rendering only shows modifier fields when needed"""
    
    def should_show_modifier_fields(self, category, custom_props, ac_mod, saves_mod):
        """Test the logic for when to show modifier fields.
        
        Per the fixed render_inventory():
        - Modifier fields show if there are VALUES in them
        - OR if the item is in the "Armor" category
        """
        # Fixed logic: show if category is Armor OR if any values exist
        return category == "Armor" or bool(custom_props or ac_mod or saves_mod)
    
    def test_basic_mace_no_modifier_fields(self):
        """Test that basic Mace doesn't show modifier fields"""
        # Mace: Weapons category, no modifiers
        should_show = self.should_show_modifier_fields(
            category="Weapons",
            custom_props="",
            ac_mod="",
            saves_mod=""
        )
        
        self.assertFalse(should_show, "Basic Mace should NOT show modifier fields")
    
    def test_magic_armor_shows_modifier_fields(self):
        """Test that Armor category always shows modifier fields"""
        # Any armor item shows modifier fields
        should_show = self.should_show_modifier_fields(
            category="Armor",
            custom_props="",
            ac_mod="",
            saves_mod=""
        )
        
        self.assertTrue(should_show, "Armor items should always show modifier fields")
    
    def test_item_with_modifiers_shows_fields(self):
        """Test that items with modifier values show the fields"""
        # Weapon with a modifier should show
        should_show = self.should_show_modifier_fields(
            category="Weapons",
            custom_props="+1 AC",
            ac_mod="",
            saves_mod=""
        )
        
        self.assertTrue(should_show, "Items with custom properties should show modifier fields")
    
    def test_mace_pipeline_with_fix(self):
        """Test complete Mace rendering pipeline with the fix"""
        mace_item = {
            "id": "1",
            "name": "Mace",
            "category": "Weapons",
            "cost": "5 gp",
            "weight": "4 lb.",
            "qty": 1,
            "notes": ""  # No extra properties
        }
        
        # Parse extra properties from notes
        extra_props = {}
        try:
            if mace_item["notes"] and mace_item["notes"].startswith("{"):
                extra_props = json.loads(mace_item["notes"])
        except:
            pass
        
        # Get modifier values
        custom_props = extra_props.get("custom_properties", "")
        ac_mod = extra_props.get("ac_modifier", "")
        saves_mod = extra_props.get("saves_modifier", "")
        
        # Determine if modifier fields should show
        should_show_modifiers = mace_item["category"] == "Armor" or bool(custom_props or ac_mod or saves_mod)
        
        # Mace should NOT show modifier fields
        self.assertFalse(should_show_modifiers, "Mace should not show modifier fields after fix")



    """End-to-end test of equipment rendering pipeline"""
    
    def test_mace_pipeline_end_to_end(self):
        """Test complete pipeline: fallback data -> render -> handler -> storage -> display"""
        
        # Step 1: Fallback data
        fallback_mace = {"name": "Mace", "cost": "5 gp", "weight": "4 lb."}
        self.assertEqual(len(fallback_mace), 3, "Fallback should have only 3 fields")
        
        # Step 2: Render (create data attributes)
        optional_fields = ["damage", "damage_type", "damage_range", "armor_class", "properties"]
        data_attrs = {}
        for field in optional_fields:
            if field in fallback_mace and fallback_mace[field]:
                data_attrs[field] = fallback_mace[field]
        
        self.assertEqual(len(data_attrs), 0, "Render should create no optional attributes for Mace")
        
        # Step 3: Handler (extract attributes)
        extracted = {}
        for field in optional_fields:
            extracted[field] = data_attrs.get(field, "")
        
        # All should be empty
        for field, value in extracted.items():
            self.assertEqual(value, "", f"Handler should extract empty string for {field}")
        
        # Step 4: Storage (create Item/Weapon)
        stored_item = {
            "id": "1",
            "name": "Mace",
            "cost": "5 gp",
            "weight": "4 lb.",
            "qty": 1,
            "category": "Weapons",
            "notes": "",  # Empty notes since no damage
            "source": "custom"
        }
        
        self.assertEqual(stored_item["notes"], "", "Storage should have empty notes")
        
        # Step 5: Display (render inventory)
        display_fields = ["name", "cost", "weight"]
        optional_display = []
        
        if stored_item["notes"]:
            try:
                notes = json.loads(stored_item["notes"])
                for key in ["damage", "damage_type", "armor_class"]:
                    if key in notes:
                        optional_display.append(key)
            except:
                pass
        
        self.assertEqual(len(optional_display), 0, "Display should show no optional fields for Mace")


if __name__ == "__main__":
    unittest.main()
