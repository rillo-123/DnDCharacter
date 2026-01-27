"""
Debug test to check spell library loading and domain spell lookup.
This test simulates the browser environment to check if domain spells can be found.
"""

import sys
import json
from pathlib import Path

# Setup path
assets_py = Path(__file__).parent.parent / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


def test_spell_library_loading():
    """Test that spell library loads correctly with domain spells."""
    print("\n" + "=" * 70)
    print("TEST: Spell Library Loading with Domain Spells")
    print("=" * 70)
    
    try:
        # Import spell data
        from spell_data import LOCAL_SPELLS_FALLBACK
        print(f"\n1. Loaded LOCAL_SPELLS_FALLBACK with {len(LOCAL_SPELLS_FALLBACK)} spells")
        
        # Build spell_map like spellcasting.py does
        spell_map = {}
        for spell in LOCAL_SPELLS_FALLBACK:
            spell_slug = (spell.get("slug") or "").lower()
            if spell_slug:
                spell_map[spell_slug] = spell
        
        print(f"2. Built spell_map with {len(spell_map)} spells")
        
        # Check domain spells
        domain_spells_to_check = [
            "bless", "cure-wounds", "raise-dead", "mass-cure-wounds", 
            "beacon-of-hope", "lesser-restoration", "spiritual-weapon",
            "death-ward", "guardian-of-faith"
        ]
        
        print(f"\n3. Checking domain spells in spell_map:")
        all_found = True
        for slug in domain_spells_to_check:
            if slug in spell_map:
                spell = spell_map[slug]
                print(f"   FOUND: {slug:25} (name: {spell.get('name')})")
            else:
                print(f"   MISSING: {slug:25}")
                all_found = False
        
        if all_found:
            print(f"\n SUCCESS: All domain spells found in spell_map")
            return True
        else:
            print(f"\n FAILURE: Some domain spells missing")
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spell_lookup_function():
    """Test the get_spell_by_slug function."""
    print("\n" + "=" * 70)
    print("TEST: get_spell_by_slug Function")
    print("=" * 70)
    
    try:
        # Import spellcasting module
        from spellcasting_manager import (
            SPELL_LIBRARY_STATE, 
            get_spell_by_slug, 
            set_spell_library_data
        )
        from spell_data import LOCAL_SPELLS_FALLBACK
        
        print(f"\n1. Initializing SPELL_LIBRARY_STATE with LOCAL_SPELLS_FALLBACK")
        set_spell_library_data(LOCAL_SPELLS_FALLBACK)
        print(f"   spell_map size: {len(SPELL_LIBRARY_STATE['spell_map'])}")
        print(f"   spells list size: {len(SPELL_LIBRARY_STATE['spells'])}")
        
        # Test lookups
        domain_spells = ["bless", "cure-wounds", "raise-dead", "mass-cure-wounds"]
        
        print(f"\n2. Testing get_spell_by_slug for domain spells:")
        all_found = True
        for slug in domain_spells:
            result = get_spell_by_slug(slug)
            if result:
                print(f"   FOUND: {slug:20} -> {result.get('name')}")
            else:
                print(f"   NOT FOUND: {slug:20}")
                all_found = False
        
        if all_found:
            print(f"\n SUCCESS: All domain spells found via get_spell_by_slug")
            return True
        else:
            print(f"\n FAILURE: Some domain spells not found")
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_add_spell_simulation():
    """Test the add_spell method simulation."""
    print("\n" + "=" * 70)
    print("TEST: add_spell Simulation")
    print("=" * 70)
    
    try:
        from spellcasting_manager import (
            SPELL_LIBRARY_STATE, 
            SpellcastingManager,
            set_spell_library_data
        )
        from spell_data import LOCAL_SPELLS_FALLBACK
        
        print(f"\n1. Initializing spell library")
        set_spell_library_data(LOCAL_SPELLS_FALLBACK)
        
        print(f"2. Creating SpellcastingManager")
        manager = SpellcastingManager()
        
        print(f"3. Testing add_spell for domain spells")
        domain_spells = ["bless", "cure-wounds", "raise-dead", "mass-cure-wounds"]
        
        added_count = 0
        for slug in domain_spells:
            manager.add_spell(slug, is_domain_bonus=True)
            if manager.is_spell_prepared(slug):
                print(f"   SUCCESS: Added {slug}")
                added_count += 1
            else:
                print(f"   FAILED: Could not add {slug}")
        
        print(f"\n4. Summary:")
        print(f"   Prepared spells: {len(manager.prepared)}")
        print(f"   Successfully added: {added_count}/{len(domain_spells)}")
        
        if added_count == len(domain_spells):
            print(f"\n SUCCESS: All domain spells added successfully")
            return True
        else:
            print(f"\n FAILURE: Not all domain spells were added")
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("DOMAIN SPELL DEBUG TESTS")
    print("=" * 70)
    
    results = {
        "library_loading": test_spell_library_loading(),
        "spell_lookup": test_spell_lookup_function(),
        "add_spell": test_add_spell_simulation(),
    }
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! Domain spell loading should work.")
    else:
        print(f"\n{total - passed} test(s) failed. Need to investigate.")
