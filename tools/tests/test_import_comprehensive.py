#!/usr/bin/env python3
"""
Comprehensive import test - validates the import flow works correctly.
Run this AFTER making changes to verify nothing broke.
"""

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]

    # Add assets/py to path
    sys.path.insert(0, str(root / "assets" / "py"))

    from character_models import CharacterFactory
    from spellcasting import SpellcastingManager, SPELL_LIBRARY_STATE, set_spell_library_data
    from spell_data import LOCAL_SPELLS_FALLBACK

    print("=" * 80)
    print("COMPREHENSIVE IMPORT COMPATIBILITY TEST")
    print("=" * 80)

    # Initialize like the browser does
    set_spell_library_data(LOCAL_SPELLS_FALLBACK)
    SPELL_LIBRARY_STATE["loaded"] = True

    # Test 1: Load the export file
    print("\n[TEST 1] Loading export file...")
    export_file = root / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json"
    try:
        with open(export_file, encoding="utf-8") as f:
            data = json.load(f)
        print(f"  PASS - Loaded {export_file.name}")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    # Test 2: CharacterFactory.from_dict()
    print("\n[TEST 2] Creating character via CharacterFactory.from_dict()...")
    try:
        character = CharacterFactory.from_dict(data)
        assert character.name == "Enwer", f"Expected name 'Enwer', got '{character.name}'"
        assert character.class_text == "Cleric", f"Expected class 'Cleric', got '{character.class_text}'"
        assert character.domain == "Life", f"Expected domain 'Life', got '{character.domain}'"
        print(f"  PASS - Character: {character.name} ({character.class_text}), Domain: {character.domain}")
    except Exception as e:
        print(f"  FAIL - {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 3: to_dict() round-trip
    print("\n[TEST 3] Converting back to dict via to_dict()...")
    try:
        normalized = character.to_dict()
        assert isinstance(normalized, dict), f"Expected dict, got {type(normalized)}"
        assert "identity" in normalized, "Missing 'identity' key"
        assert "level" in normalized, "Missing 'level' key"
        assert "abilities" in normalized, "Missing 'abilities' key"
        assert "spellcasting" in normalized, "Missing 'spellcasting' key"
        print(f"  PASS - All required keys present in normalized dict")
    except Exception as e:
        print(f"  FAIL - {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 4: Identity fields
    print("\n[TEST 4] Validating identity fields...")
    try:
        identity = normalized["identity"]
        required = ["name", "class", "race", "background", "alignment", "player_name", "domain", "subclass"]
        missing = [k for k in required if k not in identity]
        if missing:
            raise ValueError(f"Missing identity fields: {missing}")
        print(f"  PASS - All identity fields present")
        print(f"    - Name: {identity['name']}")
        print(f"    - Class: {identity['class']}")
        print(f"    - Race: {identity['race']}")
        print(f"    - Domain: {identity['domain']}")
        print(f"    - Subclass: {identity['subclass']}")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    # Test 5: Spellcasting data
    print("\n[TEST 5] Validating spellcasting data...")
    try:
        spellcasting = normalized["spellcasting"]
        prepared = spellcasting.get("prepared", [])
        slots = spellcasting.get("slots_used", {})
        assert len(prepared) > 0, "No prepared spells found"
        assert isinstance(slots, dict), "slots_used should be a dict"
        print(f"  PASS - Spellcasting valid")
        print(f"    - Prepared spells: {len(prepared)}")
        print(f"    - Sample spell: {prepared[0].get('name')} (slug: {prepared[0].get('slug')})")
        print(f"    - Spell slots: {slots}")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    # Test 6: Abilities
    print("\n[TEST 6] Validating abilities...")
    try:
        abilities = normalized["abilities"]
        required_abilities = ["str", "dex", "con", "int", "wis", "cha"]
        missing = [a for a in required_abilities if a not in abilities]
        if missing:
            raise ValueError(f"Missing abilities: {missing}")
        print(f"  PASS - All abilities present")
        for ability in required_abilities:
            ab = abilities[ability]
            print(f"    - {ability}: {ab.get('score')} (save proficient: {ab.get('save_proficient')})")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    # Test 7: Combat
    print("\n[TEST 7] Validating combat data...")
    try:
        combat = normalized["combat"]
        required = ["armor_class", "speed", "max_hp", "current_hp", "temp_hp"]
        missing = [k for k in required if k not in combat]
        if missing:
            raise ValueError(f"Missing combat fields: {missing}")
        print(f"  PASS - All combat fields present")
        print(f"    - AC: {combat['armor_class']}")
        print(f"    - Speed: {combat['speed']}")
        print(f"    - HP: {combat['current_hp']}/{combat['max_hp']}")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    # Test 8: Skills
    print("\n[TEST 8] Validating skills...")
    try:
        skills = normalized.get("skills", {})
        if not skills:
            raise ValueError("No skills found")
        assert "acrobatics" in skills, "Missing 'acrobatics' skill"
        assert "stealth" in skills, "Missing 'stealth' skill"
        print(f"  PASS - {len(skills)} skills present")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    # Test 9: Inventory
    print("\n[TEST 9] Validating inventory...")
    try:
        inventory = normalized.get("inventory", {})
        items = inventory.get("items", [])
        currency = inventory.get("currency", {})
        print(f"  PASS - Inventory valid")
        print(f"    - Items: {len(items)}")
        print(f"    - Currency: {currency}")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    # Test 10: JSON serialization (what gets sent to localStorage)
    print("\n[TEST 10] Testing JSON serialization for localStorage...")
    try:
        json_str = json.dumps(normalized, indent=2)
        reparsed = json.loads(json_str)
        assert reparsed["identity"]["name"] == "Enwer", "Name not preserved in JSON"
        assert reparsed["identity"]["domain"] == "Life", "Domain not preserved in JSON"
        print(f"  PASS - JSON serialization successful ({len(json_str)} chars)")
    except Exception as e:
        print(f"  FAIL - {e}")
        return 1

    print("\n" + "=" * 80)
    print("ALL TESTS PASSED - IMPORT IS FULLY COMPATIBLE")
    print("=" * 80)
    print("\nIf import still doesn't work in browser:")
    print("1. Open browser console (F12)")
    print("2. Try the import again")
    print("3. Look for [IMPORT] or [POPULATE] log messages")
    print("4. Copy any error messages and share them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
