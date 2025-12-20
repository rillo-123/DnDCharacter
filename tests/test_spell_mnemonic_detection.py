"""Test spell save mnemonic detection logic."""

import re
import pytest


class TestSpellMnemonicDetection:
    """Test that spell mnemonics are correctly detected."""

    def _detect_save_mnemonic(self, spell_desc):
        """Simulate the save mnemonic detection logic from character.py."""
        # Only match if the spell text says the target "must" make a save or "fails" one
        # This filters out spells like Bless that just mention saving throws as optional outcomes
        save_regex = re.compile(
            r"(?:must\s+(?:succeed\s+on\s+|make\s+)(?:a|an)\s+|if\s+it\s+fails\s+(?:a|an)\s+)"
            r"(strength|dexterity|constitution|intelligence|wisdom|charisma)\s+saving throw",
            re.IGNORECASE
        )
        
        ability_map = {
            "strength": "STR",
            "dexterity": "DEX",
            "constitution": "CON",
            "intelligence": "INT",
            "wisdom": "WIS",
            "charisma": "CHA",
        }
        
        save_ability = None
        match = save_regex.search(spell_desc)
        if match:
            ability = match.group(1).lower()
            save_ability = ability_map.get(ability)
        
        return save_ability

    def test_bless_no_save_mnemonic(self):
        """Bless should NOT have a save mnemonic (it just mentions saving throws)."""
        bless_desc = (
            "You bless up to three creatures of your choice within range. "
            "Whenever a target makes an attack roll or a saving throw before the spell ends, "
            "the target can roll a d4 and add the number rolled to the attack roll or saving throw."
        )
        
        result = self._detect_save_mnemonic(bless_desc)
        assert result is None, "Bless should not have a save mnemonic"
        print("✓ Bless has no save mnemonic")

    def test_sacred_flame_has_dex_save(self):
        """Sacred Flame requires a Dexterity save."""
        sacred_flame_desc = (
            "Flame-like radiance descends on a creature you can see within range. "
            "The target must succeed on a Dexterity saving throw or take 1d8 radiant damage."
        )
        
        result = self._detect_save_mnemonic(sacred_flame_desc)
        assert result == "DEX", f"Sacred Flame should have DEX save, got {result}"
        print("✓ Sacred Flame has DEX save mnemonic")

    def test_faerie_fire_has_dex_save(self):
        """Faerie Fire requires a Dexterity save."""
        faerie_fire_desc = (
            "Each object in a 20-foot cube within range is outlined in blue, green, or violet light. "
            "Any creature in the area when the spell is cast is also outlined in light "
            "if it fails a Dexterity saving throw."
        )
        
        result = self._detect_save_mnemonic(faerie_fire_desc)
        assert result == "DEX", f"Faerie Fire should have DEX save, got {result}"
        print("✓ Faerie Fire has DEX save mnemonic")

    def test_shatter_has_con_save(self):
        """Shatter requires a Constitution save."""
        shatter_desc = (
            "A sudden loud ringing noise, painfully intense, erupts from a point of your choice within range. "
            "Each creature in a 10-foot-radius sphere centered on that point must make a Constitution saving throw, "
            "taking 3d8 thunder damage on a failed save, or half as much damage on a successful one."
        )
        
        result = self._detect_save_mnemonic(shatter_desc)
        assert result == "CON", f"Shatter should have CON save, got {result}"
        print("✓ Shatter has CON save mnemonic")

    def test_hold_person_has_wis_save(self):
        """Hold Person requires a Wisdom save."""
        hold_person_desc = (
            "Choose a humanoid that you can see within range. "
            "The target must succeed on a Wisdom saving throw or be paralyzed for the duration."
        )
        
        result = self._detect_save_mnemonic(hold_person_desc)
        assert result == "WIS", f"Hold Person should have WIS save, got {result}"
        print("✓ Hold Person has WIS save mnemonic")

    def test_vicious_mockery_has_wis_save(self):
        """Vicious Mockery requires a Wisdom save."""
        vicious_mockery_desc = (
            "You unleash a string of insults laced with subtle enchantments at a creature you can see within range. "
            "If the target can hear you, it must succeed on a Wisdom saving throw "
            "or take 1d4 psychic damage and have disadvantage on the next attack roll it makes before the end of its next turn."
        )
        
        result = self._detect_save_mnemonic(vicious_mockery_desc)
        assert result == "WIS", f"Vicious Mockery should have WIS save, got {result}"
        print("✓ Vicious Mockery has WIS save mnemonic")

    def test_word_of_radiance_has_con_save(self):
        """Word of Radiance requires a Constitution save."""
        word_of_radiance_desc = (
            "You utter a divine word, and burning radiance erupts from you. "
            "Each creature of your choice that you can see within 5 feet of you must succeed on a Constitution saving throw "
            "or take 1d6 radiant damage."
        )
        
        result = self._detect_save_mnemonic(word_of_radiance_desc)
        assert result == "CON", f"Word of Radiance should have CON save, got {result}"
        print("✓ Word of Radiance has CON save mnemonic")

    def test_toll_the_dead_has_wis_save(self):
        """Toll the Dead requires a Wisdom save."""
        toll_the_dead_desc = (
            "You point at one creature you can see within range. "
            "The creature must make a Wisdom saving throw."
        )
        
        result = self._detect_save_mnemonic(toll_the_dead_desc)
        assert result == "WIS", f"Toll the Dead should have WIS save, got {result}"
        print("✓ Toll the Dead has WIS save mnemonic")

    def test_cure_wounds_no_save(self):
        """Cure Wounds should NOT have a save mnemonic."""
        cure_wounds_desc = (
            "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier. "
            "This spell has no effect on undead or constructs."
        )
        
        result = self._detect_save_mnemonic(cure_wounds_desc)
        assert result is None, "Cure Wounds should not have a save mnemonic"
        print("✓ Cure Wounds has no save mnemonic")

    def test_healing_word_no_save(self):
        """Healing Word should NOT have a save mnemonic."""
        healing_word_desc = (
            "A creature of your choice that you can see within range regains hit points "
            "equal to 1d4 + your spellcasting ability modifier. "
            "This spell has no effect on undead or constructs."
        )
        
        result = self._detect_save_mnemonic(healing_word_desc)
        assert result is None, "Healing Word should not have a save mnemonic"
        print("✓ Healing Word has no save mnemonic")

    def test_detect_magic_no_save(self):
        """Detect Magic should NOT have a save mnemonic."""
        detect_magic_desc = (
            "For the duration, you sense the presence of magic within 30 feet of you. "
            "If you sense magic in this way, you can use your action to see a faint aura around "
            "any visible creature or object in the area that bears magic, and you learn its school of magic, if any."
        )
        
        result = self._detect_save_mnemonic(detect_magic_desc)
        assert result is None, "Detect Magic should not have a save mnemonic"
        print("✓ Detect Magic has no save mnemonic")

    def test_case_insensitivity(self):
        """Save detection should be case-insensitive."""
        # All uppercase
        desc_upper = "The target MUST SUCCEED ON A DEXTERITY SAVING THROW or take damage."
        result = self._detect_save_mnemonic(desc_upper)
        assert result == "DEX", f"Should handle uppercase, got {result}"
        
        # Mixed case
        desc_mixed = "The target Must Succeed On A Dexterity Saving Throw or take damage."
        result = self._detect_save_mnemonic(desc_mixed)
        assert result == "DEX", f"Should handle mixed case, got {result}"
        
        print("✓ Case insensitivity works correctly")

    def test_all_ability_names(self):
        """Test all ability names are recognized."""
        test_cases = [
            ("must succeed on a strength saving throw", "STR"),
            ("must succeed on a dexterity saving throw", "DEX"),
            ("must make a constitution saving throw", "CON"),
            ("must make an intelligence saving throw", "INT"),
            ("must succeed on a wisdom saving throw", "WIS"),
            ("must make a charisma saving throw", "CHA"),
        ]
        
        for desc, expected_ability in test_cases:
            result = self._detect_save_mnemonic(desc)
            assert result == expected_ability, (
                f"For '{desc}', expected {expected_ability}, got {result}"
            )
        
        print("✓ All ability names recognized correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
