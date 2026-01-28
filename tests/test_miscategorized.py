#!/usr/bin/env python
"""Test script to verify breastplate filtering in weapons table."""

import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path("static/assets/py")))

from managers import InventoryManager

# Create manager 
mgr = InventoryManager()

# Add a weapon to have something in the table
weapon_id = mgr.add_item("Longsword", cost="15 gp", weight="3 lb", category="Weapons")
weapon = mgr.get_item(weapon_id)
weapon["equipped"] = True

# Add a breastplate that's MISCATEGORIZED as "Weapons" (test worst case)
breastplate_id = mgr.add_item("Breastplate +1", cost="400 gp", weight="20 lb", category="Weapons")
breastplate = mgr.get_item(breastplate_id)
breastplate["equipped"] = True

# Set the armor_class field in notes
import json
extra_props = {"armor_class": 15, "bonus": 1}  # 14 base + 1 bonus
breastplate["notes"] = json.dumps(extra_props)

print("Items created:")
print(f"1. {weapon['name']} - Category: {weapon['category']}")
print(f"2. {breastplate['name']} - Category: {breastplate['category']}, Notes: {breastplate['notes']}")

# Apply filtering logic to see what would appear
armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]

equipped_weapons = []
for item in mgr.items:
    category = item.get("category", "").lower()
    item_name = item.get("name", "").lower()
    
    is_weapon = category in ["weapons", "weapon"]
    is_armor_by_name = any(kw in item_name for kw in armor_keywords)
    
    if item.get("equipped") and is_weapon and not is_armor_by_name:
        equipped_weapons.append(item)
        print(f"✓ Would render: {item['name']}")
    else:
        print(f"✗ Would NOT render: {item['name']} (is_weapon={is_weapon}, is_armor_by_name={is_armor_by_name})")

print(f"\nFinal count in weapons table: {len(equipped_weapons)}")
