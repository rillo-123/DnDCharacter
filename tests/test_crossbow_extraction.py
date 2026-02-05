"""
Test that verifies light crossbow property extraction from character data.
This tests the actual scenario where a weapon is loaded from character export.
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from character import _extract_weapon_properties, _calculate_weapon_to_hit, ability_modifier


def test_extract_crossbow_from_character_data():
    """Test extracting light crossbow properties as loaded from character export."""
    
    # This is the exact data structure from Enwer's character export
    light_crossbow_from_export = {
        "id": "1770326109281000_948991",
        "name": "Light Crossbow",
        "cost": "25 gp",
        "weight": "varies",
        "qty": 1,
        "category": "Weapons",
        "notes": "{\"damage\": \"1d8\", \"damage_type\": \"piercing\", \"range\": \"80/320\", \"properties\": \"ammunition, loading, two-handed\"}",
        "source": "open5e",
        "equipped": True
    }
    
    # Extract properties
    bonus, damage, damage_type, weapon_range, properties_str, is_ranged = _extract_weapon_properties(light_crossbow_from_export)
    
    # Verify extraction
    print(f"Extracted from character data:")
    print(f"  bonus: {bonus}")
    print(f"  damage: {damage}")
    print(f"  damage_type: {damage_type}")
    print(f"  weapon_range: {weapon_range}")
    print(f"  properties_str: {properties_str}")
    print(f"  is_ranged: {is_ranged}")
    
    assert bonus == 0, f"Expected bonus 0, got {bonus}"
    assert damage == "1d8", f"Expected damage '1d8', got {damage}"
    assert damage_type == "piercing", f"Expected damage_type 'piercing', got {damage_type}"
    assert weapon_range == "80/320", f"Expected range '80/320', got {weapon_range}"
    assert properties_str == "ammunition, loading, two-handed", f"Expected properties 'ammunition, loading, two-handed', got '{properties_str}'"
    assert is_ranged == True, f"Light crossbow MUST be detected as ranged! Got is_ranged={is_ranged}"
    
    print("\n✓ Light crossbow was correctly detected as ranged!")


def test_crossbow_to_hit_with_extracted_data():
    """Test full to-hit calculation with extracted light crossbow data."""
    
    # Weapon data extracted from character export
    light_crossbow = {
        "id": "1770326109281000_948991",
        "name": "Light Crossbow",
        "cost": "25 gp",
        "weight": "varies",
        "qty": 1,
        "category": "Weapons", 
        "notes": "{\"damage\": \"1d8\", \"damage_type\": \"piercing\", \"range\": \"80/320\", \"properties\": \"ammunition, loading, two-handed\"}",
        "source": "open5e",
        "equipped": True
    }
    
    # Extract weapon properties
    weapon_bonus, weapon_damage, weapon_damage_type, weapon_range, weapon_properties_str, is_ranged = _extract_weapon_properties(light_crossbow)
    
    # Get weapon_properties_list as done in render_weapons_grid
    weapon_properties_list = light_crossbow.get("properties", []) if isinstance(light_crossbow.get("properties", []), list) else []
    
    # Enwer's stats
    scores = {"dex": 10, "str": 16, "con": 14, "int": 10, "wis": 13, "cha": 8}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 3  # Level 8 cleric
    
    # Calculate to-hit
    to_hit = _calculate_weapon_to_hit(weapon_bonus, is_ranged, weapon_properties_str, weapon_properties_list, scores, race_bonuses, proficiency)
    
    print(f"\nFull to-hit calculation:")
    print(f"  is_ranged: {is_ranged}")
    print(f"  weapon_properties_str: '{weapon_properties_str}'")
    print(f"  weapon_properties_list: {weapon_properties_list}")
    print(f"  DEX: 10 (mod 0)")
    print(f"  STR: 16 (mod +3)")
    print(f"  Proficiency: {proficiency}")
    print(f"  Expected to-hit: 0 + 3 = 3")
    print(f"  Actual to-hit: {to_hit}")
    
    # Should be: DEX mod (0) + proficiency (3) = 3
    expected = 3
    if to_hit != expected:
        print(f"\n✗ MISMATCH! Expected {expected}, got {to_hit}")
        print(f"  This suggests is_ranged={is_ranged} but to-hit calculated as STR-based")
        if to_hit == 6:
            print(f"  to_hit=6 indicates: STR mod (+3) + proficiency (3) = 6")
            print(f"  This proves is_ranged is being ignored or set to False!")
    else:
        print(f"\n✓ To-hit calculation is CORRECT!")
    
    assert to_hit == expected, f"Expected {expected}, got {to_hit}. is_ranged={is_ranged}"


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Light Crossbow Property Extraction")
    print("=" * 60)
    
    test_extract_crossbow_from_character_data()
    test_crossbow_to_hit_with_extracted_data()
    
    print("\n" + "=" * 60)
    print("All crossbow extraction tests passed!")
    print("=" * 60)
