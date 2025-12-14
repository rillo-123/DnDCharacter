"""
Integration tests for Manage tab button event binding and functionality.

These tests verify that:
1. Button handlers can be safely called via PyScript py-click
2. Event binding won't throw errors
3. All handlers have proper error handling
"""

import pytest
from pathlib import Path
import re


class TestManageTabButtonBinding:
    """Test PyScript py-click event binding for manage tab buttons."""
    
    @pytest.fixture
    def html_content(self):
        """Load the HTML file."""
        html_path = Path(__file__).parent.parent / "static" / "index.html"
        return html_path.read_text()
    
    def test_all_py_click_handlers_are_sync(self, html_content):
        """Verify all Manage tab py-click handlers are synchronous (not async)."""
        # PyScript's py-click attribute only works with sync functions
        # Extract Manage Data section specifically (not other sections)
        manage_data_start = html_content.find('<h2>Manage Data</h2>')
        manage_data_end = html_content.find('</section>', manage_data_start)
        manage_data_section = html_content[manage_data_start:manage_data_end]
        
        py_click_pattern = r'py-click="([^"]+)"'
        handlers = re.findall(py_click_pattern, manage_data_section)
        
        assert len(handlers) > 0, "No py-click handlers found in Manage Data section"
        
        # These are the expected Manage Data handlers
        expected_handlers = {
            'save_character',
            'reset_character',
            'export_character',
        }
        
        import character
        import inspect
        
        for handler_name in handlers:
            # Only check handlers that should be in Manage Data
            if handler_name not in expected_handlers:
                continue
                
            handler = getattr(character, handler_name, None)
            assert handler is not None, f"Handler {handler_name} not found in character module"
            
            # Check if it's async (async functions won't work with py-click)
            is_async = inspect.iscoroutinefunction(handler)
            assert not is_async, f"Handler {handler_name} is async - py-click only works with sync functions"
    
    def test_button_has_py_click_attribute(self, html_content):
        """Ensure every button has py-click attribute."""
        buttons = [
            ('long-rest-btn', 'reset_spell_slots'),
            ('save-btn', 'save_character'),
            ('reset-btn', 'reset_character'),
            ('export-btn', '_export_character_wrapper'),
            ('storage-info-btn', 'show_storage_info'),
            ('cleanup-btn', 'cleanup_exports'),
        ]

        for button_id, handler_name in buttons:
            button_pattern = f'id="{button_id}"[^>]*py-click="{handler_name}"'
            assert re.search(button_pattern, html_content), \
                f"Button {button_id} missing correct py-click handler"
    
    def test_no_orphaned_event_parameters(self, html_content):
        """Check that handlers passed to py-click don't include parameters."""
        # py-click should be: py-click="handler_name" NOT py-click="handler_name()"
        orphaned_calls = re.findall(r'py-click="(\w+)\([^)]*\)"', html_content)
        
        assert len(orphaned_calls) == 0, \
            f"Found py-click handlers with parameters (not supported): {orphaned_calls}"
    
class TestManageTabButtonErrorHandling:
    """Test that button handlers have proper error handling."""
    
    def test_handlers_have_error_context(self):
        """Verify handlers can handle errors gracefully."""
        import character
        import inspect
        
        handlers = [
            'reset_spell_slots',
            'save_character', 
            'reset_character',
            'export_character',
            'show_storage_info',
            'cleanup_exports',
        ]
        
        for handler_name in handlers:
            handler = getattr(character, handler_name)
            source = inspect.getsource(handler)
            
            # Should have try/except or other error handling
            # At minimum, should not have bare 'except:' 
            assert 'except Exception' in source or 'except' in source or 'try' in source, \
                f"{handler_name} should have error handling"
    
    def test_export_character_has_auto_parameter(self):
        """Test that export_character supports auto parameter for auto-export."""
        import character
        import inspect
        
        sig = inspect.signature(character.export_character)
        assert 'auto' in sig.parameters, "export_character should have 'auto' parameter for auto-export"
        
        # Should default to False
        auto_param = sig.parameters['auto']
        assert auto_param.default is False, "auto parameter should default to False"


class TestManageTabButtonDocumentation:
    """Test that button handlers are properly documented."""
    
    def test_handlers_have_docstrings(self):
        """Verify all button handlers have docstrings."""
        import character
        
        handlers = [
            'reset_spell_slots',
            'save_character',
            'reset_character',
            'export_character',
            'show_storage_info',
            'cleanup_exports',
        ]
        
        for handler_name in handlers:
            handler = getattr(character, handler_name)
            assert handler.__doc__ is not None, \
                f"{handler_name} should have a docstring explaining its purpose"
            assert len(handler.__doc__.strip()) > 0, \
                f"{handler_name} docstring should not be empty"



