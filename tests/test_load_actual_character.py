"""
Test that loads the actual character export and checks light crossbow data
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from character import _extract_weapon_properties, _calculate_weapon_to_hit, ability_modifier


def test_load_actual_character():
    """Load the actual character export and check light crossbow data."""
    
    # Find the most recent character export
    exports_dir = Path(__file__).parent.parent / "exports"
    json_files = sorted(exports_dir.glob("Enwer_Cleric*.json"))
    
    if not json_files:
        print("No Enwer character files found!")
        return False
    
    latest_char_file = json_files[-1]
    print(f"Loading: {latest_char_file.name}")
    
    with open(latest_char_file, 'r') as f:
        character_data = json.load(f)
    
    # Find the light crossbow in the inventory
    light_crossbow = None
    for item in character_data.get("inventory", {}).get("items", []):
        if "Light Crossbow" in item.get("name", ""):
            light_crossbow = item
            break
    
    if not light_crossbow:
        print("Light Crossbow not found in inventory!")
        return False
    
    print(f"\nLight Crossbow data from character export:")
    print(json.dumps(light_crossbow, indent=2))
    
    # Get character's ability scores
    scores = {
        "dex": character_data.get("scores", {}).get("dex", 10),
        "str": character_data.get("scores", {}).get("str", 10),
        "con": character_data.get("scores", {}).get("con", 10),
        "int": character_data.get("scores", {}).get("int", 10),
        "wis": character_data.get("scores", {}).get("wis", 10),
        "cha": character_data.get("scores", {}).get("cha", 10),
    }
    
    level = character_data.get("level", 1)
    proficiency = (level + 7) // 4  # Calculate proficiency bonus
    race_bonuses = {
        "dex": 0, "str": 0, "con": 0, "int": 0, "wis": 0, "cha": 0  # Assuming no racial bonuses for now
    }
    
    print(f"\nCharacter stats:")
    print(f"  Level: {level}")
    print(f"  Proficiency: +{proficiency}")
    print(f"  DEX: {scores['dex']}")
    print(f"  STR: {scores['str']}")
    
    # Extract weapon properties from the actual character data
    print(f"\nExtracting light crossbow properties...")
    weapon_bonus, weapon_damage, weapon_damage_type, weapon_range, weapon_properties_str, is_ranged = _extract_weapon_properties(light_crossbow)
    
    print(f"  weapon_bonus: {weapon_bonus}")
    print(f"  weapon_damage: {weapon_damage}")
    print(f"  weapon_damage_type: {weapon_damage_type}")
    print(f"  weapon_range: {weapon_range}")
    print(f"  weapon_properties_str: '{weapon_properties_str}'")
    print(f"  is_ranged: {is_ranged}")
    
    # Calculate to-hit
    weapon_properties_list = light_crossbow.get("properties", []) if isinstance(light_crossbow.get("properties", []), list) else []
    to_hit = _calculate_weapon_to_hit(weapon_bonus, is_ranged, weapon_properties_str, weapon_properties_list, scores, race_bonuses, proficiency)
    
    dex_mod = ability_modifier(scores["dex"])
    str_mod = ability_modifier(scores["str"])
    
    print(f"\nCalculating to-hit:")
    print(f"  is_ranged: {is_ranged}")
    print(f"  DEX mod: {dex_mod}")
    print(f"  STR mod: {str_mod}")
    print(f"  Proficiency: +{proficiency}")
    print(f"  Weapon bonus: {weapon_bonus}")
    
    if is_ranged:
        expected_to_hit = dex_mod + proficiency + weapon_bonus
        print(f"  Using DEX: {dex_mod} + {proficiency} = {expected_to_hit}")
    else:
        expected_to_hit = str_mod + proficiency + weapon_bonus
        print(f"  Using STR: {str_mod} + {proficiency} = {expected_to_hit}")
    
    print(f"\n  Calculated to_hit: {to_hit}")
    print(f"  Expected to_hit: {expected_to_hit}")
    
    if to_hit == expected_to_hit:
        print(f"  ✓ Match!")
    else:
        print(f"  ✗ Mismatch! Calculation doesn't match expected!")
    
    return is_ranged


if __name__ == "__main__":
    is_ranged = test_load_actual_character()
    if is_ranged:
        print("\n✓ Light crossbow is correctly identified as RANGED")
    else:
        print("\n✗ Light crossbow is NOT identified as ranged!")
