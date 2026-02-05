"""
Integration test: Full weapon rendering pipeline for light crossbow
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

# Import the actual functions from character.py
from character import _extract_weapon_properties, _calculate_weapon_to_hit, ability_modifier


def test_full_light_crossbow_rendering_pipeline():
    """
    Test the EXACT sequence that happens in render_weapons_grid():
    1. Load weapon from inventory
    2. Extract properties
    3. Calculate to-hit
    4. Verify the result
    """
    
    print("\n" + "="*70)
    print("FULL LIGHT CROSSBOW RENDERING PIPELINE TEST")
    print("="*70)
    
    # STEP 1: Weapon data as loaded from character JSON (from inventory)
    print("\nSTEP 1: Load weapon from inventory")
    weapon = {
        "id": "1770326109281000_948991",
        "name": "Light Crossbow",
        "cost": "25 gp",
        "weight": "varies",
        "qty": 1,
        "category": "Weapons",
        "notes": '{"damage": "1d8", "damage_type": "piercing", "range": "80/320", "properties": "ammunition, loading, two-handed"}',
        "source": "open5e",
        "equipped": True
    }
    print(f"  Weapon: {weapon['name']}")
    print(f"  Notes JSON: {weapon['notes']}")
    
    # STEP 2: Extract weapon properties (exactly as in render_weapons_grid line 1845)
    print("\nSTEP 2: Extract weapon properties")
    weapon_bonus, weapon_damage, weapon_damage_type, weapon_range, weapon_properties_str, is_ranged = _extract_weapon_properties(weapon)
    
    print(f"  weapon_bonus: {weapon_bonus}")
    print(f"  weapon_damage: {weapon_damage}")
    print(f"  weapon_damage_type: {weapon_damage_type}")
    print(f"  weapon_range: {weapon_range}")
    print(f"  weapon_properties_str: '{weapon_properties_str}'")
    print(f"  is_ranged: {is_ranged} ← KEY VALUE!")
    
    # STEP 3: Get weapon_properties_list (exactly as in render_weapons_grid line 1848)  
    print("\nSTEP 3: Get weapon_properties_list from weapon dict")
    weapon_properties_list = weapon.get("properties", []) if isinstance(weapon.get("properties", []), list) else []
    print(f"  weapon_properties_list: {weapon_properties_list} (empty, properties are in JSON)")
    
    # STEP 4: Get character stats (simulating Enwer)
    print("\nSTEP 4: Get character stats")
    scores = {"dex": 10, "str": 16, "con": 14, "int": 10, "wis": 13, "cha": 8}
    race_bonuses = {"dex": 0, "str": 0}
    proficiency = 3
    
    dex_mod = ability_modifier(scores["dex"] + race_bonuses.get("dex", 0))
    str_mod = ability_modifier(scores["str"] + race_bonuses.get("str", 0))
    
    print(f"  DEX: {scores['dex']} → modifier: {dex_mod}")
    print(f"  STR: {scores['str']} → modifier: {str_mod}")
    print(f"  Proficiency: +{proficiency}")
    
    # STEP 5: Calculate to-hit (exactly as in render_weapons_grid line 1862)
    print("\nSTEP 5: Calculate to-hit")
    to_hit = _calculate_weapon_to_hit(weapon_bonus, is_ranged, weapon_properties_str, weapon_properties_list, scores, race_bonuses, proficiency)
    
    print(f"  is_ranged: {is_ranged}")
    if is_ranged:
        print(f"  → Using DEX modifier: {dex_mod}")
        print(f"  Formula: DEX mod ({dex_mod}) + proficiency ({proficiency}) + weapon bonus ({weapon_bonus})")
    else:
        print(f"  → Using STR modifier: {str_mod}")
        print(f"  Formula: STR mod ({str_mod}) + proficiency ({proficiency}) + weapon bonus ({weapon_bonus})")
    
    print(f"\n  RESULT: to_hit = {to_hit}")
    
    # STEP 6: Verify the result
    print("\nSTEP 6: Verify result")
    expected = 3  # 0 (DEX) + 3 (proficiency) = 3
    if to_hit == 3:
        print(f"  ✓ CORRECT! to_hit={to_hit} (0 + 3)")
        print(f"  The light crossbow will show a to-hit of +{to_hit}")
    elif to_hit == 6:
        print(f"  ✗ WRONG! to_hit={to_hit} (should be 3)")
        print(f"  This indicates the weapon is NOT being recognized as ranged")
        print(f"  Expected: DEX (0) + Prof (3) = 3")
        print(f"  Got: STR (+3) + Prof (3) = 6")
    else:
        print(f"  ✗ UNEXPECTED! to_hit={to_hit}")
    
    assert to_hit == expected, f"Expected {expected}, got {to_hit}"
    
    print("\n" + "="*70)
    print("✓ PIPELINE TEST PASSED - Light crossbow will display correctly!")
    print("="*70)
    return to_hit


if __name__ == "__main__":
    result = test_full_light_crossbow_rendering_pipeline()
    print(f"\nFinal result: Light Crossbow will show to-hit of +{result}")
