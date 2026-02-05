"""
Unit tests for weapon to-hit calculation.
Tests the _calculate_weapon_to_hit function with various weapon types and ability scores.
"""

import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from character import _calculate_weapon_to_hit, _extract_weapon_properties, ability_modifier


def test_rapier_finesse_with_high_dex():
    """Test rapier (finesse) uses DEX when DEX > STR."""
    weapon_bonus = 0
    is_ranged = False
    weapon_properties_str = "finesse, light"
    weapon_properties_list = ["finesse", "light"]
    scores = {"dex": 17, "str": 8, "con": 10, "int": 12, "wis": 14, "cha": 13}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 4
    
    to_hit = _calculate_weapon_to_hit(
        weapon_bonus, is_ranged, weapon_properties_str, 
        weapon_properties_list, scores, race_bonuses, proficiency
    )
    
    # Should be: DEX mod (+3) + proficiency (+4) = +7
    expected = 7
    assert to_hit == expected, f"Expected {expected}, got {to_hit}. DEX=17 (+3), STR=8 (-1), Prof=4"


def test_rapier_finesse_with_high_str():
    """Test rapier (finesse) uses STR when STR > DEX."""
    weapon_bonus = 0
    is_ranged = False
    weapon_properties_str = "finesse, light"
    weapon_properties_list = ["finesse", "light"]
    scores = {"dex": 10, "str": 17, "con": 10, "int": 12, "wis": 14, "cha": 13}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 4
    
    to_hit = _calculate_weapon_to_hit(
        weapon_bonus, is_ranged, weapon_properties_str, 
        weapon_properties_list, scores, race_bonuses, proficiency
    )
    
    # Should be: STR mod (+3) + proficiency (+4) = +7
    expected = 7
    assert to_hit == expected, f"Expected {expected}, got {to_hit}. STR=17 (+3), DEX=10 (0), Prof=4"


def test_longsword_no_finesse_uses_str():
    """Test longsword (no finesse) uses STR."""
    weapon_bonus = 0
    is_ranged = False
    weapon_properties_str = "versatile"
    weapon_properties_list = ["versatile"]
    scores = {"dex": 17, "str": 14, "con": 10, "int": 12, "wis": 14, "cha": 13}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 4
    
    to_hit = _calculate_weapon_to_hit(
        weapon_bonus, is_ranged, weapon_properties_str, 
        weapon_properties_list, scores, race_bonuses, proficiency
    )
    
    # Should be: STR mod (+2) + proficiency (+4) = +6 (NOT DEX even though higher)
    expected = 6
    assert to_hit == expected, f"Expected {expected}, got {to_hit}. STR=14 (+2), DEX=17 (+3), Prof=4"


def test_shortbow_ranged_uses_dex():
    """Test ranged weapon uses DEX."""
    weapon_bonus = 0
    is_ranged = True  # Ranged weapon
    weapon_properties_str = "ammunition, light"
    weapon_properties_list = ["ammunition", "light"]
    scores = {"dex": 17, "str": 8, "con": 10, "int": 12, "wis": 14, "cha": 13}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 4
    
    to_hit = _calculate_weapon_to_hit(
        weapon_bonus, is_ranged, weapon_properties_str, 
        weapon_properties_list, scores, race_bonuses, proficiency
    )
    
    # Should be: DEX mod (+3) + proficiency (+4) = +7
    expected = 7
    assert to_hit == expected, f"Expected {expected}, got {to_hit}. DEX=17 (+3), Prof=4, is_ranged=True"


def test_light_crossbow_ranged_string_properties():
    """Test light crossbow with properties as comma-separated string (not list).
    
    This tests the actual case from Enwer's inventory where properties 
    are stored as "ammunition, loading, two-handed" (string) not a list.
    """
    weapon_bonus = 0
    is_ranged = True  # Light crossbow is ranged
    weapon_properties_str = "ammunition, loading, two-handed"  # String, not list!
    weapon_properties_list = []  # Empty list - properties are in string format
    # Enwer's stats: DEX 10, STR 16
    scores = {"dex": 10, "str": 16, "con": 14, "int": 10, "wis": 13, "cha": 8}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 3  # Level 8 cleric
    
    to_hit = _calculate_weapon_to_hit(
        weapon_bonus, is_ranged, weapon_properties_str, 
        weapon_properties_list, scores, race_bonuses, proficiency
    )
    
    # Should be: DEX mod (0) + proficiency (3) = 3 (NOT STR!)
    # If it's returning 6, that means it's using STR mod (+3) instead of DEX
    expected = 3
    assert to_hit == expected, f"Expected {expected}, got {to_hit}. DEX=10 (0), STR=16 (+3), Prof=3, is_ranged=True"


def test_extract_light_crossbow_properties():
    """Test that _extract_weapon_properties correctly identifies light crossbow as ranged.
    
    This validates that weapons with properties stored as strings in notes JSON
    are properly detected as ranged weapons.
    """
    # Light crossbow data as it's stored in Enwer's inventory
    light_crossbow = {
        "name": "Light Crossbow",
        "category": "Weapons",
        "notes": json.dumps({
            "damage": "1d8",
            "damage_type": "piercing",
            "range": "80/320",
            "properties": "ammunition, loading, two-handed"
        })
    }
    
    # Extract properties
    bonus, damage, damage_type, weapon_range, properties_str, is_ranged = _extract_weapon_properties(light_crossbow)
    
    # Verify all extractions
    assert bonus == 0, f"Expected bonus 0, got {bonus}"
    assert damage == "1d8", f"Expected damage '1d8', got {damage}"
    assert damage_type == "piercing", f"Expected damage_type 'piercing', got {damage_type}"
    assert weapon_range == "80/320", f"Expected range '80/320', got {weapon_range}"
    assert properties_str == "ammunition, loading, two-handed", f"Expected properties string with 'ammunition', got '{properties_str}'"
    assert is_ranged == True, f"Light crossbow should be detected as ranged! Got is_ranged={is_ranged}"


def test_weapon_with_bonus():
    """Test weapon with magical bonus."""
    weapon_bonus = 2
    is_ranged = False
    weapon_properties_str = "finesse"
    weapon_properties_list = ["finesse"]
    scores = {"dex": 17, "str": 8, "con": 10, "int": 12, "wis": 14, "cha": 13}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 4
    
    to_hit = _calculate_weapon_to_hit(
        weapon_bonus, is_ranged, weapon_properties_str, 
        weapon_properties_list, scores, race_bonuses, proficiency
    )
    
    # Should be: DEX mod (+3) + proficiency (+4) + weapon bonus (+2) = +9
    expected = 9
    assert to_hit == expected, f"Expected {expected}, got {to_hit}"


def test_ability_modifier():
    """Test ability modifier calculation."""
    assert ability_modifier(17) == 3, "DEX 17 should give +3"
    assert ability_modifier(8) == -1, "STR 8 should give -1"
    assert ability_modifier(10) == 0, "CON 10 should give 0"
    assert ability_modifier(20) == 5, "WIS 20 should give +5"


if __name__ == "__main__":
    test_ability_modifier()
    print("✓ ability_modifier tests passed")
    
    test_rapier_finesse_with_high_dex()
    print("✓ rapier with high DEX test passed")
    
    test_rapier_finesse_with_high_str()
    print("✓ rapier with high STR test passed")
    
    test_longsword_no_finesse_uses_str()
    print("✓ longsword no-finesse test passed")
    
    test_shortbow_ranged_uses_dex()
    print("✓ shortbow ranged test passed")
    
    test_weapon_with_bonus()
    print("✓ weapon with bonus test passed")
    
    test_light_crossbow_ranged_string_properties()
    print("✓ light crossbow to-hit calculation test passed")
    
    test_extract_light_crossbow_properties()
    print("✓ extract light crossbow properties test passed")
    
    print("\nAll weapon to-hit tests passed!")
