"""
Test spell rendering and GUI display issues.
"""

import sys
import os
from pathlib import Path

# Setup path
assets_py = Path(__file__).parent.parent / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


def test_spellcasting_manager_state():
    """Check SpellcastingManager internal state."""
    print("\n=== TEST: SpellcastingManager state ===")
    
    try:
        from spellcasting_manager import SpellcastingManager, SPELL_LIBRARY_STATE
        
        manager = SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        # Check internal state
        print(f"\n  spellbook keys: {list(manager.spellbook.keys())}")
        print(f"  spellbook['cleric']: {manager.spellbook.get('cleric', {})}")
        
        print(f"\n  prepared_spells keys: {list(manager.prepared_spells.keys())}")
        print(f"  prepared_spells['cleric']: {manager.prepared_spells.get('cleric', [])}")
        
        print(f"\n  SPELL_LIBRARY_STATE['loaded']: {SPELL_LIBRARY_STATE.get('loaded')}")
        print(f"  SPELL_LIBRARY_STATE['spells'] count: {len(SPELL_LIBRARY_STATE.get('spells', []))}")
        print(f"  SPELL_LIBRARY_STATE['spell_map'] count: {len(SPELL_LIBRARY_STATE.get('spell_map', {}))}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_render_spellbook():
    """Test the render_spellbook method."""
    print("\n=== TEST: render_spellbook ===")
    
    try:
        from spellcasting_manager import SpellcastingManager, SPELL_LIBRARY_STATE
        
        # Setup spell library with some mock data
        SPELL_LIBRARY_STATE['loaded'] = True
        SPELL_LIBRARY_STATE['spells'] = [
            {'slug': 'cure-wounds', 'name': 'Cure Wounds', 'level': 1, 'classes': ['cleric']},
            {'slug': 'bless', 'name': 'Bless', 'level': 1, 'classes': ['cleric']},
            {'slug': 'aid', 'name': 'Aid', 'level': 2, 'classes': ['cleric']},
        ]
        SPELL_LIBRARY_STATE['spell_map'] = {
            'cure-wounds': SPELL_LIBRARY_STATE['spells'][0],
            'bless': SPELL_LIBRARY_STATE['spells'][1],
            'aid': SPELL_LIBRARY_STATE['spells'][2],
        }
        
        manager = SpellcastingManager()
        print(f"✓ SpellcastingManager created with mock spells")
        
        # Load state with prepared spells
        state = {
            'spellbook': {
                'cleric': {
                    '0': ['cure-wounds'],
                    '1': ['bless'],
                    '2': ['aid'],
                }
            },
            'prepared': ['cure-wounds', 'bless'],
        }
        
        manager.load_state(state)
        print(f"✓ State loaded")
        
        # Check what render_spellbook would do
        print(f"\n  manager.spellbook: {manager.spellbook}")
        print(f"  manager.prepared_spells: {manager.prepared_spells}")
        
        # Check render methods exist
        has_render = hasattr(manager, 'render_spellbook')
        print(f"  has render_spellbook: {has_render}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spell_filtering():
    """Test spell filtering for display."""
    print("\n=== TEST: Spell filtering ===")
    
    try:
        from spellcasting_manager import SpellcastingManager
        
        manager = SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        # Test apply_spell_filters method
        has_filter = hasattr(manager, 'apply_spell_filters')
        print(f"  has apply_spell_filters: {has_filter}")
        
        # Check for filter-related attributes
        filter_attrs = [
            'filtered_spells',
            'spell_filters',
            'active_filters',
        ]
        
        for attr in filter_attrs:
            has_it = hasattr(manager, attr)
            value = getattr(manager, attr, None)
            print(f"  {attr}: {has_it}")
            if value is not None:
                if isinstance(value, dict):
                    print(f"    dict with {len(value)} entries")
                elif isinstance(value, list):
                    print(f"    list with {len(value)} entries")
                else:
                    print(f"    {type(value).__name__}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_get_eligible_spells():
    """Test get_eligible_spells method."""
    print("\n=== TEST: get_eligible_spells ===")
    
    try:
        from spellcasting_manager import SpellcastingManager, SPELL_LIBRARY_STATE
        
        # Setup
        SPELL_LIBRARY_STATE['loaded'] = True
        SPELL_LIBRARY_STATE['spells'] = [
            {'slug': 'cure-wounds', 'name': 'Cure Wounds', 'level': 1, 'classes': ['cleric']},
            {'slug': 'bless', 'name': 'Bless', 'level': 1, 'classes': ['cleric']},
        ]
        SPELL_LIBRARY_STATE['spell_map'] = {
            'cure-wounds': SPELL_LIBRARY_STATE['spells'][0],
            'bless': SPELL_LIBRARY_STATE['spells'][1],
        }
        
        manager = SpellcastingManager()
        
        # Check if method exists
        has_method = hasattr(manager, 'get_eligible_spells')
        print(f"  has get_eligible_spells: {has_method}")
        
        if has_method:
            try:
                spells = manager.get_eligible_spells()
                print(f"✓ get_eligible_spells() executed")
                print(f"  Returned {len(spells)} spells")
            except Exception as e:
                print(f"  Error calling get_eligible_spells: {e}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_render_methods():
    """Check what render methods exist."""
    print("\n=== TEST: Render methods ===")
    
    try:
        from spellcasting_manager import SpellcastingManager
        
        manager = SpellcastingManager()
        
        # Find all render methods
        render_methods = [m for m in dir(manager) if m.startswith('render_')]
        print(f"✓ Found {len(render_methods)} render methods:")
        for method in render_methods:
            print(f"  - {method}")
        
        return len(render_methods) > 0
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dom_elements():
    """Check what DOM elements the rendering expects."""
    print("\n=== TEST: DOM element requirements ===")
    
    try:
        from spellcasting_manager import SpellcastingManager
        import inspect
        
        manager = SpellcastingManager()
        
        # Get render_spellbook source to see what elements it needs
        if hasattr(manager, 'render_spellbook'):
            source = inspect.getsource(manager.render_spellbook)
            
            # Look for get_element calls
            import re
            element_calls = re.findall(r'get_element\([\'"]([^\'"]+)[\'"]\)', source)
            
            print(f"✓ Elements needed by render_spellbook:")
            unique_elements = set(element_calls)
            for elem in sorted(unique_elements):
                print(f"  - {elem}")
            
            return True
        else:
            print("✗ No render_spellbook method found")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spell_library_load():
    """Test spell library loading."""
    print("\n=== TEST: Spell library loading ===")
    
    try:
        from spellcasting_manager import SpellcastingManager, SPELL_LIBRARY_STATE
        
        manager = SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        # Check load_spell_library method
        has_load = hasattr(manager, 'load_spell_library')
        print(f"  has load_spell_library: {has_load}")
        
        # Check what set_spell_library_data does
        has_set = hasattr(manager, 'set_spell_library_data')
        print(f"  has set_spell_library_data: {has_set}")
        
        # Current state
        print(f"\n  Current SPELL_LIBRARY_STATE:")
        print(f"    loaded: {SPELL_LIBRARY_STATE.get('loaded')}")
        print(f"    loading: {SPELL_LIBRARY_STATE.get('loading')}")
        print(f"    spells count: {len(SPELL_LIBRARY_STATE.get('spells', []))}")
        print(f"    spell_map count: {len(SPELL_LIBRARY_STATE.get('spell_map', {}))}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("SPELL RENDERING AND GUI TESTS")
    print("=" * 70)
    
    results = {
        "manager_state": test_spellcasting_manager_state(),
        "render_spellbook": test_render_spellbook(),
        "spell_filtering": test_spell_filtering(),
        "eligible_spells": test_get_eligible_spells(),
        "render_methods": test_render_methods(),
        "dom_elements": test_dom_elements(),
        "spell_library": test_spell_library_load(),
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
