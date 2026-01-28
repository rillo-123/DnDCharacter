#!/usr/bin/env python
"""Test script to debug breastplate +1 in weapons table."""

import json
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path("static/assets/py")))

from managers import InventoryManager

# Create manager and add breastplate
mgr = InventoryManager()
item_id = mgr.add_item("Breastplate +1", cost="400 gp", weight="20 lb")
item = mgr.get_item(item_id)

print("Item created:")
print(f"  Name: {item['name']}")
print(f"  Category: {item['category']}")
print(f"  Bonus: {item.get('bonus', 'N/A')}")
print(f"  Armor Class: {item.get('armor_class', 'N/A')}")
print(f"  Notes: {item.get('notes', 'N/A')}")

# Set as equipped
item["equipped"] = True

# Check filtering logic
armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "shield", "helmet"]
is_weapon = item.get("category", "").lower() in ["weapons", "weapon"]
is_armor_by_name = any(kw in item["name"].lower() for kw in armor_keywords)

print(f"\nFiltering:")
print(f"  is_weapon: {is_weapon}")
print(f"  is_armor_by_name: {is_armor_by_name}")
print(f"  Would be in weapons table: {is_weapon and not is_armor_by_name}")
