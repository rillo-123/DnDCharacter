"""
Integration test simulating the user's workflow with domain spells.
Tests that a Level 9 Cleric with the Life domain gets domain spells.
"""

import sys
import json
from pathlib import Path

# Setup path
assets_py = Path(__file__).parent.parent / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


def test_domain_spell_workflow():
    """Test the complete workflow: Create cleric, set domain, add domain spells."""
    print("\n" + "=" * 70)
    print("INTEGRATION TEST: Domain Spell Workflow (Level 9 Life Cleric)")
    print("=" * 70)
    
    try:
        from spellcasting_manager import (
            SPELL_LIBRARY_STATE, 
            SpellcastingManager,
            set_spell_library_data
        )
        from spell_data import LOCAL_SPELLS_FALLBACK
        from character import get_domain_bonus_spells
        
        # Step 1: Initialize spell library
        print("\n1. Initializing spell library with LOCAL_SPELLS_FALLBACK")
        set_spell_library_data(LOCAL_SPELLS_FALLBACK)
        print(f"   Spell library ready: {len(SPELL_LIBRARY_STATE['spell_map'])} spells in map")
        
        # Step 2: Create a SpellcastingManager (simulating character sheet)
        print("\n2. Creating SpellcastingManager for Level 9 Cleric")
        manager = SpellcastingManager()
        print(f"   Manager created, prepared spells: {len(manager.prepared)}")
        
        # Step 3: Get domain bonus spells for Life domain at level 9
        print("\n3. Getting Life domain bonus spells for Level 9")
        domain_spells = get_domain_bonus_spells("Life", 9)
        print(f"   Domain spells retrieved: {len(domain_spells)}")
        print(f"   Spells: {', '.join(domain_spells)}")
        
        # Step 4: Add domain spells to prepared list
        print("\n4. Adding domain spells to prepared spells")
        added_count = 0
        failed_spells = []
        for spell_slug in domain_spells:
            manager.add_spell(spell_slug, is_domain_bonus=True)
            if manager.is_spell_prepared(spell_slug):
                print(f"   ADDED: {spell_slug}")
                added_count += 1
            else:
                print(f"   FAILED: {spell_slug}")
                failed_spells.append(spell_slug)
        
        # Step 5: Verify results
        print(f"\n5. Results:")
        print(f"   Total prepared spells: {len(manager.prepared)}")
        print(f"   Domain spells added: {added_count}/{len(domain_spells)}")
        
        # List the prepared spells
        if manager.prepared:
            print(f"\n   Prepared spell list:")
            for spell in manager.prepared:
                is_domain_str = " [DOMAIN]" if spell.get("is_domain_bonus") else ""
                print(f"      - {spell.get('name', 'Unknown')} (level {spell.get('level')}){is_domain_str}")
        
        # Check for domain spells specifically
        domain_spells_prepared = [s for s in manager.prepared if s.get("is_domain_bonus")]
        print(f"\n   Domain bonus spells marked: {len(domain_spells_prepared)}")
        
        success = (added_count == len(domain_spells)) and (len(failed_spells) == 0)
        
        if success:
            print(f"\n SUCCESS: All {added_count} domain spells successfully added!")
            return True
        else:
            print(f"\n FAILURE: Failed to add {len(failed_spells)} spells: {', '.join(failed_spells)}")
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_export_import_workflow():
    """Test that exported spells with is_domain_bonus flag can be re-imported."""
    print("\n" + "=" * 70)
    print("TEST: Export/Import Domain Spells Workflow")
    print("=" * 70)
    
    try:
        from spellcasting_manager import (
            SPELL_LIBRARY_STATE, 
            SpellcastingManager,
            set_spell_library_data
        )
        from spell_data import LOCAL_SPELLS_FALLBACK
        from character import get_domain_bonus_spells
        
        # Step 1: Create manager and add domain spells
        print("\n1. Setting up manager with domain spells")
        set_spell_library_data(LOCAL_SPELLS_FALLBACK)
        manager1 = SpellcastingManager()
        
        domain_spells = get_domain_bonus_spells("Life", 9)
        for spell_slug in domain_spells:
            manager1.add_spell(spell_slug, is_domain_bonus=True)
        
        print(f"   Added {len(manager1.prepared)} spells to manager1")
        
        # Step 2: Export the state
        print("\n2. Exporting spellcasting state")
        exported_state = manager1.export_state()
        print(f"   Exported {len(exported_state.get('prepared', []))} spells")
        
        # Show domain spells in export
        domain_in_export = [s for s in exported_state.get('prepared', []) if s.get('is_domain_bonus')]
        print(f"   Domain spells in export: {len(domain_in_export)}")
        
        # Step 3: Import into new manager
        print("\n3. Importing into new manager")
        manager2 = SpellcastingManager()
        manager2.load_state(exported_state)
        print(f"   Imported {len(manager2.prepared)} spells to manager2")
        
        # Step 4: Verify domain spells preserved
        domain_in_manager2 = [s for s in manager2.prepared if s.get('is_domain_bonus')]
        print(f"   Domain spells in manager2: {len(domain_in_manager2)}")
        
        if len(domain_in_manager2) == len(domain_in_export):
            print(f"\n SUCCESS: Domain spells preserved through export/import!")
            return True
        else:
            print(f"\n FAILURE: Domain spells lost during export/import")
            return False
            
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("DOMAIN SPELL INTEGRATION TESTS")
    print("=" * 70)
    
    results = {
        "domain_spell_workflow": test_domain_spell_workflow(),
        "export_import_workflow": test_export_import_workflow(),
    }
    
    print("\n" + "=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll integration tests passed! Domain spells should work correctly.")
    else:
        print(f"\n{total - passed} test(s) failed. Domain spell feature may not work properly.")
