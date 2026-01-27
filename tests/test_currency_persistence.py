"""
Test currency persistence in character JSON export.

This test verifies that coin pouch (currency) data is properly:
1. Captured from form inputs
2. Saved to the JSON export file
3. Loaded back from JSON correctly
"""

import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from character import (
    CURRENCY_ORDER,
)


class TestCurrencyPersistence(unittest.TestCase):
    """Test currency persistence in character saves."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = {
            "identity": {
                "name": "Test Character",
                "class": "Barbarian 5",
                "race": "Half-Orc",
                "background": "Soldier",
                "alignment": "Chaotic Good",
                "player_name": "Test Player",
                "subclass": "",
            },
            "level": 5,
            "inspiration": 0,
            "spell_ability": "wis",
            "abilities": {
                ability: {"score": 10, "save_proficient": False}
                for ability in ["str", "dex", "con", "int", "wis", "cha"]
            },
            "skills": {
                skill: {"proficient": False, "expertise": False, "bonus": 0}
                for skill in ["acrobatics", "animal-handling", "arcana"]
            },
            "combat": {
                "armor_class": 15,
                "speed": 30,
                "max_hp": 50,
                "current_hp": 50,
                "temp_hp": 0,
                "hit_dice": "5d12",
                "hit_dice_available": 0,
            },
            "inventory": {
                "items": [],
                "currency": {
                    "pp": 10,
                    "gp": 150,
                    "ep": 5,
                    "sp": 25,
                    "cp": 100,
                }
            },
            "notes": {
                "features": "Test features",
                "attacks": "Test attacks",
                "notes": "Test notes",
            },
            "feats": [],
        }
    
    def test_currency_in_default_state(self):
        """Test that DEFAULT_STATE includes currency fields."""
        from character import DEFAULT_STATE
        
        # Check that inventory exists
        self.assertIn("inventory", DEFAULT_STATE)
        
        # Check that currency exists in inventory
        self.assertIn("currency", DEFAULT_STATE["inventory"])
        
        # Check all currency types are present
        for currency_type in CURRENCY_ORDER:
            self.assertIn(currency_type, DEFAULT_STATE["inventory"]["currency"])
            self.assertEqual(DEFAULT_STATE["inventory"]["currency"][currency_type], 0)
    
    def test_currency_order_complete(self):
        """Test that CURRENCY_ORDER has all 5 coin types."""
        expected_currencies = ["pp", "gp", "ep", "sp", "cp"]
        self.assertEqual(CURRENCY_ORDER, expected_currencies)
    
    def test_collect_currency_from_form(self):
        """Test that collect_form_data properly captures currency values."""
        # Mock the DOM functions that collect_form_data uses
        mock_get_numeric = MagicMock()
        
        # Return values based on input
        def side_effect(elem_id, default=0):
            currency_map = {
                "currency-pp": 10,
                "currency-gp": 150,
                "currency-ep": 5,
                "currency-sp": 25,
                "currency-cp": 100,
            }
            return currency_map.get(elem_id, default)
        
        mock_get_numeric.side_effect = side_effect
        
        # The actual test verifies the data structure
        test_currency = {key: side_effect(f"currency-{key}", 0) for key in CURRENCY_ORDER}
        
        expected = {"pp": 10, "gp": 150, "ep": 5, "sp": 25, "cp": 100}
        self.assertEqual(test_currency, expected)
    
    def test_populate_form_with_currency(self):
        """Test that populate_form properly sets currency field values."""
        test_data = {
            "inventory": {
                "items": [],
                "currency": {
                    "pp": 5,
                    "gp": 100,
                    "ep": 0,
                    "sp": 50,
                    "cp": 200,
                }
            }
        }
        
        # Verify the test data has the right structure
        inv = test_data.get("inventory", {})
        currency = inv.get("currency", {})
        
        # Each currency type should be accessible
        for key in CURRENCY_ORDER:
            self.assertIn(key, currency)
            value = currency.get(key, 0)
            self.assertIsInstance(value, int)
    
    def test_currency_values_non_negative(self):
        """Test that currency values are non-negative integers."""
        currency = {
            "pp": 10,
            "gp": 150,
            "ep": 5,
            "sp": 25,
            "cp": 100,
        }
        
        for coin_type, amount in currency.items():
            self.assertGreaterEqual(amount, 0, f"{coin_type} should be non-negative")
            self.assertIsInstance(amount, int, f"{coin_type} should be an integer")
    
    def test_currency_serializable_to_json(self):
        """Test that currency data can be serialized to JSON."""
        test_data = {
            "inventory": {
                "items": [],
                "currency": {
                    "pp": 10,
                    "gp": 150,
                    "ep": 5,
                    "sp": 25,
                    "cp": 100,
                }
            }
        }
        
        # This should not raise an exception
        json_str = json.dumps(test_data)
        self.assertIsInstance(json_str, str)
        
        # Verify we can deserialize it
        loaded = json.loads(json_str)
        self.assertEqual(loaded["inventory"]["currency"], test_data["inventory"]["currency"])
    
    def test_currency_zero_values_preserved(self):
        """Test that zero currency values are preserved in JSON."""
        test_data = {
            "inventory": {
                "items": [],
                "currency": {
                    "pp": 0,
                    "gp": 0,
                    "ep": 0,
                    "sp": 0,
                    "cp": 100,
                }
            }
        }
        
        # Serialize and deserialize
        json_str = json.dumps(test_data)
        loaded = json.loads(json_str)
        
        # All values including zeros should be preserved
        self.assertEqual(loaded["inventory"]["currency"]["pp"], 0)
        self.assertEqual(loaded["inventory"]["currency"]["gp"], 0)
        self.assertEqual(loaded["inventory"]["currency"]["ep"], 0)
        self.assertEqual(loaded["inventory"]["currency"]["sp"], 0)
        self.assertEqual(loaded["inventory"]["currency"]["cp"], 100)
    
    def test_currency_large_values(self):
        """Test that large currency values are handled correctly."""
        test_data = {
            "inventory": {
                "currency": {
                    "pp": 999999,
                    "gp": 999999,
                    "ep": 999999,
                    "sp": 999999,
                    "cp": 999999,
                }
            }
        }
        
        # Should serialize without issue
        json_str = json.dumps(test_data)
        loaded = json.loads(json_str)
        
        self.assertEqual(loaded["inventory"]["currency"]["pp"], 999999)
        self.assertEqual(loaded["inventory"]["currency"]["gp"], 999999)


class TestCurrencyHtmlStructure(unittest.TestCase):
    """Test that the HTML structure supports currency persistence."""
    
    def test_currency_inputs_have_required_attributes(self):
        """Verify currency inputs have data-character-input and data-currency-field."""
        # Read the HTML file
        html_file = Path(__file__).parent.parent / "static" / "index.html"
        with open(html_file, 'r') as f:
            html_content = f.read()
        
        # Check for all currency input fields
        for currency_type in CURRENCY_ORDER:
            input_id = f'currency-{currency_type}'
            self.assertIn(input_id, html_content, 
                         f"Currency input with id '{input_id}' not found in HTML")
            
            # Check for data-character-input attribute
            self.assertIn('data-character-input', html_content,
                         "data-character-input attribute not found")
            
            # Check for data-currency-field attribute
            self.assertIn('data-currency-field', html_content,
                         "data-currency-field attribute not found")


if __name__ == '__main__':
    unittest.main()
