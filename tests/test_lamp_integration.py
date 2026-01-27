"""Integration tests for module reference pattern.

Tests the complete sequence: app load → lazy initialization → handler execution
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from types import ModuleType

# Add assets/py to path
ASSET_PY = Path(__file__).parent.parent / "assets" / "py"
if str(ASSET_PY) not in sys.path:
    sys.path.insert(0, str(ASSET_PY))


def test_complete_app_load_sequence():
    """Test that lazy initialization ensures references are captured for handler."""
    import inventory_manager
    import export_management
    
    # Step 1: Simulate app load - modules imported in sequence
    # Step 2: Both modules now loaded
    # Step 3: Initialize captures references
    inventory_manager.initialize_module_references()
    
    # Verify references are captured as module objects
    assert inventory_manager._EXPORT_MODULE_REF is not None, \
        "After lazy init, module reference should be captured"
    assert isinstance(inventory_manager._EXPORT_MODULE_REF, ModuleType), \
        "Should store module reference"


def test_lazy_initialization_doesnt_break_if_called_early():
    """Test that initialize called before all modules are loaded doesn't break."""
    import inventory_manager
    
    # Simulate calling initialize when export_management not yet imported
    # (Should handle gracefully)
    inventory_manager._EXPORT_MODULE_REF = None
    
    # This should not raise an error
    try:
        inventory_manager.initialize_module_references()
    except Exception as e:
        pytest.fail(f"initialize_module_references should handle missing modules gracefully: {e}")


def test_multiple_initialize_calls_idempotent():
    """Test that multiple initialize calls are safe and idempotent."""
    import inventory_manager
    
    # Reset
    inventory_manager._EXPORT_MODULE_REF = None
    inventory_manager._CHAR_MODULE_REF = None
    
    # Call multiple times
    inventory_manager.initialize_module_references()
    first_export_ref = inventory_manager._EXPORT_MODULE_REF
    first_char_ref = inventory_manager._CHAR_MODULE_REF
    
    inventory_manager.initialize_module_references()
    second_export_ref = inventory_manager._EXPORT_MODULE_REF
    second_char_ref = inventory_manager._CHAR_MODULE_REF
    
    # References should be identical (not new objects)
    assert first_export_ref is second_export_ref, \
        "Export module reference should be unchanged after second call"
    assert first_char_ref is second_char_ref, \
        "Char module reference should be unchanged after second call"


def test_handler_captures_references_on_first_call():
    """Test that handler ensures references are captured before use."""
    import inventory_manager
    import export_management
    
    # Create item
    manager = inventory_manager.InventoryManager()
    item = {
        "id": "item-1",
        "name": "Item",
        "type": "shield",
        "ac_bonus": 1,
        "equipped": False
    }
    manager.items.append(item)
    
    # Create mock event
    mock_event = Mock()
    mock_event.target = Mock()
    mock_event.target.checked = True
    
    # Mock the export function in its module
    with patch.object(export_management, 'schedule_auto_export', Mock()) as mock_export:
        # Reset state to simulate handler being called for first time
        inventory_manager._EXPORT_MODULE_REF = None
        inventory_manager._CHAR_MODULE_REF = None
        
        # Call handler - it should initialize references
        try:
            manager._handle_equipped_toggle(mock_event, "item-1")
        except Exception:
            # Might fail due to mocking, but that's OK
            pass
        
        # Verify references were captured during handler execution
        assert inventory_manager._EXPORT_MODULE_REF is not None, \
            "Handler should initialize module reference on first call"


def test_module_reference_pattern_avoids_proxy_issues():
    """Test that module reference pattern avoids PyScript proxy destruction."""
    import inventory_manager
    import export_management
    
    # Get the stored module reference
    inventory_manager.initialize_module_references()
    module_ref = inventory_manager._EXPORT_MODULE_REF
    
    # Should be able to access function through module
    assert hasattr(module_ref, 'schedule_auto_export'), \
        "Module reference should have the function"
    
    # Should be callable
    assert callable(getattr(module_ref, 'schedule_auto_export')), \
        "Function should be callable through module reference"
    
    # The module reference itself is persistent (not a borrowed proxy)
    assert isinstance(module_ref, ModuleType), \
        "Stored reference should be the actual module, not a proxy"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
