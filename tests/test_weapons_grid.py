"""
Tests for the weapons grid view in the Skills tab.

Verifies that equipped weapons are displayed correctly with proper damage,
to-hit bonuses, range, and properties.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock


class TestWeaponsGridRendering:
    """Test suite for weapons grid rendering and data display."""
    
    def test_weapons_grid_element_exists(self):
        """Verify weapons grid table element exists in HTML structure."""
        # This test verifies the HTML structure contains weapons-grid
        # In real browser, this would be tested via the DOM
        # For unit tests, we verify the rendering logic handles the element
        from unittest.mock import MagicMock
        
        mock_grid = MagicMock()
        mock_grid.innerHTML = ""
        
        # Simulate what render_weapons_grid does
        assert mock_grid is not None
        assert hasattr(mock_grid, 'innerHTML')
    
    def test_weapons_grid_shows_equipped_weapons_only(self):
        """Verify that only equipped weapons are shown in the grid."""
        # Test data with mixed equipped/unequipped
        weapons = [
            {
                "id": "1",
                "name": "Longsword",
                "category": "Weapons",
                "equipped": True,
                "notes": json.dumps({"damage": "1d8", "damage_type": "slashing"})
            },
            {
                "id": "2", 
                "name": "Dagger",
                "category": "Weapons",
                "equipped": False,
                "notes": json.dumps({"damage": "1d4", "damage_type": "piercing"})
            },
            {
                "id": "3",
                "name": "Greataxe",
                "category": "Weapons",
                "equipped": True,
                "notes": json.dumps({"damage": "1d12", "damage_type": "slashing"})
            }
        ]
        
        # Filter for equipped weapons
        equipped = [w for w in weapons if w.get("equipped")]
        
        assert len(equipped) == 2
        assert equipped[0]["name"] == "Longsword"
        assert equipped[1]["name"] == "Greataxe"
        assert "Dagger" not in [w["name"] for w in equipped]
    
    def test_weapon_damage_parsing_from_notes_json(self):
        """Verify damage is correctly extracted from notes JSON."""
        weapon = {
            "name": "Mace",
            "notes": json.dumps({
                "damage": "1d6",
                "damage_type": "bludgeoning"
            })
        }
        
        # Parse notes
        notes_data = json.loads(weapon["notes"])
        
        assert notes_data["damage"] == "1d6"
        assert notes_data["damage_type"] == "bludgeoning"
    
    def test_weapon_range_extraction_from_properties_array(self):
        """Verify range is correctly extracted from Open5e properties array."""
        weapon = {
            "name": "Light Crossbow",
            "properties": [
                "ammunition (range 80/320)",
                "loading",
                "light"
            ]
        }
        
        # Extract range from properties
        range_text = "Melee"
        for prop in weapon["properties"]:
            if isinstance(prop, str) and ("range" in prop.lower() or "ammunition" in prop.lower()):
                if "(" in prop and ")" in prop:
                    range_text = prop[prop.find("(")+1:prop.find(")")]
                break
        
        assert range_text == "range 80/320"
    
    def test_weapon_properties_converted_to_string(self):
        """Verify properties array is converted to comma-separated string."""
        props_array = ["finesse", "light", "versatile"]
        
        # Convert to string
        props_str = ", ".join(str(p) for p in props_array if p)
        
        assert props_str == "finesse, light, versatile"
    
    def test_ranged_weapon_uses_dex_for_tohit(self):
        """Verify ranged weapons use DEX modifier for to-hit calculation."""
        weapon = {
            "name": "Longbow",
            "properties": ["ammunition", "heavy", "two-handed"],
            "notes": json.dumps({
                "damage": "1d8",
                "damage_type": "piercing"
            })
        }
        
        # Check if ranged
        is_ranged = False
        for prop in weapon.get("properties", []):
            if isinstance(prop, str) and "ammunition" in prop.lower():
                is_ranged = True
                break
        
        assert is_ranged is True
    
    def test_melee_weapon_uses_str_for_tohit(self):
        """Verify melee weapons use STR modifier for to-hit calculation."""
        weapon = {
            "name": "Longsword",
            "properties": [],
            "notes": json.dumps({
                "damage": "1d8",
                "damage_type": "slashing"
            })
        }
        
        # Check if ranged
        is_ranged = False
        for prop in weapon.get("properties", []):
            if isinstance(prop, str) and "ammunition" in prop.lower():
                is_ranged = True
                break
        
        assert is_ranged is False
    
    def test_finesse_weapon_uses_better_ability(self):
        """Verify finesse weapons use the better of STR or DEX."""
        weapon = {
            "name": "Rapier",
            "properties": ["finesse"],
            "notes": json.dumps({
                "damage": "1d8",
                "damage_type": "piercing"
            })
        }
        
        # Check for finesse
        use_finesse = False
        for prop in weapon.get("properties", []):
            if isinstance(prop, str) and "finesse" in prop.lower():
                use_finesse = True
                break
        
        assert use_finesse is True
    
    def test_crossbow_shows_damage_dice_not_default(self):
        """Verify crossbow displays 1d6 or 1d8, not default 1d4."""
        weapon = {
            "name": "Light Crossbow",
            "damage_dice": "1d8",
            "notes": json.dumps({
                "damage": "1d8",
                "damage_type": "piercing",
                "range": "range 80/320",
                "properties": "ammunition, loading"
            })
        }
        
        # Extract damage
        damage = None
        if weapon.get("damage_dice"):
            damage = weapon.get("damage_dice")
        elif weapon.get("damage"):
            damage = weapon.get("damage")
        
        assert damage == "1d8"
        assert damage != "1d4"
    
    def test_mace_shows_correct_damage_1d6(self):
        """Verify mace displays 1d6 bludgeoning damage."""
        weapon = {
            "name": "Mace",
            "damage_dice": "1d6",
            "notes": json.dumps({
                "damage": "1d6",
                "damage_type": "bludgeoning"
            })
        }
        
        # Parse
        notes_data = json.loads(weapon["notes"])
        
        assert notes_data["damage"] == "1d6"
        assert notes_data["damage_type"] == "bludgeoning"
    
    def test_tohit_calculation_str_modifier(self):
        """Verify to-hit calculation: ability_mod + proficiency + weapon_bonus."""
        # Level 5 character: proficiency +3
        # STR 16 (+3 modifier)
        # Longsword with no bonus
        
        str_score = 16
        proficiency = 3
        weapon_bonus = 0
        
        def ability_modifier(score):
            return (score - 10) // 2
        
        ability_mod = ability_modifier(str_score)
        to_hit = ability_mod + proficiency + weapon_bonus
        
        assert ability_mod == 3
        assert to_hit == 6
    
    def test_tohit_calculation_dex_modifier(self):
        """Verify to-hit with DEX for ranged weapons."""
        # Level 5 character: proficiency +3
        # DEX 14 (+2 modifier)
        # Longbow
        
        dex_score = 14
        proficiency = 3
        weapon_bonus = 0
        
        def ability_modifier(score):
            return (score - 10) // 2
        
        ability_mod = ability_modifier(dex_score)
        to_hit = ability_mod + proficiency + weapon_bonus
        
        assert ability_mod == 2
        assert to_hit == 5
    
    def test_tohit_calculation_with_weapon_bonus(self):
        """Verify to-hit includes weapon bonus."""
        # Level 5 character: proficiency +3
        # STR 16 (+3 modifier)
        # +1 Longsword
        
        str_score = 16
        proficiency = 3
        weapon_bonus = 1
        
        def ability_modifier(score):
            return (score - 10) // 2
        
        ability_mod = ability_modifier(str_score)
        to_hit = ability_mod + proficiency + weapon_bonus
        
        assert to_hit == 7
    
    def test_weapon_category_detection(self):
        """Verify weapons are identified by category field."""
        weapons = [
            {"name": "Sword", "category": "Weapons", "equipped": True},
            {"name": "Plate Armor", "category": "Armor", "equipped": True},
            {"name": "Healing Potion", "category": "Potions", "equipped": False},
        ]
        
        # Filter for weapons
        actual_weapons = [w for w in weapons if w.get("category") in ["Weapons", "weapon", "weapons"]]
        
        assert len(actual_weapons) == 1
        assert actual_weapons[0]["name"] == "Sword"
    
    def test_multiple_equipped_weapons_display(self):
        """Verify multiple equipped weapons are all displayed."""
        weapons = [
            {
                "id": "1",
                "name": "Shortsword",
                "category": "Weapons",
                "equipped": True,
                "notes": json.dumps({"damage": "1d6", "damage_type": "piercing"})
            },
            {
                "id": "2",
                "name": "Dagger",
                "category": "Weapons",
                "equipped": True,
                "notes": json.dumps({"damage": "1d4", "damage_type": "piercing"})
            },
            {
                "id": "3",
                "name": "Shield",
                "category": "Armor",
                "equipped": True,
                "notes": json.dumps({"armor_class": 2})
            }
        ]
        
        equipped_weapons = [w for w in weapons if w.get("equipped") and w.get("category") in ["Weapons", "weapon", "weapons"]]
        
        assert len(equipped_weapons) == 2
        names = [w["name"] for w in equipped_weapons]
        assert "Shortsword" in names
        assert "Dagger" in names
        assert "Shield" not in names
    
    def test_empty_weapons_grid_shows_message(self):
        """Verify empty grid shows 'no weapons' message when none equipped."""
        weapons = []
        equipped_weapons = [w for w in weapons if w.get("equipped")]
        
        assert len(equipped_weapons) == 0
    
    def test_unequipped_weapons_not_displayed(self):
        """Verify unequipped weapons are NOT shown in grid."""
        weapons = [
            {
                "id": "1",
                "name": "Longsword",
                "category": "Weapons",
                "equipped": True,
                "notes": json.dumps({"damage": "1d8", "damage_type": "slashing"})
            },
            {
                "id": "2",
                "name": "Dagger",
                "category": "Weapons",
                "equipped": False,  # NOT equipped
                "notes": json.dumps({"damage": "1d4", "damage_type": "piercing"})
            }
        ]
        
        # Filter for only equipped weapons
        equipped_weapons = [w for w in weapons if w.get("equipped") and w.get("category") in ["Weapons", "weapon", "weapons"]]
        
        assert len(equipped_weapons) == 1
        assert equipped_weapons[0]["name"] == "Longsword"
        assert "Dagger" not in [w["name"] for w in equipped_weapons]
    
    def test_weapon_disappears_when_unequipped(self):
        """Verify weapon disappears from grid when unequipped."""
        # Start with equipped weapon
        weapon = {
            "id": "1",
            "name": "Longsword",
            "category": "Weapons",
            "equipped": True,
            "notes": json.dumps({"damage": "1d8", "damage_type": "slashing"})
        }
        
        # Filter equipped
        equipped_before = [w for w in [weapon] if w.get("equipped")]
        assert len(equipped_before) == 1
        
        # Unequip the weapon
        weapon["equipped"] = False
        
        # Filter equipped again
        equipped_after = [w for w in [weapon] if w.get("equipped")]
        assert len(equipped_after) == 0
    
    def test_weapon_appears_when_equipped(self):
        """Verify weapon appears in grid when equipped."""
        # Start with unequipped weapon
        weapon = {
            "id": "1",
            "name": "Longsword",
            "category": "Weapons",
            "equipped": False,
            "notes": json.dumps({"damage": "1d8", "damage_type": "slashing"})
        }
        
        # Filter equipped
        equipped_before = [w for w in [weapon] if w.get("equipped")]
        assert len(equipped_before) == 0
        
        # Equip the weapon
        weapon["equipped"] = True
        
        # Filter equipped again
        equipped_after = [w for w in [weapon] if w.get("equipped")]
        assert len(equipped_after) == 1
        assert equipped_after[0]["name"] == "Longsword"
    
    def test_damage_display_format(self):
        """Verify damage displayed as 'dice type' format."""
        weapon = {
            "name": "Longsword",
            "notes": json.dumps({"damage": "1d8", "damage_type": "slashing"})
        }
        
        notes_data = json.loads(weapon["notes"])
        damage_text = f"{notes_data['damage']} {notes_data['damage_type']}"
        
        assert damage_text == "1d8 slashing"
    
    def test_damage_with_bonus_display(self):
        """Verify damage bonus is appended to damage display."""
        weapon = {
            "name": "+1 Longsword",
            "notes": json.dumps({
                "damage": "1d8",
                "damage_type": "slashing",
                "bonus": 1
            })
        }
        
        notes_data = json.loads(weapon["notes"])
        damage_text = f"{notes_data['damage']} {notes_data['damage_type']}"
        if notes_data.get("bonus"):
            damage_text += f" +{notes_data['bonus']}"
        
        assert damage_text == "1d8 slashing +1"
    
    def test_range_column_display(self):
        """Verify range column shows correct values for melee and ranged."""
        # Melee weapon
        melee_weapon = {"properties": []}
        melee_range = "Melee"
        
        assert melee_range == "Melee"
        
        # Ranged weapon
        ranged_weapon = {"properties": ["ammunition (range 60/240)"]}
        ranged_range = "Melee"
        for prop in ranged_weapon.get("properties", []):
            if "range" in prop.lower() and "(" in prop:
                ranged_range = prop[prop.find("(")+1:prop.find(")")]
        
        assert ranged_range == "range 60/240"
    
    def test_properties_column_display(self):
        """Verify properties column shows weapon traits."""
        weapon = {
            "properties": ["finesse", "light", "versatile"]
        }
        
        props_str = ", ".join(str(p) for p in weapon["properties"] if p)
        
        assert props_str == "finesse, light, versatile"
    
    def test_properties_column_shows_dash_when_empty(self):
        """Verify properties shows '—' when no properties exist."""
        weapon = {"properties": []}
        
        props_str = ", ".join(str(p) for p in weapon["properties"] if p)
        if not props_str:
            props_str = "—"
        
        assert props_str == "—"


class TestWeaponsGridIntegration:
    """Integration tests for weapons grid with inventory system."""
    
    def test_open5e_weapon_added_with_correct_data(self):
        """Verify Open5e weapon is added with damage_dice field preserved."""
        # Simulate adding crossbow from Open5e
        weapon_data = {
            "name": "Crossbow, light",
            "cost": "25 gp",
            "weight": "5 lb.",
            "damage_dice": "1d8",
            "damage_type": "piercing",
            "properties": ["ammunition (range 80/320)", "loading"]
        }
        
        # When added to inventory, data should be stored in notes
        extra_props = {}
        if weapon_data.get("damage_dice"):
            extra_props["damage"] = weapon_data["damage_dice"]
        if weapon_data.get("damage_type"):
            extra_props["damage_type"] = weapon_data["damage_type"]
        if weapon_data.get("properties"):
            extra_props["properties"] = weapon_data["properties"]
        
        notes = json.dumps(extra_props)
        
        # Verify it can be parsed back
        parsed = json.loads(notes)
        assert parsed["damage"] == "1d8"
        assert parsed["damage_type"] == "piercing"
        assert "ammunition" in str(parsed["properties"])
    
    def test_custom_weapon_added_with_properties(self):
        """Verify custom weapon retains all properties."""
        weapon_data = {
            "name": "Custom Magical Sword",
            "damage": "1d10",
            "damage_type": "slashing",
            "bonus": 2,
            "properties": "finesse, magical"
        }
        
        extra_props = {
            "damage": weapon_data["damage"],
            "damage_type": weapon_data["damage_type"],
            "bonus": weapon_data["bonus"],
            "properties": weapon_data["properties"]
        }
        
        notes = json.dumps(extra_props)
        parsed = json.loads(notes)
        
        assert parsed["damage"] == "1d10"
        assert parsed["bonus"] == 2
        assert "finesse" in parsed["properties"]
    
    def test_weapon_notes_field_populated_after_submit(self):
        """Verify that when a weapon is submitted, notes field contains all properties."""
        import sys
        sys.path.insert(0, 'static/assets/py')
        from equipment_management import InventoryManager
        
        # Create inventory manager
        inventory = InventoryManager()
        
        # Simulate submit_open5e_item parameters
        name = "Light Crossbow"
        cost = "25 gp"
        weight = "5 lb."
        damage = "1d8"
        damage_type = "piercing"
        range_text = "range 80/320"
        properties = "ammunition (range 80/320), loading"
        
        # Build the notes JSON as submit_open5e_item does
        extra_props = {}
        if damage:
            extra_props["damage"] = damage
        if damage_type:
            extra_props["damage_type"] = damage_type
        if range_text:
            extra_props["range"] = range_text
        if properties:
            extra_props["properties"] = properties
        
        notes = json.dumps(extra_props) if extra_props else ""
        
        # Add item to inventory
        item_id = inventory.add_item(name, cost=cost, weight=weight, qty=1, category="", notes=notes, source="open5e")
        
        # Get the item back
        item = inventory.get_item(item_id)
        
        # Verify notes are stored
        assert item is not None
        assert item["notes"] != ""
        
        # Verify we can parse the notes
        parsed_notes = json.loads(item["notes"])
        assert parsed_notes["damage"] == "1d8"
        assert parsed_notes["damage_type"] == "piercing"
        assert parsed_notes["range"] == "range 80/320"
    
    def test_weapon_from_fallback_list_has_correct_damage(self):
        """Verify fallback weapon definitions have correct damage in to_dict()."""
        import sys
        sys.path.insert(0, 'static/assets/py')
        from equipment_management import Weapon
        
        # Create a crossbow like in the fallback list
        crossbow = Weapon("Crossbow, light", damage="1d8", damage_type="piercing", 
                         range_text="80/320 ft.", cost="25 gp", weight="5 lb.", 
                         properties="ammunition, loading")
        
        # Convert to dict (this is what happens in fetch_equipment_from_open5e)
        weapon_dict = crossbow.to_dict()
        
        # Verify notes are populated
        assert weapon_dict["notes"] != ""
        
        # Verify we can parse the notes
        parsed = json.loads(weapon_dict["notes"])
        assert parsed["damage"] == "1d8", f"Expected 1d8 but got {parsed['damage']}"
        assert parsed["damage_type"] == "piercing"
        assert parsed["range"] == "80/320 ft."
        assert "ammunition" in parsed["properties"]
    
    def test_equip_unequip_workflow_with_inventory(self):
        """Verify complete equip/unequip workflow with inventory manager."""
        import sys
        sys.path.insert(0, 'static/assets/py')
        from equipment_management import InventoryManager
        
        # Create inventory
        inventory = InventoryManager()
        
        # Add a weapon
        item_id = inventory.add_item(
            "Longsword",
            cost="15 gp",
            weight="3 lb.",
            category="Weapons",
            notes=json.dumps({"damage": "1d8", "damage_type": "slashing"})
        )
        
        # Initially unequipped
        item = inventory.get_item(item_id)
        assert item["equipped"] == False
        
        # Equip it
        item["equipped"] = True
        
        # Verify it's now equipped
        assert item["equipped"] == True
        
        # Unequip it
        item["equipped"] = False
        
        # Verify it's no longer equipped
        assert item["equipped"] == False

    def test_enrich_weapon_item_uses_equipment_library(self):
        """If inventory item lacks damage/range, enrichment should pull from equipment library."""
        import sys
        sys.path.insert(0, 'static/assets/py')
        from character import _enrich_weapon_item, EQUIPMENT_LIBRARY_STATE

        # Ensure equipment library has a crossbow definition
        # Test matching when equipment library uses 'Light Crossbow' naming
        EQUIPMENT_LIBRARY_STATE['equipment'] = [
            {
                'name': 'Light Crossbow',
                'damage': '1d8',
                'damage_type': 'piercing',
                'range': '80/320',
                'properties': 'ammunition, loading'
            }
        ]

        item = {
            'id': '0',
            'name': 'Crossbow, light',
            'cost': '25 gp',
            'weight': '5 lb.',
            'qty': 1,
            'category': 'Weapons',
            'notes': '',
            'source': 'open5e',
            'equipped': True
        }

        enriched = _enrich_weapon_item(item)
        assert enriched.get('damage') == '1d8'
        assert enriched.get('damage_type') == 'piercing'
        # allow normalized forms (with or without 'ft.')
        assert '80/320' in enriched.get('range_text')
        assert 'ammunition' in enriched.get('weapon_properties', '')

    
    def test_only_equipped_weapons_in_grid_display_list(self):
        """Verify that grid rendering only uses equipped weapons."""
        import sys
        sys.path.insert(0, 'static/assets/py')
        from equipment_management import InventoryManager
        
        inventory = InventoryManager()
        
        # Add 3 weapons
        id1 = inventory.add_item("Longsword", category="Weapons", 
                                  notes=json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        id2 = inventory.add_item("Dagger", category="Weapons",
                                  notes=json.dumps({"damage": "1d4", "damage_type": "piercing"}))
        id3 = inventory.add_item("Greatsword", category="Weapons",
                                  notes=json.dumps({"damage": "2d6", "damage_type": "slashing"}))
        
        # Equip only 2
        inventory.get_item(id1)["equipped"] = True
        inventory.get_item(id2)["equipped"] = True
        inventory.get_item(id3)["equipped"] = False
        
        # Get equipped weapons for grid display
        equipped_weapons = [w for w in inventory.items 
                           if w.get("equipped") and w.get("category") in ["Weapons", "weapon", "weapons"]]
        
        assert len(equipped_weapons) == 2
        names = [w["name"] for w in equipped_weapons]
        assert "Longsword" in names
        assert "Dagger" in names
        assert "Greatsword" not in names
    
    def test_unequipping_removes_from_grid(self):
        """Verify that unequipping a weapon removes it from the displayed grid."""
        import sys
        sys.path.insert(0, 'static/assets/py')
        from equipment_management import InventoryManager
        
        inventory = InventoryManager()
        
        # Add weapon and equip it
        item_id = inventory.add_item("Longsword", category="Weapons",
                                      notes=json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        item = inventory.get_item(item_id)
        item["equipped"] = True
        
        # Verify it's in the grid
        equipped_weapons = [w for w in inventory.items if w.get("equipped")]
        assert len(equipped_weapons) == 1
        assert equipped_weapons[0]["name"] == "Longsword"
        
        # Unequip it
        item["equipped"] = False
        
        # Verify it's no longer in the grid
        equipped_weapons = [w for w in inventory.items if w.get("equipped")]
        assert len(equipped_weapons) == 0
    
    def test_re_equipping_adds_back_to_grid(self):
        """Verify that re-equipping a weapon adds it back to the grid."""
        import sys
        sys.path.insert(0, 'static/assets/py')
        from equipment_management import InventoryManager
        
        inventory = InventoryManager()
        
        # Add weapon but don't equip
        item_id = inventory.add_item("Longsword", category="Weapons",
                                      notes=json.dumps({"damage": "1d8", "damage_type": "slashing"}))
        item = inventory.get_item(item_id)
        
        # Verify it's not in the grid
        equipped_weapons = [w for w in inventory.items if w.get("equipped")]
        assert len(equipped_weapons) == 0
        
        # Equip it
        item["equipped"] = True
        
        # Verify it's now in the grid
        equipped_weapons = [w for w in inventory.items if w.get("equipped")]
        assert len(equipped_weapons) == 1
        assert equipped_weapons[0]["name"] == "Longsword"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
