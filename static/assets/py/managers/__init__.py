"""Manager modules for DnD Character Sheet.

This package contains all manager classes that handle specific domains:
- character_manager: Character stats and synchronization
- weapons_manager: Weapon collection management
- armor_manager: Armor collection management  
- inventory_manager: Inventory management
- entity_manager: Base entity manager
- spellcasting_manager: Spell management
- equipment_event_manager: Equipment event handling
- class_manager: Character class management
- race_manager: Race management

Re-exports all managers for convenient importing.
"""

from .character_manager import CharacterManager, initialize_character_manager, get_character_manager
from .class_manager import (
    CharacterClassInfo, 
    CLASS_REGISTRY, 
    CharacterFactory, 
    Bard, 
    Cleric, 
    initialize_class_manager, 
    get_class_manager,
    get_class_info,
    get_class_hit_die,
    get_class_armor_proficiencies,
    get_class_weapon_proficiencies,
)
from .race_manager import (
    RACE_ABILITY_BONUSES, 
    RaceManager, 
    initialize_race_manager, 
    get_race_manager,
    get_race_ability_bonuses,
)
from .entity_manager import EntityManager

# Conditional imports for manager files in root (for backward compatibility)
try:
    from weapons_manager import WeaponsCollectionManager, WeaponEntity, initialize_weapons_manager, get_weapons_manager
except ImportError:
    WeaponsCollectionManager = WeaponEntity = initialize_weapons_manager = get_weapons_manager = None

try:
    from armor_manager import ArmorCollectionManager, ArmorEntity, initialize_armor_manager, get_armor_manager, calculate_total_ac_from_armor_manager
except ImportError:
    ArmorCollectionManager = ArmorEntity = initialize_armor_manager = get_armor_manager = calculate_total_ac_from_armor_manager = None

try:
    from inventory_manager import InventoryManager, initialize_inventory_manager, get_inventory_manager
except ImportError:
    InventoryManager = initialize_inventory_manager = get_inventory_manager = None

try:
    from spellcasting_manager import SpellcasterManager, SPELL_LIBRARY_STATE, set_spell_library_data, load_spell_library, SpellcastingManager, initialize_spellcasting_manager, get_spellcasting_manager
except ImportError:
    SpellcasterManager = SPELL_LIBRARY_STATE = set_spell_library_data = load_spell_library = SpellcastingManager = initialize_spellcasting_manager = get_spellcasting_manager = None

try:
    from equipment_event_manager import EquipmentEventManager, register_all_events, initialize_equipment_event_manager, get_equipment_event_manager
except ImportError:
    EquipmentEventManager = register_all_events = initialize_equipment_event_manager = get_equipment_event_manager = None

__all__ = [
    # Character Manager
    "CharacterManager",
    "initialize_character_manager",
    "get_character_manager",
    # Class Manager
    "CharacterClassInfo",
    "CLASS_REGISTRY",
    "CharacterFactory",
    "Bard",
    "Cleric",
    "initialize_class_manager",
    "get_class_manager",
    "get_class_info",
    "get_class_hit_die",
    "get_class_armor_proficiencies",
    "get_class_weapon_proficiencies",
    # Race Manager
    "RACE_ABILITY_BONUSES",
    "RaceManager",
    "initialize_race_manager",
    "get_race_manager",
    "get_race_ability_bonuses",
    # Entity Manager
    "EntityManager",
    # Weapons Manager
    "WeaponsCollectionManager",
    "WeaponEntity",
    "initialize_weapons_manager",
    "get_weapons_manager",
    # Armor Manager
    "ArmorCollectionManager",
    "ArmorEntity",
    "initialize_armor_manager",
    "get_armor_manager",
    "calculate_total_ac_from_armor_manager",
    # Inventory Manager
    "InventoryManager",
    "initialize_inventory_manager",
    "get_inventory_manager",
    # Spellcasting Manager
    "SpellcasterManager",
    "SPELL_LIBRARY_STATE",
    "set_spell_library_data",
    "load_spell_library",
    "SpellcastingManager",
    "initialize_spellcasting_manager",
    "get_spellcasting_manager",
    # Equipment Event Manager
    "EquipmentEventManager",
    "register_all_events",
    "initialize_equipment_event_manager",
    "get_equipment_event_manager",
]

