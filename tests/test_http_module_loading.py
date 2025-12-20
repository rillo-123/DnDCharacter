"""
Unit tests for HTTP-based module loading in PyScript environment.
Tests the workaround that manually fetches modules via HTTP.
"""

import sys
import os
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch, MagicMock


def test_load_module_from_http_simulation():
    """Test simulating the _load_module_from_http function."""
    print("\n=== TEST: _load_module_from_http simulation ===")
    
    # Simulate the function that will be in character.py
    def _load_module_from_http(module_name: str, url: str, source_code: str = None):
        """Load a Python module from HTTP URL and add to sys.modules."""
        try:
            print(f"  Loading {module_name} from {url}")
            
            # In real scenario, this would use open_url(url).read()
            # For testing, we'll accept source_code parameter
            if source_code is None:
                raise ImportError(f"Cannot fetch {url}")
            
            module = ModuleType(module_name)
            exec(source_code, module.__dict__)
            sys.modules[module_name] = module
            print(f"  ✓ {module_name} loaded successfully")
            return module
        except Exception as e:
            print(f"  ✗ Failed to load {module_name}: {e}")
            return None
    
    # Test 1: Load spell_data
    spell_data_code = """
SPELL_CLASS_SYNONYMS = {"cleric": ["cleric"]}
SPELL_CLASS_DISPLAY_NAMES = {"cleric": "Cleric"}
LOCAL_SPELLS_FALLBACK = []
"""
    
    spell_data = _load_module_from_http("spell_data", "http://localhost:8080/assets/py/spell_data.py", spell_data_code)
    assert spell_data is not None, "spell_data module should load"
    assert hasattr(spell_data, 'SPELL_CLASS_SYNONYMS'), "spell_data should have SPELL_CLASS_SYNONYMS"
    assert sys.modules.get('spell_data') == spell_data, "spell_data should be in sys.modules"
    print("  ✓ spell_data loaded and available in sys.modules")
    
    # Test 2: Load spellcasting (which depends on spell_data)
    spellcasting_code = """
from spell_data import SPELL_CLASS_SYNONYMS

class SpellcastingManager:
    def __init__(self):
        self.synonyms = SPELL_CLASS_SYNONYMS

SPELL_LIBRARY_STATE = {"loaded": False}

def set_spell_library_data(data):
    pass

def load_spell_library(x=None):
    pass

def apply_spell_filters(auto_select=False):
    pass

def sync_prepared_spells_with_library():
    pass
"""
    
    spellcasting = _load_module_from_http("spellcasting", "http://localhost:8080/assets/py/spellcasting.py", spellcasting_code)
    assert spellcasting is not None, "spellcasting module should load"
    assert hasattr(spellcasting, 'SpellcastingManager'), "spellcasting should have SpellcastingManager"
    assert sys.modules.get('spellcasting') == spellcasting, "spellcasting should be in sys.modules"
    print("  ✓ spellcasting loaded and available in sys.modules")
    
    # Test 3: Verify we can access attributes
    manager = spellcasting.SpellcastingManager()
    assert manager.synonyms == {"cleric": ["cleric"]}, "SpellcastingManager should access spell_data"
    print("  ✓ SpellcastingManager can access spell_data attributes")
    
    return True


def test_http_module_loading_with_real_files():
    """Test loading actual Python files from the workspace."""
    print("\n=== TEST: Load actual Python files ===")
    
    spell_data_path = Path(__file__).parent.parent / "static" / "assets" / "py" / "spell_data.py"
    spellcasting_path = Path(__file__).parent.parent / "static" / "assets" / "py" / "spellcasting.py"
    
    assert spell_data_path.exists(), f"spell_data.py should exist at {spell_data_path}"
    assert spellcasting_path.exists(), f"spellcasting.py should exist at {spellcasting_path}"
    print(f"  ✓ spell_data.py exists: {spell_data_path}")
    print(f"  ✓ spellcasting.py exists: {spellcasting_path}")
    
    # Read files
    with open(spell_data_path) as f:
        spell_data_source = f.read()
    
    with open(spellcasting_path) as f:
        spellcasting_source = f.read()
    
    print(f"  ✓ spell_data.py: {len(spell_data_source)} bytes")
    print(f"  ✓ spellcasting.py: {len(spellcasting_source)} bytes")
    
    # Test syntax
    try:
        compile(spell_data_source, str(spell_data_path), 'exec')
        print("  ✓ spell_data.py syntax is valid")
    except SyntaxError as e:
        print(f"  ✗ spell_data.py syntax error: {e}")
        return False
    
    try:
        compile(spellcasting_source, str(spellcasting_path), 'exec')
        print("  ✓ spellcasting.py syntax is valid")
    except SyntaxError as e:
        print(f"  ✗ spellcasting.py syntax error: {e}")
        return False
    
    return True


def test_fallback_import_chain():
    """Test the fallback import chain from character.py."""
    print("\n=== TEST: Fallback import chain ===")
    
    # First, load spell_data with its own dependencies
    assets_py = Path(__file__).parent.parent / "static" / "assets" / "py"
    if str(assets_py) not in sys.path:
        sys.path.insert(0, str(assets_py))
    
    try:
        print("  Attempting: import spell_data")
        import spell_data
        print("  ✓ spell_data imported successfully")
        
        # Verify it has required attributes
        required_attrs = [
            'SPELL_CLASS_SYNONYMS',
            'SPELL_CLASS_DISPLAY_NAMES',
            'LOCAL_SPELLS_FALLBACK',
        ]
        for attr in required_attrs:
            assert hasattr(spell_data, attr), f"spell_data should have {attr}"
        print(f"  ✓ spell_data has all required attributes: {', '.join(required_attrs)}")
        
    except Exception as e:
        print(f"  ✗ Failed to import spell_data: {e}")
        return False
    
    # Now test spellcasting import (with spell_data available)
    try:
        print("  Attempting: import spellcasting")
        import spellcasting
        print("  ✓ spellcasting imported successfully")
        
        # Verify it has required attributes
        required_attrs = [
            'SpellcastingManager',
            'SPELL_LIBRARY_STATE',
            'set_spell_library_data',
            'load_spell_library',
            'apply_spell_filters',
            'sync_prepared_spells_with_library',
        ]
        for attr in required_attrs:
            assert hasattr(spellcasting, attr), f"spellcasting should have {attr}"
        print(f"  ✓ spellcasting has all required attributes")
        
        # Verify SpellcastingManager is a class
        assert callable(spellcasting.SpellcastingManager), "SpellcastingManager should be callable"
        print("  ✓ SpellcastingManager is callable (can be instantiated)")
        
    except Exception as e:
        print(f"  ✗ Failed to import spellcasting: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_http_server_accessibility():
    """Test that all required files are accessible via HTTP."""
    print("\n=== TEST: HTTP server accessibility ===")
    
    import urllib.request
    import urllib.error
    
    files_to_check = [
        'spell_data.py',
        'spellcasting.py',
        'character.py',
        'character_models.py',
    ]
    
    base_url = "http://localhost:8080/assets/py"
    all_accessible = True
    
    for filename in files_to_check:
        url = f"{base_url}/{filename}"
        try:
            with urllib.request.urlopen(url) as response:
                status = response.status
                size = len(response.read())
                if status == 200:
                    print(f"  ✓ {filename}: 200 OK ({size} bytes)")
                else:
                    print(f"  ✗ {filename}: {status}")
                    all_accessible = False
        except urllib.error.HTTPError as e:
            print(f"  ✗ {filename}: HTTP {e.code}")
            all_accessible = False
        except urllib.error.URLError as e:
            print(f"  ✗ {filename}: Connection error - {e.reason}")
            print(f"      (Is the server running on port 8080?)")
            all_accessible = False
        except Exception as e:
            print(f"  ✗ {filename}: {type(e).__name__}: {e}")
            all_accessible = False
    
    return all_accessible


def test_module_exec_independence():
    """Test that modules can be loaded via exec() without full import."""
    print("\n=== TEST: Module exec independence ===")
    
    # Simple module that doesn't depend on anything
    simple_module_code = """
class TestClass:
    value = 42

def test_function():
    return "test"

TEST_CONSTANT = "test_value"
"""
    
    try:
        module = ModuleType("test_simple")
        exec(simple_module_code, module.__dict__)
        
        assert hasattr(module, 'TestClass'), "Module should have TestClass"
        assert hasattr(module, 'test_function'), "Module should have test_function"
        assert hasattr(module, 'TEST_CONSTANT'), "Module should have TEST_CONSTANT"
        
        # Test they work
        obj = module.TestClass()
        assert obj.value == 42, "TestClass.value should be 42"
        assert module.test_function() == "test", "test_function should return 'test'"
        
        print("  ✓ Simple module loaded via exec() works correctly")
        return True
    except Exception as e:
        print(f"  ✗ Failed to exec simple module: {e}")
        return False


def test_sys_modules_registration():
    """Test that sys.modules registration allows imports from other modules."""
    print("\n=== TEST: sys.modules registration ===")
    
    # Create a mock module
    mock_module_code = """
VALUE = "from_mock"
ANSWER = 42
"""
    
    try:
        # Register mock_data in sys.modules
        mock_data = ModuleType("mock_data")
        exec(mock_module_code, mock_data.__dict__)
        sys.modules["mock_data"] = mock_data
        
        # Now create a module that imports from mock_data
        dependent_code = """
from mock_data import VALUE, ANSWER

class Dependent:
    data = VALUE
    answer = ANSWER
"""
        
        dependent = ModuleType("dependent")
        exec(dependent_code, dependent.__dict__)
        sys.modules["dependent"] = dependent
        
        # Verify it worked
        assert dependent.Dependent.data == "from_mock", "Should access VALUE from mock_data"
        assert dependent.Dependent.answer == 42, "Should access ANSWER from mock_data"
        
        print("  ✓ Modules in sys.modules can import from each other")
        
        # Clean up
        del sys.modules["mock_data"]
        del sys.modules["dependent"]
        
        return True
    except Exception as e:
        print(f"  ✗ Failed sys.modules test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("HTTP MODULE LOADING TESTS")
    print("=" * 70)
    
    results = {
        "http_simulation": test_load_module_from_http_simulation(),
        "real_files": test_http_module_loading_with_real_files(),
        "fallback_chain": test_fallback_import_chain(),
        "http_server": test_http_server_accessibility(),
        "exec_independence": test_module_exec_independence(),
        "sys_modules": test_sys_modules_registration(),
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
        print("\n✓ All HTTP module loading tests passed!")
        print("   The workaround should work in the browser.")
    else:
        print("\n✗ Some tests failed - see details above.")
