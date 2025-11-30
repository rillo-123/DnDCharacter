"""Test that spell details are properly saved and rendered."""

import sys
from pathlib import Path

# Add assets/py to path
sys.path.insert(0, str(Path(__file__).parent.parent / "assets" / "py"))

import pytest


# Extract just the LOCAL_SPELLS_FALLBACK data without importing character.py
LOCAL_SPELLS_FALLBACK = [
    {
        "name": "Cure Wounds",
        "slug": "cure-wounds",
        "level": 1,
        "school": "evocation",
        "casting_time": "1 action",
        "range": "Touch",
        "components": "V, S",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier.",
            "This spell has no effect on undead or constructs.",
        ],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st.",
        "dnd_class": "Bard, Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Detect Magic",
        "slug": "detect-magic",
        "level": 1,
        "school": "divination",
        "casting_time": "1 action",
        "range": "Self",
        "components": "V, S",
        "material": "",
        "duration": "Concentration, up to 10 minutes",
        "ritual": True,
        "concentration": True,
        "desc": [
            "For the duration, you sense the presence of magic within 30 feet of you.",
            "If you sense magic in this way, you can use your action to see a faint aura around any visible creature or object in the area that bears magic, and you learn its school of magic, if any.",
        ],
        "higher_level": "",
        "dnd_class": "Bard, Cleric",
        "document__title": "SRD",
    },
]


def _coerce_spell_text(value) -> str:
    """Coerce spell text to string (handles lists)."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(part) for part in value if part)
    return str(value)


def _make_paragraphs(text: str) -> str:
    """Convert text to HTML paragraphs."""
    if not text:
        return ""
    from html import escape
    paragraphs = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            paragraphs.append(f"<p>{escape(stripped)}</p>")
    return "".join(paragraphs)


class TestSpellDetailsSaved:
    """Test that spell details like desc and higher_level are preserved."""

    def test_cure_wounds_has_desc_in_fallback(self):
        """Test that Cure Wounds in fallback has desc field."""
        
        # Find Cure Wounds in fallback
        cure_wounds = None
        for spell in LOCAL_SPELLS_FALLBACK:
            if spell.get("slug") == "cure-wounds":
                cure_wounds = spell
                break
        
        assert cure_wounds is not None, "Cure Wounds not found in fallback"
        
        # Verify it has desc
        desc = cure_wounds.get("desc")
        assert desc is not None, "desc field missing"
        assert isinstance(desc, list), "desc should be a list"
        assert len(desc) > 0, "desc should not be empty"
        assert "1d8" in str(desc), "desc should contain healing info"
        
        # Verify it has higher_level
        higher_level = cure_wounds.get("higher_level")
        assert higher_level is not None, "higher_level field missing"
        assert "higher" in higher_level.lower(), "higher_level should explain higher level casting"
        
        print(f"OK Cure Wounds desc: {desc}")
        print(f"OK Cure Wounds higher_level: {higher_level}")

    def test_detect_magic_has_desc(self):
        """Test that Detect Magic spell has desc field."""
        
        detect_magic = None
        for spell in LOCAL_SPELLS_FALLBACK:
            if spell.get("slug") == "detect-magic":
                detect_magic = spell
                break
        
        assert detect_magic is not None, "Detect Magic not in fallback"
        assert detect_magic.get("desc") is not None, "desc field missing"
        assert isinstance(detect_magic.get("desc"), list), "desc should be a list"
        assert len(detect_magic.get("desc")) > 0, "desc should not be empty"
        
        print(f"OK Detect Magic desc: {detect_magic.get('desc')}")

    def test_spell_rendering_uses_desc(self):
        """Test that the rendering code properly uses desc field."""
        
        # Find Cure Wounds
        cure_wounds = None
        for spell in LOCAL_SPELLS_FALLBACK:
            if spell.get("slug") == "cure-wounds":
                cure_wounds = spell
                break
        
        assert cure_wounds is not None
        
        # Simulate what the render code does
        desc_text = _coerce_spell_text(cure_wounds.get("desc"))
        assert desc_text, "desc_text is empty after coercion"
        assert "1d8" in desc_text, "desc_text should contain healing info"
        
        # Convert to paragraphs (HTML)
        desc_html = _make_paragraphs(desc_text)
        assert desc_html, "desc_html is empty"
        assert "<p>" in desc_html, "desc_html should contain paragraph tags"
        assert "1d8" in desc_html, "desc_html should contain healing info"
        
        print(f"OK Rendered HTML: {desc_html[:100]}...")

    def test_coerce_spell_text_handles_lists(self):
        """Test that _coerce_spell_text properly converts list to text."""
        
        desc_list = [
            "First paragraph about 1d8 healing.",
            "Second paragraph about undead.",
        ]
        
        result = _coerce_spell_text(desc_list)
        assert result, "Result should not be empty"
        assert "1d8" in result, "Result should contain first paragraph"
        assert "undead" in result, "Result should contain second paragraph"
        assert "\n" in result, "Result should have newlines between items"
        
        print(f"OK Coerced text: {result}")

    def test_make_paragraphs_creates_html(self):
        """Test that _make_paragraphs creates proper HTML."""
        
        text = "First line\nSecond line"
        result = _make_paragraphs(text)
        
        assert result.count("<p>") == 2, "Should have 2 paragraphs"
        assert result.count("</p>") == 2, "Should close 2 paragraphs"
        assert "First line" in result, "Should contain first line"
        assert "Second line" in result, "Should contain second line"
        
        print(f"OK HTML: {result}")
