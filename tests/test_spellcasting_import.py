"""Test that spellcasting module imports correctly and spell sanitization works."""
import sys
import os

# Add the assets/py directory to the path so we can import character module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'assets', 'py'))

# Mock the PyScript/JS dependencies before importing
class MockConsole:
    @staticmethod
    def log(*args): pass
    @staticmethod
    def warn(*args): pass
    @staticmethod
    def error(*args): pass

class MockDocument:
    pass

class MockWindow:
    pass

sys.modules['js'] = type(sys)('js')
sys.modules['js'].console = MockConsole()
sys.modules['js'].document = MockDocument()
sys.modules['js'].window = MockWindow()

# Now we can import
from character_models import CharacterFactory
from spell_data import (
    LOCAL_SPELLS_FALLBACK,
    SPELL_CLASS_SYNONYMS,
    SPELL_CLASS_DISPLAY_NAMES,
)


def test_spell_class_synonyms_not_empty():
    """Test that SPELL_CLASS_SYNONYMS is populated."""
    assert len(SPELL_CLASS_SYNONYMS) > 0, "SPELL_CLASS_SYNONYMS should not be empty"
    assert "wizard" in SPELL_CLASS_SYNONYMS, "wizard should be in SPELL_CLASS_SYNONYMS"
    assert "cleric" in SPELL_CLASS_SYNONYMS, "cleric should be in SPELL_CLASS_SYNONYMS"
    print(f"[PASS] SPELL_CLASS_SYNONYMS has {len(SPELL_CLASS_SYNONYMS)} entries")


def test_spell_class_display_names_not_empty():
    """Test that SPELL_CLASS_DISPLAY_NAMES is populated."""
    assert len(SPELL_CLASS_DISPLAY_NAMES) > 0, "SPELL_CLASS_DISPLAY_NAMES should not be empty"
    assert "wizard" in SPELL_CLASS_DISPLAY_NAMES, "wizard should be in SPELL_CLASS_DISPLAY_NAMES"
    print(f"[PASS] SPELL_CLASS_DISPLAY_NAMES has {len(SPELL_CLASS_DISPLAY_NAMES)} entries")


def test_spellcasting_manager_imports():
    """Test that spellcasting module can be imported."""
    try:
        from spellcasting_manager import SpellcastingManager, SPELL_LIBRARY_STATE
        assert SpellcastingManager is not None, "SpellcastingManager should not be None"
        assert SPELL_LIBRARY_STATE is not None, "SPELL_LIBRARY_STATE should not be None"
        print("[PASS] SpellcastingManager imports successfully")
    except ImportError as e:
        raise AssertionError(f"Failed to import spellcasting_manager: {e}")


def test_character_module_with_spellcasting():
    """Test that character module imports with spellcasting."""
    try:
        from character import SPELLCASTING_MANAGER, SUPPORTED_SPELL_CLASSES
        # SPELLCASTING_MANAGER might be None if spellcasting import failed, but we should have SUPPORTED_SPELL_CLASSES
        assert len(SUPPORTED_SPELL_CLASSES) > 0, "SUPPORTED_SPELL_CLASSES should not be empty"
        print("[PASS] character module imported successfully")
        print(f"    SUPPORTED_SPELL_CLASSES: {SUPPORTED_SPELL_CLASSES}")
        if SPELLCASTING_MANAGER is not None:
            print(f"    SPELLCASTING_MANAGER is available")
        else:
            print(f"    WARNING: SPELLCASTING_MANAGER is None (spellcasting import may have failed)")
    except ImportError as e:
        raise AssertionError(f"Failed to import character with spellcasting: {e}")


def test_normalize_class_token():
    """Test that normalize_class_token works correctly."""
    from character import normalize_class_token
    
    # Test basic class names
    assert normalize_class_token("Wizard") == "wizard", "Wizard should normalize to wizard"
    assert normalize_class_token("CLERIC") == "cleric", "CLERIC should normalize to cleric"
    assert normalize_class_token("bard") == "bard", "bard should normalize to bard"
    
    # Test with extra spaces
    assert normalize_class_token("  Wizard  ") == "wizard", "Wizard with spaces should normalize to wizard"
    
    # Test with dashes (gets converted to spaces, but "cleric domain" isn't a recognized class, so returns None)
    result = normalize_class_token("Cleric-Domain")
    assert result is None or result == "cleric", f"Cleric-Domain should return None or cleric, got {result}"
    
    print("[PASS] normalize_class_token works correctly")


def test_sanitize_spell_record_with_open5e_format():
    """Test sanitizing a spell with Open5e format data."""
    from character import sanitize_spell_record
    
    # Create a mock Open5e spell
    open5e_spell = {
        "slug": "magic-missile",
        "name": "Magic Missile",
        "level": 1,
        "level_int": 1,
        "school": "evocation",
        "dnd_class": "Sorcerer, Wizard",
        "spell_lists": ["sorcerer", "wizard"],
        "casting_time": "1 action",
        "range": "120 feet",
        "components": "V, S",
        "duration": "Instantaneous",
        "concentration": False,
        "ritual": False,
        "desc": "A missile of magical force darts all the way up to 120 feet in a straight line toward a target you can see.",
        "document__title": "PHB",
        "document__slug": "players-handbook",
    }
    
    # Sanitize it
    result = sanitize_spell_record(open5e_spell)
    
    # Should not be None
    assert result is not None, "sanitize_spell_record should return a spell, not None"
    
    # Should have expected fields
    assert result.get("slug") == "magic-missile", "slug should be preserved"
    assert result.get("name") == "Magic Missile", "name should be preserved"
    assert len(result.get("classes", [])) > 0, "classes should not be empty"
    
    print(f"[PASS] sanitize_spell_record works: {result.get('name')} has classes {result.get('classes')}")


def test_sanitize_spell_list():
    """Test sanitizing a list of spells."""
    from character import sanitize_spell_list
    
    # Create mock Open5e spells
    spells = [
        {
            "slug": "magic-missile",
            "name": "Magic Missile",
            "level": 1,
            "level_int": 1,
            "school": "evocation",
            "dnd_class": "Sorcerer, Wizard",
            "casting_time": "1 action",
            "range": "120 feet",
            "components": "V, S",
            "duration": "Instantaneous",
            "document__title": "PHB",
        },
        {
            "slug": "shield",
            "name": "Shield",
            "level": 1,
            "level_int": 1,
            "school": "abjuration",
            "dnd_class": "Wizard",
            "casting_time": "1 reaction",
            "range": "Self",
            "components": "V, S",
            "duration": "1 round",
            "document__title": "PHB",
        },
    ]
    
    # Sanitize the list
    result = sanitize_spell_list(spells)
    
    # Should have both spells
    assert len(result) == 2, f"Should have 2 spells, got {len(result)}"
    
    # Check first spell
    assert result[0]["slug"] == "magic-missile", "First spell should be magic-missile"
    assert len(result[0]["classes"]) > 0, "magic-missile should have classes"
    
    print(f"[PASS] sanitize_spell_list works: {len(result)} spells sanitized successfully")


if __name__ == '__main__':
    print("\n=== Testing Spellcasting Module ===\n")
    
    test_spell_class_synonyms_not_empty()
    test_spell_class_display_names_not_empty()
    test_spellcasting_manager_imports()
    test_character_module_with_spellcasting()
    test_normalize_class_token()
    test_sanitize_spell_record_with_open5e_format()
    test_sanitize_spell_list()
    
    print("\n[SUCCESS] All spellcasting import tests passed!\n")
