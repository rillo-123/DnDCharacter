#!/usr/bin/env python
"""Comprehensive test of breastplate +1 in weapons table flow."""

import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path("static/assets/py")))

from managers import InventoryManager

print("=" * 70)
print("TEST: Breastplate +1 Filtering in Weapons Table")
print("=" * 70)

# Simulate what happens when equipment is imported
print("\n1. Creating items in inventory...")
mgr = InventoryManager()

# Add items
weapon = mgr.add_item("Longsword", cost="15 gp", weight="3 lb", category="Weapons")
breastplate = mgr.add_item("Breastplate +1", cost="400 gp", weight="20 lb")

print(f"   - Longsword: {mgr.get_item(weapon)['category']}")
print(f"   - Breastplate +1: {mgr.get_item(breastplate)['category']}")

# Equip both
mgr.get_item(weapon)["equipped"] = True
mgr.get_item(breastplate)["equipped"] = True

# Update notes on breastplate to include armor_class and bonus
notes = {"armor_class": 15, "bonus": 1}
mgr.get_item(breastplate)["notes"] = json.dumps(notes)

print("\n2. Applying weapons table filter...")
# This is the exact filter from character.py render_equipped_attack_grid()
armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
equipped_weapons = []

for item in mgr.items:
    category = item.get("category", "").lower()
    item_name = item.get("name", "").lower()
    is_equipped = item.get("equipped", False)
    
    is_weapon = category in ["weapons", "weapon"]
    is_armor_by_name = any(kw in item_name for kw in armor_keywords)
    
    print(f"\n   Item: {item['name']}")
    print(f"     Category: {category}")
    print(f"     Equipped: {is_equipped}")
    print(f"     is_weapon: {is_weapon}")
    print(f"     is_armor_by_name: {is_armor_by_name}")
    
    if is_equipped and is_weapon and not is_armor_by_name:
        equipped_weapons.append(item)
        print(f"     Result: ✓ WOULD APPEAR in weapons table")
    else:
        print(f"     Result: ✗ Would NOT appear")

print(f"\n3. Final Count:")
print(f"   Items in weapons table: {len(equipped_weapons)}")
print(f"   Items: {[i['name'] for i in equipped_weapons]}")

if len(equipped_weapons) == 1 and equipped_weapons[0]['name'] == "Longsword":
    print("\n✓ TEST PASSED: Breastplate +1 was correctly filtered out")
else:
    print("\n✗ TEST FAILED: Breastplate +1 appeared in weapons table or wrong items present")
    for item in equipped_weapons:
        print(f"   - {item['name']}: category={item.get('category')}, notes={item.get('notes')}")
