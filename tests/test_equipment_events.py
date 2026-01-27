"""
Test Equipment Event System

Tests that all events from the equipment table generate correct events
and trigger appropriate manager methods.

Event Flow:
    User Action → DOM Event → Event Listener → Manager Method → Data Update → GUI Redraw
"""

import sys
import os
import unittest
import json
from unittest.mock import Mock, MagicMock, patch, call

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'py'))

# Mock browser modules ONLY for this test file
_original_js = sys.modules.get('js')
_original_pyodide = sys.modules.get('pyodide')
_original_pyodide_ffi = sys.modules.get('pyodide.ffi')
_original_armor = sys.modules.get('armor_manager')
_original_character = sys.modules.get('character')

# Temporarily mock browser modules
sys.modules['js'] = MagicMock()
sys.modules['pyodide'] = MagicMock()
sys.modules['pyodide.ffi'] = MagicMock()

# Mock armor_manager and character modules for event handler imports
mock_armor_manager = MagicMock()
mock_armor_manager.set_armor_bonus = Mock(return_value=True)
sys.modules['armor_manager'] = mock_armor_manager

mock_character = MagicMock()
mock_character.update_calculations = Mock()
sys.modules['character'] = mock_character

# Now import the module under test
from equipment_event_manager import EquipmentEventListener


def tearDownModule():
    """Restore original modules and clear equipment_event_manager from cache."""
    # Remove equipment_event_manager from cache so other tests import it fresh
    if 'equipment_event_manager' in sys.modules:
        del sys.modules['equipment_event_manager']
    
    # Restore original modules
    if _original_js is not None:
        sys.modules['js'] = _original_js
    elif 'js' in sys.modules:
        del sys.modules['js']
    
    if _original_pyodide is not None:
        sys.modules['pyodide'] = _original_pyodide
    elif 'pyodide' in sys.modules:
        del sys.modules['pyodide']
    
    if _original_pyodide_ffi is not None:
        sys.modules['pyodide.ffi'] = _original_pyodide_ffi
    elif 'pyodide.ffi' in sys.modules:
        del sys.modules['pyodide.ffi']
    
    if _original_armor is not None:
        sys.modules['armor_manager'] = _original_armor
    elif 'armor_manager' in sys.modules:
        del sys.modules['armor_manager']
    
    if _original_character is not None:
        sys.modules['character'] = _original_character
    elif 'character' in sys.modules:
        del sys.modules['character']


class MockInventoryManager:
    """Mock inventory manager for testing."""
    
    def __init__(self, items=None):
        self.items = items or []
        
        # Mock all event handler methods
        self._handle_bonus_change = Mock()
        self._handle_item_toggle = Mock()
        self._handle_item_remove = Mock()
        self._handle_qty_change = Mock()
        self._handle_category_change = Mock()
        self._handle_equipped_toggle = Mock()
        self._handle_modifier_change = Mock()
        self._handle_armor_only_toggle = Mock()
        
        # Mock redraw methods
        self.redraw_armor_items = Mock()
        self.render_inventory = Mock()
    
    def get_item(self, item_id):
        """Get item by ID."""
        for item in self.items:
            if item.get("id") == item_id:
                return item
        return None
    
    def update_item(self, item_id, updates):
        """Update item."""
        for item in self.items:
            if item.get("id") == item_id:
                item.update(updates)
                return True
        return False


class MockEvent:
    """Mock DOM event."""
    
    def __init__(self, target_value="", target_checked=False, target_attrs=None):
        self.target = Mock()
        self.target.value = target_value
        self.target.checked = target_checked
        self.target.getAttribute = lambda key: (target_attrs or {}).get(key)


class TestEquipmentEventListenerInitialization(unittest.TestCase):
    """Test event listener initialization."""
    
    def test_listener_initializes_with_inventory_manager(self):
        """Event listener should store reference to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        assert listener.inventory_manager == inventory
    
    def test_listener_initializes_update_flag_to_false(self):
        """Event listener should initialize _is_updating flag to False."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        assert listener._is_updating is False
    
    def test_listener_can_be_created_without_errors(self):
        """Event listener creation should not raise exceptions."""
        inventory = MockInventoryManager()
        try:
            listener = EquipmentEventListener(inventory)
            assert listener is not None
        except Exception as e:
            self.fail(f"Event listener initialization raised exception: {e}")


class TestBonusChangeEvent(unittest.TestCase):
    """Test bonus change event handling."""
    
    def test_bonus_change_parses_integer_value(self):
        """Bonus change should parse integer from input."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="2", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        # Should call set_armor_bonus with parsed integer
        mock_armor_manager.set_armor_bonus.assert_called_once()
        args = mock_armor_manager.set_armor_bonus.call_args[0]
        assert args[1] == "armor1"  # item_id
        assert args[2] == 2  # bonus value as int
    
    def test_bonus_change_handles_empty_value(self):
        """Empty bonus value should default to 0."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        args = mock_armor_manager.set_armor_bonus.call_args[0]
        assert args[2] == 0  # Should default to 0
    
    def test_bonus_change_handles_invalid_value(self):
        """Invalid bonus value should default to 0."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="abc", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        args = mock_armor_manager.set_armor_bonus.call_args[0]
        assert args[2] == 0  # Should default to 0
    
    def test_bonus_change_armor_calls_set_armor_bonus(self):
        """Bonus change on armor should call set_armor_bonus."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        # Reset mock before test
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        mock_armor_manager.set_armor_bonus.assert_called_once_with(inventory, "armor1", 1)
    
    def test_bonus_change_armor_triggers_redraw(self):
        """Bonus change on armor should trigger inventory redraw."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.return_value = True
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        inventory.redraw_armor_items.assert_called_once()
    
    def test_bonus_change_armor_triggers_calculations(self):
        """Bonus change on armor should trigger AC recalculation."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.return_value = True
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        mock_character.update_calculations.assert_called_once()
    
    def test_bonus_change_weapon_delegates_to_inventory(self):
        """Bonus change on weapon should delegate to inventory manager."""
        inventory = MockInventoryManager([
            {"id": "weapon1", "category": "Weapon", "name": "Longsword +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "weapon1"})
        
        listener.on_bonus_change(event, "weapon1")
        
        inventory._handle_bonus_change.assert_called_once_with(event, "weapon1")
    
    def test_bonus_change_item_not_found(self):
        """Bonus change on non-existent item should handle gracefully."""
        inventory = MockInventoryManager([])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "missing"})
        
        # Should not raise exception
        try:
            listener.on_bonus_change(event, "missing")
        except Exception as e:
            self.fail(f"on_bonus_change raised exception: {e}")


class TestEventLoopPrevention(unittest.TestCase):
    """Test event loop prevention mechanism."""
    
    def test_is_updating_flag_prevents_reentrant_calls(self):
        """Event handler should skip when _is_updating is True."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        # Simulate programmatic update in progress
        listener._is_updating = True
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        # Should NOT call set_armor_bonus when updating
        mock_armor_manager.set_armor_bonus.assert_not_called()
    
    def test_is_updating_flag_set_during_update(self):
        """_is_updating flag should be set during update."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        flag_states = []
        
        def capture_flag(*args):
            flag_states.append(listener._is_updating)
            return True
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.side_effect = capture_flag
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        # Flag should have been True during set_armor_bonus call
        assert True in flag_states
        
        # Reset side_effect
        mock_armor_manager.set_armor_bonus.side_effect = None
        mock_armor_manager.set_armor_bonus.return_value = True
    
    def test_is_updating_flag_cleared_after_update(self):
        """_is_updating flag should be cleared after update completes."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.return_value = True
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        # Flag should be cleared after event completes
        assert listener._is_updating is False
    
    def test_is_updating_flag_cleared_on_exception(self):
        """_is_updating flag should be cleared even if exception occurs."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.side_effect = Exception("Test error")
        mock_character.update_calculations.reset_mock()
        
        try:
            listener.on_bonus_change(event, "armor1")
        except:
            pass
        
        # Flag should be cleared even after exception
        assert listener._is_updating is False
        
        # Reset side_effect
        mock_armor_manager.set_armor_bonus.side_effect = None
        mock_armor_manager.set_armor_bonus.return_value = True


class TestOtherEquipmentEvents(unittest.TestCase):
    """Test other equipment event handlers."""
    
    def test_toggle_item_delegates_to_inventory(self):
        """Toggle item should delegate to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent()
        listener.on_toggle_item(event, "item1")
        
        inventory._handle_item_toggle.assert_called_once_with(event, "item1")
    
    def test_remove_item_delegates_to_inventory(self):
        """Remove item should delegate to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent()
        listener.on_remove_item(event, "item1")
        
        inventory._handle_item_remove.assert_called_once_with(event, "item1")
    
    def test_qty_change_delegates_to_inventory(self):
        """Quantity change should delegate to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent()
        listener.on_qty_change(event, "item1")
        
        inventory._handle_qty_change.assert_called_once_with(event, "item1")
    
    def test_category_change_delegates_to_inventory(self):
        """Category change should delegate to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent()
        listener.on_category_change(event, "item1")
        
        inventory._handle_category_change.assert_called_once_with(event, "item1")
    
    def test_equipped_toggle_delegates_to_inventory(self):
        """Equipped toggle should delegate to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent()
        listener.on_equipped_toggle(event, "item1")
        
        inventory._handle_equipped_toggle.assert_called_once_with(event, "item1")
    
    def test_modifier_change_delegates_to_inventory(self):
        """Modifier change should delegate to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent()
        listener.on_modifier_change(event, "item1", "ac")
        
        inventory._handle_modifier_change.assert_called_once_with(event, "item1", "ac")
    
    def test_armor_only_toggle_delegates_to_inventory(self):
        """Armor only toggle should delegate to inventory manager."""
        inventory = MockInventoryManager()
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent()
        listener.on_armor_only_toggle(event, "item1")
        
        inventory._handle_armor_only_toggle.assert_called_once_with(event, "item1")


class TestEventChaining(unittest.TestCase):
    """Test that events trigger the full chain: event → manager → update → redraw."""
    
    def test_armor_bonus_change_full_chain(self):
        """Armor bonus change should trigger: set_armor_bonus → redraw → calculations."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="2", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.return_value = True
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        # Verify full chain
        mock_armor_manager.set_armor_bonus.assert_called_once()  # 1. Manager setter called
        inventory.redraw_armor_items.assert_called_once()  # 2. UI redrawn
        mock_character.update_calculations.assert_called_once()  # 3. Calculations updated
    
    def test_armor_bonus_change_order(self):
        """Armor bonus change should call methods in correct order."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        call_order = []
        
        def mock_set_bonus(*args):
            call_order.append("set_bonus")
            return True
        
        def mock_redraw():
            call_order.append("redraw")
        
        def mock_calc():
            call_order.append("calculations")
        
        inventory.redraw_armor_items = mock_redraw
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.side_effect = mock_set_bonus
        mock_character.update_calculations.reset_mock()
        mock_character.update_calculations.side_effect = mock_calc
        
        listener.on_bonus_change(event, "armor1")
        
        # Verify order: set_bonus → redraw → calculations
        assert call_order == ["set_bonus", "redraw", "calculations"]
        
        # Reset side_effects
        mock_armor_manager.set_armor_bonus.side_effect = None
        mock_armor_manager.set_armor_bonus.return_value = True
        mock_character.update_calculations.side_effect = None
    
    def test_failed_set_bonus_skips_redraw(self):
        """If set_armor_bonus fails, should not trigger redraw or calculations."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate +1"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.return_value = False  # Simulate failure
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        # Should NOT call redraw or calculations if setter failed
        inventory.redraw_armor_items.assert_not_called()
        mock_character.update_calculations.assert_not_called()
        
        # Reset return value
        mock_armor_manager.set_armor_bonus.return_value = True


class TestEventParameterExtraction(unittest.TestCase):
    """Test that events correctly extract parameters from DOM."""
    
    def test_extracts_item_id_from_data_attribute(self):
        """Event should extract item_id from data-item-bonus attribute."""
        inventory = MockInventoryManager([
            {"id": "test-item-123", "category": "Armor", "name": "Test Armor"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="1", target_attrs={"data-item-bonus": "test-item-123"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.return_value = True
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "test-item-123")
        
        # Verify correct item_id was passed
        args = mock_armor_manager.set_armor_bonus.call_args[0]
        assert args[1] == "test-item-123"
    
    def test_parses_positive_bonus_values(self):
        """Event should correctly parse positive bonus values."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Breastplate"}
        ])
        listener = EquipmentEventListener(inventory)
        
        for test_value in ["1", "2", "3", "10"]:
            event = MockEvent(target_value=test_value, target_attrs={"data-item-bonus": "armor1"})
            
            mock_armor_manager.set_armor_bonus.reset_mock()
            mock_armor_manager.set_armor_bonus.return_value = True
            mock_character.update_calculations.reset_mock()
            
            listener.on_bonus_change(event, "armor1")
            
            args = mock_armor_manager.set_armor_bonus.call_args[0]
            assert args[2] == int(test_value)
    
    def test_handles_negative_bonus_values(self):
        """Event should correctly parse negative bonus values."""
        inventory = MockInventoryManager([
            {"id": "armor1", "category": "Armor", "name": "Cursed Armor"}
        ])
        listener = EquipmentEventListener(inventory)
        
        event = MockEvent(target_value="-1", target_attrs={"data-item-bonus": "armor1"})
        
        mock_armor_manager.set_armor_bonus.reset_mock()
        mock_armor_manager.set_armor_bonus.return_value = True
        mock_character.update_calculations.reset_mock()
        
        listener.on_bonus_change(event, "armor1")
        
        args = mock_armor_manager.set_armor_bonus.call_args[0]
        assert args[2] == -1


if __name__ == "__main__":
    unittest.main()
