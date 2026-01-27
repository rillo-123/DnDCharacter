"""
Test Character Combat Properties

Tests the new combat properties added to the Character class:
- proficiency_bonus
- initiative_bonus  
- speed
- passive_perception
- passive_investigation
- passive_insight
"""

import sys
import os
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'static', 'assets', 'py'))

from character_models import Character


class TestCharacterProficiencyBonus(unittest.TestCase):
    """Test Character.proficiency_bonus property."""
    
    def test_proficiency_bonus_level_1(self):
        """Proficiency bonus is +2 at level 1."""
        char = Character({"level": 1})
        self.assertEqual(char.proficiency_bonus, 2)
    
    def test_proficiency_bonus_level_5(self):
        """Proficiency bonus is +3 at level 5."""
        char = Character({"level": 5})
        self.assertEqual(char.proficiency_bonus, 3)
    
    def test_proficiency_bonus_level_9(self):
        """Proficiency bonus is +4 at level 9."""
        char = Character({"level": 9})
        self.assertEqual(char.proficiency_bonus, 4)
    
    def test_proficiency_bonus_level_13(self):
        """Proficiency bonus is +5 at level 13."""
        char = Character({"level": 13})
        self.assertEqual(char.proficiency_bonus, 5)
    
    def test_proficiency_bonus_level_17(self):
        """Proficiency bonus is +6 at level 17."""
        char = Character({"level": 17})
        self.assertEqual(char.proficiency_bonus, 6)
    
    def test_proficiency_bonus_level_20(self):
        """Proficiency bonus is +6 at level 20."""
        char = Character({"level": 20})
        self.assertEqual(char.proficiency_bonus, 6)


class TestCharacterInitiativeBonus(unittest.TestCase):
    """Test Character.initiative_bonus property."""
    
    def test_initiative_with_dex_10(self):
        """Initiative is +0 with DEX 10."""
        char = Character({"abilities": {"dex": {"score": 10}}})
        self.assertEqual(char.initiative_bonus, 0)
    
    def test_initiative_with_dex_14(self):
        """Initiative is +2 with DEX 14."""
        char = Character({"abilities": {"dex": {"score": 14}}})
        self.assertEqual(char.initiative_bonus, 2)
    
    def test_initiative_with_dex_18(self):
        """Initiative is +4 with DEX 18."""
        char = Character({"abilities": {"dex": {"score": 18}}})
        self.assertEqual(char.initiative_bonus, 4)
    
    def test_initiative_with_dex_8(self):
        """Initiative is -1 with DEX 8."""
        char = Character({"abilities": {"dex": {"score": 8}}})
        self.assertEqual(char.initiative_bonus, -1)
    
    def test_initiative_with_no_dex(self):
        """Initiative defaults to +0 when DEX not set (defaults to 10)."""
        char = Character({})
        self.assertEqual(char.initiative_bonus, 0)


class TestCharacterSpeed(unittest.TestCase):
    """Test Character.speed property."""
    
    def test_speed_default(self):
        """Speed defaults to 30 feet."""
        char = Character({})
        self.assertEqual(char.speed, 30)
    
    def test_speed_custom(self):
        """Speed can be set to custom value."""
        char = Character({"speed": 40})
        self.assertEqual(char.speed, 40)


class TestCharacterPassivePerception(unittest.TestCase):
    """Test Character.passive_perception property."""
    
    def test_passive_perception_base(self):
        """Passive perception is 10 + WIS mod with no proficiency."""
        char = Character({"abilities": {"wis": {"score": 14}}, "skills": {}})
        self.assertEqual(char.passive_perception, 12)  # 10 + 2
    
    def test_passive_perception_with_proficiency(self):
        """Passive perception adds proficiency when proficient."""
        char = Character({
            "level": 5,
            "abilities": {"wis": {"score": 14}},
            "skills": {"perception": 1}  # Proficient
        })
        self.assertEqual(char.passive_perception, 15)  # 10 + 2 (WIS) + 3 (prof)
    
    def test_passive_perception_with_expertise(self):
        """Passive perception adds double proficiency with expertise."""
        char = Character({
            "level": 5,
            "abilities": {"wis": {"score": 14}},
            "skills": {"perception": 2}  # Expertise
        })
        self.assertEqual(char.passive_perception, 18)  # 10 + 2 (WIS) + 6 (2x prof)
    
    def test_passive_perception_low_wisdom(self):
        """Passive perception with low WIS."""
        char = Character({"abilities": {"wis": {"score": 8}}, "skills": {}})
        self.assertEqual(char.passive_perception, 9)  # 10 - 1
    
    def test_passive_perception_no_skills_data(self):
        """Passive perception works without skills data."""
        char = Character({"abilities": {"wis": {"score": 12}}})
        self.assertEqual(char.passive_perception, 11)  # 10 + 1


class TestCharacterPassiveInvestigation(unittest.TestCase):
    """Test Character.passive_investigation property."""
    
    def test_passive_investigation_base(self):
        """Passive investigation is 10 + INT mod with no proficiency."""
        char = Character({"abilities": {"int": {"score": 16}}, "skills": {}})
        self.assertEqual(char.passive_investigation, 13)  # 10 + 3
    
    def test_passive_investigation_with_proficiency(self):
        """Passive investigation adds proficiency when proficient."""
        char = Character({
            "level": 9,
            "abilities": {"int": {"score": 16}},
            "skills": {"investigation": 1}
        })
        self.assertEqual(char.passive_investigation, 17)  # 10 + 3 (INT) + 4 (prof)
    
    def test_passive_investigation_with_expertise(self):
        """Passive investigation adds double proficiency with expertise."""
        char = Character({
            "level": 9,
            "abilities": {"int": {"score": 16}},
            "skills": {"investigation": 2}
        })
        self.assertEqual(char.passive_investigation, 21)  # 10 + 3 (INT) + 8 (2x prof)


class TestCharacterPassiveInsight(unittest.TestCase):
    """Test Character.passive_insight property."""
    
    def test_passive_insight_base(self):
        """Passive insight is 10 + WIS mod with no proficiency."""
        char = Character({"abilities": {"wis": {"score": 16}}, "skills": {}})
        self.assertEqual(char.passive_insight, 13)  # 10 + 3
    
    def test_passive_insight_with_proficiency(self):
        """Passive insight adds proficiency when proficient."""
        char = Character({
            "level": 13,
            "abilities": {"wis": {"score": 16}},
            "skills": {"insight": 1}
        })
        self.assertEqual(char.passive_insight, 18)  # 10 + 3 (WIS) + 5 (prof)
    
    def test_passive_insight_with_expertise(self):
        """Passive insight adds double proficiency with expertise."""
        char = Character({
            "level": 13,
            "abilities": {"wis": {"score": 16}},
            "skills": {"insight": 2}
        })
        self.assertEqual(char.passive_insight, 23)  # 10 + 3 (WIS) + 10 (2x prof)


class TestCharacterCombatPropertiesIntegration(unittest.TestCase):
    """Test integration of combat properties."""
    
    def test_all_properties_available(self):
        """All combat properties are accessible."""
        char = Character({
            "level": 8,
            "abilities": {
                "str": {"score": 12}, "dex": {"score": 14}, "con": {"score": 13},
                "int": {"score": 10}, "wis": {"score": 16}, "cha": {"score": 8}
            },
            "skills": {"perception": 1, "investigation": 0, "insight": 1}
        })
        
        # All properties should be accessible
        self.assertIsInstance(char.proficiency_bonus, int)
        self.assertIsInstance(char.initiative_bonus, int)
        self.assertIsInstance(char.speed, int)
        self.assertIsInstance(char.passive_perception, int)
        self.assertIsInstance(char.passive_investigation, int)
        self.assertIsInstance(char.passive_insight, int)
    
    def test_cleric_level_8_combat_properties(self):
        """Verify combat properties for level 8 Cleric (Enwer)."""
        char = Character({
            "level": 8,
            "abilities": {
                "str": {"score": 12}, "dex": {"score": 10}, "con": {"score": 14},
                "int": {"score": 8}, "wis": {"score": 18}, "cha": {"score": 14}
            },
            "skills": {"perception": 1, "insight": 1}  # Proficient
        })
        
        self.assertEqual(char.proficiency_bonus, 3)  # Level 8 = +3
        self.assertEqual(char.initiative_bonus, 0)  # DEX 10 = +0
        self.assertEqual(char.passive_perception, 17)  # 10 + 4 (WIS) + 3 (prof)
        self.assertEqual(char.passive_investigation, 9)  # 10 - 1 (INT), no prof
        self.assertEqual(char.passive_insight, 17)  # 10 + 4 (WIS) + 3 (prof)


if __name__ == '__main__':
    unittest.main()
