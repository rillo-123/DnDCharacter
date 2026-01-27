#!/usr/bin/env python
"""Debug script to check Breastplate +1 AC calculation."""
import json
import sys

# Add static/assets/py to path for imports
sys.path.insert(0, "static/assets/py")

from character import Character

# Load the character
char = Character()
char.load_character()

# Look for "Breastplate" armor item
found = False
for item in char.inventory_manager.items:
    if "breastplate" in item.get("name", "").lower():
        found = True
        print(f"\n=== Found Breastplate Item ===")
        print(f"Name: {item.get('name')}")
        print(f"Category: {item.get('category')}")
        print(f"Qty: {item.get('qty')}")
        print(f"Equipped: {item.get('equipped')}")
        print(f"Notes (raw): {item.get('notes')}")
        
        # Parse notes
        notes_str = item.get("notes", "")
        if notes_str and notes_str.startswith("{"):
            try:
                extra_props = json.loads(notes_str)
                print(f"\nNotes (parsed):")
                for key, val in extra_props.items():
                    print(f"  {key}: {val}")
            except Exception as e:
                print(f"Error parsing notes: {e}")
        
        # Get the armor entity from armor manager
        if char.armor_manager:
            for armor in char.armor_manager.armor_pieces:
                if "breastplate" in armor.entity.get("name", "").lower():
                    print(f"\n=== Armor Entity ===")
                    print(f"Final name: {armor.final_name}")
                    print(f"Final AC: {armor.final_ac}")
                    print(f"Final armor type: {armor.final_armor_type}")
                    
                    # Debug the calculation
                    print(f"\n=== AC Calculation Debug ===")
                    print(f"Entity armor_type field: {armor.entity.get('armor_type', '(not set)')}")
                    
                    # Check notes for armor_type
                    notes_str = armor.entity.get("notes", "")
                    if notes_str and notes_str.startswith("{"):
                        try:
                            extra_props = json.loads(notes_str)
                            print(f"Notes armor_class: {extra_props.get('armor_class')}")
                            print(f"Notes bonus: {extra_props.get('bonus')}")
                            print(f"Notes armor_type: {extra_props.get('armor_type')}")
                        except:
                            pass
                    
                    # Character stats
                    print(f"\nCharacter DEX: {armor.character_stats.get('dex', 10)}")
                    dex_mod = (armor.character_stats.get('dex', 10) - 10) // 2
                    print(f"DEX modifier: {dex_mod}")

if not found:
    print("No Breastplate found in inventory")
    print(f"\nAvailable armor items:")
    for item in char.inventory_manager.items:
        if item.get("category") == "Armor":
            print(f"  - {item.get('name')} (qty: {item.get('qty')})")
