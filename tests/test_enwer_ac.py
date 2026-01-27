"""Test AC calculation for Enwer's exact equipment loadout."""

import json
import sys
from pathlib import Path

# Add static assets to path
sys.path.insert(0, str(Path(__file__).parent / "static" / "assets" / "py"))

# Mock inventory manager with Enwer's equipment
class MockInventoryManager:
    def __init__(self):
        self.items = [
            {
                "id": "1769114653896999_365239",
                "name": "Crossbow, light",
                "cost": "25 gp",
                "weight": "5 lb.",
                "qty": 1,
                "category": "Weapons",
                "notes": "",
                "source": "open5e",
                "equipped": True
            },
            {
                "id": "1769117350600999_801998",
                "name": "Mace",
                "cost": "5 gp",
                "weight": "4 lb.",
                "qty": 1,
                "category": "Weapons",
                "notes": '{"damage": "1d6", "damage_type": "bludgeoning"}',
                "source": "open5e",
                "equipped": True
            },
            {
                "id": "1769292369772000_398703",
                "name": "Shield",
                "cost": "10 gp",
                "weight": "6 lb.",
                "qty": 1,
                "category": "Armor",
                "notes": '{"bonus": 3, "armor_type": "Shield"}',
                "source": "open5e",
                "equipped": True
            },
            {
                "id": "1769336806421000_630123",
                "name": "Breastplate",
                "cost": "400 gp",
                "weight": "20 lb.",
                "qty": 1,
                "category": "Armor",
                "notes": '{"armor_class": "14", "armor_type": "medium"}',
                "source": "open5e",
                "equipped": True
            }
        ]

# Test with armor manager
from armor_manager import ArmorEntity, ArmorCollectionManager

def test_enwer_equipment_ac():
    """Test AC with Enwer's exact equipment: Breastplate + Shield (+1)."""
    print("\n=== Testing Enwer's Equipment ===")
    print("Equipment:")
    print("  - Breastplate (AC 14, Medium Armor)")
    print("  - Shield +1 (bonus: 3 = base 2 + magical 1)")
    print("  - DEX: 10 (modifier: 0)")
    print("\nExpected AC: 14 (armor) + 0 (DEX) + 3 (shield) = 17")
    print("Exported AC: 15 (WRONG!)")
    
    character_stats = {"dex": 10}
    
    # Test breastplate
    breastplate_data = {
        "id": "1769336806421000_630123",
        "name": "Breastplate",
        "cost": "400 gp",
        "weight": "20 lb.",
        "qty": 1,
        "category": "Armor",
        "notes": '{"armor_class": "14", "armor_type": "medium"}',
        "source": "open5e",
        "equipped": True
    }
    
    print("\n--- Testing Breastplate ---")
    breastplate = ArmorEntity(breastplate_data, character_stats)
    breastplate_ac = breastplate._calculate_ac()
    print(f"Breastplate AC: {breastplate_ac}")
    print(f"Breastplate type: {breastplate.final_armor_type}")
    
    # Test shield
    shield_data = {
        "id": "1769292369772000_398703",
        "name": "Shield",
        "cost": "10 gp",
        "weight": "6 lb.",
        "qty": 1,
        "category": "Armor",
        "notes": '{"bonus": 3, "armor_type": "Shield"}',
        "source": "open5e",
        "equipped": True
    }
    
    print("\n--- Testing Shield ---")
    shield = ArmorEntity(shield_data, character_stats)
    shield_ac = shield._calculate_ac()
    print(f"Shield AC: {shield_ac} (should be 0 because shields are bonuses, not AC)")
    print(f"Shield type: {shield.final_armor_type}")
    
    # Parse shield bonus
    shield_notes = json.loads(shield_data["notes"])
    shield_bonus = shield_notes.get("bonus", 2)
    print(f"Shield bonus from notes: +{shield_bonus}")
    
    # Calculate total AC
    total_ac = breastplate_ac + shield_bonus
    print(f"\n--- Final Calculation ---")
    print(f"Total AC: {breastplate_ac} (breastplate) + {shield_bonus} (shield) = {total_ac}")
    
    if total_ac == 17:
        print("✓ CORRECT! AC is 17")
    else:
        print(f"✗ WRONG! AC is {total_ac}, expected 17")
    
    # Test with ArmorCollectionManager
    print("\n--- Testing with ArmorCollectionManager ---")
    inv_mgr = MockInventoryManager()
    armor_mgr = ArmorCollectionManager(inv_mgr)
    armor_mgr.character_stats = character_stats
    armor_mgr._build_armor_entities()
    
    print(f"Found {len(armor_mgr.armor_pieces)} armor pieces")
    for piece in armor_mgr.armor_pieces:
        ac = piece._calculate_ac()
        print(f"  - {piece.entity.get('name')}: AC={ac}, Type={piece.final_armor_type}")

if __name__ == "__main__":
    test_enwer_equipment_ac()
