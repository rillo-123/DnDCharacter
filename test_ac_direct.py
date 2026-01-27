"""
Direct test of calculate_armor_class() function with Enwer's equipment.
This test mocks the global INVENTORY_MANAGER to test the actual function.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add static assets to path
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))


def test_calculate_armor_class_with_breastplate_and_shield():
    """Test calculate_armor_class() with Breastplate + Shield +1."""
    
    # Import character module
    import character
    
    # Mock inventory manager with Enwer's equipment
    mock_inventory = Mock()
    mock_inventory.items = [
        {
            "id": "1",
            "name": "Breastplate",
            "category": "Armor",
            "equipped": True,
            "notes": '{"armor_class": "14", "armor_type": "medium"}'
        },
        {
            "id": "2",
            "name": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": '{"bonus": 3, "armor_type": "Shield"}'
        },
        {
            "id": "3",
            "name": "Mace",
            "category": "Weapons",
            "equipped": True,
            "notes": '{"damage": "1d6", "damage_type": "bludgeoning"}'
        }
    ]
    
    # Mock the form values
    def mock_get_numeric_value(field_id, default):
        if field_id == "dex-score":
            return 10  # DEX 10 = +0 modifier
        return default
    
    def mock_is_equipable(item):
        return True
    
    # Patch the global variables and functions
    with patch.object(character, 'INVENTORY_MANAGER', mock_inventory):
        with patch.object(character, 'get_numeric_value', side_effect=mock_get_numeric_value):
            with patch.object(character, 'is_equipable', side_effect=mock_is_equipable):
                # Call the function
                print("\n=== Testing calculate_armor_class() ===")
                ac = character.calculate_armor_class()
                print(f"Result: AC = {ac}")
                
                # Verify
                expected = 17  # 14 (breastplate) + 0 (DEX) + 3 (shield)
                if ac == expected:
                    print(f"✓ SUCCESS: AC is {ac} (expected {expected})")
                    return True
                else:
                    print(f"✗ FAILURE: AC is {ac}, expected {expected}")
                    print("\nBreakdown:")
                    print("  - Breastplate: AC 14 (medium armor)")
                    print("  - DEX modifier: +0 (DEX 10)")
                    print("  - Shield +1: +3 (base 2 + magical 1)")
                    print(f"  - Expected total: 14 + 0 + 3 = 17")
                    print(f"  - Actual total: {ac}")
                    return False


if __name__ == "__main__":
    success = test_calculate_armor_class_with_breastplate_and_shield()
    exit(0 if success else 1)
