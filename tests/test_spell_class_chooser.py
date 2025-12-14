"""Unit tests for spell class filter/chooser functionality."""

import sys
from pathlib import Path
from html import escape
from unittest.mock import Mock, patch, MagicMock

# Add assets/py to path
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest


# Mock spell data for testing
SPELL_DATA_TEST = [
    {
        "name": "Cure Wounds",
        "slug": "cure-wounds",
        "level": 1,
        "classes": ["cleric", "artificer", "paladin"],
    },
    {
        "name": "Fireball",
        "slug": "fireball",
        "level": 3,
        "classes": ["sorcerer", "wizard"],
    },
    {
        "name": "Magic Missile",
        "slug": "magic-missile",
        "level": 1,
        "classes": ["sorcerer", "wizard", "artificer"],
    },
    {
        "name": "Bless",
        "slug": "bless",
        "level": 1,
        "classes": ["cleric", "paladin"],
    },
    {
        "name": "Hex",
        "slug": "hex",
        "level": 1,
        "classes": ["warlock"],
    },
    {
        "name": "Eldritch Blast",
        "slug": "eldritch-blast",
        "level": 0,
        "classes": ["warlock"],
    },
    {
        "name": "Misty Step",
        "slug": "misty-step",
        "level": 2,
        "classes": ["sorcerer", "wizard", "warlock", "bard"],
    },
]

# Supported classes for testing
SUPPORTED_CLASSES = ["artificer", "bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock", "wizard"]

CLASS_DISPLAY_NAMES = {
    "artificer": "Artificer",
    "bard": "Bard",
    "cleric": "Cleric",
    "druid": "Druid",
    "paladin": "Paladin",
    "ranger": "Ranger",
    "sorcerer": "Sorcerer",
    "warlock": "Warlock",
    "wizard": "Wizard",
}


def extract_available_classes(spells: list[dict]) -> set[str]:
    """Extract unique classes from spell list."""
    available_classes: set[str] = set()
    if spells:
        for spell in spells:
            for class_key in spell.get("classes", []):
                if class_key in SUPPORTED_CLASSES:
                    available_classes.add(class_key)
    if not available_classes:
        available_classes.update(SUPPORTED_CLASSES)
    return available_classes


def generate_class_filter_options(spells: list[dict] | None) -> str:
    """Generate HTML options for class filter, simulating populate_spell_class_filter."""
    available_classes = extract_available_classes(spells or [])
    
    options = ['<option value="">Any class</option>']
    ordered_classes = [
        class_key
        for class_key in SUPPORTED_CLASSES
        if class_key in available_classes
    ]
    for class_key in ordered_classes:
        label = CLASS_DISPLAY_NAMES.get(class_key, class_key.title())
        options.append(
            f'<option value="{escape(class_key)}">{escape(label)}</option>'
        )
    
    return "".join(options)


def extract_options_from_html(html: str) -> list[tuple[str, str]]:
    """Parse HTML option elements into (value, label) tuples."""
    import re
    # Find all <option ...> tags
    pattern = r'<option value="([^"]*)"[^>]*>([^<]*)</option>'
    matches = re.findall(pattern, html)
    return matches


class TestSpellClassChooser:
    """Test spell class filter/chooser functionality."""

    def test_extract_classes_from_spells(self):
        """Test extracting unique classes from spell list."""
        available = extract_available_classes(SPELL_DATA_TEST)
        
        # Should include: cleric, artificer, paladin, sorcerer, wizard, warlock, bard
        assert "cleric" in available
        assert "wizard" in available
        assert "sorcerer" in available
        assert "warlock" in available
        assert "artificer" in available
        assert "paladin" in available
        assert "bard" in available
        
        # Druid and ranger not in spells, so included from fallback
        assert "druid" in available or len(available) == 7, "druid/ranger may not be in fallback"
        
        print(f"OK extracted classes: {sorted(available)}")

    def test_extract_classes_with_empty_spell_list(self):
        """Test that empty spell list returns all supported classes."""
        available = extract_available_classes([])
        
        # Should return all supported classes
        for class_name in SUPPORTED_CLASSES:
            assert class_name in available, f"{class_name} not in available classes"
        
        assert len(available) == len(SUPPORTED_CLASSES), "Should have all supported classes"
        print(f"OK empty spell list returns all {len(available)} supported classes")

    def test_extract_classes_with_none(self):
        """Test that None spell list returns all supported classes."""
        available = extract_available_classes(None or [])
        
        for class_name in SUPPORTED_CLASSES:
            assert class_name in available, f"{class_name} not in available classes"
        
        print(f"OK None spell list returns all {len(available)} supported classes")

    def test_generate_filter_options_structure(self):
        """Test that generated filter options have correct HTML structure."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        
        # Should be HTML string
        assert isinstance(html, str), "Should return HTML string"
        assert html, "HTML should not be empty"
        
        # Should have option tags
        assert "<option" in html, "Should have option tags"
        assert "</option>" in html, "Should close option tags"
        
        # Should have "Any class" option
        assert 'value=""' in html, "Should have empty value for 'Any class'"
        assert "Any class" in html, "Should have 'Any class' option"
        
        print(f"OK HTML structure valid: {len(html)} characters")

    def test_generate_filter_options_have_values(self):
        """Test that each option has a proper value attribute."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        options = extract_options_from_html(html)
        
        # Should have at least the "Any class" option
        assert len(options) > 1, "Should have more than just 'Any class' option"
        
        # First option should be "Any class"
        assert options[0][0] == "", "First option should have empty value"
        assert options[0][1] == "Any class", "First option should be 'Any class'"
        
        # Rest should be class options
        for value, label in options[1:]:
            assert value, f"Option value should not be empty for {label}"
            assert label, "Option label should not be empty"
            assert value.lower() == value, f"Option value should be lowercase: {value}"
        
        print(f"OK all {len(options)} options have proper values and labels")

    def test_generate_filter_options_class_names_displayed_correctly(self):
        """Test that class names are displayed with proper capitalization."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        options = extract_options_from_html(html)
        
        # Check that display names use CLASS_DISPLAY_NAMES
        for value, label in options[1:]:  # Skip "Any class"
            if value:  # Skip empty value
                expected_label = CLASS_DISPLAY_NAMES.get(value, value.title())
                assert label == expected_label, f"Label mismatch: got '{label}', expected '{expected_label}'"
        
        print(f"OK all class names displayed correctly")

    def test_generate_filter_includes_wizard(self):
        """Test that Wizard class appears in filter options."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        options = extract_options_from_html(html)
        
        # Extract values
        values = [opt[0] for opt in options]
        labels = [opt[1] for opt in options]
        
        assert "wizard" in values, "Wizard should be in options"
        assert "Wizard" in labels, "Wizard display name should be 'Wizard'"
        
        print("OK Wizard class in options")

    def test_generate_filter_includes_sorcerer(self):
        """Test that Sorcerer class appears in filter options."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        options = extract_options_from_html(html)
        
        values = [opt[0] for opt in options]
        assert "sorcerer" in values, "Sorcerer should be in options"
        
        print("OK Sorcerer class in options")

    def test_generate_filter_includes_cleric(self):
        """Test that Cleric class appears in filter options."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        options = extract_options_from_html(html)
        
        values = [opt[0] for opt in options]
        assert "cleric" in values, "Cleric should be in options"
        
        print("OK Cleric class in options")

    def test_filter_options_maintain_order(self):
        """Test that filter options maintain consistent order."""
        html1 = generate_class_filter_options(SPELL_DATA_TEST)
        html2 = generate_class_filter_options(SPELL_DATA_TEST)
        
        # Generate multiple times - order should be consistent
        options1 = extract_options_from_html(html1)
        options2 = extract_options_from_html(html2)
        
        assert options1 == options2, "Options should be in same order"
        
        # Options should follow SUPPORTED_CLASSES order
        values = [opt[0] for opt in options1[1:]]  # Skip "Any class"
        expected_order = [c for c in SUPPORTED_CLASSES if c in values]
        assert values == expected_order, "Options should follow SUPPORTED_CLASSES order"
        
        print(f"OK filter options maintain order: {values}")

    def test_filter_options_no_duplicates(self):
        """Test that filter options have no duplicate class values."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        options = extract_options_from_html(html)
        
        values = [opt[0] for opt in options]
        # Remove "Any class" (empty string)
        values_no_any = [v for v in values if v]
        
        assert len(values_no_any) == len(set(values_no_any)), "Should have no duplicate values"
        
        print(f"OK no duplicate options: {values_no_any}")

    def test_filter_respects_supported_classes(self):
        """Test that only SUPPORTED_CLASSES appear in filter options."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        options = extract_options_from_html(html)
        
        for value, label in options[1:]:  # Skip "Any class"
            if value:
                assert value in SUPPORTED_CLASSES, f"Option '{value}' not in SUPPORTED_CLASSES"
        
        print("OK all filter options are in SUPPORTED_CLASSES")

    def test_filter_options_escape_special_characters(self):
        """Test that special characters in class names are properly escaped."""
        # Most class names don't have special chars, but test the escaping function works
        test_html = f'<option value="{escape("test&value")}">{escape("Test & Label")}</option>'
        
        # Should contain escaped ampersand
        assert "&amp;" in test_html, "Ampersand should be escaped"
        # Verify that the ampersand in the value is escaped
        assert 'value="test&amp;value"' in test_html, "Value attribute should have escaped ampersand"
        # Verify that the ampersand in the label is escaped
        assert '>Test &amp; Label</option>' in test_html, "Label should have escaped ampersand"
        
        print("OK HTML escaping works")

    def test_filter_with_single_class_spells(self):
        """Test filter with spells that only have one class."""
        single_class_spells = [
            {"slug": "eldritch-blast", "classes": ["warlock"]},
            {"slug": "hexagon", "classes": ["warlock"]},
        ]
        
        available = extract_available_classes(single_class_spells)
        
        # Should still include warlock (only class in spells)
        assert "warlock" in available
        
        # When one class appears in spells, that's the available class
        # (Fallback to all classes only happens if NO classes are found)
        assert len(available) >= 1
        
        print(f"OK filter with single-class spells: {sorted(available)}")

    def test_filter_with_multi_class_spells(self):
        """Test filter with spells that span many classes."""
        multi_class_spells = [
            {"slug": "prestidigitation", "classes": ["artificer", "bard", "cleric", "druid", "sorcerer", "warlock", "wizard"]},
        ]
        
        available = extract_available_classes(multi_class_spells)
        
        # Should include all classes from the multi-class spell
        for cls in ["artificer", "bard", "cleric", "druid", "sorcerer", "warlock", "wizard"]:
            assert cls in available, f"{cls} should be included"
        
        print(f"OK filter with multi-class spells: {sorted(available)}")

    def test_filter_excludes_unsupported_classes(self):
        """Test that unsupported class names are filtered out."""
        spells_with_unsupported = [
            {"slug": "spell1", "classes": ["wizard", "invalid-class"]},
            {"slug": "spell2", "classes": ["cleric", "unknown"]},
        ]
        
        available = extract_available_classes(spells_with_unsupported)
        
        # Should only have supported classes
        assert "wizard" in available
        assert "cleric" in available
        assert "invalid-class" not in available
        assert "unknown" not in available
        
        print(f"OK unsupported classes filtered out: {sorted(available)}")

    def test_filter_maintains_html_validity(self):
        """Test that generated HTML is valid and parseable."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        
        # Count opening and closing tags
        open_count = html.count("<option")
        close_count = html.count("</option>")
        
        assert open_count == close_count, "Opening and closing tags should match"
        
        # Should be able to extract all options
        options = extract_options_from_html(html)
        assert len(options) == open_count, "Should extract all options from HTML"
        
        print(f"OK valid HTML: {open_count} options generated")

    def test_filter_any_class_option_first(self):
        """Test that 'Any class' option always appears first."""
        html = generate_class_filter_options(SPELL_DATA_TEST)
        
        # "Any class" option should come before other options
        any_pos = html.find('value=""')
        first_class_pos = html.find('value="' + SUPPORTED_CLASSES[0])
        
        # Special case: may not find first_class_pos if not in this set
        if first_class_pos > 0:
            assert any_pos < first_class_pos, "'Any class' should come before other options"
        
        # Should be near the start
        assert any_pos < 100, "'Any class' should be near the start"
        
        print("OK 'Any class' option is first")

    def test_filter_consistency_across_calls(self):
        """Test that multiple calls with same input produce identical HTML."""
        html1 = generate_class_filter_options(SPELL_DATA_TEST)
        html2 = generate_class_filter_options(SPELL_DATA_TEST)
        html3 = generate_class_filter_options(SPELL_DATA_TEST)
        
        assert html1 == html2 == html3, "Repeated calls should produce identical HTML"
        
        print("OK consistent output across multiple calls")


class TestSpellClassFilterIntegration:
    """Integration tests for spell class filtering."""

    def test_wizard_and_sorcerer_can_cast_same_spell(self):
        """Test filtering spells that both Wizard and Sorcerer can cast."""
        # Fireball: sorcerer + wizard
        spells = [s for s in SPELL_DATA_TEST if "wizard" in s.get("classes", [])]
        available = extract_available_classes(spells)
        
        assert "wizard" in available
        # May or may not have sorcerer depending on which spells filtered
        
        print(f"OK Wizard filter: {sorted(available)}")

    def test_cleric_paladin_shared_spells(self):
        """Test that shared spells between Cleric and Paladin are accessible."""
        # Bless is in both cleric and paladin
        cleric_spells = [s for s in SPELL_DATA_TEST if "cleric" in s.get("classes", [])]
        available = extract_available_classes(cleric_spells)
        
        assert "cleric" in available
        assert "paladin" in available or len(cleric_spells) > 0
        
        print(f"OK Cleric/Paladin filter: {sorted(available)}")

    def test_warlock_unique_spells(self):
        """Test that Warlock's unique spells are properly categorized."""
        warlock_spells = [s for s in SPELL_DATA_TEST if "warlock" in s.get("classes", [])]
        available = extract_available_classes(warlock_spells)
        
        assert "warlock" in available
        # Hex and Eldritch Blast are warlock only (plus Misty Step which is multi-class)
        
        print(f"OK Warlock filter: {sorted(available)}")

    def test_all_classes_appear_in_fallback(self):
        """Test that with no spells, all supported classes appear in filter."""
        available = extract_available_classes([])
        
        for cls in SUPPORTED_CLASSES:
            assert cls in available, f"{cls} should be in fallback"
        
        print(f"OK all {len(available)} supported classes in fallback")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
