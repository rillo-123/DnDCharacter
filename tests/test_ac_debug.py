"""
Diagnostic test to check actual inventory armor AC calculations.

This test reads from localStorage (if running in browser) or 
tests the actual data structure.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest
from managers import ArmorEntity


def test_armor_type_detection():
    """Test that armor_type field is properly recognized."""
    
    # Test case 1: With armor_type in direct field
    armor1 = {
        "id": "1",
        "name": "Breastplate",
        "armor_class": 14,
        "armor_type": "Medium Armor",  # Direct field
        "category": "Armor",
        "equipped": True,
        "notes": json.dumps({"armor_class": 15, "bonus": 1})
    }
    
    entity1 = ArmorEntity(armor1, {"dex": 10})
    ac1 = entity1._calculate_ac()
    
    print(f"\nCase 1 (armor_type in direct field):")
    print(f"  armor_type: '{entity1.final_armor_type}'")
    print(f"  AC calculated: {ac1}")
    print(f"  Expected: 15 (from notes)")
    
    assert ac1 == 15
    
    # Test case 2: Without armor_type (missing field)
    armor2 = {
        "id": "2",
        "name": "Breastplate",
        "armor_class": 14,
        # NO armor_type field!
        "category": "Armor",
        "equipped": True,
        "notes": json.dumps({"armor_class": 15, "bonus": 1})
    }
    
    entity2 = ArmorEntity(armor2, {"dex": 10})
    ac2 = entity2._calculate_ac()
    
    print(f"\nCase 2 (NO armor_type field):")
    print(f"  armor_type: '{entity2.final_armor_type}'")
    print(f"  AC calculated: {ac2}")
    print(f"  Expected: 15 (from notes, no DEX applied)")
    
    # Without armor_type, DEX won't be added because the condition:
    # add_dex = "light" in armor_type or "medium" in armor_type
    # will be False when armor_type is empty string or "—"
    
    # Test case 3: With armor_type in notes (nested)
    armor3 = {
        "id": "3",
        "name": "Breastplate",
        "armor_class": 14,
        # NO armor_type in direct field
        "category": "Armor",
        "equipped": True,
        "notes": json.dumps({
            "armor_class": 15, 
            "bonus": 1,
            "armor_type": "Medium Armor"  # In notes
        })
    }
    
    entity3 = ArmorEntity(armor3, {"dex": 10})
    
    # Note: The current implementation doesn't check notes for armor_type
    # It only checks direct field, which will be missing here
    print(f"\nCase 3 (armor_type in notes, not direct field):")
    print(f"  armor_type: '{entity3.final_armor_type}'")
    print(f"  Expected: '—' (not found in direct field)")


def test_zero_ac_issue():
    """Test if armor with AC 0 or negative would show as '—'."""
    
    armor = {
        "id": "1",
        "name": "Bad Armor",
        "armor_class": 0,  # Zero or missing
        "armor_type": "Medium Armor",
        "category": "Armor",
        "equipped": True,
        "notes": ""
    }
    
    entity = ArmorEntity(armor, {"dex": 10})
    final_ac = entity.final_ac  # This is the property that returns "—"
    
    print(f"\nZero AC test:")
    print(f"  AC calculated: {entity._calculate_ac()}")
    print(f"  final_ac property: '{final_ac}'")
    print(f"  Expected: '—' (dashes)")
    
    assert final_ac == "—"


def test_ac_11_reverse_engineering():
    """Work backwards: what would give AC 11?"""
    
    scenarios = [
        {
            "name": "Leather (11) + DEX 10",
            "armor_class": 11,
            "armor_type": "Light Armor",
            "notes": "",
            "dex": 10
        },
        {
            "name": "Plate (18) - DEX 7 penalty",
            "armor_class": 18,
            "armor_type": "Heavy Armor",
            "notes": "",
            "dex": 7  # This shouldn't matter for heavy armor
        },
        {
            "name": "Medium (14) - DEX 3 (mod -3)",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "notes": "",
            "dex": 4  # DEX 4 = -3 modifier, but DEX isn't subtracted from non-light/medium
        },
        {
            "name": "Light (10) + DEX 12 (mod +1)",
            "armor_class": 10,
            "armor_type": "Light Armor",
            "notes": "",
            "dex": 12
        },
    ]
    
    print(f"\nReverse engineering AC 11:")
    for scenario in scenarios:
        armor = {
            "id": "1",
            "name": scenario["name"],
            "armor_class": scenario["armor_class"],
            "armor_type": scenario["armor_type"],
            "category": "Armor",
            "equipped": True,
            "notes": scenario["notes"]
        }
        
        entity = ArmorEntity(armor, {"dex": scenario["dex"]})
        ac = entity._calculate_ac()
        
        print(f"  {scenario['name']}: AC = {ac}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
