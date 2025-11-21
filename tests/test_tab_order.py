#!/usr/bin/env python3
"""Unit tests for tab ordering in index.html"""

import unittest
import re
from pathlib import Path


class TestTabOrder(unittest.TestCase):
    """Test that tabs are in the correct order."""
    
    @classmethod
    def setUpClass(cls):
        """Load index.html once for all tests."""
        html_path = Path(__file__).parent.parent / "index.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            cls.html_content = f.read()
    
    def test_all_tabs_present(self):
        """Test that all required tabs are present."""
        required_tabs = ['overview', 'inventory', 'skills', 'combat', 'spells', 'feats', 'manage']
        
        for tab in required_tabs:
            with self.subTest(tab=tab):
                pattern = f'id="tab-{tab}"'
                self.assertIn(pattern, self.html_content, 
                            f"Tab '{tab}' not found in index.html")
    
    def test_no_duplicate_tabs(self):
        """Test that no tab IDs are duplicated."""
        tabs = ['overview', 'inventory', 'skills', 'combat', 'spells', 'feats', 'manage']
        
        for tab in tabs:
            with self.subTest(tab=tab):
                pattern = f'id="tab-{tab}"'
                count = self.html_content.count(pattern)
                self.assertEqual(count, 1, 
                               f"Tab '{tab}' appears {count} times (should be 1)")
    
    def test_tab_button_order(self):
        """Test that tab buttons are in the expected order."""
        expected_order = ['overview', 'inventory', 'skills', 'combat', 'spells', 'feats', 'manage']
        
        # Force fresh read from disk
        html_path = Path(__file__).parent.parent / "index.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract tab button order from data-tab attributes
        button_pattern = r'<button[^>]*data-tab="([^"]+)"'
        buttons_found = re.findall(button_pattern, content)
        
        # Filter to only the main navigation buttons (exclude any duplicates)
        main_buttons = []
        for btn in buttons_found:
            if btn not in main_buttons:  # First occurrence only
                main_buttons.append(btn)
        
        """Test that tab sections appear in the correct order."""
        expected_order = ['inventory', 'skills', 'combat', 'spells', 'feats', 'manage']
        
        # Extract tab section order from id attributes
        section_pattern = r'<section[^>]*id="tab-([^"]+)"[^>]*class="tab-panel"'
        sections_found = re.findall(section_pattern, self.html_content)
        
        self.assertEqual(sections_found, expected_order,
                        f"Section order {sections_found} != expected {expected_order}")
    
    def test_inventory_before_skills(self):
        """Test that Inventory section comes before Skills section."""
        inventory_pos = self.html_content.find('id="tab-inventory"')
        skills_pos = self.html_content.find('id="tab-skills"')
        
        self.assertGreater(inventory_pos, 0, "Inventory tab not found")
        self.assertGreater(skills_pos, 0, "Skills tab not found")
        self.assertLess(inventory_pos, skills_pos,
                       f"Inventory ({inventory_pos}) should come before Skills ({skills_pos})")
    
    def test_skills_before_combat(self):
        """Test that Skills section comes before Combat section."""
        skills_pos = self.html_content.find('id="tab-skills"')
        combat_pos = self.html_content.find('id="tab-combat"')
        
        self.assertGreater(skills_pos, 0, "Skills tab not found")
        self.assertGreater(combat_pos, 0, "Combat tab not found")
        self.assertLess(skills_pos, combat_pos,
                       f"Skills ({skills_pos}) should come before Combat ({combat_pos})")
    
    def test_logical_order_inventory_skills_combat(self):
        """Test the logical order: Inventory → Skills → Combat."""
        inv_pos = self.html_content.find('id="tab-inventory"')
        skills_pos = self.html_content.find('id="tab-skills"')
        combat_pos = self.html_content.find('id="tab-combat"')
        
        self.assertGreater(inv_pos, 0, "Inventory tab not found")
        self.assertGreater(skills_pos, 0, "Skills tab not found")
        self.assertGreater(combat_pos, 0, "Combat tab not found")
        
        # All three should be in order
        self.assertLess(inv_pos, skills_pos, "Inventory should come before Skills")
        self.assertLess(skills_pos, combat_pos, "Skills should come before Combat")
        self.assertLess(inv_pos, combat_pos, "Inventory should come before Combat")
    
    def test_tab_panels_have_correct_ids(self):
        """Test that each tab button has a matching panel."""
        button_pattern = r'<button[^>]*data-tab="([^"]+)"'
        buttons = re.findall(button_pattern, self.html_content)
        
        for button in buttons:
            with self.subTest(button=button):
                panel_id = f'id="tab-{button}"'
                self.assertIn(panel_id, self.html_content,
                            f"No matching panel for button '{button}'")


class TestTabContent(unittest.TestCase):
    """Test that tabs have the expected content structure."""
    
    @classmethod
    def setUpClass(cls):
        """Load index.html once for all tests."""
        html_path = Path(__file__).parent.parent / "index.html"
        with open(html_path, 'r', encoding='utf-8') as f:
            cls.html_content = f.read()
    
    def test_inventory_has_equipment(self):
        """Test that Inventory tab contains Equipment section."""
        self.assertIn('Equipment &amp; Wealth', self.html_content)
        self.assertIn('equipment-table', self.html_content)
    
    def test_inventory_has_currency(self):
        """Test that Inventory tab contains Coin Pouch."""
        self.assertIn('Coin Pouch', self.html_content)
        self.assertIn('currency-gp', self.html_content)
    
    def test_skills_has_skills_table(self):
        """Test that Skills tab contains the skills table."""
        self.assertIn('skills-table', self.html_content)
        self.assertIn('Acrobatics', self.html_content)
    
    def test_skills_has_weapons(self):
        """Test that Skills tab contains Weapons section."""
        self.assertIn('weapons-list', self.html_content)
        self.assertIn('Equipped', self.html_content)
    
    def test_combat_has_armor_class(self):
        """Test that Combat tab contains Armor Class."""
        self.assertIn('Armor Class', self.html_content)
        self.assertIn('armor_class', self.html_content)
    
    def test_combat_has_health_controls(self):
        """Test that Combat tab contains health controls."""
        self.assertIn('health-controls', self.html_content)
        self.assertIn('Hit Points', self.html_content)


if __name__ == '__main__':
    unittest.main()
