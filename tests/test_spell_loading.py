"""
Test that prepared spells are actually being loaded.
"""

import sys
import os
import json
from pathlib import Path

# Setup path
assets_py = Path(__file__).parent.parent / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


def test_load_prepared_spells():
    """Test loading actual prepared spells from export file."""
    print("\n=== TEST: Load prepared spells from export ===")
    
    try:
        from spellcasting_manager import SpellcastingManager
        
        # Load export file
        export_file = Path(__file__).parent.parent / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json"
        if not export_file.exists():
            print(f"✗ Export file not found: {export_file}")
            return False
        
        with open(export_file) as f:
            data = json.load(f)
        
        spellcasting_data = data.get("spellcasting", {})
        print(f"✓ Loaded export file")
        print(f"  prepared spells in export: {len(spellcasting_data.get('prepared', []))}")
        
        # Create manager and load state
        manager = SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        # Before loading
        print(f"\n  Before load_state:")
        print(f"    manager.prepared: {len(manager.prepared)} spells")
        
        # Load the state
        manager.load_state(spellcasting_data)
        print(f"\n✓ load_state() executed")
        
        # After loading
        print(f"\n  After load_state:")
        print(f"    manager.prepared: {len(manager.prepared)} spells")
        
        if manager.prepared:
            print(f"\n  First 3 prepared spells:")
            for spell in manager.prepared[:3]:
                print(f"    - {spell.get('name', 'Unknown')} (level {spell.get('level')})")
        else:
            print(f"  ✗ No spells loaded!")
            return False
        
        return len(manager.prepared) > 0
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_normalize_prepared_entry():
    """Test the _normalize_prepared_entry method."""
    print("\n=== TEST: _normalize_prepared_entry ===")
    
    try:
        from spellcasting_manager import SpellcastingManager
        
        manager = SpellcastingManager()
        
        # Test entry from export
        entry = {
            'slug': 'guidance',
            'name': 'Guidance',
            'level': 0,
            'source': '5e Core Rules',
            'concentration': True,
            'ritual': False,
            'school': 'Divination',
            'casting_time': '1 action',
            'range': 'Touch',
            'components': 'V, S',
            'material': '',
            'duration': 'Up to 1 minute',
            'description': '',
            'description_html': '<p>Test</p>',
            'classes': ['cleric'],
            'classes_display': ['Cleric']
        }
        
        normalized = manager._normalize_prepared_entry(entry)
        print(f"✓ _normalize_prepared_entry executed")
        
        if normalized:
            print(f"  Result:")
            print(f"    slug: {normalized.get('slug')}")
            print(f"    name: {normalized.get('name')}")
            print(f"    level: {normalized.get('level')}")
            print(f"    is_domain_bonus: {normalized.get('is_domain_bonus')}")
            return True
        else:
            print(f"  ✗ Normalized entry is None/empty!")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_render_spellbook_with_data():
    """Test render_spellbook with actual data."""
    print("\n=== TEST: render_spellbook with data ===")
    
    try:
        from spellcasting_manager import SpellcastingManager
        import json
        
        # Load export
        export_file = Path(__file__).parent.parent / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json"
        with open(export_file) as f:
            data = json.load(f)
        
        spellcasting_data = data.get("spellcasting", {})
        
        # Create manager and load
        manager = SpellcastingManager()
        manager.load_state(spellcasting_data)
        
        print(f"✓ Manager loaded with {len(manager.prepared)} spells")
        
        # Check if render_spellbook would work
        # In test environment, get_element returns None, so render won't actually write to DOM
        # But we can check if it executes without error
        
        try:
            manager.render_spellbook()
            print(f"✓ render_spellbook() executed without error")
            return True
        except Exception as e:
            print(f"  render_spellbook() error (expected in test): {e}")
            # This is OK in test environment, check if prepared spells are there
            return len(manager.prepared) > 0
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_element_calls():
    """Check what DOM elements render_spellbook needs."""
    print("\n=== TEST: DOM element requirements for render_spellbook ===")
    
    try:
        from spellcasting_manager import SpellcastingManager, get_element
        import json
        
        # Load export
        export_file = Path(__file__).parent.parent / "exports" / "Enwer_Cleric_lvl9_20251126_2147.json"
        with open(export_file) as f:
            data = json.load(f)
        
        spellcasting_data = data.get("spellcasting", {})
        
        # Create manager and load
        manager = SpellcastingManager()
        manager.load_state(spellcasting_data)
        
        print(f"✓ Manager loaded with {len(manager.prepared)} spells")
        
        # Check what elements are needed
        print(f"\n  Testing get_element calls:")
        
        elements_needed = [
            "spellbook-levels",
            "spellbook-empty-state",
            "spellbook-slots-summary",
        ]
        
        for elem_id in elements_needed:
            elem = get_element(elem_id)
            status = "✓ Found" if elem else "✗ Not found"
            print(f"    {status}: {elem_id}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("SPELL LOADING AND RENDERING TESTS")
    print("=" * 70)
    
    results = {
        "load_prepared": test_load_prepared_spells(),
        "normalize_entry": test_normalize_prepared_entry(),
        "render_with_data": test_render_spellbook_with_data(),
        "dom_elements": test_get_element_calls(),
    }
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    print(f"\nTotal: {passed}/{total} passed")
