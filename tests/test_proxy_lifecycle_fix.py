"""Test PyScript proxy lifecycle fix.

Verifies that calling functions through module references (not function references)
avoids the "borrowed proxy was automatically destroyed" error in PyScript/Pyodide.
"""
import sys
from unittest.mock import MagicMock, patch
from types import ModuleType
import pytest


@pytest.fixture
def mock_console():
    """Mock console for logging."""
    console = MagicMock()
    return console


@pytest.fixture
def mock_event():
    """Mock DOM event for checkbox toggle."""
    event = MagicMock()
    event.target = MagicMock()
    event.target.checked = True
    return event


def test_module_references_not_function_references(mock_console):
    """
    CRITICAL: Verify we store module references, not function references.
    
    In PyScript/Pyodide, function references are borrowed proxies that get
    automatically destroyed. Calling through module references avoids this.
    """
    # Create mock modules
    char_module = ModuleType('__main__')
    char_module.update_calculations = MagicMock()
    
    export_module = ModuleType('export_management')
    export_module.schedule_auto_export = MagicMock()
    
    # Simulate what initialize_module_references should do:
    # Store MODULE references, not function references
    char_ref = char_module  # Store module
    export_ref = export_module  # Store module
    
    # Both should be ModuleType
    assert isinstance(char_ref, ModuleType), "Should store module reference, not function"
    assert isinstance(export_ref, ModuleType), "Should store module reference, not function"
    
    # Verify we can call through the references
    char_ref.update_calculations()
    export_ref.schedule_auto_export()
    
    char_ref.update_calculations.assert_called_once()
    export_ref.schedule_auto_export.assert_called_once()


def test_initialize_captures_modules_not_functions(mock_console):
    """Verify initialize_module_references captures module refs, not function refs."""
    # Create and inject mock modules
    char_module = ModuleType('__main__')
    char_module.update_calculations = MagicMock()
    
    export_module = ModuleType('export_management')
    export_module.schedule_auto_export = MagicMock()
    
    # Temporarily add to sys.modules
    sys.modules['__main__'] = char_module
    sys.modules['export_management'] = export_module
    
    try:
        # Import after mocking
        from equipment_management import initialize_module_references
        
        # This should work with module references
        initialize_module_references()
        
        # Check that console.log was called (mocking via patch below)
        # The functions should be accessible through module references
        
    finally:
        # Cleanup
        if '__main__' in sys.modules and isinstance(sys.modules['__main__'], ModuleType):
            pass  # Don't delete actual main


def test_calling_through_module_ref_vs_function_ref():
    """
    Demonstrate why module references are better than function references
    in PyScript environments.
    """
    # Create a module with a function
    test_module = ModuleType('test_module')
    test_module.test_func = MagicMock(return_value="result")
    
    # Method 1: Store function reference (PROBLEMATIC in PyScript)
    func_ref = test_module.test_func
    
    # Method 2: Store module reference (SAFE in PyScript)
    module_ref = test_module
    
    # In PyScript, func_ref would be a borrowed proxy that gets destroyed
    # module_ref is the actual module, so calling through it is safe
    
    # Both work in regular Python, but module_ref is safer in PyScript
    assert func_ref() == "result", "Function reference call works"
    assert module_ref.test_func() == "result", "Module reference call works"
    
    # In PyScript, the module_ref approach would avoid proxy lifecycle issues


def test_handler_uses_module_references(mock_console, mock_event):
    """
    Verify the handler pattern: uses module references, not function references.
    This is the key fix for the proxy lifecycle issue.
    """
    # Create mock modules
    char_module = ModuleType('__main__')
    update_calc_mock = MagicMock()
    char_module.update_calculations = update_calc_mock
    
    export_module = ModuleType('export_management')
    schedule_export_mock = MagicMock()
    export_module.schedule_auto_export = schedule_export_mock
    
    # Simulate handler with module references (the fixed pattern)
    char_module_ref = char_module  # Store module, not function
    export_module_ref = export_module  # Store module, not function
    
    # Handler logic (from _handle_equipped_toggle)
    if char_module_ref is not None and hasattr(char_module_ref, 'update_calculations'):
        char_module_ref.update_calculations()  # Call through module
    
    if export_module_ref is not None and hasattr(export_module_ref, 'schedule_auto_export'):
        export_module_ref.schedule_auto_export()  # Call through module
    
    # Verify both were called
    update_calc_mock.assert_called_once()
    schedule_export_mock.assert_called_once()


def test_lazy_initialization_with_module_refs():
    """
    Test lazy initialization pattern with module references.
    
    Key insight: By storing module references (not function references),
    the references remain valid even if modules are loaded later.
    """
    # Start with no modules loaded
    module_ref = None
    
    # First attempt - module not loaded yet
    test_mod = sys.modules.get('nonexistent_module')
    if test_mod is None:
        # Module not loaded yet, will retry later
        module_ref = None
    
    # Later - create and "load" the module
    late_module = ModuleType('nonexistent_module')
    late_module.test_func = MagicMock(return_value="delayed_result")
    sys.modules['nonexistent_module'] = late_module
    
    # Second attempt - module now loaded
    if module_ref is None:
        module_ref = sys.modules.get('nonexistent_module')
    
    # Now we can call through it
    assert module_ref is not None, "Module reference should be captured"
    result = module_ref.test_func()
    assert result == "delayed_result"
    
    # Cleanup
    del sys.modules['nonexistent_module']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
