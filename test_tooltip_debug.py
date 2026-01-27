"""
Test to diagnose the tooltip showing wrong values.
Tests the case where tooltip might show "armor 15 dex +0 shield +1" but total is 14.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from armor_manager import ArmorEntity


def test_breastplate_with_bonus_in_notes():
    """Test if Breastplate has bonus incorrectly stored in armor_class."""
    
    # Scenario 1: Correct format - Breastplate +1 with AC 15 in notes
    print("\n=== Scenario 1: Breastplate +1 (AC 15 in notes) ===")
    armor_data_correct = {
        "id": "1",
        "name": "Breastplate +1",
        "category": "Armor",
        "equipped": True,
        "notes": '{"armor_class": "15", "armor_type": "medium"}'
    }
    
    armor = ArmorEntity(armor_data_correct, {"dex": 10})
    ac = armor._calculate_ac()
    print(f"Armor AC (from notes): 15")
    print(f"Calculated AC: {ac} (should be 15 for medium armor with DEX 10)")
    
    # Scenario 2: Incorrect format - Breastplate with AC 14 AND bonus 1 stored
    print("\n=== Scenario 2: Breastplate with AC 14 + bonus 1 (WRONG) ===")
    armor_data_wrong = {
        "id": "2",
        "name": "Breastplate",
        "category": "Armor",
        "equipped": True,
        "notes": '{"armor_class": "14", "bonus": 1, "armor_type": "medium"}'
    }
    
    armor2 = ArmorEntity(armor_data_wrong, {"dex": 10})
    ac2 = armor2._calculate_ac()
    print(f"Armor AC (from notes): 14")
    print(f"Bonus in notes: 1 (SHOULD NOT BE HERE FOR ARMOR)")
    print(f"Calculated AC: {ac2} (should be 14, bonus is ignored for armor)")
    
    # Scenario 3: Base Breastplate
    print("\n=== Scenario 3: Base Breastplate (AC 14) ===")
    armor_data_base = {
        "id": "3",
        "name": "Breastplate",
        "category": "Armor",
        "equipped": True,
        "notes": '{"armor_class": "14", "armor_type": "medium"}'
    }
    
    armor3 = ArmorEntity(armor_data_base, {"dex": 10})
    ac3 = armor3._calculate_ac()
    print(f"Armor AC (from notes): 14")
    print(f"Calculated AC: {ac3} (should be 14)")
    
    # Shield testing
    print("\n=== Shield Bonus Testing ===")
    shield_data = {
        "id": "4",
        "name": "Shield",
        "category": "Armor",
        "equipped": True,
        "notes": '{"bonus": 3, "armor_type": "Shield"}'
    }
    
    shield = ArmorEntity(shield_data, {"dex": 10})
    shield_notes = json.loads(shield.entity.get("notes", "{}"))
    shield_bonus = shield_notes.get("bonus", 2)
    print(f"Shield bonus (from notes): {shield_bonus}")
    print(f"Expected: 3 (base 2 + magical 1)")
    
    # Final calculation
    print("\n=== Final AC Calculation ===")
    print(f"Breastplate +1: AC {ac} (from scenario 1)")
    print(f"Shield +1: +{shield_bonus}")
    print(f"Total AC: {ac} + {shield_bonus} = {ac + shield_bonus}")
    print(f"Expected: 15 + 3 = 18")
    
    if ac + shield_bonus == 18:
        print("✓ CORRECT")
    else:
        print(f"✗ WRONG - got {ac + shield_bonus}, expected 18")


if __name__ == "__main__":
    test_breastplate_with_bonus_in_notes()
