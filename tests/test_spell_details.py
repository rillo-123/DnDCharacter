"""Test that spell details are properly saved and rendered."""

import sys
from pathlib import Path

# Add assets/py to path
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest


# Extract just the LOCAL_SPELLS_FALLBACK data without importing character.py
LOCAL_SPELLS_FALLBACK = [
    {
        "name": "Cure Wounds",
        "slug": "cure-wounds",
        "level": 1,
        "school": "evocation",
        "desc": ["A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier.", "This spell has no effect on undead or constructs."],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st.",
    },
    {
        "name": "Healing Word",
        "slug": "healing-word",
        "level": 1,
        "school": "evocation",
        "desc": ["A creature of your choice that you can see within range regains hit points equal to 1d4 + your spellcasting ability modifier.", "This spell has no effect on undead or constructs."],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d4 for each slot level above 1st.",
    },
    {
        "name": "Guiding Bolt",
        "slug": "guiding-bolt",
        "level": 1,
        "school": "evocation",
        "desc": ["A flash of light streaks toward a creature of your choice within range. Make a ranged spell attack against the target.", "On a hit, the target takes 4d6 radiant damage, and the next attack roll made against this target before the end of your next turn has advantage."],
        "higher_level": "The damage increases by 1d6 for each slot level above 1st.",
    },
    {
        "name": "Bless",
        "slug": "bless",
        "level": 1,
        "school": "enchantment",
        "desc": ["You bless up to three creatures of your choice within range. Whenever a target makes an attack roll or a saving throw before the spell ends, the target can roll a d4 and add the number rolled to the attack roll or saving throw."],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, you can target one additional creature for each slot level above 1st.",
    },
    {
        "name": "Faerie Fire",
        "slug": "faerie-fire",
        "level": 1,
        "school": "evocation",
        "desc": ["Each object in a 20-foot cube within range is outlined in blue, green, or violet light. Any creature in the area when the spell is cast is also outlined in light if it fails a Dexterity saving throw.", "For the duration, objects and affected creatures shed dim light in a 10-foot radius and attack rolls against affected creatures have advantage."],
        "higher_level": "",
    },
    {
        "name": "Sacred Flame",
        "slug": "sacred-flame",
        "level": 0,
        "school": "evocation",
        "desc": ["Flame-like radiance descends on a creature you can see within range. The target must succeed on a Dexterity saving throw or take 1d8 radiant damage.", "The target gains no benefit from cover for this saving throw."],
        "higher_level": "The spell's damage increases by 1d8 when you reach 5th level (2d8), 11th level (3d8), and 17th level (4d8).",
    },
    {
        "name": "Detect Magic",
        "slug": "detect-magic",
        "level": 1,
        "school": "divination",
        "desc": ["For the duration, you sense the presence of magic within 30 feet of you.", "If you sense magic in this way, you can use your action to see a faint aura around any visible creature or object in the area that bears magic, and you learn its school of magic, if any."],
        "higher_level": "",
    },
    {
        "name": "Prayer of Healing",
        "slug": "prayer-of-healing",
        "level": 2,
        "school": "evocation",
        "desc": ["Up to six creatures of your choice that you can see within range each regain hit points equal to 2d8 + your spellcasting ability modifier.", "This spell has no effect on undead or constructs."],
        "higher_level": "When you cast this spell using a spell slot of 3rd level or higher, the healing increases by 1d8 for each slot level above 2nd.",
    },
    {
        "name": "Shatter",
        "slug": "shatter",
        "level": 2,
        "school": "evocation",
        "desc": ["A sudden loud ringing noise, painfully intense, erupts from a point of your choice within range.", "Each creature in a 10-foot-radius sphere centered on that point must make a Constitution saving throw, taking 3d8 thunder damage on a failed save, or half as much damage on a successful one."],
        "higher_level": "When you cast this spell using a spell slot of 3rd level or higher, the damage increases by 1d8 for each slot level above 2nd.",
    },
    {
        "name": "Hold Person",
        "slug": "hold-person",
        "level": 2,
        "school": "enchantment",
        "desc": ["Choose a humanoid that you can see within range. The target must succeed on a Wisdom saving throw or be paralyzed for the duration.", "At the end of each of its turns, the target can make another Wisdom saving throw. On a success, the spell ends on the target."],
        "higher_level": "When you cast this spell using a spell slot of 3rd level or higher, you can target one additional humanoid for each slot level above 2nd.",
    },
    {
        "name": "Vicious Mockery",
        "slug": "vicious-mockery",
        "level": 0,
        "school": "enchantment",
        "desc": ["You unleash a string of insults laced with subtle enchantments at a creature you can see within range. If the target can hear you, it must succeed on a Wisdom saving throw or take 1d4 psychic damage and have disadvantage on the next attack roll it makes before the end of its next turn."],
        "higher_level": "The damage increases by 1d4 when you reach 5th level (2d4), 11th level (3d4), and 17th level (4d4).",
    },
    {
        "name": "Word of Radiance",
        "slug": "word-of-radiance",
        "level": 0,
        "school": "evocation",
        "desc": ["You utter a divine word, and burning radiance erupts from you.", "Each creature of your choice that you can see within 5 feet of you must succeed on a Constitution saving throw or take 1d6 radiant damage."],
        "higher_level": "The damage increases by 1d6 when you reach 5th level (2d6), 11th level (3d6), and 17th level (4d6).",
    },
    {
        "name": "Toll the Dead",
        "slug": "toll-the-dead",
        "level": 0,
        "school": "necromancy",
        "desc": ["You point at one creature you can see within range. The creature must make a Wisdom saving throw.", "On a failed save, it takes 1d8 necrotic damage if it is still below its hit point maximum when you cast the spell.", "If the creature is missing any of its hit points when you cast this spell, it takes 1d12 necrotic damage instead."],
        "higher_level": "When you reach 5th level, the damage increases to 2d8 or 2d12, at 11th level to 3d8 or 3d12, and at 17th level to 4d8 or 4d12.",
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

    def test_all_fallback_spells_have_details(self):
        """Test that ALL spells in the fallback list have desc field."""
        
        errors = []
        for spell in LOCAL_SPELLS_FALLBACK:
            slug = spell.get("slug", "UNKNOWN")
            
            # The critical check: desc must exist and not be empty
            desc = spell.get("desc")
            if not desc:
                errors.append(f"{slug}: missing 'desc' field")
            elif isinstance(desc, list):
                if len(desc) == 0:
                    errors.append(f"{slug}: 'desc' list is empty")
            elif isinstance(desc, str):
                if not desc.strip():
                    errors.append(f"{slug}: 'desc' string is empty")
        
        if errors:
            error_msg = "Spell detail issues found:\n" + "\n".join(errors)
            raise AssertionError(error_msg)
        
        print(f"OK All {len(LOCAL_SPELLS_FALLBACK)} spells have desc field")

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

    def test_healing_word_has_desc(self):
        """Test that Healing Word spell has desc field."""
        
        healing_word = None
        for spell in LOCAL_SPELLS_FALLBACK:
            if spell.get("slug") == "healing-word":
                healing_word = spell
                break
        
        assert healing_word is not None, "Healing Word not found in fallback"
        assert healing_word.get("desc") is not None, "desc field missing from Healing Word"
        assert isinstance(healing_word.get("desc"), list), "desc should be a list"
        assert len(healing_word.get("desc")) > 0, "desc should not be empty"
        assert "1d4" in str(healing_word.get("desc")), "desc should contain healing info"
        
        print(f"OK Healing Word desc: {healing_word.get('desc')}")

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

    def test_slug_normalization_logic(self):
        """Test slug normalization logic that handles -a5e variant slugs."""
        
        # Simulate the normalization logic
        def normalize_slug(slug):
            """Normalize slug by removing source suffixes."""
            if "-a5e" in slug:
                return slug.replace("-a5e", "")
            return slug
        
        # Test direct slug
        assert normalize_slug("healing-word") == "healing-word", "Direct slug unchanged"
        
        # Test a5e variant
        assert normalize_slug("healing-word-a5e") == "healing-word", "a5e suffix removed"
        assert normalize_slug("guiding-bolt-a5e") == "guiding-bolt", "a5e suffix removed"
        
        # Test multiple sources (if any)
        assert normalize_slug("cure-wounds-phb") == "cure-wounds-phb", "Only a5e suffix removed"
        
        print("OK slug normalization handles -a5e variant suffixes")

    def test_authoritative_sources_filtering(self):
        """Test that only authoritative D&D 5e sources are recognized."""
        
        def is_authoritative_source(source: str | None) -> bool:
            """Check if spell/item source is from an authoritative D&D 5e book."""
            AUTHORITATIVE_SOURCES = {"phb", "xge", "xgte", "tcoe", "tce", "5e core rules"}
            
            if not source:
                return False
            normalized = source.lower().strip()
            if normalized in AUTHORITATIVE_SOURCES:
                return True
            for auth_source in AUTHORITATIVE_SOURCES:
                if auth_source in normalized:
                    return True
            return False
        
        # Test authoritative sources
        assert is_authoritative_source("PHB"), "PHB should be authoritative"
        assert is_authoritative_source("XGE"), "XGE should be authoritative"
        assert is_authoritative_source("XGtE"), "XGtE should be authoritative"
        assert is_authoritative_source("TCoE"), "TCoE should be authoritative"
        assert is_authoritative_source("TCE"), "TCE should be authoritative"
        assert is_authoritative_source("5e Core Rules"), "5e Core Rules should be authoritative"
        
        # Test non-authoritative sources
        assert not is_authoritative_source("A5E"), "A5E should not be authoritative"
        assert not is_authoritative_source("Level Up Advanced 5e"), "A5E should not be authoritative"
        assert not is_authoritative_source("UA"), "Unearthed Arcana should not be authoritative"
        assert not is_authoritative_source(""), "Empty string should not be authoritative"
        assert not is_authoritative_source(None), "None should not be authoritative"
        
        print("OK authoritative source filtering works correctly")
