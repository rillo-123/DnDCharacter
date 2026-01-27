#!/usr/bin/env python
"""Check character inventory for breastplate items."""

import json

# Load character data
with open('config.json') as f:
    data = json.load(f)

character = data.get('character', {})
items = character.get('items', [])

# Find any breastplate items
print('Searching for breastplate items...')
found_any = False
for item in items:
    if 'breastplate' in item.get('name', '').lower():
        found_any = True
        print(f'\nFound: {item["name"]}')
        print(f'  Category: {item.get("category", "N/A")}')
        print(f'  Equipped: {item.get("equipped", False)}')
        print(f'  Bonus: {item.get("bonus", "N/A")}')
        print(f'  Armor Class: {item.get("armor_class", "N/A")}')
        notes = item.get("notes", "")
        if notes:
            print(f'  Notes: {notes[:100]}...')

if not found_any:
    print("No breastplate items found in inventory")
