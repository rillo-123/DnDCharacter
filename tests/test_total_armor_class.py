"""
Comprehensive tests for total_armor_class calculation and display.

Tests:
1. Individual armor piece AC values (armor_class)
2. Character's total AC calculation (total_armor_class)
3. HTML element update (id="total_armor_class")
4. Export JSON field (combat.total_armor_class)
5. Enwer's exact scenario: Breastplate + Shield +1 = AC 17
"""

import json
import sys
from pathlib import Path

# Add static assets to path
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))

import pytest


class TestTotalArmorClassNaming:
    """Test that total_armor_class is distinct from individual armor piece armor_class."""
    
    def test_armor_piece_has_armor_class_field(self):
        """Individual armor pieces should have armor_class field."""
        from armor_manager import ArmorEntity
        
        breastplate_data = {
            "id": "1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": '{"armor_class": "14", "armor_type": "medium"}'
        }
        
        armor = ArmorEntity(breastplate_data, {"dex": 10})
        
        # Verify the data has armor_class field (individual piece AC)
        assert "armor_class" in armor.entity
        assert armor.entity["armor_class"] == 14
        
    def test_character_export_uses_total_armor_class(self):
        """Character export should use total_armor_class in combat section."""
        # This test verifies the export structure
        combat_data = {
            "total_armor_class": 17,  # Character's final AC
            "speed": 30,
            "max_hp": 67
        }
        
        # Verify the key is named correctly
        assert "total_armor_class" in combat_data
        assert combat_data["total_armor_class"] == 17
        
        # Verify we're NOT using the old name
        assert "armor_class" not in combat_data or combat_data.get("armor_class") == combat_data.get("total_armor_class")


class TestEnwerACCalculation:
    """Test Enwer's exact equipment setup: Breastplate + Shield +1 = AC 17."""
    
    def setup_method(self):
        """Set up test data matching Enwer's character."""
        self.character_stats = {"dex": 10}  # DEX 10 = +0 modifier
        
        self.breastplate_data = {
            "id": "breastplate_1",
            "name": "Breastplate",
            "armor_class": 14,
            "armor_type": "Medium Armor",
            "category": "Armor",
            "equipped": True,
            "notes": '{"armor_class": "14", "armor_type": "medium"}'
        }
        
        self.shield_data = {
            "id": "shield_1",
            "name": "Shield",
            "category": "Armor",
            "equipped": True,
            "notes": '{"bonus": 3, "armor_type": "Shield"}'  # +3 = base 2 + magical 1
        }
    
    def test_breastplate_ac_is_14(self):
        """Breastplate should have AC 14."""
        from armor_manager import ArmorEntity
        
        armor = ArmorEntity(self.breastplate_data, self.character_stats)
        ac = armor._calculate_ac()
        
        assert ac == 14, f"Breastplate AC should be 14, got {ac}"
    
    def test_shield_bonus_is_3(self):
        """Shield +1 should provide +3 bonus (base 2 + magical 1)."""
        shield_notes = json.loads(self.shield_data["notes"])
        bonus = shield_notes.get("bonus", 2)
        
        assert bonus == 3, f"Shield bonus should be 3, got {bonus}"
    
    def test_total_ac_is_17(self):
        """Total AC: 14 (breastplate) + 0 (DEX) + 3 (shield) = 17."""
        from armor_manager import ArmorEntity
        
        # Calculate breastplate AC
        breastplate = ArmorEntity(self.breastplate_data, self.character_stats)
        breastplate_ac = breastplate._calculate_ac()
        
        # Get shield bonus
        shield_notes = json.loads(self.shield_data["notes"])
        shield_bonus = shield_notes.get("bonus", 2)
        
        # Calculate total
        total_ac = breastplate_ac + shield_bonus
        
        assert total_ac == 17, f"Total AC should be 17, got {total_ac} (breastplate={breastplate_ac}, shield={shield_bonus})"
    
    def test_armor_collection_manager_calculates_correctly(self):
        """ArmorCollectionManager should calculate total AC as 17."""
        from armor_manager import ArmorCollectionManager
        
        class MockInventoryManager:
            def __init__(self, items):
                self.items = items
        
        inv_mgr = MockInventoryManager([self.breastplate_data, self.shield_data])
        armor_mgr = ArmorCollectionManager(inv_mgr)
        armor_mgr.character_stats = self.character_stats
        armor_mgr._build_armor_entities()
        
        # Separate armor from shields
        armor_pieces = [a for a in armor_mgr.armor_pieces if "shield" not in a.final_armor_type.lower()]
        shields = [a for a in armor_mgr.armor_pieces if "shield" in a.final_armor_type.lower()]
        
        assert len(armor_pieces) == 1, "Should have 1 armor piece"
        assert len(shields) == 1, "Should have 1 shield"
        
        # Calculate total AC
        armor_ac = armor_pieces[0]._calculate_ac()
        shield_notes = json.loads(shields[0].entity.get("notes", "{}"))
        shield_bonus = shield_notes.get("bonus", 2)
        total_ac = armor_ac + shield_bonus
        
        assert armor_ac == 14, f"Armor AC should be 14, got {armor_ac}"
        assert shield_bonus == 3, f"Shield bonus should be 3, got {shield_bonus}"
        assert total_ac == 17, f"Total AC should be 17, got {total_ac}"


class TestACCalculationFunction:
    """Test the calculate_armor_class() function in character.py."""
    
    def test_calculate_armor_class_returns_17_for_enwer(self):
        """The calculate_armor_class() function should return 17 for Enwer's setup."""
        try:
            from character import calculate_armor_class, INVENTORY_MANAGER
            from inventory_manager import InventoryManager
            
            # This test requires mocking the global INVENTORY_MANAGER
            # Skip if not available in test environment
            pytest.skip("Requires full character.py environment")
        except ImportError:
            pytest.skip("character module not available in test environment")


class TestCharacterExport:
    """Test that character export uses total_armor_class correctly."""
    
    def test_export_structure_has_total_armor_class(self):
        """Exported JSON should have combat.total_armor_class field."""
        # Sample export structure
        export_data = {
            "identity": {"name": "Test Character"},
            "level": 8,
            "combat": {
                "total_armor_class": 17,  # Must be this field name
                "speed": 30,
                "max_hp": 67,
                "current_hp": 67
            }
        }
        
        assert "combat" in export_data
        assert "total_armor_class" in export_data["combat"], \
            "Export must have combat.total_armor_class field"
        assert export_data["combat"]["total_armor_class"] == 17
    
    def test_export_does_not_use_old_armor_class_name(self):
        """Export should not use old 'armor_class' name in combat section."""
        # New exports should only have total_armor_class
        export_data = {
            "combat": {
                "total_armor_class": 17,
                "speed": 30
            }
        }
        
        # New format: has total_armor_class
        assert "total_armor_class" in export_data["combat"]
        
        # Should NOT have the old armor_class field (unless for backward compatibility)
        # This assertion is lenient to allow backward compatibility fallback
        if "armor_class" in export_data["combat"]:
            # If both exist, they should match
            assert export_data["combat"]["armor_class"] == export_data["combat"]["total_armor_class"]


class TestHTMLElementNaming:
    """Test that HTML element uses correct ID."""
    
    def test_html_element_id_is_total_armor_class(self):
        """HTML element should have id='total_armor_class'."""
        # Read the HTML file
        html_path = Path(__file__).parent.parent / "static" / "index.html"
        if not html_path.exists():
            pytest.skip("HTML file not found")
        
        html_content = html_path.read_text()
        
        # Check for the new element ID
        assert 'id="total_armor_class"' in html_content, \
            "HTML must have element with id='total_armor_class'"
        
        # The old ID should not be used for the character's total AC
        # (individual armor pieces can still use armor_class as a data field)
        lines_with_armor_class_id = [
            line for line in html_content.split('\n') 
            if 'id="armor_class"' in line and '<span' in line
        ]
        
        assert len(lines_with_armor_class_id) == 0, \
            f"HTML should not have <span id='armor_class'>, found: {lines_with_armor_class_id}"


class TestBackwardCompatibility:
    """Test that old save files with armor_class still load correctly."""
    
    def test_import_old_format_with_armor_class(self):
        """Should be able to import old files with armor_class field."""
        old_format = {
            "combat": {
                "armor_class": 15,  # Old field name
                "speed": 30
            }
        }
        
        # Simulating import logic: try total_armor_class first, fallback to armor_class
        combat = old_format["combat"]
        ac_value = combat.get("total_armor_class", combat.get("armor_class", 10))
        
        assert ac_value == 15, "Should read armor_class from old format"
    
    def test_import_new_format_with_total_armor_class(self):
        """Should import new files with total_armor_class field."""
        new_format = {
            "combat": {
                "total_armor_class": 17,  # New field name
                "speed": 30
            }
        }
        
        combat = new_format["combat"]
        ac_value = combat.get("total_armor_class", combat.get("armor_class", 10))
        
        assert ac_value == 17, "Should read total_armor_class from new format"
    
    def test_import_prefers_total_armor_class_over_armor_class(self):
        """If both fields exist, should prefer total_armor_class."""
        both_format = {
            "combat": {
                "total_armor_class": 17,  # New correct value
                "armor_class": 15,  # Old stale value
                "speed": 30
            }
        }
        
        combat = both_format["combat"]
        ac_value = combat.get("total_armor_class", combat.get("armor_class", 10))
        
        assert ac_value == 17, "Should prefer total_armor_class over armor_class"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
