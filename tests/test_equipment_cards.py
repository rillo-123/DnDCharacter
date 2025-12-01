"""
Unit tests for equipment card HTML generation.

Tests the new equipment card display system that mirrors the spell library design.
"""

import unittest
from html import escape


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


class TestEquipmentCardHTML(unittest.TestCase):
    """Test equipment card HTML generation"""

    def test_basic_equipment_card_structure(self):
        """Test that equipment card has correct HTML structure"""
        item = {
            "name": "Longsword",
            "cost": "15 gp",
            "weight": "3 lb.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-card"', html)
        self.assertIn('class="equipment-summary"', html)
        self.assertIn('class="equipment-name"', html)
        self.assertIn('Longsword', html)

    def test_equipment_card_contains_add_button(self):
        """Test that equipment card includes an Add button"""
        item = {
            "name": "Dagger",
            "cost": "2 gp",
            "weight": "1 lb.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-action"', html)
        self.assertIn('>Add</button>', html)
        self.assertIn('data-equipment-name="Dagger"', html)

    def test_equipment_card_with_cost_and_weight(self):
        """Test that cost and weight are displayed"""
        item = {
            "name": "Plate Armor",
            "cost": "1500 gp",
            "weight": "65 lb.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('1500 gp', html)
        self.assertIn('65 lb.', html)

    def test_equipment_card_with_damage(self):
        """Test that damage is included when present"""
        item = {
            "name": "Greatsword",
            "cost": "50 gp",
            "weight": "6 lb.",
            "damage": "2d6",
            "damage_type": "slashing",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-specs"', html)
        self.assertIn('2d6', html)
        self.assertIn('slashing', html)

    def test_equipment_card_with_armor_class(self):
        """Test that AC is displayed for armor"""
        item = {
            "name": "Leather Armor",
            "cost": "5 gp",
            "weight": "10 lb.",
            "armor_class": "11",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-specs"', html)
        self.assertIn('AC 11', html)

    def test_equipment_card_with_range(self):
        """Test that range is displayed for weapons"""
        item = {
            "name": "Longbow",
            "cost": "50 gp",
            "weight": "3 lb.",
            "damage": "1d8",
            "damage_type": "piercing",
            "range": "150/600 ft.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('150/600 ft.', html)

    def test_equipment_card_escapes_html_special_chars(self):
        """Test that HTML special characters are escaped"""
        item = {
            "name": "Test & Item",
            "cost": "10 gp",
            "weight": "1 lb.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('Test &amp; Item', html)

    def test_equipment_card_button_has_all_data_attributes(self):
        """Test that button has all necessary data attributes"""
        item = {
            "name": "Mace",
            "cost": "5 gp",
            "weight": "4 lb.",
            "damage": "1d6",
            "damage_type": "bludgeoning",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('data-equipment-name=', html)
        self.assertIn('data-equipment-cost=', html)
        self.assertIn('data-equipment-weight=', html)
        self.assertIn('data-equipment-damage=', html)
        self.assertIn('data-equipment-damage-type=', html)

    def test_equipment_card_without_specs(self):
        """Test that card without damage/AC/range doesn't include specs div"""
        item = {
            "name": "Rope",
            "cost": "1 gp",
            "weight": "10 lb.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-card"', html)
        self.assertIn('1 gp', html)
        self.assertNotIn('class="equipment-specs"', html)

    def test_equipment_card_details_separator(self):
        """Test that cost and weight are separated by middle dot"""
        item = {
            "name": "Shield",
            "cost": "10 gp",
            "weight": "6 lb.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('10 gp', html)
        self.assertIn('6 lb.', html)
        self.assertIn('·', html)

    def test_multiple_equipment_cards(self):
        """Test building multiple equipment cards"""
        items = [
            {"name": "Sword", "cost": "15 gp", "weight": "3 lb."},
            {"name": "Shield", "cost": "10 gp", "weight": "6 lb."},
            {"name": "Rope", "cost": "1 gp", "weight": "10 lb."},
        ]
        
        html_list = [build_equipment_card_html(item) for item in items]
        
        self.assertEqual(len(html_list), 3)
        for html in html_list:
            self.assertIn('class="equipment-card"', html)
            self.assertIn('class="equipment-action"', html)


class TestEquipmentCardDataAttributes(unittest.TestCase):
    """Test that equipment card buttons have correct data attributes"""

    def test_button_data_attributes_preserved(self):
        """Test that all equipment data is stored in button attributes"""
        item = {
            "name": "Longsword",
            "cost": "15 gp",
            "weight": "3 lb.",
            "damage": "1d8",
            "damage_type": "slashing",
            "range": "melee",
            "properties": "versatile",
            "ac": "",
            "armor_class": "",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('data-equipment-name="Longsword"', html)
        self.assertIn('data-equipment-cost="15 gp"', html)
        self.assertIn('data-equipment-weight="3 lb."', html)
        self.assertIn('data-equipment-damage="1d8"', html)
        self.assertIn('data-equipment-damage-type="slashing"', html)
        self.assertIn('data-equipment-range="melee"', html)


class TestEquipmentCardFormatting(unittest.TestCase):
    """Test formatting of equipment cards"""

    def test_card_formatting_consistency(self):
        """Test that card formatting is consistent across items"""
        items = [
            {"name": "Item 1", "cost": "1 gp", "weight": "1 lb."},
            {"name": "Item 2", "cost": "100 gp", "weight": "50 lb."},
        ]
        
        html_list = [build_equipment_card_html(item) for item in items]
        
        for html in html_list:
            self.assertIn('<div class="equipment-card"', html)
            self.assertIn('<div class="equipment-summary"', html)
            self.assertIn('<div class="equipment-header"', html)
            self.assertIn('<button type="button" class="equipment-action"', html)

    def test_card_with_special_characters_in_name(self):
        """Test that items with special characters are handled"""
        item = {
            "name": "Mithril Chainmail",
            "cost": "50 gp",
            "weight": "20 lb.",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('Mithril Chainmail', html)
        self.assertIn('class="equipment-card"', html)

    def test_card_with_complex_damage_specs(self):
        """Test card with multiple damage specs"""
        item = {
            "name": "Magic Sword +1",
            "cost": "varies",
            "weight": "3 lb.",
            "damage": "1d8+1",
            "damage_type": "slashing",
            "range": "melee",
            "armor_class": "",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('1d8+1', html)
        self.assertIn('slashing', html)
        self.assertIn('melee', html)


class TestEquipmentCardEdgeCases(unittest.TestCase):
    """Test edge cases in equipment card generation"""

    def test_card_with_missing_optional_fields(self):
        """Test card generation with minimal fields"""
        item = {
            "name": "Unknown Item",
            "cost": "Unknown",
            "weight": "Unknown",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-card"', html)
        self.assertIn('Unknown Item', html)

    def test_card_with_empty_strings(self):
        """Test card with empty optional fields"""
        item = {
            "name": "Test Item",
            "cost": "10 gp",
            "weight": "5 lb.",
            "damage": "",
            "damage_type": "",
            "range": "",
            "properties": "",
            "ac": "",
            "armor_class": "",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-card"', html)
        self.assertNotIn('class="equipment-specs"', html)

    def test_card_with_none_values(self):
        """Test card with None values in optional fields"""
        item = {
            "name": "Test Item",
            "cost": "10 gp",
            "weight": "5 lb.",
            "damage": None,
            "damage_type": None,
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('class="equipment-card"', html)

    def test_card_button_click_data_structure(self):
        """Test that button data can be extracted for click handling"""
        item = {
            "name": "Sword",
            "cost": "15 gp",
            "weight": "3 lb.",
            "damage": "1d8",
            "damage_type": "slashing",
            "range": "melee",
            "properties": "versatile",
            "ac": "",
            "armor_class": "",
        }
        html = build_equipment_card_html(item)
        
        self.assertIn('type="button"', html)
        self.assertIn('class="equipment-action"', html)
        self.assertIn('data-equipment-name=', html)


class TestEquipmentCardIntegration(unittest.TestCase):
    """Integration tests for equipment cards"""

    def test_equipment_library_common_items(self):
        """Test generation of cards for common D&D equipment"""
        common_items = [
            {
                "name": "Longsword",
                "cost": "15 gp",
                "weight": "3 lb.",
                "damage": "1d8",
                "damage_type": "slashing",
            },
            {
                "name": "Leather Armor",
                "cost": "5 gp",
                "weight": "10 lb.",
                "armor_class": "11",
            },
            {
                "name": "Rope (50 feet)",
                "cost": "1 gp",
                "weight": "10 lb.",
            },
        ]
        
        for item in common_items:
            html = build_equipment_card_html(item)
            self.assertIn('class="equipment-card"', html)
            self.assertIn(item["name"], html)
            self.assertIn(item["cost"], html)
            self.assertIn(item["weight"], html)

    def test_equipment_cards_render_without_errors(self):
        """Test that all common equipment renders without errors"""
        weapons = [
            {"name": "Dagger", "cost": "2 gp", "weight": "1 lb.", "damage": "1d4", "damage_type": "piercing"},
            {"name": "Shortsword", "cost": "10 gp", "weight": "2 lb.", "damage": "1d6", "damage_type": "piercing"},
            {"name": "Mace", "cost": "5 gp", "weight": "4 lb.", "damage": "1d6", "damage_type": "bludgeoning"},
        ]
        
        armor = [
            {"name": "Leather", "cost": "5 gp", "weight": "10 lb.", "armor_class": "11"},
            {"name": "Chain Mail", "cost": "75 gp", "weight": "55 lb.", "armor_class": "16"},
            {"name": "Plate", "cost": "1500 gp", "weight": "65 lb.", "armor_class": "18"},
        ]
        
        gear = [
            {"name": "Rope (50 feet)", "cost": "1 gp", "weight": "10 lb."},
            {"name": "Backpack", "cost": "2 gp", "weight": "5 lb."},
            {"name": "Bedroll", "cost": "0.1 gp", "weight": "10 lb."},
        ]
        
        all_items = weapons + armor + gear
        
        for item in all_items:
            try:
                html = build_equipment_card_html(item)
                self.assertIsNotNone(html)
                self.assertIn('class="equipment-card"', html)
            except Exception as e:
                self.fail(f"Failed to render equipment card for {item['name']}: {e}")


if __name__ == '__main__':
    unittest.main()
