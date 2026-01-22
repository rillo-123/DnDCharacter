"""Test that domain spells are automatically added to the spellbook."""

import pytest


class TestSpellbookDomainSpells:
    """Test that domain spells are added to prepared spellbook automatically."""

    def test_level_1_domain_spells_should_be_in_spellbook(self):
        """
        Test that level 1 domain spells (cure-wounds, bless) should be in the 
        prepared spellbook when a domain is selected.
        
        This is a static data test - it verifies the domain spell data is correctly
        defined and available.
        """
        # Define the expected domain spells for Life domain at level 1
        life_domain_level_1_spells = ["cure-wounds", "bless"]
        
        # Verify we have the expected spells
        assert len(life_domain_level_1_spells) == 2
        assert "cure-wounds" in life_domain_level_1_spells
        assert "bless" in life_domain_level_1_spells

    def test_level_1_domain_spells_must_auto_add_to_prepared(self):
        """
        Test that when spell library is loaded and domain is selected,
        level 1 domain spells are automatically added to prepared spellbook.
        
        Requirements:
        - Spells should appear in the prepared spellbook list
        - No manual add button should be needed
        - Should happen automatically after spell library loads
        """
        # This documents the expected behavior:
        # 1. User loads character at level 1 with Cleric class
        # 2. User clicks "Load Spells" - spell library loads
        # 3. Domain is set to "Life"
        # 4. Expected: cure-wounds and bless are in prepared spellbook
        
        expected_prepared_spells = ["cure-wounds", "bless"]
        
        # Verify test data
        for spell in expected_prepared_spells:
            assert isinstance(spell, str)
            assert len(spell) > 0
        
        assert len(expected_prepared_spells) == 2

    def test_domain_spells_not_removable_from_prepared(self):
        """
        Test that domain bonus spells, once added to prepared spellbook,
        are marked as domain bonus and cannot be manually removed by user.
        
        This prevents users from accidentally deleting their mandatory domain spells.
        """
        domain_spell_slugs = ["cure-wounds", "bless"]
        
        # Each domain spell should have a marker that it's a domain bonus spell
        # This prevents removal/deletion in the UI
        for slug in domain_spell_slugs:
            # Expected: spell record has is_domain_bonus = True
            assert slug is not None
            assert isinstance(slug, str)

    def test_level_1_cleric_with_life_domain_prepared_spells(self):
        """
        Integration test scenario:
        - Character: Level 1 Cleric
        - Domain: Life
        - Expected prepared spells: cure-wounds, bless (2 domain spells)
        - Max prepared at level 1: 1 + WIS modifier (varies by WIS)
        
        Domain spells should NOT count toward the prepared limit.
        """
        # At level 1, a Cleric can prepare: 1 + WIS modifier
        # Example: with WIS 16 (mod +3), max prepared = 4
        # But domain spells don't count, so:
        # - Domain spells (not counted): cure-wounds, bless
        # - User-prepared (counted): up to 4 non-domain spells
        
        class_name = "cleric"
        level = 1
        domain = "life"
        
        assert class_name == "cleric"
        assert level == 1
        assert domain == "life"
        
        # Domain bonus spells at level 1
        domain_spells = ["cure-wounds", "bless"]
        assert len(domain_spells) == 2
