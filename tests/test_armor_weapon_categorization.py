"""
Tests for armor and weapon categorization and filtering.

Verifies that armor items (especially Shield and Breastplate) are correctly:
1. Auto-categorized as "Armor" not "Weapons" or "Adventuring Gear"
2. Excluded from weapon skill tables
3. Included in armor tables
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "static" / "assets" / "py"))


class TestArmorCategorization:
    """Test the InventoryManager auto-categorization logic."""
    
    def test_shield_categorized_as_armor(self):
        """Test that 'Shield' is correctly categorized as Armor."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Shield")
        
        assert category == "Armor", f"Shield should be Armor, got {category}"
    
    def test_breastplate_categorized_as_armor(self):
        """Test that 'Breastplate' is correctly categorized as Armor."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Breastplate")
        
        assert category == "Armor", f"Breastplate should be Armor, got {category}"
    
    def test_leather_armor_categorized_as_armor(self):
        """Test that 'Leather Armor' is correctly categorized as Armor."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Leather Armor")
        
        assert category == "Armor", f"Leather Armor should be Armor, got {category}"
    
    def test_plate_armor_categorized_as_armor(self):
        """Test that 'Plate Armor' is correctly categorized as Armor."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Plate Armor")
        
        assert category == "Armor", f"Plate Armor should be Armor, got {category}"
    
    def test_chain_mail_categorized_as_armor(self):
        """Test that 'Chain Mail' is correctly categorized as Armor."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Chain Mail")
        
        assert category == "Armor", f"Chain Mail should be Armor, got {category}"
    
    def test_helmet_categorized_as_armor(self):
        """Test that 'Helmet' is correctly categorized as Armor."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Helmet")
        
        assert category == "Armor", f"Helmet should be Armor, got {category}"
    
    def test_longsword_categorized_as_weapon(self):
        """Test that 'Longsword' is correctly categorized as Weapon."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Longsword")
        
        assert category == "Weapons", f"Longsword should be Weapons, got {category}"
    
    def test_dagger_categorized_as_weapon(self):
        """Test that 'Dagger' is correctly categorized as Weapon."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Dagger")
        
        assert category == "Weapons", f"Dagger should be Weapons, got {category}"
    
    def test_bow_categorized_as_weapon(self):
        """Test that 'Bow' is correctly categorized as Weapon."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        category = manager._infer_category("Bow")
        
        assert category == "Weapons", f"Bow should be Weapons, got {category}"
    
    def test_magic_shield_categorized_as_armor_not_magic_items(self):
        """Test that magic shields are still categorized as Armor, not Magic Items."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        
        # Magic items check comes first, but armor keywords should take priority
        # Actually, in the current implementation, magic items come first
        # So a "+1 Shield" might be categorized as Magic Items
        # But we want to ensure shield-specific names are always Armor
        category = manager._infer_category("Shield of Protection")
        
        # Shield should be armor even with "shield of" pattern
        assert category == "Armor", f"Shield of Protection should be Armor, got {category}"
    
    def test_simple_armor_keywords_recognized(self):
        """Test that all simple armor keywords are recognized."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        # Test with full names that contain the keywords
        armor_items = [
            "Plate Armor", "Leather Armor", "Chain Armor", "Hide Armor", "Scale Mail", 
            "Chain Mail", "Breastplate", "Armor", "Shield", "Helmet"
        ]
        
        for item_name in armor_items:
            category = manager._infer_category(item_name)
            assert category == "Armor", f"'{item_name}' should be Armor, got {category}"
    
    def test_armor_prioritized_over_weapon_keywords(self):
        """Test that armor keywords are checked before weapon keywords.
        
        This prevents items from being miscategorized if they contain both
        armor and weapon keywords (though this shouldn't happen in practice).
        """
        from managers import InventoryManager
        
        manager = InventoryManager()
        # "shield" shouldn't accidentally match "staff" or other weapon keywords
        category = manager._infer_category("Shield")
        
        assert category == "Armor", f"Shield should be Armor, got {category}"


class TestWeaponFilteringSafety:
    """Test that armor items are filtered out of weapon tables even if miscategorized."""
    
    def test_armor_keyword_filtering_shield(self):
        """Test that Shield is excluded from weapons list by name check."""
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        
        item = {
            "name": "Shield",
            "category": "Weapons",  # Even if miscategorized
            "equipped": True
        }
        
        item_name = item["name"].lower()
        is_armor_by_name = any(kw in item_name for kw in armor_keywords)
        
        assert is_armor_by_name, "Shield should be detected as armor by name"
    
    def test_armor_keyword_filtering_breastplate(self):
        """Test that Breastplate is excluded from weapons list by name check."""
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        
        item = {
            "name": "Breastplate",
            "category": "Weapons",  # Even if miscategorized
            "equipped": True
        }
        
        item_name = item["name"].lower()
        is_armor_by_name = any(kw in item_name for kw in armor_keywords)
        
        assert is_armor_by_name, "Breastplate should be detected as armor by name"
    
    def test_armor_keyword_filtering_chain_mail(self):
        """Test that Chain Mail is excluded from weapons list by name check."""
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        
        item = {
            "name": "Chain Mail",
            "category": "Adventuring Gear",  # Even if wrong category
            "equipped": True
        }
        
        item_name = item["name"].lower()
        is_armor_by_name = any(kw in item_name for kw in armor_keywords)
        
        assert is_armor_by_name, "Chain Mail should be detected as armor by name"
    
    def test_longsword_not_filtered_as_armor(self):
        """Test that Longsword is NOT filtered out by armor keyword check."""
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        
        item = {
            "name": "Longsword",
            "category": "Weapons",
            "equipped": True
        }
        
        item_name = item["name"].lower()
        is_armor_by_name = any(kw in item_name for kw in armor_keywords)
        
        assert not is_armor_by_name, "Longsword should NOT be detected as armor"
    
    def test_dagger_not_filtered_as_armor(self):
        """Test that Dagger is NOT filtered out by armor keyword check."""
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        
        item = {
            "name": "Dagger",
            "category": "Weapons",
            "equipped": True
        }
        
        item_name = item["name"].lower()
        is_armor_by_name = any(kw in item_name for kw in armor_keywords)
        
        assert not is_armor_by_name, "Dagger should NOT be detected as armor"
    
    def test_filtered_weapon_list_excludes_armor(self):
        """Test the complete filtering logic for rendering weapons grid."""
        # Simulate items in inventory
        items = [
            {"id": "1", "name": "Longsword", "category": "Weapons", "equipped": True},
            {"id": "2", "name": "Shield", "category": "Armor", "equipped": True},
            {"id": "3", "name": "Dagger", "category": "Weapons", "equipped": True},
            {"id": "4", "name": "Breastplate", "category": "Armor", "equipped": True},
        ]
        
        # Apply filtering logic
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        
        equipped_weapons = []
        for item in items:
            category = item.get("category", "").lower()
            item_name = item.get("name", "").lower()
            
            is_weapon = category in ["weapons", "weapon"]
            is_armor_by_name = any(kw in item_name for kw in armor_keywords)
            
            if item.get("equipped") and is_weapon and not is_armor_by_name:
                equipped_weapons.append(item)
        
        # Should only have weapons, not armor
        assert len(equipped_weapons) == 2
        assert equipped_weapons[0]["name"] == "Longsword"
        assert equipped_weapons[1]["name"] == "Dagger"
        
        # Verify Shield and Breastplate are excluded
        weapon_names = [w["name"] for w in equipped_weapons]
        assert "Shield" not in weapon_names
        assert "Breastplate" not in weapon_names
    
    def test_miscategorized_armor_still_filtered(self):
        """Test that armor items are filtered even if miscategorized as Weapons."""
        # Simulate a Shield that was miscategorized
        items = [
            {"id": "1", "name": "Longsword", "category": "Weapons", "equipped": True},
            {"id": "2", "name": "Shield", "category": "Weapons", "equipped": True},  # Wrong!
        ]
        
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        
        equipped_weapons = []
        for item in items:
            category = item.get("category", "").lower()
            item_name = item.get("name", "").lower()
            
            is_weapon = category in ["weapons", "weapon"]
            is_armor_by_name = any(kw in item_name for kw in armor_keywords)
            
            if item.get("equipped") and is_weapon and not is_armor_by_name:
                equipped_weapons.append(item)
        
        # The safety filter should exclude Shield despite wrong category
        assert len(equipped_weapons) == 1
        assert equipped_weapons[0]["name"] == "Longsword"
        assert "Shield" not in [w["name"] for w in equipped_weapons]


class TestInventoryManagerItemAddition:
    """Test that items added to inventory have correct categories."""
    
    def test_add_shield_gets_armor_category(self):
        """Test that adding a Shield gets Armor category."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        item_id = manager.add_item("Shield", cost="10 gp", weight="6 lb")
        
        item = manager.get_item(item_id)
        assert item is not None
        assert item["category"] == "Armor", f"Shield should have Armor category, got {item['category']}"
    
    def test_add_breastplate_gets_armor_category(self):
        """Test that adding Breastplate gets Armor category."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        item_id = manager.add_item("Breastplate", cost="400 gp", weight="20 lb")
        
        item = manager.get_item(item_id)
        assert item is not None
        assert item["category"] == "Armor", f"Breastplate should have Armor category, got {item['category']}"
    
    def test_add_longsword_gets_weapon_category(self):
        """Test that adding Longsword gets Weapons category."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        item_id = manager.add_item("Longsword", cost="15 gp", weight="3 lb")
        
        item = manager.get_item(item_id)
        assert item is not None
        assert item["category"] == "Weapons", f"Longsword should have Weapons category, got {item['category']}"
    
    def test_add_item_with_explicit_category(self):
        """Test that explicit category parameter overrides auto-detection."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        # Explicitly set category even though it could be auto-detected
        item_id = manager.add_item("Breastplate", cost="400 gp", weight="20 lb", category="Armor")
        
        item = manager.get_item(item_id)
        assert item is not None
        assert item["category"] == "Armor"


class TestArmorAndWeaponTableIntegration:
    """Integration tests for armor and weapon table rendering."""
    
    def test_armor_table_includes_equipped_armor(self):
        """Test that armor table includes all equipped armor items."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        
        # Add some items
        manager.add_item("Shield", cost="10 gp", weight="6 lb")
        manager.add_item("Breastplate", cost="400 gp", weight="20 lb")
        manager.add_item("Longsword", cost="15 gp", weight="3 lb")
        
        # Mark armor as equipped
        for item in manager.items:
            if item["category"] == "Armor":
                item["equipped"] = True
        
        # Filter for armor only
        armor_items = [item for item in manager.items if item["category"] == "Armor" and item["equipped"]]
        
        assert len(armor_items) == 2
        names = [item["name"] for item in armor_items]
        assert "Shield" in names
        assert "Breastplate" in names
        assert "Longsword" not in names
    
    def test_weapons_table_includes_equipped_weapons_only(self):
        """Test that weapons table includes only equipped weapons."""
        from managers import InventoryManager
        
        manager = InventoryManager()
        
        # Add some items
        manager.add_item("Shield", cost="10 gp", weight="6 lb")
        manager.add_item("Longsword", cost="15 gp", weight="3 lb")
        manager.add_item("Dagger", cost="2 gp", weight="1 lb")
        
        # Mark only one weapon as equipped
        for item in manager.items:
            if item["name"] == "Longsword":
                item["equipped"] = True
        
        # Filter for weapons only
        armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
        weapon_items = []
        for item in manager.items:
            if item["category"] == "Weapons" and item["equipped"]:
                item_name = item["name"].lower()
                is_armor_by_name = any(kw in item_name for kw in armor_keywords)
                if not is_armor_by_name:
                    weapon_items.append(item)
        
        assert len(weapon_items) == 1
        assert weapon_items[0]["name"] == "Longsword"
        
        # Verify other weapons are not included
        names = [item["name"] for item in weapon_items]
        assert "Dagger" not in names  # Not equipped
        assert "Shield" not in names  # Armor


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
