"""
Test module loading in PyScript environment and local testing.
Diagnoses why spellcasting module can't be imported in PyScript.
"""

import sys
import os
from pathlib import Path


def test_module_sys_path():
    """Check sys.path to see where Python looks for modules."""
    print("\n=== TEST: sys.path content ===")
    print(f"Python executable: {sys.executable}")
    print(f"Current directory: {os.getcwd()}")
    print("\nModule search paths (sys.path):")
    for i, path in enumerate(sys.path, 1):
        exists = "✓" if os.path.exists(path) else "✗"
        print(f"  {i}. {exists} {path}")
    
    # Check for assets/py specifically
    assets_py = Path(os.getcwd()) / "assets" / "py"
    print(f"\nassets/py path: {assets_py}")
    print(f"  Exists: {assets_py.exists()}")
    if assets_py.exists():
        print(f"  Is directory: {assets_py.is_dir()}")
        files = list(assets_py.glob("*.py"))
        print(f"  Python files: {len(files)}")
        for f in files[:5]:
            print(f"    - {f.name}")


def test_module_import_direct():
    """Try to import spellcasting directly."""
    print("\n=== TEST: Direct import ===")
    try:
        import spellcasting
        print("✓ spellcasting imported successfully")
        print(f"  Location: {spellcasting.__file__}")
        return True
    except ModuleNotFoundError as e:
        print(f"✗ spellcasting import failed: {e}")
        return False
    except ImportError as e:
        print(f"✗ spellcasting import error: {e}")
        return False


def test_module_sys_path_add():
    """Try to add assets/py to sys.path and import."""
    print("\n=== TEST: Add to sys.path and import ===")
    
    assets_py = Path(__file__).parent.parent / "assets" / "py"
    print(f"Attempting to add: {assets_py}")
    
    if str(assets_py) not in sys.path:
        sys.path.insert(0, str(assets_py))
        print(f"✓ Added to sys.path[0]")
    
    try:
        import spellcasting
        print("✓ spellcasting imported successfully after path update")
        print(f"  Location: {spellcasting.__file__}")
        
        # Check for required attributes
        required_attrs = [
            'SpellcastingManager',
            'SPELL_LIBRARY_STATE',
            'set_spell_library_data',
            'load_spell_library',
        ]
        
        for attr in required_attrs:
            has_attr = hasattr(spellcasting, attr)
            status = "✓" if has_attr else "✗"
            print(f"  {status} {attr}")
        
        return True
    except Exception as e:
        print(f"✗ spellcasting import still failed: {e}")
        return False


def test_spell_data_import():
    """Check if spell_data can be imported."""
    print("\n=== TEST: spell_data import ===")
    
    assets_py = Path(__file__).parent.parent / "assets" / "py"
    if str(assets_py) not in sys.path:
        sys.path.insert(0, str(assets_py))
    
    try:
        import spell_data
        print("✓ spell_data imported successfully")
        print(f"  Location: {spell_data.__file__}")
        
        required = [
            'SPELL_CLASS_SYNONYMS',
            'SPELL_CLASS_DISPLAY_NAMES',
            'SUPPORTED_SPELL_CLASSES',
        ]
        
        for attr in required:
            has_attr = hasattr(spell_data, attr)
            status = "✓" if has_attr else "✗"
            print(f"  {status} {attr}")
        
        return True
    except Exception as e:
        print(f"✗ spell_data import failed: {e}")
        return False


def test_character_import():
    """Check if character can be imported."""
    print("\n=== TEST: character import ===")
    
    assets_py = Path(__file__).parent.parent / "assets" / "py"
    if str(assets_py) not in sys.path:
        sys.path.insert(0, str(assets_py))
    
    try:
        import character
        print("✓ character imported successfully")
        print(f"  Location: {character.__file__}")
        
        print(f"  SPELLCASTING_MANAGER: {character.SPELLCASTING_MANAGER}")
        print(f"  SpellcastingManager: {character.SpellcastingManager}")
        
        return True
    except Exception as e:
        print(f"✗ character import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_spellcasting_syntax():
    """Check spellcasting.py for syntax errors."""
    print("\n=== TEST: spellcasting.py syntax ===")
    
    spellcasting_file = Path(__file__).parent.parent / "assets" / "py" / "spellcasting.py"
    print(f"File: {spellcasting_file}")
    print(f"Exists: {spellcasting_file.exists()}")
    
    if not spellcasting_file.exists():
        print("✗ File not found")
        return False
    
    try:
        with open(spellcasting_file, 'r') as f:
            code = f.read()
        
        compile(code, str(spellcasting_file), 'exec')
        print("✓ spellcasting.py syntax is valid")
        
        # Check for the specific issue
        if 'PACT_MAGIC_TABLE_OLD,' in code:
            print("⚠ WARNING: Found 'PACT_MAGIC_TABLE_OLD,' in file (should be removed)")
            lines = code.split('\n')
            for i, line in enumerate(lines, 1):
                if 'PACT_MAGIC_TABLE_OLD,' in line:
                    print(f"  Line {i}: {line}")
            return False
        else:
            print("✓ No stray PACT_MAGIC_TABLE_OLD found")
        
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_pyscript_import_mechanism():
    """Simulate how PyScript loads modules."""
    print("\n=== TEST: PyScript module loading simulation ===")
    
    # In PyScript, modules need to be in the same directory or in PYTHONPATH
    # Check what directories PyScript would search
    
    print("Simulating PyScript import search:")
    
    # 1. Check current working directory
    cwd = Path.cwd()
    print(f"\n1. Current working directory: {cwd}")
    print(f"   Has assets/py/spellcasting.py: {(cwd / 'assets' / 'py' / 'spellcasting.py').exists()}")
    
    # 2. Check if spellcasting.py is in root
    print(f"\n2. Root directory: {cwd}")
    print(f"   Has spellcasting.py: {(cwd / 'spellcasting.py').exists()}")
    
    # 3. Check PYTHONPATH
    pythonpath = os.environ.get('PYTHONPATH', 'Not set')
    print(f"\n3. PYTHONPATH: {pythonpath}")
    
    # 4. PyScript typically needs files accessible via HTTP or in specific paths
    print(f"\n4. PyScript module loading notes:")
    print(f"   - PyScript looks in the same directory as HTML file")
    print(f"   - PyScript looks in 'py' subdirectory")
    print(f"   - Module must be importable from HTML file's location")
    print(f"   - sys.path may not include all directories initially")
    
    return True


def test_import_order_issue():
    """Check if there's a circular import or import order issue."""
    print("\n=== TEST: Import order and circular dependencies ===")
    
    assets_py = Path(__file__).parent.parent / "assets" / "py"
    if str(assets_py) not in sys.path:
        sys.path.insert(0, str(assets_py))
    
    print("Attempting import chain:")
    
    try:
        print("\n1. Importing spell_data...")
        import spell_data
        print("   ✓ spell_data imported")
    except Exception as e:
        print(f"   ✗ spell_data failed: {e}")
        return False
    
    try:
        print("\n2. Importing spellcasting...")
        import spellcasting
        print("   ✓ spellcasting imported")
    except Exception as e:
        print(f"   ✗ spellcasting failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        print("\n3. Importing character...")
        import character
        print("   ✓ character imported")
    except Exception as e:
        print(f"   ✗ character failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("PYSCRIPT ENVIRONMENT DIAGNOSTICS")
    print("=" * 70)
    
    results = {
        "sys.path": test_module_sys_path(),
        "direct_import": test_module_import_direct(),
        "sys_path_add": test_module_sys_path_add(),
        "spell_data": test_spell_data_import(),
        "spellcasting_syntax": test_spellcasting_syntax(),
        "pyscript_sim": test_pyscript_import_mechanism(),
        "import_order": test_import_order_issue(),
        "character": test_character_import(),
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
    
    if passed == total:
        print("\n✓ All diagnostics passed - modules should load correctly")
    else:
        print("\n✗ Some diagnostics failed - see above for details")
