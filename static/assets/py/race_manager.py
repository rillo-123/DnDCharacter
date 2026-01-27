"""Race management for D&D characters following the manager pattern.

This module handles character races and their ability score bonuses,
providing a centralized source for race-related data and calculations.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, Optional

RACE_ABILITY_BONUSES: Dict[str, Dict[str, int]] = {
    "human": {"str": 1, "dex": 1, "con": 1, "int": 1, "wis": 1, "cha": 1},
    "elf": {"dex": 2},
    "high elf": {"dex": 2, "int": 1},
    "wood elf": {"dex": 2, "wis": 1},
    "dark elf": {"dex": 2, "cha": 1},
    "dwarf": {"con": 2},
    "mountain dwarf": {"con": 2, "str": 2},
    "hill dwarf": {"con": 2, "wis": 1},
    "halfling": {"dex": 2},
    "lightfoot halfling": {"dex": 2, "cha": 1},
    "stout halfling": {"dex": 2, "con": 1},
    "dragonborn": {"str": 2, "cha": 1},
    "gnome": {"int": 2},
    "forest gnome": {"int": 2, "dex": 1},
    "rock gnome": {"int": 2, "con": 1},
    "half-elf": {"cha": 2, "str": 1, "con": 1},
    "half-orc": {"str": 2, "con": 1},
    "tiefling": {"cha": 2, "int": 1},
}


def get_race_ability_bonuses(race: str) -> Dict[str, int]:
    """Get ability score bonuses for a given race.
    
    Args:
        race: Race name (will be normalized to lowercase with whitespace stripped)
    
    Returns:
        Dictionary mapping ability keys (str, dex, con, int, wis, cha) to bonus values.
        Returns empty dict if race not found.
    
    Example:
        >>> bonuses = get_race_ability_bonuses("High Elf")
        >>> bonuses["dex"]
        2
        >>> bonuses["int"]
        1
    """
    if not race:
        return {}
    race_lower = race.strip().lower()
    return copy.copy(RACE_ABILITY_BONUSES.get(race_lower, {}))


def get_race_list() -> list[str]:
    """Get list of all available races.
    
    Returns:
        Sorted list of race names
    """
    return sorted(RACE_ABILITY_BONUSES.keys())


def race_exists(race: str) -> bool:
    """Check if a race exists in the database.
    
    Args:
        race: Race name to check
    
    Returns:
        True if race exists, False otherwise
    """
    if not race:
        return False
    race_lower = race.strip().lower()
    return race_lower in RACE_ABILITY_BONUSES


def apply_race_bonuses(abilities: Dict[str, Any], race: str) -> Dict[str, Any]:
    """Apply race ability bonuses to character abilities.
    
    Args:
        abilities: Character abilities dictionary with 'score' keys
        race: Race name
    
    Returns:
        Updated abilities dictionary with bonuses applied
    """
    bonuses = get_race_ability_bonuses(race)
    result = copy.deepcopy(abilities)
    
    for ability_key, bonus in bonuses.items():
        if ability_key in result:
            current_score = int(result[ability_key].get("score", 10) or 10)
            result[ability_key]["score"] = current_score + bonus
    
    return result


class RaceManager:
    """Manager for character races and racial bonuses.
    
    Provides centralized access to race data and bonuses following
    the manager pattern used in other parts of the application.
    """

    def __init__(self) -> None:
        """Initialize the race manager."""
        self._race_data = RACE_ABILITY_BONUSES

    def get_bonuses(self, race: str) -> Dict[str, int]:
        """Get ability bonuses for a race.
        
        Args:
            race: Race name
        
        Returns:
            Dictionary of ability bonuses
        """
        return get_race_ability_bonuses(race)

    def get_all_races(self) -> list[str]:
        """Get list of all available races.
        
        Returns:
            Sorted list of race names
        """
        return get_race_list()

    def has_race(self, race: str) -> bool:
        """Check if a race exists.
        
        Args:
            race: Race name
        
        Returns:
            True if race exists
        """
        return race_exists(race)

    def apply_bonuses_to_character(self, character: Any, race: str) -> None:
        """Apply race bonuses to a character instance.
        
        Args:
            character: Character instance with abilities dict
            race: Race name
        """
        if not hasattr(character, "_abilities"):
            return
        
        bonuses = self.get_bonuses(race)
        for ability_key, bonus in bonuses.items():
            try:
                current_score = character._abilities[ability_key].get("score", 10)
                character._abilities[ability_key]["score"] = int(current_score or 10) + bonus
            except (KeyError, AttributeError):
                pass


def initialize_race_manager() -> RaceManager:
    """Initialize and return the race manager.
    
    Returns:
        RaceManager instance
    """
    return RaceManager()


def get_race_manager() -> RaceManager:
    """Get the global race manager instance.
    
    Returns:
        RaceManager instance
    """
    return RaceManager()


__all__ = [
    "RACE_ABILITY_BONUSES",
    "get_race_ability_bonuses",
    "get_race_list",
    "race_exists",
    "apply_race_bonuses",
    "RaceManager",
    "initialize_race_manager",
    "get_race_manager",
]
