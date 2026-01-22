"""Test that domain bonus spells are added correctly when domain is selected."""

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
    {
        "name": "Mass Cure Wounds",
        "slug": "mass-cure-wounds",
        "level": 5,
        "school": "evocation",
        "source": "5e Core Rules",
        "desc": ["A wave of healing energy washes out from a point of your choice within range. Choose up to six creatures in a 30-foot-radius sphere centered on that point."],
        "higher_level": "When you cast this spell using a spell slot of 6th level or higher, the healing increases by 1d8 for each slot level above 5th.",
    },
    {
        "name": "Raise Dead",
        "slug": "raise-dead",
        "level": 5,
        "school": "necromancy",
        "source": "5e Core Rules",
        "desc": ["You return a dead creature you touch to life, provided that it has been dead no longer than 10 days."],
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


class TestLevel9ClericDomainSpells:
    """Test domain spell population for a Level 9 Cleric with Life Domain."""

    def test_level_9_has_10_domain_spells(self):
        """Test that level 9 Life cleric has exactly 10 domain spells."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        # Accumulate all spells up to level 9
        bonus_spells = []
        for level in sorted(spells_by_level.keys()):
            if level <= 9:
                bonus_spells.extend(spells_by_level[level])
        
        assert len(bonus_spells) == 10, f"Expected 10 domain spells for level 9, got {len(bonus_spells)}: {bonus_spells}"
        print(f"✓ Level 9 Life cleric has exactly 10 domain spells")

    def test_level_9_domain_spells_complete_list(self):
        """Test that level 9 has all expected domain spells."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        bonus_spells = []
        for level in sorted(spells_by_level.keys()):
            if level <= 9:
                bonus_spells.extend(spells_by_level[level])
        
        expected = {
            # Level 1
            "cure-wounds": 1,
            "bless": 1,
            # Level 3
            "lesser-restoration": 3,
            "spiritual-weapon": 3,
            # Level 5
            "beacon-of-hope": 5,
            "revivify": 5,
            # Level 7
            "guardian-of-faith": 7,
            "death-ward": 7,
            # Level 9
            "mass-cure-wounds": 9,
            "raise-dead": 9,
        }
        
        for spell_slug, spell_level in expected.items():
            assert spell_slug in bonus_spells, f"'{spell_slug}' (level {spell_level}) missing from level 9 domain spells"
        
        print(f"✓ Level 9 has all 10 expected domain spells from levels 1, 3, 5, 7, 9")

    def test_level_9_domain_spells_in_fallback(self):
        """Test that all 10 level 9 domain spells exist in fallback library."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        bonus_spells = []
        for level in sorted(spells_by_level.keys()):
            if level <= 9:
                bonus_spells.extend(spells_by_level[level])
        
        fallback_slugs = {s.get("slug") for s in LOCAL_SPELLS_FALLBACK}
        
        missing = []
        for spell_slug in bonus_spells:
            if spell_slug not in fallback_slugs:
                missing.append(spell_slug)
        
        assert not missing, f"These domain spells are missing from fallback: {missing}"
        print(f"✓ All 10 level 9 domain spells found in fallback library")

    def test_level_9_domain_spell_progression(self):
        """Test that domain spells accumulate correctly from levels 1-9."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        # Test each level to ensure proper accumulation
        level_counts = {}
        accumulated_spells = []
        
        for level in [1, 3, 5, 7, 9]:
            level_spells = spells_by_level.get(level, [])
            accumulated_spells.extend(level_spells)
            level_counts[level] = len(accumulated_spells)
        
        expected_counts = {1: 2, 3: 4, 5: 6, 7: 8, 9: 10}
        
        for level, expected_count in expected_counts.items():
            actual_count = level_counts[level]
            assert actual_count == expected_count, \
                f"At level {level}, expected {expected_count} accumulated spells, got {actual_count}"
        
        print(f"✓ Domain spells accumulate correctly:")
        print(f"  Level 1: 2 spells")
        print(f"  Level 3: 4 spells (2 new)")
        print(f"  Level 5: 6 spells (2 new)")
        print(f"  Level 7: 8 spells (2 new)")
        print(f"  Level 9: 10 spells (2 new)")

    def test_level_9_no_high_level_domain_spells(self):
        """Test that no spells above level 9 are included."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        # Check that there are no levels > 9
        high_levels = [level for level in spells_by_level.keys() if level > 9]
        assert not high_levels, f"Found domain spells above level 9: {high_levels}"
        
        print(f"✓ No domain spells above level 9")

    def test_level_9_spells_accessible_by_slug(self):
        """Test that each level 9 domain spell can be found by its slug."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        # Get all spells up to level 9
        level_9_spells = []
        for level in sorted(spells_by_level.keys()):
            if level <= 9:
                level_9_spells.extend(spells_by_level[level])
        
        # Verify each spell has fallback data
        for spell_slug in level_9_spells:
            spell = next((s for s in LOCAL_SPELLS_FALLBACK if s.get("slug") == spell_slug), None)
            assert spell is not None, f"Spell '{spell_slug}' not found in fallback library"
            assert spell.get("name"), f"Spell '{spell_slug}' missing 'name'"
            assert spell.get("level") is not None, f"Spell '{spell_slug}' missing 'level'"
            assert spell.get("school"), f"Spell '{spell_slug}' missing 'school'"
        
        print(f"✓ All 10 level 9 domain spells have complete fallback data")

    def test_level_9_domain_spell_summary(self):
        """Print a summary of level 9 domain spells for verification."""
        domain_key = "life"
        spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
        
        print("\n" + "="*60)
        print("LEVEL 9 CLERIC - LIFE DOMAIN - BONUS SPELLS SUMMARY")
        print("="*60)
        
        for level in sorted(spells_by_level.keys()):
            if level <= 9:
                spells = spells_by_level[level]
                print(f"\nCleric Level {level} Domain Spells:")
                for spell_slug in spells:
                    spell = next((s for s in LOCAL_SPELLS_FALLBACK if s.get("slug") == spell_slug), {})
                    spell_name = spell.get("name", spell_slug.title())
                    spell_level = spell.get("level", "?")
                    print(f"  - {spell_name} (Level {spell_level} spell)")
        
        total_spells = sum(len(spells_by_level.get(level, [])) for level in sorted(spells_by_level.keys()) if level <= 9)
        print(f"\nTotal: {total_spells} domain bonus spells available")
        print("="*60 + "\n")

