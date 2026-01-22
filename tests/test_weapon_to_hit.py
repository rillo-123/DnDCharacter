"""
Unit tests for weapon to-hit calculation.
Tests the _calculate_weapon_to_hit function with various weapon types and ability scores.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from character import _calculate_weapon_to_hit, ability_modifier


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
    
    print("\nAll weapon to-hit tests passed!")
