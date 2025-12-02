"""Test spell merging from fallback list into Open5e results."""
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
from spell_data import LOCAL_SPELLS_FALLBACK, SPELL_CLASS_DISPLAY_NAMES
from character import sanitize_spell_list


def test_fallback_spells_have_required_fields():
    """Test that all fallback spells have required fields."""
    required_fields = ['name', 'slug', 'level', 'dnd_class', 'document__title']
    
    for spell in LOCAL_SPELLS_FALLBACK:
        for field in required_fields:
            assert field in spell, f"Spell {spell.get('name', 'Unknown')} missing field: {field}"
        assert spell['slug'], f"Spell {spell['name']} has empty slug"


def test_toll_the_dead_in_fallback():
    """Test that Toll the Dead is in the fallback list."""
    slugs = [spell.get('slug') for spell in LOCAL_SPELLS_FALLBACK]
    assert 'toll-the-dead' in slugs, "Toll the Dead not found in fallback spells"
    
    # Find the spell and verify its data
    toll_spell = next(s for s in LOCAL_SPELLS_FALLBACK if s.get('slug') == 'toll-the-dead')
    assert 'Cleric' in toll_spell['dnd_class'], "Toll the Dead should be available to Clerics"
    assert 'Wizard' in toll_spell['dnd_class'], "Toll the Dead should be available to Wizards"
    assert toll_spell['level'] == 0, "Toll the Dead should be a cantrip (level 0)"


def test_word_of_radiance_in_fallback():
    """Test that Word of Radiance is in the fallback list."""
    slugs = [spell.get('slug') for spell in LOCAL_SPELLS_FALLBACK]
    assert 'word-of-radiance' in slugs, "Word of Radiance not found in fallback spells"
    
    # Find the spell and verify its data
    word_spell = next(s for s in LOCAL_SPELLS_FALLBACK if s.get('slug') == 'word-of-radiance')
    assert 'Cleric' in word_spell['dnd_class'], "Word of Radiance should be available to Clerics"
    assert word_spell['level'] == 0, "Word of Radiance should be a cantrip (level 0)"


def test_sanitize_fallback_spells():
    """Test that fallback spells sanitize correctly."""
    sanitized = sanitize_spell_list(LOCAL_SPELLS_FALLBACK)
    
    # Should have spells after sanitization
    assert len(sanitized) > 0, "Fallback spells sanitized to empty list"
    
    # Check for our new spells in sanitized list
    sanitized_slugs = {s.get('slug') for s in sanitized}
    assert 'toll-the-dead' in sanitized_slugs, "Toll the Dead not in sanitized list"
    assert 'word-of-radiance' in sanitized_slugs, "Word of Radiance not in sanitized list"
    
    # Verify sanitized spell structure
    for spell in sanitized:
        assert 'slug' in spell
        assert 'name' in spell
        assert 'level_int' in spell
        assert 'classes' in spell
        assert len(spell['classes']) > 0, f"Spell {spell['name']} has no classes"


def test_spell_merge_simulation():
    """Simulate the spell merge that happens in load_spell_library."""
    # Simulate Open5e results (smaller set)
    open5e_spells = [
        {
            "name": "Cure Wounds",
            "slug": "cure-wounds",
            "level": 1,
            "dnd_class": "Bard, Cleric",
            "document__title": "PHB",
        }
    ]
    
    # Merge fallback spells that aren't in Open5e
    existing_slugs = {spell.get('slug') for spell in open5e_spells if spell.get('slug')}
    merged = open5e_spells.copy()
    
    for fallback_spell in LOCAL_SPELLS_FALLBACK:
        if fallback_spell.get('slug') not in existing_slugs:
            merged.append(fallback_spell)
    
    # Sanitize the merged list
    sanitized = sanitize_spell_list(merged)
    
    # Verify our new spells are in the merged/sanitized list
    sanitized_slugs = {s.get('slug') for s in sanitized}
    assert 'toll-the-dead' in sanitized_slugs, "Toll the Dead lost during merge/sanitize"
    assert 'word-of-radiance' in sanitized_slugs, "Word of Radiance lost during merge/sanitize"
    assert 'cure-wounds' in sanitized_slugs, "Cure Wounds (from Open5e) lost during merge/sanitize"


if __name__ == '__main__':
    test_fallback_spells_have_required_fields()
    print("✓ Fallback spells have required fields")
    
    test_toll_the_dead_in_fallback()
    print("✓ Toll the Dead is in fallback")
    
    test_word_of_radiance_in_fallback()
    print("✓ Word of Radiance is in fallback")
    
    test_sanitize_fallback_spells()
    print("✓ Fallback spells sanitize correctly")
    
    test_spell_merge_simulation()
    print("✓ Spell merge simulation works")
    
    print("\n✅ All spell merge tests passed!")
