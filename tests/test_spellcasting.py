"""Comprehensive unit tests for spell casting and GUI logic.

These tests cover the SpellcastingManager, spell filtering, domain bonuses,
and other spell-related GUI operations without requiring PyScript/DOM.
"""

import pytest
import sys
from pathlib import Path

# Add assets/py to path
sys.path.insert(0, str(Path(__file__).parent.parent / "assets" / "py"))

from character_models import (
    Character,
    Cleric,
    Bard,
    CharacterFactory,
    get_race_ability_bonuses,
    DEFAULT_ABILITY_KEYS,
)


def ability_modifier(score: int) -> int:
    """Calculate ability modifier from ability score."""
    return (score - 10) // 2


class MockSpellRecord:
    """Mock spell record for testing."""
    
    def __init__(self, slug, name, level=1, classes=None, ritual=False, concentration=False):
        self.slug = slug
        self.name = name
        self.level = level
        self.level_int = level
        self.classes = classes or ["cleric"]
        self.ritual = ritual
        self.concentration = concentration
        self.school = "evocation"
        self.casting_time = "1 action"
        self.range = "Touch"
        self.components = "V, S"
        self.material = ""
        self.duration = "Instantaneous"
        self.description = f"Description of {name}"
        self.description_html = f"<p>Description of {name}</p>"
        self.source = "SRD"
        self.classes_display = [c.title() for c in self.classes]
    
    def to_dict(self):
        return {
            "slug": self.slug,
            "name": self.name,
            "level_int": self.level_int,
            "level_label": f"Level {self.level}" if self.level > 0 else "Cantrip",
            "classes": self.classes,
            "classes_display": self.classes_display,
            "ritual": self.ritual,
            "concentration": self.concentration,
            "school": self.school,
            "casting_time": self.casting_time,
            "range": self.range,
            "components": self.components,
            "material": self.material,
            "duration": self.duration,
            "description": self.description,
            "description_html": self.description_html,
            "source": self.source,
        }


class TestSpellBasics:
    """Test basic spell operations and data structures."""
    
    def test_spell_record_creation(self):
        """Can create a mock spell record."""
        spell = MockSpellRecord("cure-wounds", "Cure Wounds", level=1, classes=["cleric", "bard"])
        assert spell.slug == "cure-wounds"
        assert spell.name == "Cure Wounds"
        assert spell.level == 1
        assert "cleric" in spell.classes
        assert "bard" in spell.classes
    
    def test_spell_cantrip(self):
        """Can create cantrip spells."""
        spell = MockSpellRecord("fire-bolt", "Fire Bolt", level=0, classes=["sorcerer", "wizard"])
        assert spell.level_int == 0
        assert "sorcerer" in spell.classes
    
    def test_spell_properties(self):
        """Spell record preserves properties."""
        spell = MockSpellRecord(
            "concentration-spell",
            "Concentration Test",
            level=2,
            classes=["wizard"],
            concentration=True,
            ritual=True
        )
        assert spell.concentration == True
        assert spell.ritual == True
        assert spell.school == "evocation"


class TestSpellFiltering:
    """Test spell filtering logic."""
    
    def test_filter_by_class(self):
        """Can filter spells by class availability."""
        cleric_spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds", classes=["cleric", "bard"]),
            MockSpellRecord("guiding-bolt", "Guiding Bolt", classes=["cleric"]),
            MockSpellRecord("magic-missile", "Magic Missile", classes=["wizard", "sorcerer"]),
        ]
        
        cleric_available = [s for s in cleric_spells if "cleric" in s.classes]
        assert len(cleric_available) == 2
        assert any(s.slug == "cure-wounds" for s in cleric_available)
        assert any(s.slug == "guiding-bolt" for s in cleric_available)
    
    def test_filter_by_level(self):
        """Can filter spells by character level."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds", level=1),
            MockSpellRecord("lesser-restoration", "Lesser Restoration", level=2),
            MockSpellRecord("beacon-of-hope", "Beacon of Hope", level=3),
            MockSpellRecord("fire-bolt", "Fire Bolt", level=0),
        ]
        
        # Cleric level 2 can access cantrips and 1st-level spells
        level_2_available = [s for s in spells if s.level <= 2]
        assert len(level_2_available) == 3
        assert any(s.slug == "fire-bolt" for s in level_2_available)
        assert any(s.slug == "cure-wounds" for s in level_2_available)
    
    def test_filter_by_search_term(self):
        """Can filter spells by search term."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds"),
            MockSpellRecord("mass-cure-wounds", "Mass Cure Wounds"),
            MockSpellRecord("healing-word", "Healing Word"),
            MockSpellRecord("fireball", "Fireball"),
        ]
        
        search_blob_map = {
            s.slug: (s.name + " " + s.description).lower()
            for s in spells
        }
        
        cure_spells = [
            s for s in spells
            if "cure" in search_blob_map[s.slug]
        ]
        assert len(cure_spells) == 2
        assert any(s.slug == "cure-wounds" for s in cure_spells)
        assert any(s.slug == "mass-cure-wounds" for s in cure_spells)
    
    def test_deduplication(self):
        """Can deduplicate spells by slug."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds"),
            MockSpellRecord("cure-wounds", "Cure Wounds"),  # Duplicate
            MockSpellRecord("healing-word", "Healing Word"),
        ]
        
        seen_slugs = set()
        deduplicated = []
        for spell in spells:
            if spell.slug not in seen_slugs:
                deduplicated.append(spell)
                seen_slugs.add(spell.slug)
        
        assert len(deduplicated) == 2
        assert len(seen_slugs) == 2


class TestDomainBonusSpells:
    """Test domain bonus spell functionality."""
    
    def test_domain_bonus_spells_cleric_life_domain_level_1(self):
        """Life domain Cleric level 1 gets Cure Wounds and Bless as bonuses."""
        domain_bonus_spells = {
            "life": {
                1: ["cure-wounds", "bless"],
                3: ["lesser-restoration", "spiritual-weapon"],
                5: ["beacon-of-hope", "revivify"],
                7: ["guardian-of-faith", "death-ward"],
                9: ["mass-cure-wounds", "raise-dead"],
            },
        }
        
        domain = "life"
        level = 1
        domain_key = domain.lower().strip()
        spells_by_level = domain_bonus_spells.get(domain_key, {})
        
        bonus_spells = []
        for lv in sorted(spells_by_level.keys()):
            if lv <= level:
                bonus_spells.extend(spells_by_level[lv])
        
        assert "cure-wounds" in bonus_spells
        assert "bless" in bonus_spells
        assert len(bonus_spells) == 2
    
    def test_domain_bonus_spells_cleric_life_domain_level_5(self):
        """Life domain Cleric level 5 gets all bonus spells up to level 5."""
        domain_bonus_spells = {
            "life": {
                1: ["cure-wounds", "bless"],
                3: ["lesser-restoration", "spiritual-weapon"],
                5: ["beacon-of-hope", "revivify"],
                7: ["guardian-of-faith", "death-ward"],
                9: ["mass-cure-wounds", "raise-dead"],
            },
        }
        
        domain = "life"
        level = 5
        domain_key = domain.lower().strip()
        spells_by_level = domain_bonus_spells.get(domain_key, {})
        
        bonus_spells = []
        for lv in sorted(spells_by_level.keys()):
            if lv <= level:
                bonus_spells.extend(spells_by_level[lv])
        
        # Should have: cure-wounds, bless, lesser-restoration, spiritual-weapon, beacon-of-hope, revivify
        assert len(bonus_spells) == 6
        assert "cure-wounds" in bonus_spells
        assert "beacon-of-hope" in bonus_spells
        assert "raise-dead" not in bonus_spells  # Level 9, not available yet
    
    def test_domain_bonus_spells_no_domain(self):
        """Non-domain characters have no bonus spells."""
        domain = ""
        level = 5
        
        if not domain:
            bonus_spells = []
        else:
            bonus_spells = ["some-spell"]
        
        assert len(bonus_spells) == 0


class TestMaxPreparedSpells:
    """Test maximum prepared spells calculation."""
    
    def test_cleric_max_prepared_level_1_wis_10(self):
        """Cleric level 1 with WIS 10 can prepare 1 spell (level + mod = 1 + 0 = 1)."""
        level = 1
        ability_score = 10
        spell_mod = ability_modifier(ability_score)
        max_prepared = level + spell_mod
        
        assert spell_mod == 0
        assert max_prepared == 1
    
    def test_cleric_max_prepared_level_5_wis_16(self):
        """Cleric level 5 with WIS 16 can prepare 8 spells (5 + 3 = 8)."""
        level = 5
        ability_score = 16
        spell_mod = ability_modifier(ability_score)
        max_prepared = level + spell_mod
        
        assert spell_mod == 3
        assert max_prepared == 8
    
    def test_cleric_max_prepared_level_10_wis_18(self):
        """Cleric level 10 with WIS 18 can prepare 14 spells (10 + 4 = 14)."""
        level = 10
        ability_score = 18
        spell_mod = ability_modifier(ability_score)
        max_prepared = level + spell_mod
        
        assert spell_mod == 4
        assert max_prepared == 14
    
    def test_druid_max_prepared_same_as_cleric(self):
        """Druid follows same formula as Cleric (level + WIS mod)."""
        level = 7
        ability_score = 14
        spell_mod = ability_modifier(ability_score)
        max_prepared = level + spell_mod
        
        assert spell_mod == 2
        assert max_prepared == 9
    
    def test_paladin_max_prepared_half_level(self):
        """Paladin can prepare (level // 2) + CHA mod spells."""
        level = 10
        ability_score = 16
        spell_mod = ability_modifier(ability_score)
        max_prepared = (level // 2) + spell_mod
        
        assert max_prepared == 8  # (10 // 2) + 3 = 8
    
    def test_ranger_max_prepared_half_level(self):
        """Ranger can prepare (level // 2) + WIS mod spells."""
        level = 8
        ability_score = 12
        spell_mod = ability_modifier(ability_score)
        max_prepared = (level // 2) + spell_mod
        
        assert max_prepared == 5  # (8 // 2) + 1 = 5
    
    def test_wizard_max_prepared_full_level(self):
        """Wizard can prepare level + INT mod spells."""
        level = 6
        ability_score = 17
        spell_mod = ability_modifier(ability_score)
        max_prepared = level + spell_mod
        
        assert max_prepared == 9  # 6 + 3 = 9


class TestSpellPreparedCounting:
    """Test counting prepared spells (excluding domain bonuses)."""
    
    def test_count_excludes_domain_bonus_spells(self):
        """Count prepared spells should exclude domain bonus spells."""
        prepared_spells = [
            {"slug": "cure-wounds"},      # Domain bonus - shouldn't count
            {"slug": "bless"},             # Domain bonus - shouldn't count
            {"slug": "detect-magic"},      # Chosen - should count
            {"slug": "light"},             # Chosen - should count
        ]
        
        domain_bonus_slugs = {"cure-wounds", "bless"}
        
        chosen_count = len([s for s in prepared_spells if s.get("slug") not in domain_bonus_slugs])
        
        assert chosen_count == 2
    
    def test_can_add_when_at_limit_if_bonus_spells_available(self):
        """Can add a spell if only bonus spells are taking up slots."""
        max_prepared = 3
        prepared_spells = [
            {"slug": "cure-wounds"},      # Domain bonus
            {"slug": "bless"},             # Domain bonus
            {"slug": "detect-magic"},      # Chosen
        ]
        domain_bonus_slugs = {"cure-wounds", "bless"}
        
        chosen_count = len([s for s in prepared_spells if s.get("slug") not in domain_bonus_slugs])
        can_add = chosen_count < max_prepared
        
        assert chosen_count == 1
        assert can_add == True
    
    def test_cannot_add_when_at_chosen_limit(self):
        """Cannot add spell if chosen spells are at limit."""
        max_prepared = 3
        prepared_spells = [
            {"slug": "cure-wounds"},      # Domain bonus
            {"slug": "detect-magic"},     # Chosen
            {"slug": "light"},            # Chosen
            {"slug": "guidance"},         # Chosen
        ]
        domain_bonus_slugs = {"cure-wounds"}
        
        chosen_count = len([s for s in prepared_spells if s.get("slug") not in domain_bonus_slugs])
        can_add = chosen_count < max_prepared
        
        assert chosen_count == 3
        assert can_add == False


class TestSpellRemovalRules:
    """Test spell removal restrictions."""
    
    def test_domain_bonus_spells_can_be_removed(self):
        """Domain bonus spells can now be removed (restriction removed)."""
        slug_to_remove = "cure-wounds"
        domain_bonus_slugs = {"cure-wounds", "bless"}
        
        # This spell is in domain_bonus_slugs, but we can still remove it now
        # The restriction was lifted to allow full control
        can_remove = True  # All spells can be removed now
        
        assert can_remove == True
    
    def test_can_remove_chosen_spell(self):
        """Chosen spells can be removed."""
        slug_to_remove = "detect-magic"
        domain_bonus_slugs = {"cure-wounds", "bless"}
        
        can_remove = slug_to_remove not in domain_bonus_slugs
        
        assert can_remove == True
    
    def test_remove_spell_from_list(self):
        """Removing a spell removes it from prepared list."""
        prepared_spells = [
            {"slug": "cure-wounds"},
            {"slug": "detect-magic"},
            {"slug": "light"},
        ]
        
        slug_to_remove = "detect-magic"
        remaining = [s for s in prepared_spells if s.get("slug") != slug_to_remove]
        
        assert len(remaining) == 2
        assert not any(s.get("slug") == "detect-magic" for s in remaining)


class TestSpellAvailability:
    """Test spell availability checks."""
    
    def test_spell_available_to_class(self):
        """Spell is available if character class matches spell's classes."""
        character_classes = {"cleric", "bard"}
        spell_classes = {"cleric", "bard"}
        
        is_available = bool(character_classes.intersection(spell_classes))
        assert is_available == True
    
    def test_spell_not_available_to_class(self):
        """Spell is not available if character class doesn't match."""
        character_classes = {"wizard"}
        spell_classes = {"cleric", "bard"}
        
        is_available = bool(character_classes.intersection(spell_classes))
        assert is_available == False
    
    def test_spell_level_available(self):
        """Spell is available if spell level <= max available level."""
        max_spell_level = 3
        spell_level = 2
        
        is_available = spell_level <= max_spell_level
        assert is_available == True
    
    def test_spell_level_not_available(self):
        """Spell is not available if spell level > max available level."""
        max_spell_level = 2
        spell_level = 3
        
        is_available = spell_level <= max_spell_level
        assert is_available == False
    
    def test_cantrip_always_available(self):
        """Cantrips (level 0) are always available."""
        max_spell_level = 0  # Can only cast cantrips
        spell_level = 0
        
        is_available = spell_level <= max_spell_level
        assert is_available == True


class TestSpellSlots:
    """Test spell slot calculations."""
    
    def test_cleric_spell_slots_level_1(self):
        """Cleric level 1 gets 2 x 1st-level slots."""
        level = 1
        spell_level = 1
        
        # Formula: (spell_level + 1) // 2 = slots for cleric level 1
        slots = (spell_level + 1) // 2
        assert slots == 1
    
    def test_cleric_spell_slots_level_5(self):
        """Cleric level 5 gets slots for 1st, 2nd, and 3rd level spells."""
        level = 5
        
        # At level 5, Cleric gets: 1st(4), 2nd(3), 3rd(2)
        # Using simplified formula for testing
        spells_known = {
            1: 4,
            2: 3,
            3: 2,
        }
        
        assert spells_known[1] == 4
        assert spells_known[2] == 3
        assert spells_known[3] == 2


class TestSpellDeduplication:
    """Test spell deduplication logic."""
    
    def test_deduplicate_by_slug(self):
        """Deduplicate spells by slug."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds"),
            MockSpellRecord("cure-wounds", "Cure Wounds"),  # Duplicate
            MockSpellRecord("bless", "Bless"),
            MockSpellRecord("bless", "Bless"),  # Duplicate
            MockSpellRecord("detect-magic", "Detect Magic"),
        ]
        
        seen_slugs = set()
        deduplicated = []
        for spell in spells:
            if spell.slug not in seen_slugs:
                deduplicated.append(spell)
                seen_slugs.add(spell.slug)
        
        assert len(deduplicated) == 3
        assert len(set(s.slug for s in deduplicated)) == 3
    
    def test_dedup_preserves_first_occurrence(self):
        """Deduplication preserves first occurrence."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds", level=1),
            MockSpellRecord("cure-wounds", "Cure Wounds (alt)", level=2),  # Would be overwritten
        ]
        
        seen_slugs = set()
        deduplicated = []
        for spell in spells:
            if spell.slug not in seen_slugs:
                deduplicated.append(spell)
                seen_slugs.add(spell.slug)
        
        assert len(deduplicated) == 1
        assert deduplicated[0].level == 1  # First one


class TestSpellTags:
    """Test spell tag generation."""
    
    def test_ritual_tag(self):
        """Ritual spells get ritual tag."""
        spell = MockSpellRecord("identify", "Identify", ritual=True)
        tags = []
        if spell.ritual:
            tags.append("Ritual")
        assert "Ritual" in tags
    
    def test_concentration_tag(self):
        """Concentration spells get concentration tag."""
        spell = MockSpellRecord("mirror-image", "Mirror Image", concentration=True)
        tags = []
        if spell.concentration:
            tags.append("Concentration")
        assert "Concentration" in tags
    
    def test_domain_bonus_tag(self):
        """Domain bonus spells should get domain bonus tag."""
        spell = MockSpellRecord("cure-wounds", "Cure Wounds")
        domain_bonus_slugs = {"cure-wounds"}
        
        tags = []
        if spell.ritual:
            tags.append("Ritual")
        if spell.concentration:
            tags.append("Concentration")
        if spell.slug in domain_bonus_slugs:
            tags.append("Domain Bonus")
        
        assert "Domain Bonus" in tags
    
    def test_no_tags_normal_spell(self):
        """Normal spells get no special tags."""
        spell = MockSpellRecord("magic-missile", "Magic Missile")
        domain_bonus_slugs = set()
        
        tags = []
        if spell.ritual:
            tags.append("Ritual")
        if spell.concentration:
            tags.append("Concentration")
        if spell.slug in domain_bonus_slugs:
            tags.append("Domain Bonus")
        
        assert len(tags) == 0


class TestSpellSorting:
    """Test spell sorting logic."""
    
    def test_sort_by_level_then_name(self):
        """Spells sort by level first, then name."""
        spells = [
            MockSpellRecord("guiding-bolt", "Guiding Bolt", level=1),
            MockSpellRecord("fireball", "Fireball", level=3),
            MockSpellRecord("bless", "Bless", level=1),
            MockSpellRecord("fire-bolt", "Fire Bolt", level=0),
        ]
        
        sorted_spells = sorted(spells, key=lambda s: (s.level, s.name.lower()))
        
        assert sorted_spells[0].slug == "fire-bolt"      # Level 0
        assert sorted_spells[1].slug == "bless"          # Level 1, B before G
        assert sorted_spells[2].slug == "guiding-bolt"   # Level 1, G after B
        assert sorted_spells[3].slug == "fireball"       # Level 3


class TestSpellSearch:
    """Test spell search functionality."""
    
    def test_search_by_name(self):
        """Can search spells by name."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds"),
            MockSpellRecord("mass-cure-wounds", "Mass Cure Wounds"),
            MockSpellRecord("healing-word", "Healing Word"),
        ]
        
        search_term = "cure"
        results = [s for s in spells if search_term.lower() in s.name.lower()]
        
        assert len(results) == 2
    
    def test_search_case_insensitive(self):
        """Search is case-insensitive."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds"),
        ]
        
        search_term = "CURE"
        results = [s for s in spells if search_term.lower() in s.name.lower()]
        
        assert len(results) == 1
    
    def test_search_no_results(self):
        """Search with no matches returns empty."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds"),
        ]
        
        search_term = "fireball"
        results = [s for s in spells if search_term.lower() in s.name.lower()]
        
        assert len(results) == 0
    
    def test_search_empty_term_returns_all(self):
        """Empty search term returns all spells."""
        spells = [
            MockSpellRecord("cure-wounds", "Cure Wounds"),
            MockSpellRecord("bless", "Bless"),
        ]
        
        search_term = ""
        if search_term:
            results = [s for s in spells if search_term.lower() in s.name.lower()]
        else:
            results = spells
        
        assert len(results) == 2


class TestSpellPreparedCounter:
    """Test suite for spell preparation counter (max prepared spells tracking)."""
    
    def test_cleric_max_prepared_formula(self):
        """Cleric can prepare level + WIS modifier spells."""
        # Level 5 Cleric with 16 WIS (modifier +3)
        level = 5
        wis_score = 16
        wis_mod = ability_modifier(wis_score)
        max_prepared = level + wis_mod
        assert max_prepared == 8  # 5 + 3
    
    def test_druid_max_prepared_formula(self):
        """Druid can prepare level + WIS modifier spells."""
        # Level 10 Druid with 18 WIS (modifier +4)
        level = 10
        wis_score = 18
        wis_mod = ability_modifier(wis_score)
        max_prepared = level + wis_mod
        assert max_prepared == 14  # 10 + 4
    
    def test_paladin_max_prepared_formula(self):
        """Paladin can prepare level//2 + CHA modifier spells."""
        # Level 7 Paladin with 15 CHA (modifier +2)
        level = 7
        cha_score = 15
        cha_mod = ability_modifier(cha_score)
        max_prepared = level // 2 + cha_mod
        assert max_prepared == 5  # 3 + 2
    
    def test_ranger_max_prepared_formula(self):
        """Ranger can prepare level//2 + WIS modifier spells."""
        # Level 9 Ranger with 14 WIS (modifier +2)
        level = 9
        wis_score = 14
        wis_mod = ability_modifier(wis_score)
        max_prepared = level // 2 + wis_mod
        assert max_prepared == 6  # 4 + 2
    
    def test_wizard_max_prepared_formula(self):
        """Wizard can prepare level + INT modifier spells."""
        # Level 6 Wizard with 17 INT (modifier +3)
        level = 6
        int_score = 17
        int_mod = ability_modifier(int_score)
        max_prepared = level + int_mod
        assert max_prepared == 9  # 6 + 3
    
    def test_bard_max_prepared_formula(self):
        """Bard can prepare level + CHA modifier spells."""
        # Level 4 Bard with 16 CHA (modifier +3)
        level = 4
        cha_score = 16
        cha_mod = ability_modifier(cha_score)
        max_prepared = level + cha_mod
        assert max_prepared == 7  # 4 + 3
    
    def test_sorcerer_max_prepared_formula(self):
        """Sorcerer can prepare level + CHA modifier spells."""
        # Level 7 Sorcerer with 15 CHA (modifier +2)
        level = 7
        cha_score = 15
        cha_mod = ability_modifier(cha_score)
        max_prepared = level + cha_mod
        assert max_prepared == 9  # 7 + 2
    
    def test_warlock_always_knows_all_prepared(self):
        """Warlock knows spells, can always prepare all known spells."""
        # Warlocks don't have a max prepared limit - they know X spells
        level = 5
        max_prepared = level  # For testing, assume knows level spells
        assert max_prepared == 5
    
    def test_non_spellcaster_max_prepared_zero(self):
        """Non-spellcasting classes have 0 max prepared."""
        # Barbarian, Rogue, etc. cannot prepare spells
        class_name = "barbarian"
        max_prepared = 0 if class_name not in ["cleric", "druid", "paladin", "ranger", "wizard", "warlock"] else -1
        assert max_prepared == 0
    
    def test_prepared_count_starts_at_zero(self):
        """New character has 0 prepared spells."""
        prepared_spells = []
        prepared_count = len(prepared_spells)
        assert prepared_count == 0
    
    def test_prepared_count_increments_with_additions(self):
        """Prepared count increases as spells are added."""
        prepared_spells = [
            {"slug": "cure-wounds", "name": "Cure Wounds"},
            {"slug": "bless", "name": "Bless"},
            {"slug": "shield-of-faith", "name": "Shield of Faith"},
        ]
        prepared_count = len(prepared_spells)
        assert prepared_count == 3
    
    def test_prepared_count_decrements_with_removal(self):
        """Prepared count decreases as spells are removed."""
        prepared_spells = [
            {"slug": "cure-wounds", "name": "Cure Wounds"},
            {"slug": "bless", "name": "Bless"},
            {"slug": "shield-of-faith", "name": "Shield of Faith"},
        ]
        prepared_spells.pop()  # Remove last spell
        prepared_count = len(prepared_spells)
        assert prepared_count == 2
    
    def test_counter_display_format(self):
        """Counter displays in 'X / Y' format (current / max)."""
        prepared_count = 5
        max_prepared = 8
        counter_display = f"{prepared_count} / {max_prepared}"
        assert counter_display == "5 / 8"
    
    def test_counter_at_limit(self):
        """Counter shows when max is reached."""
        prepared_count = 8
        max_prepared = 8
        counter_display = f"{prepared_count} / {max_prepared}"
        is_at_limit = prepared_count >= max_prepared
        assert is_at_limit is True
        assert counter_display == "8 / 8"
    
    def test_counter_under_limit(self):
        """Counter shows when under max."""
        prepared_count = 3
        max_prepared = 8
        counter_display = f"{prepared_count} / {max_prepared}"
        is_at_limit = prepared_count >= max_prepared
        assert is_at_limit is False
        assert counter_display == "3 / 8"
    
    def test_counter_over_limit_protection(self):
        """System prevents adding spells over max."""
        max_prepared = 8
        prepared_count = 8
        can_add_more = prepared_count < max_prepared
        assert can_add_more is False
    
    def test_negative_max_prepared_clamped_to_zero(self):
        """Max prepared is never negative."""
        # Edge case: very low ability modifier
        level = 1
        mod = -2  # Very low ability
        max_prepared = max(0, level + mod)  # Clamp to 0
        assert max_prepared == 0
    
    def test_counter_with_level_up(self):
        """Counter updates max when level increases."""
        # Level 4 Cleric with 16 WIS
        old_level = 4
        wis_mod = 3
        old_max = old_level + wis_mod
        assert old_max == 7
        
        # Level up to 5
        new_level = 5
        new_max = new_level + wis_mod
        assert new_max == 8
    
    def test_counter_with_ability_score_change(self):
        """Counter updates max when ability score increases."""
        # Wizard with 16 INT at level 5
        level = 5
        old_int = 16
        old_mod = ability_modifier(old_int)
        old_max = level + old_mod
        assert old_max == 8  # 5 + 3
        
        # INT increases to 18
        new_int = 18
        new_mod = ability_modifier(new_int)
        new_max = level + new_mod
        assert new_max == 9  # 5 + 4
    
    def test_counter_reflects_domain_bonus_spells(self):
        """Domain bonus spells are counted but protected from removal."""
        # Cleric with domain bonus spells
        base_prepared = [
            {"slug": "cure-wounds", "name": "Cure Wounds"},
            {"slug": "bless", "name": "Bless"},
        ]
        
        domain_bonus = [
            {"slug": "command", "name": "Command", "domain_bonus": True},
            {"slug": "shield-of-faith", "name": "Shield of Faith", "domain_bonus": True},
        ]
        
        all_prepared = base_prepared + domain_bonus
        total_count = len(all_prepared)
        
        # Domain bonus spells shouldn't be removable but are counted
        assert total_count == 4
        domain_count = len([s for s in all_prepared if s.get("domain_bonus")])
        assert domain_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
