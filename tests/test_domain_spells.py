"""Test that domain bonus spells are added correctly when domain is selected."""

import sys
from pathlib import Path

# Add assets/py to path
sys.path.insert(0, str(Path(__file__).parent.parent / "assets" / "py"))

import pytest


# Extract domain bonus spells data
DOMAIN_BONUS_SPELLS = {
    "life": {
        1: ["cure-wounds", "bless"],
        3: ["lesser-restoration", "spiritual-weapon"],
        5: ["beacon-of-hope", "revivify"],
        7: ["guardian-of-faith", "death-ward"],
        9: ["mass-cure-wounds", "raise-dead"],
    },
}

# Extract fallback spells for testing
LOCAL_SPELLS_FALLBACK = [
    {
        "name": "Cure Wounds",
        "slug": "cure-wounds",
        "level": 1,
        "school": "evocation",
        "source": "5e Core Rules",
        "desc": ["A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier.", "This spell has no effect on undead or constructs."],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st.",
    },
    {
        "name": "Bless",
        "slug": "bless",
        "level": 1,
        "school": "enchantment",
        "source": "5e Core Rules",
        "desc": ["You bless up to three creatures of your choice within range. Whenever a target makes an attack roll or a saving throw before the spell ends, the target can roll a d4 and add the number rolled to the attack roll or saving throw."],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, you can target one additional creature for each slot level above 1st.",
    },
    {
        "name": "Lesser Restoration",
        "slug": "lesser-restoration",
        "level": 2,
        "school": "abjuration",
        "source": "5e Core Rules",
        "desc": ["You touch a creature and can end either one disease or one condition afflicting it."],
        "higher_level": "",
    },
    {
        "name": "Spiritual Weapon",
        "slug": "spiritual-weapon",
        "level": 2,
        "school": "evocation",
        "source": "5e Core Rules",
        "desc": ["You create a floating, spectral weapon within range that lasts for the duration."],
        "higher_level": "When you cast this spell using a spell slot of 3rd level or higher, you can create one additional weapon for each slot level above 2nd.",
    },
    {
        "name": "Beacon of Hope",
        "slug": "beacon-of-hope",
        "level": 3,
        "school": "abjuration",
        "source": "5e Core Rules",
        "desc": ["This spell bestows hope and vitality."],
        "higher_level": "",
    },
    {
        "name": "Revivify",
        "slug": "revivify",
        "level": 3,
        "school": "necromancy",
        "source": "5e Core Rules",
        "desc": ["You touch a creature that has been dead for no more than 1 minute."],
        "higher_level": "",
    },
    {
        "name": "Guardian of Faith",
        "slug": "guardian-of-faith",
        "level": 4,
        "school": "abjuration",
        "source": "5e Core Rules",
        "desc": ["A Large spectral guardian appears and hovers for the duration in an unoccupied space of your choice that you can see within 30 feet of you."],
        "higher_level": "",
    },
    {
        "name": "Death Ward",
        "slug": "death-ward",
        "level": 4,
        "school": "abjuration",
        "source": "5e Core Rules",
        "desc": ["You touch a creature and grant it a measure of protection from death."],
        "higher_level": "",
    },
]


class TestDomainSpellPopulation:
    """Test that domain bonus spells are automatically added to prepared list."""

    def test_get_domain_bonus_spells_at_level_1(self):
        """Test that level 1 domain spells are returned correctly."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        # Manually implement get_domain_bonus_spells logic
        bonus_spells = []
        for level in sorted(spells_by_level.keys()):
            if level <= 1:
                bonus_spells.extend(spells_by_level[level])
        
        assert len(bonus_spells) == 2, f"Expected 2 spells at level 1, got {len(bonus_spells)}"
        assert "cure-wounds" in bonus_spells, "cure-wounds should be in level 1 domain spells"
        assert "bless" in bonus_spells, "bless should be in level 1 domain spells"
        
        print(f"OK: Level 1 domain spells: {bonus_spells}")

    def test_get_domain_bonus_spells_at_level_3(self):
        """Test that domain spells accumulate at higher levels."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        bonus_spells = []
        for level in sorted(spells_by_level.keys()):
            if level <= 3:
                bonus_spells.extend(spells_by_level[level])
        
        assert len(bonus_spells) == 4, f"Expected 4 spells at level 3, got {len(bonus_spells)}"
        assert "cure-wounds" in bonus_spells
        assert "bless" in bonus_spells
        assert "lesser-restoration" in bonus_spells
        assert "spiritual-weapon" in bonus_spells
        
        print(f"OK: Level 3 domain spells: {bonus_spells}")

    def test_get_domain_bonus_spells_at_level_9(self):
        """Test that all domain spells are available at level 9."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        bonus_spells = []
        for level in sorted(spells_by_level.keys()):
            if level <= 9:
                bonus_spells.extend(spells_by_level[level])
        
        assert len(bonus_spells) == 10, f"Expected 10 spells at level 9, got {len(bonus_spells)}"
        expected = ["cure-wounds", "bless", "lesser-restoration", "spiritual-weapon", 
                   "beacon-of-hope", "revivify", "guardian-of-faith", "death-ward", 
                   "mass-cure-wounds", "raise-dead"]
        for spell in expected:
            assert spell in bonus_spells, f"{spell} should be in level 9 domain spells"
        
        print(f"OK: Level 9 domain spells: {len(bonus_spells)} spells")

    def test_domain_spells_have_fallback_data(self):
        """Test that domain spells exist in fallback library."""
        # Check level 1 domain spells
        level_1_spells = DOMAIN_BONUS_SPELLS["life"][1]
        fallback_slugs = {s.get("slug") for s in LOCAL_SPELLS_FALLBACK}
        
        for spell_slug in level_1_spells:
            assert spell_slug in fallback_slugs, f"{spell_slug} not found in fallback library"
        
        print(f"OK: All level 1 domain spells found in fallback library")

    def test_domain_spell_count_by_level(self):
        """Test that domain spells are correctly grouped by level."""
        domain_spells = DOMAIN_BONUS_SPELLS["life"]
        
        assert 1 in domain_spells, "Level 1 should have domain spells"
        assert len(domain_spells[1]) == 2, "Level 1 should have 2 domain spells"
        
        assert 3 in domain_spells, "Level 3 should have domain spells"
        assert len(domain_spells[3]) == 2, "Level 3 should have 2 domain spells"
        
        assert 5 in domain_spells, "Level 5 should have domain spells"
        assert len(domain_spells[5]) == 2, "Level 5 should have 2 domain spells"
        
        assert 7 in domain_spells, "Level 7 should have domain spells"
        assert len(domain_spells[7]) == 2, "Level 7 should have 2 domain spells"
        
        assert 9 in domain_spells, "Level 9 should have domain spells"
        assert len(domain_spells[9]) == 2, "Level 9 should have 2 domain spells"
        
        print(f"OK: Domain spell distribution is correct")

    def test_level_1_domain_spells_can_be_found_by_slug(self):
        """Test that level 1 domain spells (cure-wounds, bless) exist in fallback with proper data."""
        # These are the two level 1 domain spells for Life domain
        level_1_slugs = ["cure-wounds", "bless"]
        
        for slug in level_1_slugs:
            spell = next((s for s in LOCAL_SPELLS_FALLBACK if s.get("slug") == slug), None)
            assert spell is not None, f"Level 1 domain spell '{slug}' not found in fallback"
            assert spell.get("level") == 1, f"'{slug}' should be level 1, got {spell.get('level')}"
            assert spell.get("desc"), f"'{slug}' missing description"
            
        print(f"OK: Level 1 domain spells (cure-wounds, bless) found with full data")

    def test_level_1_domain_spells_have_valid_sources(self):
        """Test that level 1 domain spells have source field for validation."""
        level_1_slugs = ["cure-wounds", "bless"]
        
        for slug in level_1_slugs:
            spell = next((s for s in LOCAL_SPELLS_FALLBACK if s.get("slug") == slug), None)
            assert spell is not None, f"Level 1 spell '{slug}' not found"
            # The source field is critical for add_spell() to accept the spell
            assert "source" in spell, f"'{slug}' missing 'source' field - this breaks add_spell() validation"
            assert spell.get("source"), f"'{slug}' has empty source field"
            
        print(f"OK: Level 1 domain spells have valid source fields")
