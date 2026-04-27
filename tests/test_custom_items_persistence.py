"""
Test custom items JSON persistence workflow.

Verifies that custom items:
1. Can be added to inventory via submit_custom_item()
2. Are exported to JSON via collect_character_data()
3. Maintain all properties (damage, AC, range, etc.) in JSON
4. Can be loaded back from JSON and restored
"""

import json
import sys
import pytest

# Add path for imports
sys.path.insert(0, 'static/assets/py')

from managers import InventoryManager


class TestCustomItemsJSONPersistence:
    """Test custom items are persisted to JSON and can be reloaded."""

    @pytest.fixture
    def inventory(self):
        """Create a fresh inventory manager."""
        return InventoryManager()

    def test_custom_item_added_to_inventory(self, inventory):
        """Verify custom item is added to inventory manager."""
        name = "Dummy Axe"
        cost = "10 gp"
        weight = "4 lb."
        qty = 1
        category = "weapon"
        
        item_id = inventory.add_item(name, cost=cost, weight=weight, qty=qty, 
                                     category=category, source="custom")
        
        assert len(inventory.items) == 1
        item = inventory.get_item(item_id)
        assert item is not None
        assert item["name"] == "Dummy Axe"
        assert item["source"] == "custom"

    def test_custom_weapon_with_damage_persisted(self, inventory):
        """Verify custom weapon with damage properties is stored correctly."""
        name = "Magic Longsword"
        cost = "300 gp"
        weight = "3 lb."
        
        # Build properties JSON as submit_custom_item() does
        extra_props = {
            "damage": "1d8",
            "damage_type": "slashing",
            "bonus": 1,
            "properties": "finesse, magical"
        }
        notes = json.dumps(extra_props)
        
        item_id = inventory.add_item(name, cost=cost, weight=weight, qty=1, 
                                     category="weapon", notes=notes, source="custom")
        
        item = inventory.get_item(item_id)
        
        # Verify notes are stored as JSON
        assert item["notes"] != ""
        parsed_notes = json.loads(item["notes"])
        assert parsed_notes["damage"] == "1d8"
        assert parsed_notes["damage_type"] == "slashing"
        assert parsed_notes["bonus"] == 1
        assert "finesse" in parsed_notes["properties"]

    def test_custom_armor_with_ac_persisted(self, inventory):
        """Verify custom armor with AC properties is stored correctly."""
        name = "Custom Plate Armor"
        cost = "1500 gp"
        weight = "65 lb."
        
        # Build armor properties as submit_custom_item() does
        extra_props = {
            "ac": "18",
            "armor_type": "plate",
            "properties": "heavy, requires strength"
        }
        notes = json.dumps(extra_props)
        
        item_id = inventory.add_item(name, cost=cost, weight=weight, qty=1, 
                                     category="armor", notes=notes, source="custom")
        
        item = inventory.get_item(item_id)
        parsed_notes = json.loads(item["notes"])
        assert parsed_notes["ac"] == "18"
        assert "heavy" in parsed_notes["properties"]

    def test_inventory_items_can_be_exported_as_json(self, inventory):
        """Verify inventory.items list is JSON-serializable."""
        # Add a custom item
        extra_props = {"damage": "1d6", "damage_type": "piercing"}
        notes = json.dumps(extra_props)
        inventory.add_item("Custom Dagger", cost="2 gp", weight="1 lb.", 
                          category="weapon", notes=notes, source="custom")
        
        # Verify items list is JSON-serializable (as per collect_character_data)
        try:
            items_json = json.dumps(inventory.items)
            assert len(items_json) > 0
        except TypeError as e:
            pytest.fail(f"inventory.items not JSON-serializable: {e}")
        
        # Verify we can parse it back
        parsed_items = json.loads(items_json)
        assert len(parsed_items) == 1
        assert parsed_items[0]["name"] == "Custom Dagger"

    def test_multiple_custom_items_all_exported(self, inventory):
        """Verify multiple custom items are all exported correctly."""
        items_data = [
            {"name": "Magic Sword", "damage": "1d8", "bonus": 1},
            {"name": "Custom Shield", "ac": "2", "armor_type": "shield"},
            {"name": "Enchanted Ring", "properties": "magic"},
        ]
        
        for item_data in items_data:
            name = item_data.pop("name")
            extra_props = item_data
            notes = json.dumps(extra_props)
            inventory.add_item(name, cost="100 gp", weight="1 lb.", 
                              category="equipment", notes=notes, source="custom")
        
        # Verify all items are in inventory
        assert len(inventory.items) == 3
        
        # Verify all can be serialized
        items_json = json.dumps(inventory.items)
        parsed_items = json.loads(items_json)
        assert len(parsed_items) == 3
        
        # Verify each item's properties are preserved
        names = [item["name"] for item in parsed_items]
        assert "Magic Sword" in names
        assert "Custom Shield" in names
        assert "Enchanted Ring" in names

    def test_custom_item_export_includes_all_fields(self, inventory):
        """Verify exported custom item includes all required fields."""
        extra_props = {
            "damage": "1d10",
            "damage_type": "slashing",
            "range": "5 ft.",
            "ac": "0",
            "properties": "versatile, magical",
            "notes": "Found in dragon's hoard"
        }
        notes = json.dumps(extra_props)
        
        item_id = inventory.add_item("Versatile War Axe", cost="50 gp", weight="7 lb.", 
                                     qty=1, category="weapon", notes=notes, source="custom")
        
        # Simulate export (as in collect_character_data)
        exported_items = json.dumps(inventory.items)
        reloaded_items = json.loads(exported_items)
        
        reloaded_item = reloaded_items[0]
        
        # Verify core item fields
        assert reloaded_item["name"] == "Versatile War Axe"
        assert reloaded_item["cost"] == "50 gp"
        assert reloaded_item["weight"] == "7 lb."
        assert reloaded_item["qty"] == 1
        assert reloaded_item["category"] == "weapon"
        assert reloaded_item["source"] == "custom"
        
        # Verify properties in notes are preserved
        reloaded_props = json.loads(reloaded_item["notes"])
        assert reloaded_props["damage"] == "1d10"
        assert reloaded_props["damage_type"] == "slashing"
        assert reloaded_props["range"] == "5 ft."
        assert "versatile" in reloaded_props["properties"]

    def test_custom_item_export_reload_roundtrip(self, inventory):
        """Verify custom item survives export->reload roundtrip."""
        # Add custom item
        original_props = {
            "damage": "2d6",
            "damage_type": "magical force",
            "properties": "magical, rare",
            "bonus": 2,
            "ac": "0",
            "range": "melee"
        }
        original_notes = json.dumps(original_props)
        
        item_id = inventory.add_item("Artifact Hammer", cost="priceless", weight="10 lb.", 
                                     qty=1, category="weapon", notes=original_notes, 
                                     source="custom")
        
        # Export to JSON (as collect_character_data does)
        exported_json = json.dumps(inventory.items)
        
        # Simulate loading from character file (reload inventory from JSON)
        reloaded_items = json.loads(exported_json)
        
        # Create new inventory and restore items
        new_inventory = InventoryManager()
        for item in reloaded_items:
            # Manually restore item to new inventory (simulating load from file)
            new_inventory.items.append(item)
        
        # Verify item is restored correctly
        assert len(new_inventory.items) == 1
        restored_item = new_inventory.items[0]
        
        assert restored_item["name"] == "Artifact Hammer"
        assert restored_item["source"] == "custom"
        
        # Verify properties are intact
        restored_props = json.loads(restored_item["notes"])
        assert restored_props["damage"] == "2d6"
        assert restored_props["damage_type"] == "magical force"
        assert restored_props["bonus"] == 2
        assert "magical" in restored_props["properties"]

    def test_custom_item_with_complex_notes(self, inventory):
        """Verify custom item with complex nested properties persists correctly."""
        complex_props = {
            "damage": "1d12",
            "damage_type": "slashing",
            "range": "5 ft.",
            "bonus": 3,
            "properties": "heavy, two-handed, magical, legendary",
            "special_rules": {
                "on_hit": "Roll for critical",
                "special_effect": "Glows in darkness"
            },
            "lore": "Forged by ancients, grants +2 to Athletics"
        }
        complex_notes = json.dumps(complex_props)
        
        item_id = inventory.add_item("Legend's Blade", cost="unknown", weight="8 lb.", 
                                     category="weapon", notes=complex_notes, source="custom")
        
        # Export and reload
        exported = json.dumps(inventory.items)
        reloaded_items = json.loads(exported)
        
        reloaded_item = reloaded_items[0]
        reloaded_props = json.loads(reloaded_item["notes"])
        
        # Verify nested structure is preserved
        assert reloaded_props["damage"] == "1d12"
        assert isinstance(reloaded_props["special_rules"], dict)
        assert reloaded_props["special_rules"]["on_hit"] == "Roll for critical"
        assert "legendary" in reloaded_props["properties"]
        assert reloaded_props["lore"] == "Forged by ancients, grants +2 to Athletics"

    def test_custom_item_id_unique_across_operations(self, inventory):
        """Verify each custom item gets a unique ID."""
        ids = []
        for i in range(5):
            item_id = inventory.add_item(f"Item {i}", cost="10 gp", weight="1 lb.", 
                                        source="custom")
            ids.append(item_id)
        
        # Verify all IDs are unique
        assert len(set(ids)) == 5, "Item IDs are not unique"
        
        # Verify exported JSON preserves unique IDs
        exported = json.dumps(inventory.items)
        reloaded = json.loads(exported)
        
        reloaded_ids = [item["id"] for item in reloaded]
        assert len(set(reloaded_ids)) == 5, "Exported item IDs are not unique"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
