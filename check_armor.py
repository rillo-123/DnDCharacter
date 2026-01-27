#!/usr/bin/env python
"""Check character inventory for armor items."""

import json

# Load character data
with open('config.json') as f:
    data = json.load(f)

character = data.get('character', {})
items = character.get('items', [])

# Find armor items
print('Armor items in inventory:')
armor_count = 0
for item in items:
    category = item.get('category', '').lower()
    if category == 'armor':
        armor_count += 1
        print(f'\n{armor_count}. {item["name"]}')
        print(f'   Equipped: {item.get("equipped", False)}')
        print(f'   Bonus: {item.get("bonus", "N/A")}')
        print(f'   Armor Class: {item.get("armor_class", "N/A")}')
        notes = item.get("notes", "")
        if notes:
            try:
                notes_data = json.loads(notes)
                print(f'   Notes (JSON): {json.dumps(notes_data, indent=4)}')
            except:
                print(f'   Notes (text): {notes[:100]}')

if armor_count == 0:
    print("No armor items found")
