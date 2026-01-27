"""Domain models and helpers for representing D&D characters in PySheet.

This module introduces a small object model that wraps the raw dictionary data
used elsewhere in the application.  It provides a `Character` base class with
attribute helpers plus focused subclasses for supported classes like Bards and
Clerics.  The intent is to offer typed accessors (e.g. `character.attributes.str`)
while keeping compatibility with the existing JSON schema.

Class and race management have been extracted to separate manager modules:
- class_manager.py: CharacterClassInfo, CLASS_REGISTRY, class-related functions, Bard and Cleric classes
- race_manager.py: RACE_ABILITY_BONUSES, race-related functions
"""

from __future__ import annotations

import copy
import re
from typing import Any, Dict, Iterable, Iterator, Mapping, MutableMapping, Optional, Tuple

# Import from manager modules (organized in managers package)
from managers import (
    CharacterClassInfo,
    CLASS_REGISTRY,
    get_class_info,
    get_class_hit_die,
    get_class_armor_proficiencies,
    get_class_weapon_proficiencies,
    Bard,
    Cleric,
    CharacterFactory,
    RACE_ABILITY_BONUSES,
    get_race_ability_bonuses,
)

DEFAULT_ABILITY_KEYS: Tuple[str, ...] = ("str", "dex", "con", "int", "wis", "cha")

AbilityState = Dict[str, Any]


class AbilityAccessor:
    """Proxy object that exposes ability scores via attribute access.

    Example usage::

        character.attributes.str = 14
        bonus = character.attributes["dex"]
        proficient = character.attributes.is_proficient("wis")

    The accessor mutates the underlying ability dictionary in-place so changes
    automatically flow back to the owning ``Character`` instance.
    """

    __slots__ = ("_abilities", "_keys")

    def __init__(
        self,
        ability_table: Optional[MutableMapping[str, AbilityState]] = None,
        ability_keys: Iterable[str] = DEFAULT_ABILITY_KEYS,
    ) -> None:
        object.__setattr__(self, "_keys", tuple(ability_keys))
        abilities: MutableMapping[str, AbilityState]
        if ability_table is None:
            abilities = {}
        else:
            abilities = ability_table
        for key in tuple(abilities.keys()):
            if key not in ability_keys:
                # Preserve unknown keys but skip normalization.
                continue
        for key in ability_keys:
            entry = abilities.get(key)
            if not isinstance(entry, Mapping):
                entry = {}
            abilities[key] = {
                "score": int(entry.get("score", 10) or 10),
                "save_proficient": bool(entry.get("save_proficient", False)),
            }
        object.__setattr__(self, "_abilities", abilities)

    def __getattr__(self, name: str) -> int:
        if name in self._abilities:
            return int(self._abilities[name].get("score", 10))
        raise AttributeError(f"Unknown ability '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        if name in {"_abilities", "_keys"}:
            object.__setattr__(self, name, value)
            return
        if name not in self._abilities:
            raise AttributeError(f"Unknown ability '{name}'")
        self._abilities[name]["score"] = int(value)

    def __getitem__(self, key: str) -> int:
        return int(self._abilities[key].get("score", 10))

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in self._abilities:
            raise KeyError(key)
        self._abilities[key]["score"] = int(value)

    def items(self) -> Iterator[Tuple[str, int]]:
        for key in self._keys:
            yield key, int(self._abilities[key].get("score", 10))

    def to_mapping(self) -> Dict[str, AbilityState]:
        return copy.deepcopy(dict(self._abilities))

    # Saving throw proficiency helpers -------------------------------------------------
    def is_proficient(self, key: str) -> bool:
        state = self._abilities.get(key)
        return bool(state and state.get("save_proficient", False))

    def set_proficient(self, key: str, value: bool) -> None:
        if key not in self._abilities:
            raise KeyError(key)
        self._abilities[key]["save_proficient"] = bool(value)

    def proficiencies(self) -> Dict[str, bool]:
        return {
            key: bool(self._abilities[key].get("save_proficient", False))
            for key in self._keys
        }


class Character:
    """Base representation of a character sheet state."""

    DEFAULT_NAME = "Unnamed Hero"

    __slots__ = ("_data", "_abilities", "_class_key")

    def __init__(self, data: Optional[Dict[str, Any]] = None, *, class_key: str = "") -> None:
        payload: Dict[str, Any] = copy.deepcopy(data) if data else {}
        self._data = payload
        self._ensure_identity_defaults()
        ability_table = self._data.setdefault("abilities", {})
        self._abilities = AbilityAccessor(ability_table, DEFAULT_ABILITY_KEYS)
        self._class_key = class_key or self._derive_class_key(self.class_text)

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _ensure_identity_defaults(self) -> None:
        identity = self._data.setdefault("identity", {})
        for key in ("name", "class", "race", "background", "alignment", "player_name", "subclass", "domain"):
            identity.setdefault(key, "")
        if "level" not in self._data:
            self._data["level"] = 1
        else:
            self._data["level"] = max(1, int(self._data.get("level", 1) or 1))
        self._data["inspiration"] = int(self._data.get("inspiration", 0) or 0)
        spell_ability = (self._data.get("spell_ability") or "int").lower()
        self._data["spell_ability"] = spell_ability

    @staticmethod
    def _extract_class_tokens(raw: Optional[str]) -> Tuple[str, ...]:
        if not raw:
            return tuple()
        tokens = re.findall(r"[a-z]+", raw.lower())
        return tuple(tokens)

    @classmethod
    def _derive_class_key(cls, raw: Optional[str]) -> str:
        tokens = cls._extract_class_tokens(raw)
        return tokens[0] if tokens else ""

    # ------------------------------------------------------------------
    # basic identity properties
    # ------------------------------------------------------------------
    @property
    def name(self) -> str:
        return self._data["identity"].get("name", "")

    @name.setter
    def name(self, value: Optional[str]) -> None:
        self._data["identity"]["name"] = (value or "").strip()

    @property
    def class_text(self) -> str:
        return self._data["identity"].get("class", "")

    @class_text.setter
    def class_text(self, value: Optional[str]) -> None:
        text = (value or "").strip()
        self._data["identity"]["class"] = text
        self._class_key = self._derive_class_key(text)

    @property
    def class_key(self) -> str:
        return self._class_key

    @property
    def race(self) -> str:
        return self._data["identity"].get("race", "")

    @race.setter
    def race(self, value: Optional[str]) -> None:
        self._data["identity"]["race"] = (value or "").strip()

    @property
    def background(self) -> str:
        return self._data["identity"].get("background", "")

    @background.setter
    def background(self, value: Optional[str]) -> None:
        self._data["identity"]["background"] = (value or "").strip()

    @property
    def alignment(self) -> str:
        return self._data["identity"].get("alignment", "")

    @alignment.setter
    def alignment(self, value: Optional[str]) -> None:
        self._data["identity"]["alignment"] = (value or "").strip()

    @property
    def domain(self) -> str:
        return self._data["identity"].get("domain", "")

    @domain.setter
    def domain(self, value: Optional[str]) -> None:
        self._data["identity"]["domain"] = (value or "").strip()

    @property
    def player_name(self) -> str:
        return self._data["identity"].get("player_name", "")

    @player_name.setter
    def player_name(self, value: Optional[str]) -> None:
        self._data["identity"]["player_name"] = (value or "").strip()

    @property
    def subclass(self) -> str:
        return self._data["identity"].get("subclass", "")

    @subclass.setter
    def subclass(self, value: Optional[str]) -> None:
        self._data["identity"]["subclass"] = (value or "").strip()

    # ------------------------------------------------------------------
    # numeric/meta properties
    # ------------------------------------------------------------------
    @property
    def level(self) -> int:
        return int(self._data.get("level", 1) or 1)

    @level.setter
    def level(self, value: Any) -> None:
        self._data["level"] = max(1, int(value or 1))

    @property
    def inspiration(self) -> int:
        return int(self._data.get("inspiration", 0) or 0)

    @inspiration.setter
    def inspiration(self, value: Any) -> None:
        self._data["inspiration"] = max(0, int(value or 0))

    @property
    def spell_ability(self) -> str:
        return (self._data.get("spell_ability") or "int").lower()

    @spell_ability.setter
    def spell_ability(self, value: Optional[str]) -> None:
        self._data["spell_ability"] = (value or "int").lower()

    @property
    def attributes(self) -> AbilityAccessor:
        return self._abilities

    # ------------------------------------------------------------------
    # combat properties
    # ------------------------------------------------------------------
    @property
    def proficiency_bonus(self) -> int:
        """Calculate proficiency bonus based on character level.
        
        Returns:
            Proficiency bonus (2 at level 1, increases every 4 levels)
        """
        level = max(1, min(20, self.level))
        return 2 + (level - 1) // 4
    
    @property
    def initiative_bonus(self) -> int:
        """Calculate initiative bonus (DEX modifier).
        
        Returns:
            Initiative bonus (+DEX modifier)
        """
        dex_score = self._abilities.dex
        return (dex_score - 10) // 2
    
    @property
    def speed(self) -> int:
        """Get character movement speed.
        
        Returns:
            Movement speed in feet (default 30 for most races)
        """
        # TODO: This should be configurable per race and could have modifiers
        # For now, return a sensible default
        return self._data.get("speed", 30)
    
    @property
    def passive_perception(self) -> int:
        """Calculate passive Perception (10 + WIS modifier + proficiency if proficient).
        
        Returns:
            Passive Perception score
        """
        wis_score = self._abilities.wis
        wis_mod = (wis_score - 10) // 2
        
        # Check if proficient in Perception
        skills = self._data.get("skills", {})
        perception_prof = skills.get("perception", 0)  # 0=none, 1=proficient, 2=expertise
        
        prof_bonus = 0
        if perception_prof > 0:
            prof_bonus = self.proficiency_bonus * perception_prof
        
        return 10 + wis_mod + prof_bonus
    
    @property
    def passive_investigation(self) -> int:
        """Calculate passive Investigation (10 + INT modifier + proficiency if proficient).
        
        Returns:
            Passive Investigation score
        """
        int_score = self._abilities.int
        int_mod = (int_score - 10) // 2
        
        # Check if proficient in Investigation
        skills = self._data.get("skills", {})
        investigation_prof = skills.get("investigation", 0)
        
        prof_bonus = 0
        if investigation_prof > 0:
            prof_bonus = self.proficiency_bonus * investigation_prof
        
        return 10 + int_mod + prof_bonus
    
    @property
    def passive_insight(self) -> int:
        """Calculate passive Insight (10 + WIS modifier + proficiency if proficient).
        
        Returns:
            Passive Insight score
        """
        wis_score = self._abilities.wis
        wis_mod = (wis_score - 10) // 2
        
        # Check if proficient in Insight
        skills = self._data.get("skills", {})
        insight_prof = skills.get("insight", 0)
        
        prof_bonus = 0
        if insight_prof > 0:
            prof_bonus = self.proficiency_bonus * insight_prof
        
        return 10 + wis_mod + prof_bonus

    # ------------------------------------------------------------------
    # manager helper methods
    # ------------------------------------------------------------------
    def get_ability_modifier(self, ability: str) -> int:
        """Get ability modifier for a specific ability.
        
        Args:
            ability: Ability key ('str', 'dex', 'con', 'int', 'wis', 'cha')
        
        Returns:
            Ability modifier (-5 to +5 typical range)
        """
        score = self._abilities[ability]
        return (score - 10) // 2
    
    def get_stats_dict(self) -> Dict[str, int]:
        """Get a dict representation of character stats for managers.
        
        This provides compatibility for managers that expect a dict,
        while the Character instance is the single source of truth.
        
        Returns:
            Dict with keys: str, dex, proficiency
        """
        return {
            "str": self._abilities.str,
            "dex": self._abilities.dex,
            "proficiency": self.proficiency_bonus
        }
    
    # ------------------------------------------------------------------
    # derived helpers
    # ------------------------------------------------------------------
    def header_summary(self) -> str:
        parts = []
        class_text = self.class_text.strip()
        if class_text:
            parts.append(class_text)
        elif self.level:
            parts.append(f"Level {self.level}")
        race = self.race.strip()
        if race:
            parts.append(race)
        return " · ".join(parts) if parts else "Ready for adventure"

    def display_name(self) -> str:
        return self.name.strip() or self.DEFAULT_NAME

    # ------------------------------------------------------------------
    # serialization helpers
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        payload = copy.deepcopy(self._data)
        # ensure abilities stay normalized before exporting
        payload["abilities"] = self._abilities.to_mapping()
        return payload

    def copy(self) -> "Character":
        return self.__class__(self.to_dict(), class_key=self._class_key)


__all__ = [
    "DEFAULT_ABILITY_KEYS",
    "AbilityAccessor",
    "Character",
    "Bard",
    "Cleric",
    "CharacterFactory",
    "CharacterClassInfo",
    "CLASS_REGISTRY",
    "get_class_info",
    "get_class_hit_die",
    "get_class_armor_proficiencies",
    "get_class_weapon_proficiencies",
    "get_race_ability_bonuses",
    "RACE_ABILITY_BONUSES",
]
