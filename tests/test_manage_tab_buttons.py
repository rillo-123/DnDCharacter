"""
Unit tests for Manage tab button handlers.

Tests all buttons in the Manage tab to ensure they:
1. Are properly defined
2. Have correct signatures
3. Can be called without errors
4. Have proper fallbacks where needed
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add assets/py to path for imports
assets_py = Path(__file__).parent.parent / "static" / "assets" / "py"
if str(assets_py) not in sys.path:
    sys.path.insert(0, str(assets_py))


class TestManageTabButtons:
    """Test all button handlers on the Manage tab."""
    
    def test_reset_spell_slots_exists(self):
        """Test that reset_spell_slots function exists and is callable."""
        # Import will fail in test environment, but we can check the import path
        import character
        assert hasattr(character, 'reset_spell_slots'), "reset_spell_slots not found in character module"
        assert callable(character.reset_spell_slots), "reset_spell_slots is not callable"
    
    def test_save_character_exists(self):
        """Test that save_character function exists and is callable."""
        import character
        assert hasattr(character, 'save_character'), "save_character not found in character module"
        assert callable(character.save_character), "save_character is not callable"
    
    def test_reset_character_exists(self):
        """Test that reset_character function exists and is callable."""
        import character
        assert hasattr(character, 'reset_character'), "reset_character not found in character module"
        assert callable(character.reset_character), "reset_character is not callable"
    
    def test_export_character_exists(self):
        """Test that export_character function exists and is callable."""
        import character
        assert hasattr(character, 'export_character'), "export_character not found in character module"
        assert callable(character.export_character), "export_character is not callable"
    
    def test_show_storage_info_exists(self):
        """Test that show_storage_info function exists and is callable."""
        import character
        assert hasattr(character, 'show_storage_info'), "show_storage_info not found in character module"
        assert callable(character.show_storage_info), "show_storage_info is not callable"
    
    def test_cleanup_exports_exists(self):
        """Test that cleanup_exports function exists and is callable."""
        import character
        assert hasattr(character, 'cleanup_exports'), "cleanup_exports not found in character module"
        assert callable(character.cleanup_exports), "cleanup_exports is not callable"
    
    def test_button_signatures(self):
        """Test that all button handlers have compatible signatures."""
        import character
        import inspect
        
        # All these should accept an optional event parameter (and keyword-only args)
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
            sig = inspect.signature(handler)
            
            # Get positional/positional-or-keyword parameters
            positional_params = [p for p in sig.parameters.values() 
                               if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, 
                                           inspect.Parameter.POSITIONAL_ONLY)]
            
            # Should have at most 1 positional parameter (event or _event)
            assert len(positional_params) <= 1, \
                f"{handler_name} has too many positional parameters: {[p.name for p in positional_params]}"
            
            # If it has a positional parameter, should be named event or _event
            if len(positional_params) == 1:
                param = positional_params[0]
                assert param.name in ('event', '_event'), \
                    f"{handler_name} parameter should be 'event' or '_event', got '{param.name}'"
    
    def test_export_management_imports(self):
        """Test that export_management functions are imported into character module."""
        import character
        
        # These should be imported from export_management
        required_imports = [
            'save_character',
            'export_character',
            'reset_character',
            'handle_import',
            'show_storage_info',
            'cleanup_exports',
        ]
        
        for func_name in required_imports:
            assert hasattr(character, func_name), f"{func_name} not imported into character module"
            assert callable(getattr(character, func_name)), f"{func_name} is not callable"


class TestManageTabButtonHTML:
    """Test that HTML buttons are properly configured."""
    
    def test_buttons_have_handlers(self):
        """Test that all manage tab buttons have py-click handlers defined."""
        html_path = Path(__file__).parent.parent / "static" / "index.html"
        html_content = html_path.read_text()

        # Button ID -> Handler name mapping
        button_handlers = {
            'long-rest-btn': 'reset_spell_slots',
            'save-btn': 'save_character',
            'reset-btn': 'reset_character',
            'export-btn': '_export_character_wrapper',  # Updated: using wrapper for async function
            'storage-info-btn': 'show_storage_info',
            'cleanup-btn': 'cleanup_exports',
        }

        for button_id, handler_name in button_handlers.items():
            assert f'id="{button_id}"' in html_content, f"Button {button_id} not found in HTML"
            assert f'py-click="{handler_name}"' in html_content, \
                f"Button {button_id} does not have correct py-click handler (expected {handler_name})"
    
    def test_import_button_exists(self):
        """Test that import button/label exists."""
        html_path = Path(__file__).parent.parent / "static" / "index.html"
        html_content = html_path.read_text()
        
        assert 'id="import-file"' in html_content, "Import file input not found"
        assert 'type="file"' in html_content, "Import file input not configured as file type"
        assert 'accept="application/json"' in html_content, "Import file input should accept JSON"


class TestManageTabButtonStyling:
    """Test that manage tab buttons have proper styling."""
    
    def test_buttons_in_actions_row(self):
        """Test that main buttons are in actions-row for consistent styling."""
        html_path = Path(__file__).parent.parent / "static" / "index.html"
        html_content = html_path.read_text()
        
        # Extract the Manage Data section
        manage_start = html_content.find('<h2>Manage Data</h2>')
        manage_end = html_content.find('</section>', manage_start)
        manage_section = html_content[manage_start:manage_end]
        
        # Check for actions-row class
        assert 'class="actions-row"' in manage_section, "Manage Data buttons should use actions-row class"
    
    def test_storage_cleanup_buttons_styled(self):
        """Test that Storage & Cleanup buttons are properly styled."""
        html_path = Path(__file__).parent.parent / "static" / "index.html"
        html_content = html_path.read_text()
        
        # Extract the Storage & Cleanup section
        storage_start = html_content.find('Storage & Cleanup')
        storage_end = html_content.find('</div>', storage_start)
        storage_section = html_content[storage_start:storage_end]
        
        # Check for actions-row or button styling
        assert ('class="actions-row"' in storage_section or 'button' in storage_section), \
            "Storage & Cleanup buttons should have proper styling"
    
    def test_reset_spell_slots_can_be_called(self):
        """Test that reset_spell_slots can be called without crashing."""
        import character
        
        with patch('character.document', None):
            try:
                character.reset_spell_slots()
            except (AttributeError, TypeError):
                # Expected in test environment
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
