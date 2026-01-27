"""Character class management following the manager pattern.

This module handles D&D 5e character classes, including:
- Class metadata (hit die, proficiencies)
- Class subclasses (Bard, Cleric, etc.)
- Factory for creating typed character instances
- Class-specific features and traits
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

DEFAULT_ABILITY_KEYS: Tuple[str, ...] = ("str", "dex", "con", "int", "wis", "cha")


@dataclass(frozen=True)
class CharacterClassInfo:
    """Lightweight container for core class metadata."""

    key: str
    hit_die: str
    armor_proficiencies: Tuple[str, ...]
    weapon_proficiencies: Tuple[str, ...]


CLASS_REGISTRY: Dict[str, CharacterClassInfo] = {
    "barbarian": CharacterClassInfo(
        key="barbarian",
        hit_die="1d12",
        armor_proficiencies=("Light armor", "Medium armor", "Shields"),
        weapon_proficiencies=("Simple melee", "Martial melee"),
    ),
    "bard": CharacterClassInfo(
        key="bard",
        hit_die="1d8",
        armor_proficiencies=("Light armor",),
        weapon_proficiencies=("Simple melee", "Hand crossbows", "Longswords", "Rapiers", "Shortswords"),
    ),
    "cleric": CharacterClassInfo(
        key="cleric",
        hit_die="1d8",
        armor_proficiencies=("Light armor", "Medium armor", "Shields"),
        weapon_proficiencies=("Simple melee", "Simple ranged"),
    ),
    "druid": CharacterClassInfo(
        key="druid",
        hit_die="1d8",
        armor_proficiencies=("Light armor", "Medium armor", "Shields"),
        weapon_proficiencies=(
            "Clubs",
            "Daggers",
            "Darts",
            "Javelins",
            "Maces",
            "Quarterstaffs",
            "Scimitars",
            "Sickles",
            "Slings",
            "Spears",
        ),
    ),
    "fighter": CharacterClassInfo(
        key="fighter",
        hit_die="1d10",
        armor_proficiencies=("All armor", "Shields"),
        weapon_proficiencies=("Simple melee", "Simple ranged", "Martial melee", "Martial ranged"),
    ),
    "monk": CharacterClassInfo(
        key="monk",
        hit_die="1d8",
        armor_proficiencies=("None",),
        weapon_proficiencies=("Simple melee", "Shortswords"),
    ),
    "paladin": CharacterClassInfo(
        key="paladin",
        hit_die="1d10",
        armor_proficiencies=("All armor", "Shields"),
        weapon_proficiencies=("Simple melee", "Simple ranged", "Martial melee", "Martial ranged"),
    ),
    "ranger": CharacterClassInfo(
        key="ranger",
        hit_die="1d10",
        armor_proficiencies=("Light armor", "Medium armor", "Shields"),
        weapon_proficiencies=("Simple melee", "Simple ranged", "Martial melee", "Martial ranged"),
    ),
    "rogue": CharacterClassInfo(
        key="rogue",
        hit_die="1d8",
        armor_proficiencies=("Light armor",),
        weapon_proficiencies=("Hand crossbows", "Longswords", "Rapiers", "Shortswords", "Simple melee"),
    ),
    "sorcerer": CharacterClassInfo(
        key="sorcerer",
        hit_die="1d6",
        armor_proficiencies=("None",),
        weapon_proficiencies=("Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"),
    ),
    "warlock": CharacterClassInfo(
        key="warlock",
        hit_die="1d8",
        armor_proficiencies=("Light armor",),
        weapon_proficiencies=("Simple melee",),
    ),
    "wizard": CharacterClassInfo(
        key="wizard",
        hit_die="1d6",
        armor_proficiencies=("None",),
        weapon_proficiencies=("Daggers", "Darts", "Slings", "Quarterstaffs", "Light crossbows"),
    ),
}


def get_class_info(raw: Optional[str], character: Optional[Any] = None) -> Optional[CharacterClassInfo]:
    """Return class metadata for the first recognized class token.
    
    Args:
        raw: Raw class text string (may contain multiple tokens)
        character: Character instance with _extract_class_tokens method (optional)
    
    Returns:
        CharacterClassInfo if found, None otherwise
    """
    if not raw:
        return None
    
    # Import here to avoid circular dependency
    if character is None:
        from character_models import Character  # noqa: F401
        tokens = Character._extract_class_tokens(raw)  # noqa: F821
    else:
        tokens = character._extract_class_tokens(raw)  # noqa: E501
    
    for token in tokens:
        if token in CLASS_REGISTRY:
            return CLASS_REGISTRY[token]
    return None


def get_class_hit_die(raw: Optional[str], character: Optional[Any] = None) -> str:
    """Get the hit die for a character class.
    
    Args:
        raw: Raw class text string
        character: Character instance (optional)
    
    Returns:
        Hit die string (e.g., "1d8"), defaults to "1d8"
    """
    info = get_class_info(raw, character)
    return info.hit_die if info else "1d8"


def get_class_armor_proficiencies(raw: Optional[str], domain: str = "", character: Optional[Any] = None) -> Tuple[str, ...]:
    """Get armor proficiencies for a character class.
    
    Args:
        raw: Raw class text string
        domain: Domain name (for domain-specific proficiencies like Cleric Life Domain)
        character: Character instance (optional)
    
    Returns:
        Tuple of armor proficiency strings
    """
    info = get_class_info(raw, character)
    if not info:
        return ("None",)
    if info.key == "cleric" and domain and "life" in domain.lower():
        # Life Domain clerics get Heavy Armor proficiency.
        if "Heavy armor" not in info.armor_proficiencies:
            return info.armor_proficiencies + ("Heavy armor",)
    return info.armor_proficiencies


def get_class_weapon_proficiencies(raw: Optional[str], character: Optional[Any] = None) -> Tuple[str, ...]:
    """Get weapon proficiencies for a character class.
    
    Args:
        raw: Raw class text string
        character: Character instance (optional)
    
    Returns:
        Tuple of weapon proficiency strings
    """
    info = get_class_info(raw, character)
    return info.weapon_proficiencies if info else ("None",)


class Bard:
    """Character specialization for bards.
    
    This should be mixed with Character base class or subclassed.
    """

    @property
    def college(self) -> str:
        """Get the bard's college (stored in subclass field)."""
        return self.subclass  # type: ignore

    @college.setter
    def college(self, value: Optional[str]) -> None:
        """Set the bard's college."""
        self.subclass = value  # type: ignore

    def header_summary(self) -> str:
        """Generate header summary for bard character."""
        college = self.college.strip()
        if college:
            parts = [f"College of {college.title()} Bard"]
            race = self.race.strip()  # type: ignore
            if race:
                parts.append(race)
            return " · ".join(parts)
        return super().header_summary()  # type: ignore


class Cleric:
    """Character specialization for clerics.
    
    This should be mixed with Character base class or subclassed.
    """

    @property
    def domain(self) -> str:
        """Get the cleric's domain.
        
        For Cleric, domain is stored in subclass, but falls back to
        identity["domain"] if subclass is empty.
        """
        subclass_value = self.subclass.strip()  # type: ignore
        if subclass_value:
            return subclass_value
        # Fall back to identity["domain"] if subclass is empty
        return self._data["identity"].get("domain", "").strip()  # type: ignore

    @domain.setter
    def domain(self, value: Optional[str]) -> None:
        """Set the cleric's domain.
        
        Updates both subclass and identity["domain"] to keep them in sync.
        """
        self.subclass = value  # type: ignore
        # Also keep identity["domain"] in sync for serialization
        self._data["identity"]["domain"] = (value or "").strip()  # type: ignore

    def header_summary(self) -> str:
        """Generate header summary for cleric character."""
        domain = self.domain.strip()
        if domain:
            parts = [f"{domain.title()} Domain Cleric"]
            race = self.race.strip()  # type: ignore
            if race:
                parts.append(race)
            return " · ".join(parts)
        return super().header_summary()  # type: ignore


class CharacterFactory:
    """Factory for constructing typed character instances.
    
    Maps class keys to appropriate Character subclasses and provides
    methods for creating instances from various sources.
    """

    CLASS_MAP = {
        "artificer": "Character",  # Placeholder - not yet implemented
        "bard": "Bard",
        "cleric": "Cleric",
        "druid": "Character",  # Placeholder - not yet implemented
        "paladin": "Character",  # Placeholder - not yet implemented
        "ranger": "Character",  # Placeholder - not yet implemented
        "sorcerer": "Character",  # Placeholder - not yet implemented
        "warlock": "Character",  # Placeholder - not yet implemented
        "wizard": "Character",  # Placeholder - not yet implemented
    }

    @classmethod
    def normalize_class(cls, raw: Optional[str]) -> str:
        """Normalize raw class text to a canonical class key.
        
        Args:
            raw: Raw class text (may contain multiple tokens)
        
        Returns:
            Canonical class key or empty string if not recognized
        """
        # Import here to avoid circular dependency
        from character_models import Character  # noqa: F401
        tokens = Character._extract_class_tokens(raw)  # noqa: F821
        for token in tokens:
            if token in cls.CLASS_MAP:
                return token
        return tokens[0] if tokens else ""

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Any:
        """Create a typed character instance from a data dictionary.
        
        Args:
            data: Character data dictionary
        
        Returns:
            Typed Character subclass instance (e.g., Bard, Cleric)
        """
        from character_models import Character  # noqa: F401
        payload = data or {}
        class_key = cls.normalize_class(payload.get("identity", {}).get("class"))
        class_name = cls.CLASS_MAP.get(class_key, "Character")
        
        # Get the actual class from character_models
        if class_name == "Bard":
            # Create a Bard instance that inherits from Character
            return type("Bard", (Bard, Character), {})(payload, class_key=class_key)  # noqa: F821
        elif class_name == "Cleric":
            # Create a Cleric instance that inherits from Character
            return type("Cleric", (Cleric, Character), {})(payload, class_key=class_key)  # noqa: F821
        else:
            return Character(payload, class_key=class_key)  # noqa: F821

    @classmethod
    def create_default(cls, class_key: Optional[str] = None) -> Any:
        """Create a default character instance of the specified class.
        
        Args:
            class_key: Class key (e.g., "bard", "cleric")
        
        Returns:
            Typed Character subclass instance
        """
        from character_models import Character  # noqa: F401
        normalized = (class_key or "").lower()
        class_name = cls.CLASS_MAP.get(normalized, "Character")
        
        if class_name == "Bard":
            return type("Bard", (Bard, Character), {})(class_key=normalized)  # noqa: F821
        elif class_name == "Cleric":
            return type("Cleric", (Cleric, Character), {})(class_key=normalized)  # noqa: F821
        else:
            return Character(class_key=normalized)  # noqa: F821

    @classmethod
    def supported_classes(cls) -> Tuple[str, ...]:
        """Get tuple of all supported class keys.
        
        Returns:
            Sorted tuple of class key strings
        """
        return tuple(sorted(cls.CLASS_MAP.keys()))


def initialize_class_manager() -> CharacterFactory:
    """Initialize and return the class manager (factory).
    
    Returns:
        CharacterFactory instance
    """
    return CharacterFactory()


def get_class_manager() -> CharacterFactory:
    """Get the global class manager instance.
    
    Returns:
        CharacterFactory instance
    """
    return CharacterFactory()


__all__ = [
    "CharacterClassInfo",
    "CLASS_REGISTRY",
    "get_class_info",
    "get_class_hit_die",
    "get_class_armor_proficiencies",
    "get_class_weapon_proficiencies",
    "Bard",
    "Cleric",
    "CharacterFactory",
    "initialize_class_manager",
    "get_class_manager",
]
