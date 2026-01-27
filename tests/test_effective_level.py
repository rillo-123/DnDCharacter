"""
Debug what's happening with get_numeric_value and effective_level.
"""

import sys
import os
from pathlib import Path

# Setup path
assets_py = Path(__file__).parent.parent / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


def test_get_numeric_value():
    """Check what get_numeric_value returns."""
    print("\n=== TEST: get_numeric_value ===")
    
    try:
        from spellcasting_manager import get_numeric_value, STANDARD_SLOT_TABLE
        
        # In test environment, there's no DOM, so get_numeric_value will fail
        # But let's see what it tries to do
        try:
            result = get_numeric_value("level", 1)
            print(f"✓ get_numeric_value('level', 1) = {result}")
            print(f"  Type: {type(result)}")
        except Exception as e:
            print(f"  get_numeric_value error: {e}")
            print(f"  This is expected in test environment (no DOM)")
        
        # Check what should happen
        effective_level = 1  # Default
        print(f"\n  Using default effective_level = {effective_level}")
        print(f"  STANDARD_SLOT_TABLE has keys: {list(STANDARD_SLOT_TABLE.keys())}")
        print(f"  Is {effective_level} in STANDARD_SLOT_TABLE? {effective_level in STANDARD_SLOT_TABLE}")
        
        if effective_level in STANDARD_SLOT_TABLE:
            slot_counts = STANDARD_SLOT_TABLE[effective_level]
            print(f"  slot_counts for level {effective_level}: {slot_counts}")
            print(f"  Type: {type(slot_counts)}")
            print(f"  Length: {len(slot_counts) if hasattr(slot_counts, '__len__') else 'N/A'}")
            
            # Now test the dict comprehension
            try:
                level_slots = {level: slot_counts[level - 1] if level <= len(slot_counts) else 0 for level in range(1, 10)}
                print(f"✓ level_slots created: {level_slots}")
            except KeyError as ke:
                print(f"✗ KeyError accessing slot_counts: {ke}")
                print(f"  Trying to access slot_counts[{ke}]?")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_direct_effective_level():
    """Test with explicit effective_level."""
    print("\n=== TEST: Direct effective_level scenarios ===")
    
    try:
        from spell_data import STANDARD_SLOT_TABLE
        
        print(f"STANDARD_SLOT_TABLE structure:")
        for level in [1, 2, 3, 5, 10, 20]:
            if level in STANDARD_SLOT_TABLE:
                slot_counts = STANDARD_SLOT_TABLE[level]
                print(f"  Level {level}: {slot_counts} (type: {type(slot_counts).__name__})")
            else:
                print(f"  Level {level}: NOT FOUND")
        
        # Test the problematic case
        print(f"\nTesting effective_level = 1:")
        effective_level = 1
        slot_counts = STANDARD_SLOT_TABLE.get(
            effective_level, STANDARD_SLOT_TABLE.get(0, [0, 0, 0, 0, 0, 0, 0, 0, 0])
        )
        print(f"  slot_counts = {slot_counts}")
        print(f"  Type: {type(slot_counts)}")
        
        if isinstance(slot_counts, dict):
            print(f"  ⚠ slot_counts is a dict, not a list!")
            print(f"  Dict keys: {list(slot_counts.keys())}")
            print(f"  This will fail when trying to index with [level-1]")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("DEBUG: Effective Level and Slot Counts")
    print("=" * 70)
    
    test_get_numeric_value()
    test_direct_effective_level()
