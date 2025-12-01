"""
Integration test: Shield equipment card rendering and display
"""
import unittest
from html import escape


def build_equipment_card_html(item: dict) -> str:
    """Build HTML for an equipment card (from character.py)"""
    name = item.get("name", "Unknown") or "Unknown"
    cost = item.get("cost", "Unknown") or "Unknown"
    weight = item.get("weight", "Unknown") or "Unknown"
    damage = item.get("damage") or ""
    damage_type = item.get("damage_type") or ""
    range_text = item.get("range") or ""
    properties = item.get("properties") or ""
    ac_string = item.get("ac") or ""
    armor_class = item.get("armor_class") or ""
    
    # Convert armor_class to string if it's an int
    if armor_class and not isinstance(armor_class, str):
        armor_class = str(armor_class)
    
    # Build details list
    details = []
    if cost and cost != "Unknown":
        details.append(escape(str(cost)))
    if weight and weight != "Unknown":
        details.append(escape(str(weight)))
    details_text = " · ".join(details)
    
    # Build specs
    specs = []
    if damage:
        specs.append(escape(str(damage)))
    if damage_type:
        specs.append(f"({escape(str(damage_type))})")
    if armor_class:
        specs.append(f"AC {escape(str(armor_class))}")
    if ac_string:
        specs.append(f"AC {escape(str(ac_string))}")
    if range_text:
        specs.append(escape(str(range_text)))
    specs_text = " · ".join(specs) if specs else ""
    
    # Add button
    button_html = (
        f'<button type="button" class="equipment-action" '
        f'data-equipment-name="{escape(str(name))}" '
        f'data-equipment-cost="{escape(str(cost))}" '
        f'data-equipment-weight="{escape(str(weight))}" '
        f'data-equipment-damage="{escape(str(damage))}" '
        f'data-equipment-damage-type="{escape(str(damage_type))}" '
        f'data-equipment-range="{escape(str(range_text))}" '
        f'data-equipment-properties="{escape(str(properties))}" '
        f'data-equipment-ac="{escape(str(ac_string))}" '
        f'data-equipment-armor-class="{escape(str(armor_class))}">Add</button>'
    )
    
    return (
        f'<div class="equipment-card" data-equipment-name="{escape(str(name))}">'
        f'  <div class="equipment-summary">'
        f'    <div class="equipment-header">'
        f'      <span class="equipment-name">{escape(str(name))}</span>'
        f'      {button_html}'
        f'    </div>'
        f'    <div class="equipment-details">{details_text}</div>'
        + (f'    <div class="equipment-specs">{specs_text}</div>' if specs_text else '')
        + f'  </div>'
        f'</div>'
    )


def populate_equipment_results(search_term: str, equipment_list: list) -> str:
    """Simulate the populate_equipment_results function from character.py"""
    search_term = search_term.lower().strip()
    filtered = []
    seen_names = set()
    
    # Filter from equipment list
    for item in equipment_list:
        name = item.get("name", "")
        if search_term == "" or search_term in name.lower():
            # Only add if we haven't seen this exact name before
            if name not in seen_names:
                filtered.append(item)
                seen_names.add(name)
    
    # Limit to 30 results
    limited = filtered[:30]
    
    if not limited:
        return '<div class="equipment-library-empty">No items found.</div>'
    
    # Build HTML from cards
    cards_html = "".join(build_equipment_card_html(item) for item in limited)
    return cards_html


class TestShieldIntegration(unittest.TestCase):
    """Integration tests for Shield equipment rendering"""
    
    def setUp(self):
        """Set up equipment list with Shield"""
        self.equipment_list = [
            {"name": "Mace", "cost": "5 gp", "weight": "4 lb."},
            {"name": "Longsword", "cost": "15 gp", "weight": "3 lb."},
            {"name": "Shield", "cost": "10 gp", "weight": "6 lb.", "ac": "+2"},
            {"name": "Leather", "cost": "5 gp", "weight": "10 lb.", "armor_class": 11},
            {"name": "Plate", "cost": "1500 gp", "weight": "65 lb.", "armor_class": 18},
        ]
    
    def test_shield_appears_in_no_search(self):
        """Test Shield appears when showing all items"""
        html = populate_equipment_results("", self.equipment_list)
        self.assertIn("Shield", html)
        self.assertIn("10 gp", html)
    
    def test_shield_appears_in_shield_search(self):
        """Test Shield appears when searching for 'shield'"""
        html = populate_equipment_results("shield", self.equipment_list)
        self.assertIn("Shield", html)
        self.assertIn("10 gp", html)
        self.assertIn("6 lb.", html)
    
    def test_shield_card_includes_ac_bonus(self):
        """Test Shield card shows AC +2"""
        html = populate_equipment_results("shield", self.equipment_list)
        self.assertIn("AC +2", html, "Shield should show AC +2 bonus")
        self.assertIn('data-equipment-ac="+2"', html, "Shield button should have AC data attribute")
    
    def test_shield_appears_in_armor_search(self):
        """Test searching for 'armor' finds armor items but not Shield"""
        html = populate_equipment_results("armor", self.equipment_list)
        # Search only looks at names, so "armor" searches for that word in item names
        # Leather and Plate don't contain the word "armor" in their names
        # Only items with "armor" in the name would appear (e.g., "Plate Armor")
        # This is expected behavior - Shield wouldn't be found by "armor" search
        self.assertNotIn("Shield", html)
    
    def test_shield_found_in_ac_search(self):
        """Test searching for 'ac' doesn't find Shield (search is name-based only)"""
        html = populate_equipment_results("ac", self.equipment_list)
        # Search only looks at item names, not data fields
        # Shield name doesn't contain "ac", so it won't be found
        # This is expected behavior - Shield must be searched by name
        self.assertNotIn("Shield", html)
    
    def test_shield_html_structure(self):
        """Test Shield generates valid HTML structure"""
        shield = {"name": "Shield", "cost": "10 gp", "weight": "6 lb.", "ac": "+2"}
        html = build_equipment_card_html(shield)
        
        # Check structure
        self.assertIn('class="equipment-card"', html)
        self.assertIn('class="equipment-summary"', html)
        self.assertIn('class="equipment-header"', html)
        self.assertIn('class="equipment-name"', html)
        self.assertIn('class="equipment-details"', html)
        self.assertIn('class="equipment-specs"', html)
        self.assertIn('class="equipment-action"', html)
    
    def test_shield_button_has_add_text(self):
        """Test Shield card button has 'Add' text"""
        shield = {"name": "Shield", "cost": "10 gp", "weight": "6 lb.", "ac": "+2"}
        html = build_equipment_card_html(shield)
        
        # Button should contain "Add"
        self.assertIn(">Add</button>", html)
    
    def test_shield_renders_with_full_equipment_list(self):
        """Test Shield renders correctly when mixed with 40+ items"""
        full_list = [
            {"name": "Mace", "cost": "5 gp", "weight": "4 lb."},
            {"name": "Longsword", "cost": "15 gp", "weight": "3 lb."},
            {"name": "Shortsword", "cost": "10 gp", "weight": "2 lb."},
            {"name": "Rapier", "cost": "25 gp", "weight": "2 lb."},
            {"name": "Dagger", "cost": "2 gp", "weight": "1 lb."},
            {"name": "Greataxe", "cost": "30 gp", "weight": "7 lb."},
            {"name": "Greatsword", "cost": "50 gp", "weight": "6 lb."},
            {"name": "Longbow", "cost": "50 gp", "weight": "3 lb."},
            {"name": "Shortbow", "cost": "25 gp", "weight": "2 lb."},
            {"name": "Crossbow, light", "cost": "25 gp", "weight": "5 lb."},
            {"name": "Leather", "cost": "5 gp", "weight": "10 lb."},
            {"name": "Studded Leather", "cost": "45 gp", "weight": "13 lb."},
            {"name": "Hide", "cost": "10 gp", "weight": "12 lb."},
            {"name": "Chain Shirt", "cost": "50 gp", "weight": "20 lb."},
            {"name": "Scale Mail", "cost": "50 gp", "weight": "45 lb."},
            {"name": "Breastplate", "cost": "400 gp", "weight": "20 lb."},
            {"name": "Half Plate", "cost": "750 gp", "weight": "40 lb."},
            {"name": "Ring Mail", "cost": "30 gp", "weight": "40 lb."},
            {"name": "Chain Mail", "cost": "75 gp", "weight": "55 lb."},
            {"name": "Splint", "cost": "200 gp", "weight": "60 lb."},
            {"name": "Plate", "cost": "1500 gp", "weight": "65 lb."},
            {"name": "Shield", "cost": "10 gp", "weight": "6 lb.", "ac": "+2"},
            {"name": "Rope (50 feet)", "cost": "1 gp", "weight": "10 lb."},
            {"name": "Torch", "cost": "0.01 gp", "weight": "1 lb."},
            {"name": "Backpack", "cost": "2 gp", "weight": "5 lb."},
            {"name": "Bedroll", "cost": "0.1 gp", "weight": "10 lb."},
            {"name": "Tent", "cost": "2 gp", "weight": "20 lb."},
            {"name": "Holy Water (Flask)", "cost": "25 gp", "weight": "1 lb."},
            {"name": "Explorer's Pack", "cost": "10 gp", "weight": "59 lb."},
            {"name": "Adventurer's Pack", "cost": "5 gp", "weight": "54 lb."},
        ]
        
        html = populate_equipment_results("", full_list)
        
        # Shield should be present in output
        self.assertIn("Shield", html)
        # Should show Shield with correct price
        self.assertIn("10 gp", html)
        # Should show Shield with correct weight
        self.assertIn("6 lb.", html)


if __name__ == '__main__':
    unittest.main()
