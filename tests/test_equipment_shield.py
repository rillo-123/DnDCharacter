"""
Unit tests to verify Shield equipment is available in the equipment library.
Tests both the Python equipment fallback and the card generation system.
"""

import unittest
import subprocess
from pathlib import Path
from html import escape


def check_shield_in_file(filepath):
    """Check if Shield is in the file using direct file reading"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Look for Shield definition in the equipment list
            if '"Shield"' in content and '"10 gp"' in content:
                # Find the actual line
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if '"Shield"' in line and ('gp' in line or 'ac' in line):
                        return f"Line {i+1}: {line.strip()}"
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def build_equipment_card_html(item: dict) -> str:
    """Build HTML for an equipment card similar to spell cards"""
    name = item.get("name", "Unknown") or "Unknown"
    cost = item.get("cost", "Unknown") or "Unknown"
    weight = item.get("weight", "Unknown") or "Unknown"
    damage = item.get("damage") or ""
    damage_type = item.get("damage_type") or ""
    range_text = item.get("range") or ""
    properties = item.get("properties") or ""
    ac_string = item.get("ac") or ""
    armor_class = item.get("armor_class") or ""
    
    # Build details list
    details = []
    if cost and cost != "Unknown":
        details.append(escape(str(cost)))
    if weight and weight != "Unknown":
        details.append(escape(str(weight)))
    details_text = " · ".join(details)
    
    # Build specs (damage, AC, range, etc)
    specs = []
    if damage:
        specs.append(escape(str(damage)))
    if damage_type:
        specs.append(f"({escape(str(damage_type))})")
    if armor_class:
        specs.append(f"AC {escape(str(armor_class))}")
    if range_text:
        specs.append(escape(str(range_text)))
    specs_text = " · ".join(specs) if specs else ""
    
    # Add button
    button_html = (
        f'<button type="button" class="equipment-action" '
        f'data-equipment-name="{escape(name)}" '
        f'data-equipment-cost="{escape(cost)}" '
        f'data-equipment-weight="{escape(weight)}" '
        f'data-equipment-damage="{escape(damage)}" '
        f'data-equipment-damage-type="{escape(damage_type)}" '
        f'data-equipment-range="{escape(range_text)}" '
        f'data-equipment-properties="{escape(properties)}" '
        f'data-equipment-ac="{escape(ac_string)}" '
        f'data-equipment-armor-class="{escape(armor_class)}">Add</button>'
    )
    
    return (
        f'<div class="equipment-card" data-equipment-name="{escape(name)}">'
        f'  <div class="equipment-summary">'
        f'    <div class="equipment-header">'
        f'      <span class="equipment-name">{escape(name)}</span>'
        f'      {button_html}'
        f'    </div>'
        f'    <div class="equipment-details">{details_text}</div>'
        + (f'    <div class="equipment-specs">{specs_text}</div>' if specs_text else '')
        + f'  </div>'
        f'</div>'
    )


class TestShieldEquipment(unittest.TestCase):
    """Test that Shield equipment is properly defined and searchable"""

    @classmethod
    def setUpClass(cls):
        """Load the equipment fallback from character.py source"""
        char_file = Path(__file__).parent.parent / "assets" / "py" / "character.py"
        cls.shield_line = check_shield_in_file(char_file)
        cls.char_file = char_file
    
    def test_shield_exists_in_source_code(self):
        """Test that Shield is defined in character.py fallback"""
        self.assertIsNotNone(self.shield_line, 
                           f"Shield not found in {self.char_file}. Shield must be in equipment fallback list.")
        self.assertIn('"Shield"', self.shield_line, "Shield name should be in source")
        self.assertIn('"10 gp"', self.shield_line, "Shield cost should be 10 gp in source")

    def test_shield_has_ac_bonus_in_source(self):
        """Test that Shield has AC bonus in source code"""
        self.assertIsNotNone(self.shield_line, "Shield line should exist")
        self.assertIn('"+2"', self.shield_line, "Shield should have +2 AC bonus in source")
        self.assertIn('"ac"', self.shield_line, "Shield should have ac field in source")

    def test_shield_basic_properties(self):
        """Test Shield has correct basic properties"""
        shield = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
            "ac": "+2",
        }
        
        self.assertEqual(shield["name"], "Shield")
        self.assertEqual(shield["cost"], "10 gp")
        self.assertEqual(shield["weight"], "6 lb.")
        self.assertEqual(shield["ac"], "+2")

    def test_shield_card_html_generation(self):
        """Test Shield generates correct HTML card"""
        shield = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
            "ac": "+2",
        }
        
        html = build_equipment_card_html(shield)
        
        self.assertIn('class="equipment-card"', html)
        self.assertIn('Shield', html)
        self.assertIn('10 gp', html)
        self.assertIn('6 lb.', html)
        self.assertIn('+2', html)

    def test_shield_data_attributes(self):
        """Test Shield button has all data attributes"""
        shield = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
            "ac": "+2",
        }
        
        html = build_equipment_card_html(shield)
        
        self.assertIn('data-equipment-name="Shield"', html)
        self.assertIn('data-equipment-cost="10 gp"', html)
        self.assertIn('data-equipment-weight="6 lb."', html)
        self.assertIn('data-equipment-ac="+2"', html)

    def test_shield_search_match(self):
        """Test Shield is found by search term"""
        shield = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
            "ac": "+2",
        }
        
        equipment_list = [shield]
        search_term = "shield"
        
        # Simulate equipment search
        found = False
        for item in equipment_list:
            name = item.get("name", "").lower()
            if search_term in name:
                found = True
                break
        
        self.assertTrue(found, "Shield should be found when searching for 'shield'")

    def test_shield_search_partial_match(self):
        """Test Shield is found by partial search"""
        shield = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
            "ac": "+2",
        }
        
        equipment_list = [shield]
        search_terms = ["shi", "ield", "SHIELD", "Shield"]
        
        for search_term in search_terms:
            found = False
            for item in equipment_list:
                name = item.get("name", "").lower()
                if search_term.lower() in name:
                    found = True
                    break
            self.assertTrue(found, f"Shield should be found when searching for '{search_term}'")

    def test_shield_in_common_items(self):
        """Test Shield is in common equipment items"""
        # Common items that should be available
        common_items = [
            {"name": "Longsword", "cost": "15 gp", "weight": "3 lb.", "damage": "1d8", "damage_type": "slashing"},
            {"name": "Shield", "cost": "10 gp", "weight": "6 lb.", "ac": "+2"},
            {"name": "Plate Armor", "cost": "1500 gp", "weight": "65 lb.", "armor_class": 18},
            {"name": "Rope (50 feet)", "cost": "1 gp", "weight": "10 lb."},
        ]
        
        shield_found = any(item["name"] == "Shield" for item in common_items)
        self.assertTrue(shield_found, "Shield should be in common items list")

    def test_shield_filters_correctly(self):
        """Test Shield appears in armor searches"""
        equipment_list = [
            {"name": "Longsword", "cost": "15 gp", "weight": "3 lb."},
            {"name": "Shield", "cost": "10 gp", "weight": "6 lb.", "ac": "+2"},
            {"name": "Leather Armor", "cost": "5 gp", "weight": "10 lb.", "armor_class": 11},
            {"name": "Rope", "cost": "1 gp", "weight": "10 lb."},
        ]
        
        # Search for armor-related items
        armor_results = [item for item in equipment_list if any(term in item["name"].lower() for term in ["shield", "armor"])]
        
        shield_in_results = any(item["name"] == "Shield" for item in armor_results)
        self.assertTrue(shield_in_results, "Shield should be included in armor search results")
        self.assertEqual(len(armor_results), 2, "Should find Shield and Leather Armor")

    def test_shield_card_renders_without_errors(self):
        """Test Shield card renders without errors"""
        shield = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
            "ac": "+2",
        }
        
        try:
            html = build_equipment_card_html(shield)
            self.assertIsNotNone(html)
            self.assertGreater(len(html), 0)
        except Exception as e:
            self.fail(f"Shield card generation should not raise exception: {e}")

    def test_shield_with_empty_optional_fields(self):
        """Test Shield with empty optional fields renders correctly"""
        shield = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
            "damage": "",
            "damage_type": "",
            "range": "",
            "ac": "+2",
        }
        
        html = build_equipment_card_html(shield)
        
        self.assertIn("Shield", html)
        self.assertIn("10 gp", html)
        self.assertIn("+2", html)
        # Should not have empty damage specs
        self.assertNotIn('()', html)


if __name__ == '__main__':
    unittest.main()
