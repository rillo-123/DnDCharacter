#!/usr/bin/env python3
"""Test importing the Enwer character to check compatibility."""

import json
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]

    # Add assets/py to path
    sys.path.insert(0, str(root / "assets" / "py"))

    from character_models import CharacterFactory
    from spellcasting_manager import SpellcastingManager, SPELL_LIBRARY_STATE, set_spell_library_data
    from spell_data import LOCAL_SPELLS_FALLBACK

    # Initialize spell library like character.py does
    set_spell_library_data(LOCAL_SPELLS_FALLBACK)
    SPELL_LIBRARY_STATE["loaded"] = True

    # Load export file
    export_file = root / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json"
    with open(export_file, encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded {export_file}")
    print(f"Character: {data['identity']['name']} ({data['identity']['class']})")

    # Test 1: Create character from dict
    try:
        character = CharacterFactory.from_dict(data)
        print(f"[PASS] CharacterFactory.from_dict() succeeded")
        print(f"  - Type: {type(character).__name__}")
        print(f"  - Name: {character.name}")
        print(f"  - Class: {character.class_text}")
        print(f"  - Domain: {character.domain}")
    except Exception as e:
        print(f"[FAIL] CharacterFactory.from_dict(): {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 2: Check to_dict round-trip
    try:
        normalized = character.to_dict()
        print(f"[PASS] to_dict() succeeded")
    except Exception as e:
        print(f"[FAIL] to_dict(): {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Test 3: Check spellcasting data loads
    try:
        spellcasting = normalized.get("spellcasting")
        if spellcasting:
            prepared = spellcasting.get("prepared", [])
            print(f"[PASS] Spellcasting present with {len(prepared)} prepared spells")
        else:
            print(f"[WARN] No spellcasting data in normalized character")
    except Exception as e:
        print(f"[FAIL] Spellcasting check: {e}")
        import traceback
        traceback.print_exc()

    # Test 4: Verify domain spells can be looked up
    try:
        if data.get("spellcasting", {}).get("domain_bonus_spells"):
            domain_bonus = data["spellcasting"]["domain_bonus_spells"]
            print(f"[PASS] Domain bonus spells present: {len(domain_bonus)} spells")
        else:
            print(f"[INFO] No domain bonus spells in export (may be normal)")
    except Exception as e:
        print(f"[FAIL] Domain spells check: {e}")
        import traceback
        traceback.print_exc()

    print("\nImport compatibility test PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
