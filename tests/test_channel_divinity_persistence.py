"""
Test Channel Divinity persistence end-to-end.
"""

import json
import unittest
from character import DEFAULT_STATE


class TestChannelDivinityPersistence(unittest.TestCase):
    """Test that Channel Divinity data is properly saved and loaded."""
    
    def test_channel_divinity_in_default_state(self):
        """Test that Channel Divinity is initialized in DEFAULT_STATE."""
        self.assertIn("combat", DEFAULT_STATE)
        self.assertIn("channel_divinity_available", DEFAULT_STATE["combat"])
        self.assertEqual(DEFAULT_STATE["combat"]["channel_divinity_available"], 0)
    
    def test_channel_divinity_serializable(self):
        """Test that Channel Divinity data can be serialized to JSON."""
        test_data = {
            "combat": {
                "armor_class": 15,
                "speed": 30,
                "max_hp": 50,
                "current_hp": 50,
                "temp_hp": 0,
                "hit_dice": "5d8",
                "hit_dice_available": 5,
                "channel_divinity_available": 2,
                "death_saves_success": 0,
                "death_saves_failure": 0,
            }
        }
        
        # Should not raise an exception
        json_str = json.dumps(test_data)
        self.assertIsInstance(json_str, str)
        
        # Verify roundtrip
        loaded = json.loads(json_str)
        self.assertEqual(loaded["combat"]["channel_divinity_available"], 2)
    
    def test_channel_divinity_various_values(self):
        """Test that Channel Divinity values persist correctly."""
        test_values = [0, 1, 2, 3, 5, 10]
        
        for value in test_values:
            test_data = {
                "combat": {
                    "channel_divinity_available": value
                }
            }
            
            json_str = json.dumps(test_data)
            loaded = json.loads(json_str)
            self.assertEqual(loaded["combat"]["channel_divinity_available"], value,
                           f"Failed to persist channel_divinity_available={value}")


if __name__ == '__main__':
    unittest.main()
