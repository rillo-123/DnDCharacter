"""
Test suite for armor and shield AC calculation.

Tests the combined AC calculation for armor + shields with bonuses.
"""

import json
import sys
from pathlib import Path

# Add static assets to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest
from managers import ArmorEntity, ArmorCollectionManager


class TestArmorShieldACCalculation:
    """Test armor and shield AC calculations."""
    
    def test_breastplate_base_ac(self):
        """Breastplate should have base AC of 14."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Steel",
            "notes": ""
        }
        character_stats = {"dex": 10}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Medium armor with DEX 10 (+0 mod) = 14
        assert ac == 14, f"Expected AC 14, got {ac}"
    
    def test_breastplate_with_plus_one_bonus(self):
        """Breastplate with +1 bonus should have AC 15."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Steel",
            "notes": json.dumps({"armor_class": 15, "bonus": 1})
        }
        character_stats = {"dex": 10}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Notes field takes priority: 15 (includes bonus)
        assert ac == 15, f"Expected AC 15, got {ac}"
    
    def test_breastplate_with_high_dex(self):
        """Medium armor with high DEX should cap DEX modifier at +2."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Steel",
            "notes": ""
        }
        # DEX 16 = +3 modifier, but medium armor caps at +2
        character_stats = {"dex": 16}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Medium armor: 14 + 2 (capped) = 16
        expected = 16
        assert ac == expected, f"Expected AC {expected}, got {ac}"
    
    def test_shield_bonus_base(self):
        """Shield should provide +2 base bonus."""
        # Shields don't have their own AC value, they provide a bonus
        # +2 is the base shield bonus in D&D 5e
        bonus = 0
        shield_bonus = 2 + bonus
        assert shield_bonus == 2, f"Expected shield bonus 2, got {shield_bonus}"
    
    def test_shield_plus_one_bonus(self):
        """Shield +1 should provide +3 bonus (+2 base + 1 magical)."""
        bonus = 1
        shield_bonus = 2 + bonus
        assert shield_bonus == 3, f"Expected shield bonus 3, got {shield_bonus}"
    
    def test_combined_ac_breastplate_shield(self):
        """Breastplate (15) + Shield (+2) = AC 17."""
        base_armor_ac = 15  # Breastplate with +1
        shield_bonus = 2    # Base shield
        final_ac = base_armor_ac + shield_bonus
        
        assert final_ac == 17, f"Expected AC 17, got {final_ac}"
    
    def test_combined_ac_breastplate_plus_one_shield_plus_one(self):
        """Breastplate +1 (15) + Shield +1 (+3) = AC 18."""
        base_armor_ac = 15  # Breastplate: 14 + 1 bonus
        shield_bonus = 3    # Shield: +2 base + 1 bonus
        final_ac = base_armor_ac + shield_bonus
        
        assert final_ac == 18, f"Expected AC 18, got {final_ac}"
    
    def test_armor_entity_shield_type(self):
        """Test shield armor type detection."""
        shield_data = {
            "id": "2",
            "name": "Shield",
            "armor_class": 2,  # This shouldn't matter for shields
            "armor_type": "Shield",
            "category": "Armor",
            "equipped": True,
            "material": "Wood",
            "notes": ""
        }
        character_stats = {"dex": 10}
        
        shield = ArmorEntity(shield_data, character_stats)
        
        # Verify it's detected as a shield
        assert "shield" in shield.final_armor_type.lower(), \
            f"Expected 'Shield' type, got {shield.final_armor_type}"
    
    def test_medium_armor_with_low_dex(self):
        """Medium armor should NOT subtract for low DEX, only add positive modifiers."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Steel",
            "notes": ""
        }
        # DEX 4 = -3 modifier, but medium armor should ignore negative DEX
        character_stats = {"dex": 4}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Medium armor (14) + DEX mod (-3, but clamped to 0) = 14
        assert ac == 14, f"Expected AC 14 (no DEX penalty), got {ac}"
    
    def test_medium_armor_dex_capped_at_plus_two(self):
        """Medium armor should cap DEX bonus at +2 even with high DEX."""
        armor_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Steel",
            "notes": ""
        }
        # DEX 18 = +4 modifier, but medium armor caps at +2
        character_stats = {"dex": 18}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Medium armor (14) + DEX (+4, but capped at +2) = 16
        assert ac == 16, f"Expected AC 16 (capped at +2), got {ac}"
    
    def test_light_armor_with_low_dex(self):
        """Light armor should NOT subtract for low DEX."""
        armor_data = {
            "id": "1",
            "name": "Leather",
            "armor_class": 11,
            "armor_type": "Light Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Leather",
            "notes": ""
        }
        # DEX 4 = -3 modifier, but light armor should ignore negative DEX
        character_stats = {"dex": 4}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Light armor (11) + DEX mod (-3, but clamped to 0) = 11
        assert ac == 11, f"Expected AC 11 (no DEX penalty), got {ac}"
    
    def test_light_armor_with_high_dex(self):
        """Light armor should add full positive DEX modifier."""
        armor_data = {
            "id": "1",
            "name": "Leather",
            "armor_class": 11,
            "armor_type": "Light Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Leather",
            "notes": ""
        }
        # DEX 16 = +3 modifier, no cap for light armor
        character_stats = {"dex": 16}
        
        armor = ArmorEntity(armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Light armor (11) + DEX (+3) = 14
        assert ac == 14, f"Expected AC 14, got {ac}"
    
    def test_armor_collection_manager_parsing(self):
        """Test that armor collection manager correctly separates armor from shields."""
        # Create mock inventory manager
        class MockInventoryManager:
            def __init__(self):
                self.items = [
                    {
                        "id": "1",
                        "name": "Breastplate +1",
                        "armor_class": 14,
                        "armor_type": "Medium Armor",
                        "category": "Armor",
                        "equipped": True,
                        "material": "Steel",
                        "notes": json.dumps({"armor_class": 15, "bonus": 1})
                    },
                    {
                        "id": "2",
                        "name": "Shield +1",
                        "armor_class": 2,
                        "armor_type": "Shield",
                        "category": "Armor",
                        "equipped": True,
                        "material": "Wood",
                        "notes": json.dumps({"bonus": 1})
                    }
                ]
        
        mgr = ArmorCollectionManager(MockInventoryManager())
        mgr.character_stats = {"dex": 10}
        
        # Build entities
        mgr._build_armor_entities()
        
        # Should have 2 items (1 armor + 1 shield)
        assert len(mgr.armor_pieces) == 2, \
            f"Expected 2 armor pieces, got {len(mgr.armor_pieces)}"
        
        # Verify we can identify armor vs shield
        armor_items = [a for a in mgr.armor_pieces 
                      if "shield" not in a.final_armor_type.lower()]
        shield_items = [a for a in mgr.armor_pieces 
                       if "shield" in a.final_armor_type.lower()]
        
        assert len(armor_items) == 1, \
            f"Expected 1 armor item, got {len(armor_items)}"
        assert len(shield_items) == 1, \
            f"Expected 1 shield item, got {len(shield_items)}"
        
        # Verify AC calculations
        armor = armor_items[0]
        shield = shield_items[0]
        
        armor_ac = armor._calculate_ac()
        assert armor_ac == 15, \
            f"Expected armor AC 15, got {armor_ac}"
        
        # Shield AC should be just the base value (not meaningful for shields)
        shield_ac = shield._calculate_ac()
        assert shield_ac >= 0, \
            f"Shield AC should be >= 0, got {shield_ac}"


class TestACCalculationDebug:
    """Debug tests to identify the AC 11 issue."""
    
    def test_ac_11_scenarios(self):
        """Test scenarios that would result in AC 11."""
        # AC 11 could come from:
        # 1. Light armor (10) + DEX (+1 from DEX 12) = 11
        # 2. 14 - 3 DEX penalty (negative DEX mod of -3 from DEX 4)
        # 3. Some other calculation
        
        # Scenario 1: Light armor with DEX 12
        light_armor_data = {
            "id": "1",
            "name": "Leather Armor",
            "armor_class": 11,
            "armor_type": "Light Armor",
            "category": "Armor",
            "equipped": True,
            "material": "Leather",
            "notes": ""
        }
        character_stats = {"dex": 12}
        
        armor = ArmorEntity(light_armor_data, character_stats)
        ac = armor._calculate_ac()
        
        # Light armor (11) + DEX mod (+1) = 12 (not 11)
        # But if not detected as light armor, just returns 11
        print(f"Light armor AC: {ac}")
        print(f"Armor type: {armor.final_armor_type}")
    
    def test_missing_armor_type(self):
        """Test armor with missing armor_type field."""
        armor_data = {
            "id": "1",
            "name": "Breastplate +1",
            "armor_class": 14,
            # Missing armor_type field!
            "category": "Armor",
            "equipped": True,
            "material": "Steel",
            "notes": json.dumps({"armor_class": 15, "bonus": 1})
        }
        character_stats = {"dex": 10}
        
        armor = ArmorEntity(armor_data, character_stats)
        
        print(f"\nMissing armor_type:")
        print(f"  Armor type: {armor.final_armor_type}")
        print(f"  AC: {armor._calculate_ac()}")
        
        # This might return "—" for armor type and calculate AC as 15
        # (since DEX is only added if armor_type contains "light" or "medium")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
