"""
Test that all main modules can be imported without errors.
This catches missing module imports that tests might not detect.
"""
import sys
from pathlib import Path
import pytest

# Add the static/assets/py directory to the path
py_dir = Path(__file__).parent.parent / "static" / "assets" / "py"
sys.path.insert(0, str(py_dir))


def test_character_module_imports():
    """Test that character.py can be imported without errors."""
    # character.py executes code at module level, so we skip this test
    # It would need a full browser environment to run properly
    pytest.skip("character.py executes code at module level requiring browser environment")


def test_equipment_management_imports():
    """Test that equipment_management.py can be imported without errors."""
    try:
        import equipment_management
        assert equipment_management is not None
    except ModuleNotFoundError as e:
        pytest.fail(f"equipment_management.py has import error: {e}")


def test_inventory_manager_imports():
    """Test that inventory_manager can be imported without errors."""
    try:
        from managers import inventory_manager
        assert inventory_manager is not None
    except (ModuleNotFoundError, ImportError) as e:
        pytest.fail(f"inventory_manager import error: {e}")


def test_equipment_event_manager_imports():
    """Test that equipment_event_manager can be imported without errors."""
    try:
        from managers import equipment_event_manager
        assert equipment_event_manager is not None
    except (ModuleNotFoundError, ImportError) as e:
        pytest.fail(f"equipment_event_manager import error: {e}")


def test_armor_manager_imports():
    """Test that armor_manager can be imported without errors."""
    try:
        from managers import armor_manager
        assert armor_manager is not None
    except (ModuleNotFoundError, ImportError) as e:
        pytest.fail(f"armor_manager import error: {e}")


def test_weapons_manager_imports():
    """Test that weapons_manager can be imported without errors."""
    try:
        from managers import weapons_manager
        assert weapons_manager is not None
    except (ModuleNotFoundError, ImportError) as e:
        pytest.fail(f"weapons_manager import error: {e}")


def test_spellcasting_manager_imports():
    """Test that spellcasting_manager can be imported without errors."""
    try:
        from managers import spellcasting_manager
        assert spellcasting_manager is not None
    except (ModuleNotFoundError, ImportError) as e:
        pytest.fail(f"spellcasting_manager import error: {e}")


def test_export_management_imports():
    """Test that export_management.py can be imported without errors."""
    try:
        import export_management
        assert export_management is not None
    except ModuleNotFoundError as e:
        pytest.fail(f"export_management.py has import error: {e}")
