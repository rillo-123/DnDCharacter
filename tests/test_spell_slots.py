"""
Test spell slot management and the KeyError: 0 issue.
"""

import sys
import os
from pathlib import Path

# Setup path
assets_py = Path(__file__).parent.parent / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


def test_standard_slot_table_loaded():
    """Check if STANDARD_SLOT_TABLE is properly loaded from spell_data."""
    print("\n=== TEST: STANDARD_SLOT_TABLE loaded ===")
    
    try:
        from spell_data import STANDARD_SLOT_TABLE
        print(f"✓ STANDARD_SLOT_TABLE imported")
        print(f"  Type: {type(STANDARD_SLOT_TABLE)}")
        print(f"  Keys: {list(STANDARD_SLOT_TABLE.keys())[:10]}")
        print(f"  Total entries: {len(STANDARD_SLOT_TABLE)}")
        
        if not STANDARD_SLOT_TABLE:
            print("  ✗ WARNING: STANDARD_SLOT_TABLE is empty!")
            return False
        
        # Check structure
        for level, slots in list(STANDARD_SLOT_TABLE.items())[:3]:
            print(f"  Level {level}: {slots}")
        
        # Check for key 0 (fallback)
        has_zero = 0 in STANDARD_SLOT_TABLE
        has_one = 1 in STANDARD_SLOT_TABLE
        print(f"  Has key 0: {has_zero}")
        print(f"  Has key 1: {has_one}")
        
        return len(STANDARD_SLOT_TABLE) > 0
    except ImportError as e:
        print(f"✗ Failed to import STANDARD_SLOT_TABLE: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pact_magic_table():
    """Check if PACT_MAGIC_TABLE is loaded."""
    print("\n=== TEST: PACT_MAGIC_TABLE loaded ===")
    
    try:
        from spell_data import PACT_MAGIC_TABLE
        print(f"✓ PACT_MAGIC_TABLE imported")
        print(f"  Type: {type(PACT_MAGIC_TABLE)}")
        print(f"  Keys: {list(PACT_MAGIC_TABLE.keys())}")
        print(f"  Total entries: {len(PACT_MAGIC_TABLE)}")
        
        # Check structure
        for level, info in list(PACT_MAGIC_TABLE.items())[:3]:
            print(f"  Level {level}: {info}")
        
        return len(PACT_MAGIC_TABLE) > 0
    except ImportError as e:
        print(f"✗ Failed to import PACT_MAGIC_TABLE: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spellcasting_imports():
    """Check what spellcasting imports from spell_data."""
    print("\n=== TEST: spellcasting imports from spell_data ===")
    
    try:
        import spellcasting_manager
        print(f"✓ spellcasting module imported")
        
        # Check what it has
        required = [
            'STANDARD_SLOT_TABLE',
            'PACT_MAGIC_TABLE',
            'SPELL_LIBRARY_STATE',
            'SpellcastingManager',
        ]
        
        for attr in required:
            has_it = hasattr(spellcasting, attr)
            value = getattr(spellcasting, attr, None)
            status = "✓" if has_it else "✗"
            
            if isinstance(value, dict) and attr in ['STANDARD_SLOT_TABLE', 'PACT_MAGIC_TABLE']:
                print(f"  {status} {attr}: dict with {len(value)} entries")
            elif isinstance(value, dict):
                print(f"  {status} {attr}: dict with {len(value)} keys")
            else:
                print(f"  {status} {attr}: {type(value).__name__}")
        
        # Specifically check STANDARD_SLOT_TABLE
        st = getattr(spellcasting, 'STANDARD_SLOT_TABLE', {})
        if not st:
            print("  ✗ STANDARD_SLOT_TABLE is empty in spellcasting!")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_compute_slot_summary():
    """Test the compute_slot_summary function."""
    print("\n=== TEST: compute_slot_summary ===")
    
    try:
        import spellcasting_manager
        
        # Create a SpellcastingManager
        manager = spellcasting.SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        # Test compute_slot_summary
        result = manager.compute_slot_summary()
        print(f"✓ compute_slot_summary executed")
        print(f"  Type: {type(result)}")
        print(f"  Keys: {result.keys()}")
        
        # Check structure
        if 'levels' in result:
            levels = result['levels']
            print(f"  levels: type={type(levels).__name__}, keys={list(levels.keys())}")
            
            # Check if we have level 0 or only 1-9
            if 0 in levels:
                print(f"    ⚠ Has key 0: {levels[0]}")
            
            # Print first few entries
            for k in sorted(levels.keys())[:5]:
                print(f"    Level {k}: {levels[k]}")
        
        if 'pact' in result:
            print(f"  pact: {result['pact']}")
        
        if 'effective_level' in result:
            print(f"  effective_level: {result['effective_level']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slot_summary_access_pattern():
    """Test the exact access pattern that's causing the error."""
    print("\n=== TEST: Spell slot access pattern ===")
    
    try:
        import spellcasting_manager
        
        manager = spellcasting.SpellcastingManager()
        slot_summary = manager.compute_slot_summary()
        levels = slot_summary.get("levels", {})
        
        print(f"✓ Got slot_summary")
        print(f"  levels dict: {levels}")
        
        # Test the access pattern from render_slots_tracker
        print("\n  Testing access pattern from render_slots_tracker:")
        for level in range(1, 10):
            max_slots = levels.get(level, 0)
            print(f"    Level {level}: max_slots={max_slots}")
            
            if max_slots > 0:
                used = manager.slots_used.get(level, 0)
                available = max_slots - used
                print(f"      used={used}, available={available}")
        
        print("✓ All accesses successful")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_render_slots_tracker():
    """Test the full render_slots_tracker method."""
    print("\n=== TEST: render_slots_tracker ===")
    
    try:
        import spellcasting_manager
        
        manager = spellcasting.SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        # render_slots_tracker tries to get element, which will be None in test
        # So we'll just test the logic part manually
        slot_summary = manager.compute_slot_summary()
        levels = slot_summary.get("levels", {})
        
        tracker_items = []
        for level in range(1, 10):
            max_slots = levels.get(level, 0)
            if max_slots <= 0:
                continue
            used = manager.slots_used.get(level, 0)
            available = max_slots - used
            tracker_items.append({
                'level': level,
                'max': max_slots,
                'used': used,
                'available': available
            })
        
        print(f"✓ Tracker items: {len(tracker_items)}")
        for item in tracker_items:
            print(f"  Level {item['level']}: {item['available']}/{item['max']}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_slots_used_initialization():
    """Check if slots_used is properly initialized."""
    print("\n=== TEST: slots_used initialization ===")
    
    try:
        import spellcasting_manager
        
        manager = spellcasting.SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        slots_used = manager.slots_used
        print(f"  slots_used type: {type(slots_used)}")
        print(f"  slots_used keys: {list(slots_used.keys())}")
        print(f"  slots_used content: {slots_used}")
        
        # Check for problematic key 0
        if 0 in slots_used:
            print(f"  ⚠ Has key 0: {slots_used[0]}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_load_state_with_spells():
    """Test loading state with spell data."""
    print("\n=== TEST: load_state with spells ===")
    
    try:
        import spellcasting_manager
        
        manager = spellcasting.SpellcastingManager()
        print(f"✓ SpellcastingManager created")
        
        # Simulate some spell data
        spellbook = {
            "cleric": {
                "0": ["light", "sacred-flame"],
                "1": ["bless", "cure-wounds"],
            }
        }
        
        # Try to load a state
        try:
            # load_state expects specific structure
            state = {
                "spellbook": spellbook,
                "prepared": [],
                "slots": {},
            }
            manager.load_state(state)
            print(f"✓ load_state executed successfully")
        except Exception as e:
            print(f"  load_state error: {e}")
            # This is OK, we're just testing the slot computation part
        
        # Check slot summary again
        slot_summary = manager.compute_slot_summary()
        print(f"  slot_summary: {slot_summary}")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("SPELL SLOT SYSTEM TESTS")
    print("=" * 70)
    
    results = {
        "standard_slot_table": test_standard_slot_table_loaded(),
        "pact_magic_table": test_pact_magic_table(),
        "spellcasting_imports": test_spellcasting_imports(),
        "compute_slot_summary": test_compute_slot_summary(),
        "slot_access_pattern": test_slot_summary_access_pattern(),
        "render_slots_tracker": test_render_slots_tracker(),
        "slots_used_init": test_slots_used_initialization(),
        "load_state_with_spells": test_load_state_with_spells(),
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
