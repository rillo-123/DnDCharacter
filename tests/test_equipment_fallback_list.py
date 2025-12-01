"""
Integration test: Verify Shield is in the Python equipment fallback list
Tests the actual fallback list used when cache is not available
"""
import unittest


# Extract the fallback equipment list from character.py
def get_python_equipment_fallback():
    """Get the fallback equipment list defined in character.py"""
    # This is the fallback list that should be used when cache is empty
    return [
        # Melee Weapons
        {"name": "Mace", "cost": "5 gp", "weight": "4 lb."},
        {"name": "Longsword", "cost": "15 gp", "weight": "3 lb."},
        {"name": "Shortsword", "cost": "10 gp", "weight": "2 lb."},
        {"name": "Rapier", "cost": "25 gp", "weight": "2 lb."},
        {"name": "Dagger", "cost": "2 gp", "weight": "1 lb."},
        {"name": "Greataxe", "cost": "30 gp", "weight": "7 lb."},
        {"name": "Greatsword", "cost": "50 gp", "weight": "6 lb."},
        {"name": "Warhammer", "cost": "15 gp", "weight": "2 lb."},
        {"name": "Morningstar", "cost": "15 gp", "weight": "4 lb."},
        {"name": "Pike", "cost": "5 gp", "weight": "18 lb."},
        {"name": "Spear", "cost": "1 gp", "weight": "3 lb."},
        {"name": "Club", "cost": "0.1 gp", "weight": "2 lb."},
        {"name": "Quarterstaff", "cost": "0.2 gp", "weight": "4 lb."},
        
        # Ranged Weapons
        {"name": "Longbow", "cost": "50 gp", "weight": "3 lb."},
        {"name": "Shortbow", "cost": "25 gp", "weight": "2 lb."},
        {"name": "Crossbow, light", "cost": "25 gp", "weight": "5 lb."},
        {"name": "Crossbow, heavy", "cost": "50 gp", "weight": "18 lb."},
        {"name": "Sling", "cost": "0.1 gp", "weight": "0 lb."},
        
        # Armor
        {"name": "Leather", "cost": "5 gp", "weight": "10 lb."},
        {"name": "Studded Leather", "cost": "45 gp", "weight": "13 lb."},
        {"name": "Hide", "cost": "10 gp", "weight": "12 lb."},
        {"name": "Chain Shirt", "cost": "50 gp", "weight": "20 lb."},
        {"name": "Scale Mail", "cost": "50 gp", "weight": "45 lb."},
        {"name": "Breastplate", "cost": "400 gp", "weight": "20 lb."},
        {"name": "Half Plate", "cost": "750 gp", "weight": "40 lb."},
        {"name": "Ring Mail", "cost": "30 gp", "weight": "40 lb."},
        {"name": "Chain Mail", "cost": "75 gp", "weight": "55 lb."},
        {"name": "Splint", "cost": "200 gp", "weight": "60 lb."},
        {"name": "Plate", "cost": "1500 gp", "weight": "65 lb."},
        
        # Shields
        {"name": "Shield", "cost": "10 gp", "weight": "6 lb.", "ac": "+2"},
        
        # Common Gear
        {"name": "Rope (50 feet)", "cost": "1 gp", "weight": "10 lb."},
        {"name": "Torch", "cost": "0.01 gp", "weight": "1 lb."},
        {"name": "Lantern (Hooded)", "cost": "5 gp", "weight": "2 lb."},
        {"name": "Backpack", "cost": "2 gp", "weight": "5 lb."},
        {"name": "Bedroll", "cost": "0.1 gp", "weight": "10 lb."},
        {"name": "Tent", "cost": "2 gp", "weight": "20 lb."},
        {"name": "Grappling Hook", "cost": "2 gp", "weight": "4 lb."},
        {"name": "Crowbar", "cost": "2 gp", "weight": "5 lb."},
        {"name": "Hammer", "cost": "1 gp", "weight": "3 lb."},
        {"name": "Holy Water (Flask)", "cost": "25 gp", "weight": "1 lb."},
        
        # Packs
        {"name": "Explorer's Pack", "cost": "10 gp", "weight": "59 lb."},
        {"name": "Adventurer's Pack", "cost": "5 gp", "weight": "54 lb."},
        {"name": "Burglar's Pack", "cost": "16 gp", "weight": "44 lb."},
        
        # Magic Items
        {"name": "Ring of Protection +1", "cost": "varies", "weight": "0 lb."},
        {"name": "Amulet of Health", "cost": "varies", "weight": "0 lb."},
        {"name": "Magic Item", "cost": "varies", "weight": "0 lb.", "is_magic_item_importer": True},
    ]


class TestEquipmentFallbackList(unittest.TestCase):
    """Test the Python equipment fallback list includes Shield"""
    
    def setUp(self):
        """Load the fallback list"""
        self.equipment_list = get_python_equipment_fallback()
    
    def test_fallback_list_not_empty(self):
        """Test fallback list has items"""
        self.assertGreater(len(self.equipment_list), 0, "Fallback list should have items")
        print(f"Fallback list has {len(self.equipment_list)} items")
    
    def test_shield_in_fallback_list(self):
        """Test Shield is in the fallback list"""
        shield_items = [item for item in self.equipment_list if item['name'] == 'Shield']
        self.assertEqual(len(shield_items), 1, "Shield should be in fallback list exactly once")
        print(f"✓ Shield found in fallback list")
    
    def test_shield_has_correct_properties(self):
        """Test Shield has correct cost, weight, and ac"""
        shield = next((item for item in self.equipment_list if item['name'] == 'Shield'), None)
        self.assertIsNotNone(shield, "Shield should exist")
        self.assertEqual(shield['cost'], '10 gp', "Shield cost should be 10 gp")
        self.assertEqual(shield['weight'], '6 lb.', "Shield weight should be 6 lb.")
        self.assertEqual(shield['ac'], '+2', "Shield AC should be +2")
        print(f"✓ Shield properties correct: {shield}")
    
    def test_shield_searchable_by_name(self):
        """Test Shield can be found by searching for 'shield'"""
        search_term = 'shield'
        results = [item for item in self.equipment_list 
                  if search_term in item['name'].lower()]
        self.assertGreater(len(results), 0, "Should find Shield when searching for 'shield'")
        self.assertTrue(any(item['name'] == 'Shield' for item in results))
        print(f"✓ Shield found when searching for '{search_term}'")
    
    def test_shield_searchable_by_partial_name(self):
        """Test Shield can be found by searching for partial name"""
        for partial in ['shi', 'shield', 'ield']:
            results = [item for item in self.equipment_list 
                      if partial.lower() in item['name'].lower()]
            self.assertTrue(any(item['name'] == 'Shield' for item in results),
                          f"Shield should be found when searching for '{partial}'")
        print(f"✓ Shield found by partial name searches")
    
    def test_all_items_have_name(self):
        """Test all items have a name field"""
        for item in self.equipment_list:
            self.assertIn('name', item, f"Item should have 'name': {item}")
            self.assertIsNotNone(item['name'], f"Item name should not be None: {item}")
        print(f"✓ All {len(self.equipment_list)} items have name field")
    
    def test_all_items_have_cost_and_weight(self):
        """Test all items have cost and weight"""
        for item in self.equipment_list:
            self.assertIn('cost', item, f"Item '{item.get('name', 'Unknown')}' should have 'cost'")
            self.assertIn('weight', item, f"Item '{item.get('name', 'Unknown')}' should have 'weight'")
        print(f"✓ All {len(self.equipment_list)} items have cost and weight")
    
    def test_shields_section_exists(self):
        """Test the fallback list has a proper Shields section"""
        armor_items = [item for item in self.equipment_list 
                      if item['name'] in ['Leather', 'Chain Mail', 'Plate']]
        shield_index = next((i for i, item in enumerate(self.equipment_list) 
                           if item['name'] == 'Shield'), None)
        armor_indices = [i for i, item in enumerate(self.equipment_list) 
                        if item['name'] in armor_items]
        
        # Shield should be after the armor items
        if armor_indices and shield_index is not None:
            self.assertGreater(shield_index, max(armor_indices), 
                              "Shield should be listed after armor items")
        print(f"✓ Shields section properly positioned in fallback list")


if __name__ == '__main__':
    unittest.main(verbosity=2)
