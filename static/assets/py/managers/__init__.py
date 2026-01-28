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
from .weapons_manager import WeaponsCollectionManager, WeaponEntity, initialize_weapons_manager, get_weapons_manager
from .armor_manager import ArmorCollectionManager, ArmorEntity, initialize_armor_manager, get_armor_manager, calculate_total_ac_from_armor_manager
from .inventory_manager import InventoryManager, Weapon, Armor, Shield, Equipment, initialize_inventory_manager, get_inventory_manager
from .spellcasting_manager import SpellcasterManager, SPELL_LIBRARY_STATE, set_spell_library_data, load_spell_library, SpellcastingManager, initialize_spellcasting_manager, get_spellcasting_manager
from .equipment_event_manager import EquipmentEventListener, register_all_events, initialize_equipment_event_manager, get_equipment_event_manager

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
    "Weapon",
    "Armor", 
    "Shield",
    "Equipment",
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
    "EquipmentEventListener",
    "register_all_events",
    "initialize_equipment_event_manager",
    "get_equipment_event_manager",
]

