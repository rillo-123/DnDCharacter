"""
Equipment data loader and lookup utilities.
Centralizes all D&D 5e equipment (weapons, armor, magic items) in JSON format.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Global equipment database (loaded once on startup)
_EQUIPMENT_DB = None


def load_equipment_db() -> Dict[str, Any]:
    """Load equipment database from JSON file."""
    global _EQUIPMENT_DB
    
    if _EQUIPMENT_DB is not None:
        return _EQUIPMENT_DB
    
    try:
        data_dir = Path(__file__).parent.parent / "data"
        equipment_file = data_dir / "equipment.json"
        
        if not equipment_file.exists():
            print(f"WARNING: Equipment file not found at {equipment_file}")
            return _get_fallback_db()
        
        with open(equipment_file, 'r', encoding='utf-8') as f:
            _EQUIPMENT_DB = json.load(f)
        
        print(f"Loaded equipment database: {len(_EQUIPMENT_DB.get('weapons', []))} weapons, "
              f"{len(_EQUIPMENT_DB.get('armor', []))} armor, "
              f"{len(_EQUIPMENT_DB.get('magic_items', []))} magic items")
        
        return _EQUIPMENT_DB
    except Exception as e:
        print(f"ERROR loading equipment database: {e}")
        return _get_fallback_db()


def _get_fallback_db() -> Dict[str, Any]:
    """Fallback empty database structure."""
    return {
        "weapons": [],
        "armor": [],
        "shields": [],
        "magic_items": [],
        "adventuring_gear": []
    }


def find_weapon(name: str) -> Optional[Dict[str, Any]]:
    """Find a weapon by name (case-insensitive)."""
    db = load_equipment_db()
    name_lower = name.lower()
    
    for weapon in db.get("weapons", []):
        if weapon.get("name", "").lower() == name_lower:
            return weapon
    
    return None


def find_armor(name: str) -> Optional[Dict[str, Any]]:
    """Find armor by name (case-insensitive)."""
    db = load_equipment_db()
    name_lower = name.lower()
    
    for armor in db.get("armor", []):
        if armor.get("name", "").lower() == name_lower:
            return armor
    
    return None


def find_magic_item(name: str) -> Optional[Dict[str, Any]]:
    """Find a magic item by name (case-insensitive)."""
    db = load_equipment_db()
    name_lower = name.lower()
    
    for item in db.get("magic_items", []):
        if item.get("name", "").lower() == name_lower:
            return item
    
    return None


def get_weapons_by_class(class_name: str) -> List[Dict[str, Any]]:
    """Get all weapons a class has proficiency with."""
    db = load_equipment_db()
    class_lower = class_name.lower()
    
    matching = []
    for weapon in db.get("weapons", []):
        proficiencies = [p.lower() for p in weapon.get("proficiency_classes", [])]
        if class_lower in proficiencies:
            matching.append(weapon)
    
    return matching


def get_armor_by_class(class_name: str) -> List[Dict[str, Any]]:
    """Get all armor a class has proficiency with."""
    db = load_equipment_db()
    class_lower = class_name.lower()
    
    matching = []
    for armor in db.get("armor", []):
        proficiencies = [p.lower() for p in armor.get("proficiency_classes", [])]
        if class_lower in proficiencies:
            matching.append(armor)
    
    return matching


def has_property(weapon: Dict[str, Any], property_name: str) -> bool:
    """Check if a weapon has a specific property."""
    properties = weapon.get("properties", [])
    property_lower = property_name.lower()
    
    if isinstance(properties, list):
        return any(property_lower in str(p).lower() for p in properties)
    elif isinstance(properties, str):
        return property_lower in properties.lower()
    
    return False


def get_weapons_by_property(property_name: str) -> List[Dict[str, Any]]:
    """Get all weapons with a specific property."""
    db = load_equipment_db()
    _property_lower = property_name.lower()
    
    matching = []
    for weapon in db.get("weapons", []):
        if has_property(weapon, property_name):
            matching.append(weapon)
    
    return matching


def add_weapon_to_db(weapon: Dict[str, Any]) -> bool:
    """Add a weapon to the database, avoiding duplicates."""
    try:
        db = load_equipment_db()
        weapons = db.get("weapons", [])
        
        # Check if weapon already exists
        weapon_name = weapon.get("name", "").strip()
        if not weapon_name:
            return False
        
        for existing in weapons:
            if existing.get("name", "").lower() == weapon_name.lower():
                # Weapon already exists, don't add duplicate
                return False
        
        # Add weapon
        weapons.append(weapon)
        db["weapons"] = weapons
        
        # Save to file
        _save_equipment_db(db)
        return True
    except Exception as e:
        print(f"ERROR adding weapon to database: {e}")
        return False


def add_armor_to_db(armor: Dict[str, Any]) -> bool:
    """Add armor to the database, avoiding duplicates."""
    try:
        db = load_equipment_db()
        armors = db.get("armor", [])
        
        # Check if armor already exists
        armor_name = armor.get("name", "").strip()
        if not armor_name:
            return False
        
        for existing in armors:
            if existing.get("name", "").lower() == armor_name.lower():
                return False
        
        armors.append(armor)
        db["armor"] = armors
        
        _save_equipment_db(db)
        return True
    except Exception as e:
        print(f"ERROR adding armor to database: {e}")
        return False


def add_magic_item_to_db(item: Dict[str, Any]) -> bool:
    """Add a magic item to the database, avoiding duplicates."""
    try:
        db = load_equipment_db()
        items = db.get("magic_items", [])
        
        # Check if item already exists
        item_name = item.get("name", "").strip()
        if not item_name:
            return False
        
        for existing in items:
            if existing.get("name", "").lower() == item_name.lower():
                return False
        
        items.append(item)
        db["magic_items"] = items
        
        _save_equipment_db(db)
        return True
    except Exception as e:
        print(f"ERROR adding magic item to database: {e}")
        return False


def _save_equipment_db(db: Dict[str, Any]) -> bool:
    """Save the equipment database back to JSON file."""
    global _EQUIPMENT_DB
    try:
        data_dir = Path(__file__).parent.parent / "data"
        equipment_file = data_dir / "equipment.json"
        
        # Ensure directory exists
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Write to file with pretty formatting
        with open(equipment_file, 'w') as f:
            json.dump(db, f, indent=2)
        
        # Update global cache
        _EQUIPMENT_DB = db
        
        print(f"✓ Saved equipment database ({len(db.get('weapons', []))} weapons, "
              f"{len(db.get('armor', []))} armor, {len(db.get('magic_items', []))} magic items)")
        return True
    except Exception as e:
        print(f"ERROR saving equipment database: {e}")
        return False


def normalize_weapon_from_external(external_weapon: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a weapon from external source (Open5e, etc) to our format."""
    normalized = {
        "name": external_weapon.get("name", "Unknown"),
        "damage": external_weapon.get("damage_dice") or external_weapon.get("damage", "1d4"),
        "damage_type": external_weapon.get("damage_type", ""),
        "properties": external_weapon.get("properties", []),
        "range": external_weapon.get("range", "Melee"),
        "rarity": external_weapon.get("rarity", "common"),
        "source": external_weapon.get("document", {}).get("title", "Custom"),
    }
    return normalized


def normalize_armor_from_external(external_armor: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize armor from external source to our format."""
    normalized = {
        "name": external_armor.get("name", "Unknown"),
        "ac": external_armor.get("armor_class", 10),
        "type": external_armor.get("armor_type", "light"),
        "dex_bonus": external_armor.get("dex_bonus", True),
        "rarity": external_armor.get("rarity", "common"),
        "source": external_armor.get("document", {}).get("title", "Custom"),
    }
    return normalized


# Test/demo function
if __name__ == "__main__":
    print("Equipment Database Loader Test\n")
    
    # Load database
    db = load_equipment_db()
    
    # Test weapon lookup
    rapier = find_weapon("Rapier")
    if rapier:
        print(f"✓ Found weapon: {rapier['name']}")
        print(f"  Damage: {rapier['damage']} {rapier['damage_type']}")
        print(f"  Properties: {', '.join(rapier['properties'])}")
        print(f"  Proficiency: {', '.join(rapier['proficiency_classes'])}\n")
    
    # Test armor lookup
    plate = find_armor("Plate")
    if plate:
        print(f"✓ Found armor: {plate['name']}")
        print(f"  AC: {plate['ac']}")
        print(f"  Type: {plate['type']}\n")
    
    # Test class lookup
    bard_weapons = get_weapons_by_class("Bard")
    print(f"✓ Bard proficiencies ({len(bard_weapons)} weapons):")
    for w in bard_weapons[:5]:
        print(f"  - {w['name']}")
    print("  ...\n")
    
    # Test property lookup
    finesse_weapons = get_weapons_by_property("finesse")
    print(f"✓ Finesse weapons ({len(finesse_weapons)}):")
    for w in finesse_weapons:
        print(f"  - {w['name']}")
