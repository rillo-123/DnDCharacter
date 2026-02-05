"""
Diagnostic test: Check if weapons are being properly loaded and enriched
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

from character import (
    _enrich_weapon_item, 
    _determine_weapon_ability,
    _parse_weapon_notes,
    ability_modifier
)


def test_weapon_loading():
    """Load and test weapon enrichment"""
    
    # Load the actual character export
    exports_dir = Path(__file__).parent.parent / "exports"
    json_files = sorted(exports_dir.glob("Enwer_Cleric*.json"))
    
    if not json_files:
        print("No Enwer character files found!")
        return False
    
    latest_char_file = json_files[-1]
    print(f"Loading: {latest_char_file.name}\n")
    
    with open(latest_char_file, 'r') as f:
        character_data = json.load(f)
    
    # Get weapons
    inventory = character_data.get("inventory", {})
    items = inventory.get("items", [])
    
    print(f"Total items in inventory: {len(items)}")
    print(f"Equipped items: {sum(1 for i in items if i.get('equipped'))}\n")
    
    # Find light crossbow
    light_crossbow = None
    for item in items:
        if "Light Crossbow" in item.get("name", ""):
            light_crossbow = item
            break
    
    if not light_crossbow:
        print("✗ Light Crossbow NOT FOUND in inventory!")
        # List all equipped weapons
        print("\nEquipped weapons:")
        for item in items:
            if item.get("equipped") and item.get("category") == "Weapons":
                print(f"  - {item.get('name')}")
        return False
    
    print(f"✓ Found Light Crossbow")
    print(f"\nRaw item data:")
    print(json.dumps(light_crossbow, indent=2))
    
    # Test weapon enrichment
    print(f"\n--- Testing Weapon Enrichment ---")
    enriched = _enrich_weapon_item(light_crossbow)
    print(f"Enriched keys: {list(enriched.keys())}")
    print(f"\nEnriched data relevant to weapon calc:")
    for key in ['damage', 'damage_type', 'range', 'range_text', 'properties', 'weapon_properties', 'bonus']:
        val = enriched.get(key)
        if val is not None:
            print(f"  {key}: {val}")
    
    # Test ability determination
    print(f"\n--- Testing Ability Determination ---")
    ability_key = _determine_weapon_ability(light_crossbow, enriched)
    print(f"Determined ability: {ability_key} ('dex' is correct for ranged)")
    
    if ability_key == "dex":
        print("✓ Ability determination is CORRECT")
    else:
        print(f"✗ Ability determination is WRONG (should be 'dex', got '{ability_key}')")
    
    # Test properties parsing
    print(f"\n--- Testing Notes Parsing ---")
    notes_str = light_crossbow.get("notes", "")
    print(f"Notes JSON string: {notes_str}")
    
    parsed = _parse_weapon_notes(notes_str)
    print(f"\nParsed from notes:")
    for key, val in parsed.items():
        print(f"  {key}: {val}")
    
    # Test with DOM values (simulated)
    print(f"\n--- Simulating Browser Rendering ---")
    dex_score = character_data.get("scores", {}).get("dex", 10)
    str_score = character_data.get("scores", {}).get("str", 10)
    level = character_data.get("level", 1)
    proficiency = (level + 7) // 4
    
    dex_mod = ability_modifier(dex_score)
    str_mod = ability_modifier(str_score)
    
    print(f"Character scores:")
    print(f"  DEX: {dex_score} ({dex_mod:+d})")
    print(f"  STR: {str_score} ({str_mod:+d})")
    print(f"  Level: {level}, Proficiency: +{proficiency}")
    
    weapon_bonus = enriched.get("bonus", 0) or 0
    
    # What SHOULD happen
    if ability_key == "dex":
        expected_to_hit = dex_mod + proficiency + weapon_bonus
        print(f"\nShould use DEX:")
        print(f"  {dex_mod:+d} (DEX) + {proficiency} (prof) + {weapon_bonus} (bonus) = {expected_to_hit}")
    else:
        expected_to_hit = str_mod + proficiency + weapon_bonus
        print(f"\nShould use STR:")
        print(f"  {str_mod:+d} (STR) + {proficiency} (prof) + {weapon_bonus} (bonus) = {expected_to_hit}")
    
    print(f"\nExpected to-hit: {expected_to_hit:+d}")
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("WEAPON LOADING AND ENRICHMENT DIAGNOSTICS")
    print("=" * 70)
    print()
    
    test_weapon_loading()
    
    print("\n" + "=" * 70)
