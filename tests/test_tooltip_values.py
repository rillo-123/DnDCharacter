"""
Unit tests for tooltip_values.py - Testing TooltipValue entities and inheritance.
"""

import pytest
from tooltip_values import (
    TooltipValue,
    AbilityScoreValue,
    SaveValue,
    SkillValue,
    WeaponToHitValue,
    DamageValue,
    format_tooltip_html,
)


class TestTooltipValueBase:
    """Test base TooltipValue class."""
    
    def test_tooltip_value_initialization(self):
        """Test basic initialization."""
        tv = TooltipValue(label="Test", total=5)
        assert tv.label == "Test"
        assert tv.total == 5
        assert tv.components == []
    
    def test_add_component(self):
        """Test adding components."""
        tv = TooltipValue()
        result = tv.add_component("Mod", 3)
        
        assert result is tv  # Check chaining
        assert len(tv.components) == 1
        assert tv.components[0] == ("Mod", 3)
    
    def test_add_multiple_components(self):
        """Test adding multiple components."""
        tv = TooltipValue()
        tv.add_component("Mod", 2).add_component("Prof", 3).add_component("Bonus", 1)
        
        assert len(tv.components) == 3
        assert tv.components == [("Mod", 2), ("Prof", 3), ("Bonus", 1)]
    
    def test_recalculate_total(self):
        """Test recalculating total from components."""
        tv = TooltipValue(total=0)
        tv.add_component("Base", 10)
        tv.add_component("Bonus", 2)
        
        total = tv.recalculate_total()
        assert total == 12
        assert tv.total == 12
    
    def test_format_bonus_positive(self):
        """Test format_bonus with positive values."""
        tv = TooltipValue()
        assert tv.format_bonus(3) == "+3"
        assert tv.format_bonus(0) == "—"
        assert tv.format_bonus(-2) == "-2"
    
    def test_generate_tooltip_html_empty(self):
        """Test HTML generation with no components."""
        tv = TooltipValue()
        assert tv.generate_tooltip_html() == ""
    
    def test_generate_tooltip_html_with_components(self):
        """Test HTML generation with components."""
        tv = TooltipValue()
        tv.add_component("STR mod", 3)
        tv.add_component("Proficiency", 2)
        
        html = tv.generate_tooltip_html()
        assert '<div class="stat-tooltip multiline">' in html
        assert 'STR mod' in html
        assert 'Proficiency' in html
        assert '+3' in html
        assert '+2' in html


class TestAbilityScoreValue:
    """Test AbilityScoreValue class."""
    
    def test_ability_score_base_only(self):
        """Test ability score with base score only."""
        asv = AbilityScoreValue(ability="str", base_score=15)
        
        assert asv.ability == "STR"
        assert asv.total == 15
        assert asv.base_score == 15
        assert asv.race_bonus == 0
        assert len(asv.components) == 1
    
    def test_ability_score_with_race_bonus(self):
        """Test ability score with race bonus."""
        asv = AbilityScoreValue(ability="dex", base_score=14, race_bonus=2)
        
        assert asv.ability == "DEX"
        assert asv.total == 16
        assert asv.race_bonus == 2
        assert len(asv.components) == 2
        assert asv.components[0] == ("Base DEX", 14)
        assert asv.components[1] == ("Race bonus", 2)
    
    def test_ability_score_tooltip_html(self):
        """Test HTML tooltip for ability score."""
        asv = AbilityScoreValue(ability="con", base_score=13, race_bonus=1)
        html = asv.generate_tooltip_html()
        
        assert "Base CON" in html
        assert "Race bonus" in html
        assert "13" in html
        assert "1" in html
    
    def test_ability_score_all_abilities(self):
        """Test all six abilities."""
        abilities = ["str", "dex", "con", "int", "wis", "cha"]
        for ability in abilities:
            asv = AbilityScoreValue(ability=ability, base_score=10)
            assert asv.ability == ability.upper()
            assert asv.total == 10


class TestSaveValue:
    """Test SaveValue class."""
    
    def test_save_not_proficient(self):
        """Test save without proficiency."""
        sv = SaveValue(ability="str", ability_mod=3, proficiency=2, is_proficient=False)
        
        assert sv.total == 3
        assert len(sv.components) == 1
        assert sv.components[0] == ("Ability mod (STR)", 3)
    
    def test_save_with_proficiency(self):
        """Test save with proficiency."""
        sv = SaveValue(ability="dex", ability_mod=2, proficiency=3, is_proficient=True)
        
        assert sv.total == 5  # 2 + 3
        assert len(sv.components) == 2
        assert sv.components[0] == ("Ability mod (DEX)", 2)
        assert sv.components[1] == ("Proficiency", 3)
    
    def test_save_with_item_modifiers(self):
        """Test save with item modifiers."""
        sv = SaveValue(ability="con", ability_mod=1, proficiency=2, 
                      is_proficient=True, item_modifiers=1)
        
        assert sv.total == 4  # 1 + 2 + 1
        assert len(sv.components) == 3
        assert ("Item modifiers", 1) in sv.components
    
    def test_save_tooltip_html(self):
        """Test HTML tooltip for save."""
        sv = SaveValue(ability="wis", ability_mod=4, proficiency=2, is_proficient=True)
        html = sv.generate_tooltip_html()
        
        assert "WIS Save" in html or "Ability mod (WIS)" in html
        assert "Proficiency" in html


class TestSkillValue:
    """Test SkillValue class."""
    
    def test_skill_basic(self):
        """Test basic skill without proficiency."""
        sv = SkillValue(skill_name="Acrobatics", ability="dex", ability_mod=3)
        
        assert sv.total == 3
        assert len(sv.components) == 1
        assert sv.components[0] == ("DEX mod", 3)
    
    def test_skill_with_proficiency(self):
        """Test skill with proficiency."""
        sv = SkillValue(skill_name="Athletics", ability="str", ability_mod=2,
                       proficiency=2, is_proficient=True)
        
        assert sv.total == 4  # 2 + 2
        assert len(sv.components) == 2
    
    def test_skill_with_expertise(self):
        """Test skill with expertise (doubles proficiency)."""
        sv = SkillValue(skill_name="Stealth", ability="dex", ability_mod=1,
                       proficiency=2, is_expertise=True)
        
        assert sv.total == 5  # 1 + (2 * 2)
        assert ("Expertise", 4) in sv.components
    
    def test_skill_with_race_bonus(self):
        """Test skill with race bonus."""
        sv = SkillValue(skill_name="Perception", ability="wis", ability_mod=2,
                       race_bonus=1, proficiency=2, is_proficient=True)
        
        assert sv.total == 5  # 2 + 1 + 2
        assert ("Race bonus", 1) in sv.components


class TestWeaponToHitValue:
    """Test WeaponToHitValue class."""
    
    def test_weapon_tohit_basic(self):
        """Test basic weapon to-hit calculation."""
        w = WeaponToHitValue(weapon_name="Longsword", ability="str", 
                            ability_mod=3, proficiency=2)
        
        assert w.weapon_name == "Longsword"
        assert w.ability == "STR"
        assert w.total == 5  # 3 + 2
        assert len(w.components) == 2
    
    def test_weapon_tohit_with_bonus(self):
        """Test weapon to-hit with magical bonus."""
        w = WeaponToHitValue(weapon_name="Longsword +1", ability="str",
                            ability_mod=3, proficiency=2, weapon_bonus=1)
        
        assert w.total == 6  # 3 + 2 + 1
        assert len(w.components) == 3
        assert w.components[2] == ("Weapon bonus", 1)
    
    def test_weapon_tohit_ranged(self):
        """Test ranged weapon (uses DEX)."""
        w = WeaponToHitValue(weapon_name="Light Crossbow", ability="dex",
                            ability_mod=2, proficiency=2)
        
        assert w.ability == "DEX"
        assert w.total == 4
    
    def test_weapon_tohit_tooltip_html(self):
        """Test HTML tooltip for weapon to-hit."""
        w = WeaponToHitValue(weapon_name="Dagger", ability="str",
                            ability_mod=1, proficiency=2, weapon_bonus=0)
        html = w.generate_tooltip_html()
        
        assert "STR mod" in html
        assert "Proficiency" in html
        assert "+1" in html
        assert "+2" in html
    
    def test_weapon_tohit_negative_mod(self):
        """Test weapon to-hit with negative ability modifier."""
        w = WeaponToHitValue(weapon_name="Greatclub", ability="str",
                            ability_mod=-1, proficiency=2)
        
        assert w.total == 1  # -1 + 2


class TestDamageValue:
    """Test DamageValue class."""
    
    def test_damage_no_modifiers(self):
        """Test damage with no modifiers."""
        d = DamageValue(damage_dice="1d8", damage_type="slashing")
        
        assert d.damage_dice == "1d8"
        assert d.damage_type == "slashing"
        assert d.label == "1d8 slashing"
        assert d.total == 0
    
    def test_damage_with_ability_mod(self):
        """Test damage with ability modifier."""
        d = DamageValue(damage_dice="1d8", damage_type="piercing", ability_mod=3)
        
        assert d.total == 3
        assert len(d.components) == 1
        assert ("Ability mod", 3) in d.components
    
    def test_damage_with_bonus(self):
        """Test damage with weapon bonus."""
        d = DamageValue(damage_dice="1d6", damage_type="slashing",
                       ability_mod=2, weapon_bonus=1)
        
        assert d.total == 3
        assert len(d.components) == 2
        assert ("Ability mod", 2) in d.components
        assert ("Weapon bonus", 1) in d.components
    
    def test_damage_no_type(self):
        """Test damage without type specified."""
        d = DamageValue(damage_dice="2d6")
        assert d.label == "2d6"


class TestFormatTooltipHtml:
    """Test utility function for formatting tooltip HTML."""
    
    def test_format_tooltip_no_title(self):
        """Test formatting tooltip without title."""
        html = format_tooltip_html("", [("STR mod", 3), ("Proficiency", 2)])
        
        assert '<div class="stat-tooltip multiline">' in html
        assert "STR mod" in html
        assert "+3" in html
        assert "+2" in html
    
    def test_format_tooltip_with_title(self):
        """Test formatting tooltip with title."""
        html = format_tooltip_html("Attack Bonus", [("STR mod", 2), ("Proficiency", 3)])
        
        assert "Attack Bonus" in html
        assert "STR mod" in html
    
    def test_format_tooltip_negative_values(self):
        """Test formatting with negative values."""
        html = format_tooltip_html("Save", [("Ability mod", -2), ("Proficiency", 2)])
        
        assert "-2" in html
        assert "+2" in html
    
    def test_format_tooltip_zero_values(self):
        """Test formatting with zero values."""
        html = format_tooltip_html("Skill", [("Ability mod", 0)])
        
        assert "0" in html


class TestInheritance:
    """Test that inheritance chain works correctly."""
    
    def test_all_tooltip_values_are_tooltip_value(self):
        """Test that all specialized values inherit from TooltipValue."""
        asv = AbilityScoreValue()
        sv = SaveValue()
        skv = SkillValue()
        w = WeaponToHitValue()
        d = DamageValue()
        
        for obj in [asv, sv, skv, w, d]:
            assert isinstance(obj, TooltipValue)
            assert hasattr(obj, 'add_component')
            assert hasattr(obj, 'generate_tooltip_html')
            assert hasattr(obj, 'format_bonus')
    
    def test_polymorphic_usage(self):
        """Test that all tooltip values can be used polymorphically."""
        values = [
            AbilityScoreValue(ability="str", base_score=15),
            SaveValue(ability="dex", ability_mod=2, proficiency=2, is_proficient=True),
            SkillValue(skill_name="Acrobatics", ability="dex", ability_mod=3),
            WeaponToHitValue(weapon_name="Longsword", ability="str", 
                            ability_mod=3, proficiency=2),
        ]
        
        for val in values:
            assert isinstance(val, TooltipValue)
            assert val.total >= 0
            html = val.generate_tooltip_html()
            assert isinstance(html, str)
            if len(val.components) > 0:
                assert '<div class="stat-tooltip multiline">' in html


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
