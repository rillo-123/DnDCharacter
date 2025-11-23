"""
Unit tests for equipment chooser functionality
Tests Open5e API integration and equipment item selection
"""

import unittest
import urllib.request
import json
import re


class TestOpen5eEquipmentAPI(unittest.TestCase):
    """Test fetching equipment from Open5e API"""
    
    def test_fetch_weapons(self):
        """Test fetching weapons from Open5e"""
        try:
            with urllib.request.urlopen("https://api.open5e.com/weapons/") as response:
                data = json.loads(response.read().decode())
            
            self.assertIn("results", data)
            self.assertGreater(len(data["results"]), 0)
            
            # Verify structure of first weapon
            first_weapon = data["results"][0]
            self.assertIn("name", first_weapon)
            self.assertIn("cost", first_weapon)
            self.assertIn("weight", first_weapon)
        except Exception as e:
            self.fail(f"Failed to fetch weapons: {e}")
    
    def test_fetch_armor(self):
        """Test fetching armor from Open5e"""
        try:
            with urllib.request.urlopen("https://api.open5e.com/armor/") as response:
                data = json.loads(response.read().decode())
            
            self.assertIn("results", data)
            self.assertGreater(len(data["results"]), 0)
            
            # Verify structure of first armor
            first_armor = data["results"][0]
            self.assertIn("name", first_armor)
            self.assertIn("cost", first_armor)
            self.assertIn("weight", first_armor)
        except Exception as e:
            self.fail(f"Failed to fetch armor: {e}")
    
    def test_mace_exists(self):
        """Test that mace is available in weapons"""
        try:
            with urllib.request.urlopen("https://api.open5e.com/weapons/") as response:
                data = json.loads(response.read().decode())
            
            weapons = [item["name"] for item in data["results"]]
            self.assertIn("Mace", weapons, "Mace should be in weapons list")
        except Exception as e:
            self.fail(f"Failed to verify mace: {e}")
    
    def test_total_equipment_count(self):
        """Test total equipment items (weapons + armor)"""
        try:
            total = 0
            
            # Count weapons
            with urllib.request.urlopen("https://api.open5e.com/weapons/") as response:
                weapons = json.loads(response.read().decode())
            total += len(weapons["results"])
            
            # Count armor
            with urllib.request.urlopen("https://api.open5e.com/armor/") as response:
                armor = json.loads(response.read().decode())
            total += len(armor["results"])
            
            # Should have at least 70 items (50 weapons + 20+ armor)
            self.assertGreaterEqual(total, 70)
        except Exception as e:
            self.fail(f"Failed to count total equipment: {e}")


class TestEquipmentParsing(unittest.TestCase):
    """Test parsing of equipment cost and weight strings"""
    
    def test_parse_cost_gp(self):
        """Test parsing cost strings with 'gp' suffix"""
        cost_str = "5 gp"
        match = re.search(r'(\d+(?:\.\d+)?)', cost_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 5.0)
    
    def test_parse_weight_lb(self):
        """Test parsing weight strings with 'lb.' suffix"""
        weight_str = "4 lb."
        match = re.search(r'(\d+(?:\.\d+)?)', weight_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 4.0)
    
    def test_parse_decimal_cost(self):
        """Test parsing decimal cost"""
        cost_str = "0.5 gp"
        match = re.search(r'(\d+(?:\.\d+)?)', cost_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 0.5)
    
    def test_parse_unknown_cost(self):
        """Test parsing unknown cost format"""
        cost_str = "Unknown"
        match = re.search(r'(\d+(?:\.\d+)?)', cost_str)
        self.assertIsNone(match)
    
    def test_parse_multiple_numbers(self):
        """Test that regex gets first number only"""
        cost_str = "50 gp or 100 sp"
        match = re.search(r'(\d+(?:\.\d+)?)', cost_str)
        self.assertIsNotNone(match)
        self.assertEqual(float(match.group(1)), 50.0)


class TestEquipmentSearch(unittest.TestCase):
    """Test equipment search filtering"""
    
    def setUp(self):
        """Fetch equipment for testing"""
        all_items = []
        
        # Fetch weapons
        with urllib.request.urlopen("https://api.open5e.com/weapons/") as response:
            weapons_data = json.loads(response.read().decode())
        for weapon in weapons_data.get('results', []):
            all_items.append({
                "name": weapon.get("name", "Unknown"),
                "cost": weapon.get("cost", "N/A"),
                "weight": weapon.get("weight", "N/A")
            })
        
        # Fetch armor
        with urllib.request.urlopen("https://api.open5e.com/armor/") as response:
            armor_data = json.loads(response.read().decode())
        for armor in armor_data.get('results', []):
            all_items.append({
                "name": armor.get("name", "Unknown"),
                "cost": armor.get("cost", "N/A"),
                "weight": armor.get("weight", "N/A")
            })
        
        self.all_items = all_items
    
    def search_items(self, search_term):
        """Helper to search items"""
        return [item for item in self.all_items if search_term.lower() in item["name"].lower()]
    
    def test_search_mace(self):
        """Test searching for mace"""
        results = self.search_items("mace")
        self.assertGreater(len(results), 0)
        self.assertIn("Mace", [r["name"] for r in results])
    
    def test_search_sword(self):
        """Test searching for sword"""
        results = self.search_items("sword")
        self.assertGreater(len(results), 0)
    
    def test_search_armor(self):
        """Test searching for armor types"""
        results = self.search_items("armor")
        self.assertGreater(len(results), 0)
    
    def test_search_case_insensitive(self):
        """Test that search is case insensitive"""
        results_lower = self.search_items("mace")
        results_upper = self.search_items("MACE")
        self.assertEqual(len(results_lower), len(results_upper))
    
    def test_search_partial_match(self):
        """Test partial string matching"""
        results = self.search_items("lon")  # Should match "Longsword"
        self.assertGreater(len(results), 0)
        names = [r["name"] for r in results]
        self.assertTrue(any("Longsword" in name for name in names))
    
    def test_search_no_results(self):
        """Test search with no results"""
        results = self.search_items("xyz_nonexistent")
        self.assertEqual(len(results), 0)


if __name__ == "__main__":
    unittest.main()
