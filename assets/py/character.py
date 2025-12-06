"""PyScript driver for the PySheet D&D 5e character web app."""

import asyncio
import copy
import importlib.util
import json
import re
import sys
import uuid
from datetime import datetime, timedelta
from html import escape
from math import ceil, floor
from pathlib import Path
from typing import Union, Optional

try:
    from js import Blob, URL, console, document, window
except ImportError:
    # Mock for testing environments
    class _MockConsole:
        @staticmethod
        def log(*args): pass
        @staticmethod
        def warn(*args): pass
        @staticmethod
        def error(*args): pass
    
    Blob = None
    URL = None
    console = _MockConsole()
    document = None
    window = None

try:
    from pyodide import JsException
except ImportError:  # Pyodide >=0.23 exposes JsException under pyodide.ffi
    try:
        from pyodide.ffi import JsException  # type: ignore
    except ImportError:
        # For testing environments without pyodide
        class JsException(Exception):
            pass

try:
    from pyodide.ffi import create_proxy
except ImportError:
    # Mock for testing
    def create_proxy(func):
        return func

try:
    from pyodide.http import open_url, pyfetch
except ImportError:
    # Mocks for testing
    async def pyfetch(url, *args, **kwargs):
        raise ImportError("pyfetch not available in test environment")
    
    def open_url(url):
        raise ImportError("open_url not available in test environment")

from types import ModuleType

MODULE_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else (Path.cwd() / "assets" / "py")
)
console.log(f"DEBUG: MODULE_DIR = {MODULE_DIR}")
console.log(f"DEBUG: '__file__' in globals() = {'__file__' in globals()}")
console.log(f"DEBUG: Path.cwd() = {Path.cwd()}")
console.log(f"DEBUG: sys.path before update: {sys.path[:3]}...")

if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
    console.log(f"DEBUG: Added {MODULE_DIR} to sys.path[0]")
else:
    console.log(f"DEBUG: {MODULE_DIR} already in sys.path")

console.log(f"DEBUG: sys.path after update: {sys.path[:3]}...")

try:
    from character_models import Character, CharacterFactory, DEFAULT_ABILITY_KEYS, get_race_ability_bonuses
except ModuleNotFoundError:
    module_candidates = [
        MODULE_DIR / "character_models.py",
        Path.cwd() / "assets" / "py" / "character_models.py",
    ]
    loaded = False
    for module_path in module_candidates:
        try:
            if module_path.exists():
                spec = importlib.util.spec_from_file_location("character_models", module_path)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                sys.modules["character_models"] = module
                spec.loader.exec_module(module)
            else:
                source = open_url("assets/py/character_models.py").read()
                module = ModuleType("character_models")
                exec(source, module.__dict__)
                sys.modules["character_models"] = module
            Character = module.Character
            CharacterFactory = module.CharacterFactory
            DEFAULT_ABILITY_KEYS = module.DEFAULT_ABILITY_KEYS
            get_race_ability_bonuses = module.get_race_ability_bonuses
            loaded = True
            break
        except Exception:
            continue
    if not loaded:
        raise

# Import modular components
try:
    from entities import Entity, Spell, Ability, Resource, Equipment, Weapon, Armor, Shield
except ImportError:
    # Fallback for non-modular environments
    Entity = Spell = Ability = Resource = Equipment = Weapon = Armor = Shield = None

try:
    from browser_logger import BrowserLogger
except ImportError:
    # Fallback - BrowserLogger will be defined inline if needed
    BrowserLogger = None

try:
    from spell_data import (
        LOCAL_SPELLS_FALLBACK,
        SPELL_CLASS_SYNONYMS,
        SPELL_CLASS_DISPLAY_NAMES,
        SPELL_CORRECTIONS,
        apply_spell_corrections,
        is_spell_source_allowed,
        CLASS_CASTING_PROGRESSIONS,
        SPELLCASTING_PROGRESSION_TABLES,
        STANDARD_SLOT_TABLE,
        PACT_MAGIC_TABLE,
    )
except ImportError:
    # Fallback - spell data constants will be defined inline if needed
    LOCAL_SPELLS_FALLBACK = []
    SPELL_CLASS_SYNONYMS = {
        "artificer": ["artificer"],
        "bard": ["bard"],
        "cleric": ["cleric"],
        "druid": ["druid"],
        "paladin": ["paladin"],
        "ranger": ["ranger"],
        "sorcerer": ["sorcerer"],
        "warlock": ["warlock"],
        "wizard": ["wizard"],
    }
    SPELL_CLASS_DISPLAY_NAMES = {
        "artificer": "Artificer",
        "bard": "Bard",
        "cleric": "Cleric",
        "druid": "Druid",
        "paladin": "Paladin",
        "ranger": "Ranger",
        "sorcerer": "Sorcerer",
        "warlock": "Warlock",
        "wizard": "Wizard",
    }
    SPELL_CORRECTIONS = {}
    apply_spell_corrections = lambda spell: spell
    is_spell_source_allowed = lambda source: True
    CLASS_CASTING_PROGRESSIONS = {}
    SPELLCASTING_PROGRESSION_TABLES = {}
    STANDARD_SLOT_TABLE = {}
    PACT_MAGIC_TABLE = {}

try:
    from spellcasting import SpellcastingManager, SPELL_LIBRARY_STATE, set_spell_library_data, load_spell_library, apply_spell_filters, sync_prepared_spells_with_library
    console.log("DEBUG: spellcasting module imported successfully on first try")
except ImportError as e:
    # Fallback 1: Try adding assets/py to sys.path and retry
    console.warn(f"DEBUG: spellcasting module import failed: {e}")
    console.log("DEBUG: Attempting retry with explicit path insertion")
    
    try:
        assets_py = Path.cwd() / "assets" / "py"
        if str(assets_py) not in sys.path:
            sys.path.insert(0, str(assets_py))
            console.log(f"DEBUG: Added {assets_py} to sys.path[0]")
        
        from spellcasting import SpellcastingManager, SPELL_LIBRARY_STATE, set_spell_library_data, load_spell_library, apply_spell_filters, sync_prepared_spells_with_library
        console.log("DEBUG: spellcasting module imported successfully on retry")
    except ImportError as e2:
        # Fallback 2: All imports fail - use stubs
        console.error(f"DEBUG: spellcasting module import failed on retry: {e2}")
        SpellcastingManager = None
        SPELL_LIBRARY_STATE = {}
        set_spell_library_data = lambda x: None
        load_spell_library = lambda x=None: None
        apply_spell_filters = lambda auto_select=False: None
        sync_prepared_spells_with_library = lambda: None

try:
    from equipment_management import (
        InventoryManager,
        Item,
        Weapon,
        Armor,
        Shield,
        Equipment,
        format_money,
        format_weight,
        get_armor_type,
        get_armor_ac,
        ARMOR_TYPES,
        ARMOR_AC_VALUES,
    )
except ImportError:
    # Fallbacks for non-modular environments
    InventoryManager = None
    Item = Weapon = Armor = Shield = Equipment = None
    format_money = lambda x: str(x)
    format_weight = lambda x: str(x)
    get_armor_type = lambda x: "unknown"
    get_armor_ac = lambda x: None
    ARMOR_TYPES = {}
    ARMOR_AC_VALUES = {}

try:
    from export_management import (
        save_character,
        export_character,
        reset_character,
        handle_import,
        show_storage_info,
        cleanup_exports,
        schedule_auto_export,
    )
except ImportError:
    # Fallbacks for non-modular environments
    save_character = lambda *a, **kw: None
    export_character = lambda *a, **kw: None
    reset_character = lambda *a, **kw: None
    handle_import = lambda *a, **kw: None
    show_storage_info = lambda *a, **kw: None
    cleanup_exports = lambda *a, **kw: None
    schedule_auto_export = lambda *a, **kw: None


# Import the _AUTO_EXPORT_SUPPRESS flag from export_management module
# This is used to suppress auto-exports during bulk form updates
try:
    import export_management as _export_mgmt
except ImportError:
    _export_mgmt = None


# ===================================================================
# Authoritative D&D 5e Sources
# ===================================================================

AUTHORITATIVE_SOURCES = {
    "phb",  # Player's Handbook
    "xge",  # Xanathar's Guide to Everything
    "xgte",  # Xanathar's Guide to Everything (alternate abbreviation)
    "tcoe",  # Tasha's Cauldron of Everything
    "tce",  # Tasha's Cauldron of Everything (alternate abbreviation)
    "5e core rules",  # Official 5e core rules (equivalent to PHB)
}

def is_authoritative_source(source: Optional[str]) -> bool:
    """Check if spell/item source is from an authoritative D&D 5e book."""
    if not source:
        return False
    # Normalize source name for comparison
    normalized = source.lower().strip()
    # Check exact matches
    if normalized in AUTHORITATIVE_SOURCES:
        return True
    # Check if source contains any authoritative abbreviation or phrase
    for auth_source in AUTHORITATIVE_SOURCES:
        if auth_source in normalized:
            return True
    return False


# ===================================================================
# Logging System with Rolling 60-Day Window
# ===================================================================

class BrowserLogger:
    """Browser-based logger with automatic rolling 60-day window."""
    
    STORAGE_KEY = "pysheet_logs_v2"
    MAX_DAYS = 60
    MAX_ENTRIES_PER_DAY = 1000
    
    @staticmethod
    def _get_timestamp():
        """Get current ISO timestamp."""
        return datetime.now().isoformat()
    
    @staticmethod
    def _parse_date(iso_string):
        """Parse ISO timestamp and return date string (YYYY-MM-DD)."""
        try:
            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%Y-%m-%d")
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def _load_logs():
        """Load logs from localStorage."""
        try:
            stored = window.localStorage.getItem(BrowserLogger.STORAGE_KEY)
            if stored:
                return json.loads(stored)
        except Exception:
            pass
        return {"logs": [], "errors": []}
    
    @staticmethod
    def _save_logs(logs_data):
        """Save logs to localStorage with pruning."""
        try:
            # Prune old entries (> 60 days)
            cutoff_date = datetime.now()
            from datetime import timedelta
            cutoff_date = cutoff_date - timedelta(days=BrowserLogger.MAX_DAYS)
            cutoff_iso = cutoff_date.isoformat()
            
            # Filter logs and errors to keep only recent entries
            logs_data["logs"] = [
                entry for entry in logs_data.get("logs", [])
                if entry.get("timestamp", "") >= cutoff_iso
            ]
            logs_data["errors"] = [
                entry for entry in logs_data.get("errors", [])
                if entry.get("timestamp", "") >= cutoff_iso
            ]
            
            # Limit entries per day to prevent runaway growth
            today = datetime.now().strftime("%Y-%m-%d")
            today_logs = [e for e in logs_data["logs"] if e.get("timestamp", "").startswith(today)]
            if len(today_logs) > BrowserLogger.MAX_ENTRIES_PER_DAY:
                # Keep only the first MAX_ENTRIES_PER_DAY from today
                today_old = logs_data["logs"][-len(today_logs) + BrowserLogger.MAX_ENTRIES_PER_DAY:]
                past_logs = [e for e in logs_data["logs"] if not e.get("timestamp", "").startswith(today)]
                logs_data["logs"] = past_logs + today_old
            
            window.localStorage.setItem(BrowserLogger.STORAGE_KEY, json.dumps(logs_data))
        except Exception as exc:
            console.warn(f"PySheet: failed to save logs - {exc}")
    
    @staticmethod
    def info(message: str):
        """Log info message."""
        logs_data = BrowserLogger._load_logs()
        entry = {
            "timestamp": BrowserLogger._get_timestamp(),
            "level": "INFO",
            "message": str(message)
        }
        logs_data["logs"].append(entry)
        BrowserLogger._save_logs(logs_data)
        console.log(f"[INFO] {message}")
    
    @staticmethod
    def warning(message: str):
        """Log warning message."""
        logs_data = BrowserLogger._load_logs()
        entry = {
            "timestamp": BrowserLogger._get_timestamp(),
            "level": "WARNING",
            "message": str(message)
        }
        logs_data["logs"].append(entry)
        BrowserLogger._save_logs(logs_data)
        console.warn(f"[WARNING] {message}")
    
    @staticmethod
    def error(message: str, exc=None):
        """Log error message."""
        logs_data = BrowserLogger._load_logs()
        exc_str = str(exc) if exc else ""
        entry = {
            "timestamp": BrowserLogger._get_timestamp(),
            "level": "ERROR",
            "message": str(message),
            "exception": exc_str
        }
        logs_data["errors"].append(entry)
        BrowserLogger._save_logs(logs_data)
        console.error(f"[ERROR] {message}: {exc_str}")
    
    @staticmethod
    def get_stats():
        """Get statistics about stored logs."""
        logs_data = BrowserLogger._load_logs()
        now = datetime.now()
        from datetime import timedelta
        
        # Calculate oldest log date
        oldest_log = None
        if logs_data.get("logs"):
            try:
                oldest_log = min(logs_data["logs"], key=lambda x: x.get("timestamp", "")).get("timestamp")
            except (ValueError, KeyError):
                pass
        
        # Count logs by date
        logs_by_date = {}
        for entry in logs_data.get("logs", []):
            date_str = BrowserLogger._parse_date(entry.get("timestamp", ""))
            if date_str:
                logs_by_date[date_str] = logs_by_date.get(date_str, 0) + 1
        
        return {
            "total_logs": len(logs_data.get("logs", [])),
            "total_errors": len(logs_data.get("errors", [])),
            "days_with_logs": len(logs_by_date),
            "oldest_log": oldest_log,
            "logs_by_date": logs_by_date,
            "storage_bytes": len(json.dumps(logs_data))
        }


LOGGER = BrowserLogger()
LOCAL_STORAGE_KEY = "pysheet.character.v1"

# ===================================================================
# Universal Entity System
# ===================================================================

class Entity:
    """
    Base entity class - represents any displayable game object.
    Can be a spell, equipment, ability, resource, or custom entity.
    Provides unified interface for properties, serialization, and rendering.
    """
    def __init__(self, name: str, entity_type: str = "", description: str = ""):
        self.name = name
        self.entity_type = entity_type  # "spell", "equipment", "ability", "resource", etc.
        self.description = description
        self.properties = {}  # Dynamic properties - stores any key-value pairs
    
    def add_property(self, key: str, value):
        """Add or update a dynamic property"""
        self.properties[key] = value
        return self
    
    def get_property(self, key: str, default=None):
        """Get a property with optional default value"""
        return self.properties.get(key, default)
    
    def has_property(self, key: str) -> bool:
        """Check if property exists"""
        return key in self.properties
    
    def remove_property(self, key: str):
        """Remove a property"""
        if key in self.properties:
            del self.properties[key]
        return self
    
    def get_all_properties(self) -> dict:
        """Get all dynamic properties"""
        return self.properties.copy()
    
    def to_dict(self) -> dict:
        """Convert entity to dictionary for serialization"""
        return {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
            "properties": self.properties.copy()
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Entity':
        """Create Entity from dictionary"""
        if not isinstance(data, dict):
            return data
        
        entity = Entity(
            name=data.get("name", "Unknown"),
            entity_type=data.get("entity_type", ""),
            description=data.get("description", "")
        )
        
        # Restore properties
        for key, value in data.get("properties", {}).items():
            entity.add_property(key, value)
        
        return entity
    
    def __repr__(self) -> str:
        return f"Entity(name='{self.name}', type='{self.entity_type}', props={len(self.properties)})"


class Spell(Entity):
    """
    Spell entity - represents a D&D 5e spell with all its properties.
    Inherits from Entity for unified property handling and serialization.
    """
    def __init__(self, name: str, level: int = 0, school: str = "", 
                 casting_time: str = "", duration: str = "", ritual: bool = False,
                 concentration: bool = False, components: str = "", 
                 slug: str = "", classes: list = None, source: str = "", **kwargs):
        super().__init__(name, entity_type="spell", **kwargs)
        self.level = level
        self.school = school
        self.casting_time = casting_time
        self.duration = duration
        self.ritual = ritual
        self.concentration = concentration
        self.components = components
        self.slug = slug
        self.classes = classes or []
        self.source = source
    
    def to_dict(self) -> dict:
        """Convert spell to dictionary"""
        d = super().to_dict()
        d.update({
            "level": self.level,
            "school": self.school,
            "casting_time": self.casting_time,
            "duration": self.duration,
            "ritual": self.ritual,
            "concentration": self.concentration,
            "components": self.components,
            "slug": self.slug,
            "classes": self.classes,
            "source": self.source,
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Spell':
        """Create Spell from dictionary"""
        if not isinstance(data, dict):
            return data
        
        spell = Spell(
            name=data.get("name", "Unknown"),
            level=data.get("level", 0),
            school=data.get("school", ""),
            casting_time=data.get("casting_time", ""),
            duration=data.get("duration", ""),
            ritual=data.get("ritual", False),
            concentration=data.get("concentration", False),
            components=data.get("components", ""),
            slug=data.get("slug", ""),
            classes=data.get("classes", []),
            source=data.get("source", ""),
            description=data.get("description", "")
        )
        
        # Restore dynamic properties
        for key, value in data.get("properties", {}).items():
            spell.add_property(key, value)
        
        return spell
    
    def __repr__(self) -> str:
        level_label = f"L{self.level}" if self.level > 0 else "Cantrip"
        return f"Spell(name='{self.name}', {level_label}, school='{self.school}')"


class Ability(Entity):
    """
    Ability entity - represents class features, feats, or special abilities.
    """
    def __init__(self, name: str, ability_type: str = "feature", level_gained: int = 1, **kwargs):
        super().__init__(name, entity_type="ability", **kwargs)
        self.ability_type = ability_type  # "feature", "feat", "trait", etc.
        self.level_gained = level_gained
    
    def to_dict(self) -> dict:
        """Convert ability to dictionary"""
        d = super().to_dict()
        d.update({
            "ability_type": self.ability_type,
            "level_gained": self.level_gained,
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Ability':
        """Create Ability from dictionary"""
        if not isinstance(data, dict):
            return data
        
        ability = Ability(
            name=data.get("name", "Unknown"),
            ability_type=data.get("ability_type", "feature"),
            level_gained=data.get("level_gained", 1),
            description=data.get("description", "")
        )
        
        for key, value in data.get("properties", {}).items():
            ability.add_property(key, value)
        
        return ability
    
    def __repr__(self) -> str:
        return f"Ability(name='{self.name}', type='{self.ability_type}', L{self.level_gained})"


class Resource(Entity):
    """
    Resource entity - represents trackable resources like Ki, Rage, Channel Divinity uses.
    Supports current/max value tracking and use/restore operations.
    """
    def __init__(self, name: str, max_value: int = 0, current_value: int = None, **kwargs):
        super().__init__(name, entity_type="resource", **kwargs)
        self.max_value = max_value
        self.current_value = current_value if current_value is not None else max_value
    
    def use(self, amount: int = 1) -> int:
        """
        Use resource by specified amount.
        Returns actual amount used (capped at current value).
        """
        actual_used = min(amount, self.current_value)
        self.current_value = max(0, self.current_value - amount)
        return actual_used
    
    def restore(self, amount: int = None) -> int:
        """
        Restore resource.
        If amount is None, restores to full.
        Returns amount restored.
        """
        if amount is None:
            restored = self.max_value - self.current_value
            self.current_value = self.max_value
        else:
            actual_restored = min(amount, self.max_value - self.current_value)
            self.current_value += actual_restored
            restored = actual_restored
        return restored
    
    def is_available(self, amount: int = 1) -> bool:
        """Check if enough resource is available"""
        return self.current_value >= amount
    
    def get_percent(self) -> int:
        """Get remaining resource as percentage"""
        if self.max_value == 0:
            return 0
        return int((self.current_value / self.max_value) * 100)
    
    def to_dict(self) -> dict:
        """Convert resource to dictionary"""
        d = super().to_dict()
        d.update({
            "max_value": self.max_value,
            "current_value": self.current_value,
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Resource':
        """Create Resource from dictionary"""
        if not isinstance(data, dict):
            return data
        
        resource = Resource(
            name=data.get("name", "Unknown"),
            max_value=data.get("max_value", 0),
            current_value=data.get("current_value"),
            description=data.get("description", "")
        )
        
        for key, value in data.get("properties", {}).items():
            resource.add_property(key, value)
        
        return resource
    
    def __repr__(self) -> str:
        return f"Resource(name='{self.name}', {self.current_value}/{self.max_value})"

# ===================================================================
# Equipment Classes
# ===================================================================

class Equipment(Entity):
    """Equipment entity - base class for all equipment items"""
    def __init__(self, name: str, cost: str = "", weight: str = "", source: str = "", **kwargs):
        super().__init__(name, entity_type="equipment", **kwargs)
        self.cost = cost
        self.weight = weight
        self.source = source
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        d = super().to_dict()
        d.update({
            "cost": self.cost,
            "weight": self.weight,
            "source": self.source
        })
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Equipment':
        """Create Equipment object from dictionary"""
        if not isinstance(data, dict):
            return data  # Already an object or invalid
        
        name = data.get("name", "Unknown")
        
        # Detect type and create appropriate subclass
        if data.get("damage"):
            return Weapon.from_dict(data)
        elif data.get("armor_class") and "shield" not in name.lower():
            return Armor.from_dict(data)
        elif data.get("ac"):
            return Shield.from_dict(data)
        else:
            # Default Equipment
            return Equipment(
                name=name,
                cost=data.get("cost", ""),
                weight=data.get("weight", ""),
                source=data.get("source", ""),
                description=data.get("description", "")
            )


class Weapon(Equipment):
    """Weapon equipment with damage properties"""
    def __init__(self, name: str, damage: str = "", damage_type: str = "", 
                 range_text: str = "", properties: str = "", **kwargs):
        super().__init__(name, **kwargs)
        self.damage = damage
        self.damage_type = damage_type
        self.range = range_text
        self.properties = properties
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.damage:
            d["damage"] = self.damage
        if self.damage_type:
            d["damage_type"] = self.damage_type
        if self.range:
            d["range"] = self.range
        if self.properties:
            d["properties"] = self.properties
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Weapon':
        """Create Weapon from dictionary"""
        return Weapon(
            name=data.get("name", "Unknown"),
            cost=data.get("cost", ""),
            weight=data.get("weight", ""),
            source=data.get("source", ""),
            damage=data.get("damage", ""),
            damage_type=data.get("damage_type", ""),
            range_text=data.get("range", ""),
            properties=data.get("properties", ""),
            description=data.get("description", "")
        )


class Armor(Equipment):
    """Armor equipment with AC value"""
    def __init__(self, name: str, armor_class: Union[int, str] = "", **kwargs):
        super().__init__(name, **kwargs)
        self.armor_class = armor_class
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.armor_class:
            d["armor_class"] = self.armor_class
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Armor':
        """Create Armor from dictionary"""
        return Armor(
            name=data.get("name", "Unknown"),
            cost=data.get("cost", ""),
            weight=data.get("weight", ""),
            source=data.get("source", ""),
            armor_class=data.get("armor_class", ""),
            description=data.get("description", "")
        )


class Shield(Equipment):
    """Shield equipment with AC bonus"""
    def __init__(self, name: str, ac_bonus: str = "", **kwargs):
        super().__init__(name, **kwargs)
        self.ac_bonus = ac_bonus
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.ac_bonus:
            d["ac"] = self.ac_bonus
        return d
    
    @staticmethod
    def from_dict(data: dict) -> 'Shield':
        """Create Shield from dictionary"""
        return Shield(
            name=data.get("name", "Unknown"),
            cost=data.get("cost", ""),
            weight=data.get("weight", ""),
            source=data.get("source", ""),
            ac_bonus=data.get("ac", ""),
            description=data.get("description", "")
        )


ABILITY_ORDER = list(DEFAULT_ABILITY_KEYS)

SKILLS = {
    "acrobatics": {"ability": "dex", "label": "Acrobatics"},
    "animal_handling": {"ability": "wis", "label": "Animal Handling"},
    "arcana": {"ability": "int", "label": "Arcana"},
    "athletics": {"ability": "str", "label": "Athletics"},
    "deception": {"ability": "cha", "label": "Deception"},
    "history": {"ability": "int", "label": "History"},
    "insight": {"ability": "wis", "label": "Insight"},
    "intimidation": {"ability": "cha", "label": "Intimidation"},
    "investigation": {"ability": "int", "label": "Investigation"},
    "medicine": {"ability": "wis", "label": "Medicine"},
    "nature": {"ability": "int", "label": "Nature"},
    "perception": {"ability": "wis", "label": "Perception"},
    "performance": {"ability": "cha", "label": "Performance"},
    "persuasion": {"ability": "cha", "label": "Persuasion"},
    "religion": {"ability": "int", "label": "Religion"},
    "sleight_of_hand": {"ability": "dex", "label": "Sleight of Hand"},
    "stealth": {"ability": "dex", "label": "Stealth"},
    "survival": {"ability": "wis", "label": "Survival"},
}

SPELL_FIELDS = {
    "notes": "spell_notes",
}

OPEN5E_SPELLS_ENDPOINT = "https://api.open5e.com/spells/?limit=200&ordering=name"
OPEN5E_MAX_PAGES = 15
MAX_SPELL_RENDER = 200
SPELL_CACHE_VERSION = 4
SPELL_LIBRARY_STORAGE_KEY = f"pysheet.spells.v{SPELL_CACHE_VERSION}"

# Allowed spell sources (only from these books)
# Maps from Open5e document titles/slugs to abbreviations we accept
ALLOWED_SPELL_SOURCES_MAP = {
    # Abbreviations
    "phb": True,
    "tce": True,
    "xge": True,
    # Full names (case-insensitive match)
    "player's handbook": True,
    "players handbook": True,
    "tasha's cauldron of everything": True,
    "tashas cauldron of everything": True,
    "xanathar's guide to everything": True,
    "xanathars guide to everything": True,
    # Slugs
    "players-handbook": True,
    "tashas-cauldron-of-everything": True,
    "xanathars-guide-to-everything": True,
}

SPELL_LIBRARY_STATE = {
    "loaded": False,
    "loading": False,
    "spells": [],
    "class_options": list(CharacterFactory.supported_classes()),
    "last_profile_signature": "",
    "spell_map": {},
}

# Initialize SUPPORTED_SPELL_CLASSES with fallback
try:
    SUPPORTED_SPELL_CLASSES = set(CharacterFactory.supported_classes())
except (NameError, AttributeError):
    # Fallback if CharacterFactory is not available
    SUPPORTED_SPELL_CLASSES = set(SPELL_CLASS_SYNONYMS.keys())

WEAPON_LIBRARY_STATE = {
    "loading": False,
    "weapons": [],
    "weapon_map": {},
}

# Equipment library state - will be fetched from Open5e
EQUIPMENT_LIBRARY_STATE = {
    "loading": False,
    "loaded": False,
    "equipment": [],
    "equipment_map": {},
}

_EVENT_PROXIES: list = []
_EQUIPMENT_RESULT_PROXY = None  # Track the current equipment results listener to remove it



# Export/Import functions moved to export_management.py
# Imported above with fallback stubs





def set_spell_library_data(spells: Optional[list[dict]]) -> None:
    """Set spell library data and build lookup map with deduplication."""
    spell_list = spells or []
    
    # Deduplicate by slug to prevent duplicates in spell chooser
    seen_slugs: set[str] = set()
    deduplicated: list[dict] = []
    for spell in spell_list:
        if isinstance(spell, dict):
            slug = spell.get("slug", "")
            if slug and slug not in seen_slugs:
                deduplicated.append(spell)
                seen_slugs.add(slug)
            elif not slug:
                # Keep spells without slug (shouldn't happen, but be safe)
                deduplicated.append(spell)
    
    # Log if duplicates were removed
    if len(deduplicated) < len(spell_list):
        removed_count = len(spell_list) - len(deduplicated)
        LOGGER.info(f"Removed {removed_count} duplicate spell entries")
    
    SPELL_LIBRARY_STATE["spells"] = deduplicated
    SPELL_LIBRARY_STATE["spell_map"] = {
        spell.get("slug"): spell
        for spell in deduplicated
        if isinstance(spell, dict) and spell.get("slug")
    }


# Spell data extracted to spell_data.py
# Pre-populate with fallback spells so old saved spells can get their details at render time
set_spell_library_data(LOCAL_SPELLS_FALLBACK)
# Mark spell library as loaded so domain spells can auto-populate on page load
SPELL_LIBRARY_STATE["loaded"] = True
# Note: populate_spell_class_filter() will be called later during page initialization
# after document is ready, using the fallback spells loaded above

# InventoryManager class moved to equipment_management.py
# Imported above with fallback stub

# All InventoryManager methods also moved

INVENTORY_MANAGER = InventoryManager() if InventoryManager is not None else None
if SpellcastingManager is not None:
    try:
        SPELLCASTING_MANAGER = SpellcastingManager()
        console.log("DEBUG: SPELLCASTING_MANAGER instantiated successfully")
    except Exception as e:
        console.error(f"DEBUG: SPELLCASTING_MANAGER instantiation failed: {e}")
        SPELLCASTING_MANAGER = None
else:
    console.warn("DEBUG: SpellcastingManager class is None, cannot instantiate")
    SPELLCASTING_MANAGER = None


def reset_spellcasting_state():
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.reset_state()


def sort_prepared_spells():
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.sort_prepared_spells()


def load_spellcasting_state(state: Optional[dict]):
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.load_state(state)


def sync_prepared_spells_with_library():
    if SPELLCASTING_MANAGER is not None:
        console.log("DEBUG: sync_prepared_spells_with_library() called")
        SPELLCASTING_MANAGER.sync_with_library()
    else:
        console.warn("DEBUG: sync_prepared_spells_with_library() - SPELLCASTING_MANAGER is None")


def get_prepared_slug_set() -> set[str]:
    if SPELLCASTING_MANAGER is not None:
        prepared = SPELLCASTING_MANAGER.get_prepared_slug_set()
        console.log(f"DEBUG: get_prepared_slug_set returned {len(prepared)} spells: {list(prepared)[:5]}...")
        return prepared
    console.warn("DEBUG: get_prepared_slug_set - SPELLCASTING_MANAGER is None")
    return set()


def is_spell_prepared(slug: Optional[str]) -> bool:
    if SPELLCASTING_MANAGER is not None:
        return SPELLCASTING_MANAGER.is_spell_prepared(slug)
    return False


def add_spell_to_spellbook(slug: str):
    if SPELLCASTING_MANAGER is not None:
        console.log(f"DEBUG: add_spell_to_spellbook({slug})")
        SPELLCASTING_MANAGER.add_spell(slug)
    else:
        console.warn(f"DEBUG: add_spell_to_spellbook({slug}) - SPELLCASTING_MANAGER is None")


def remove_spell_from_spellbook(slug: str):
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.remove_spell(slug)


def render_spellbook():
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.render_spellbook()


def compute_spell_slot_summary(profile: Optional[dict] = None) -> dict:
    if SPELLCASTING_MANAGER is not None:
        return SPELLCASTING_MANAGER.compute_slot_summary(profile)
    return {}


def render_spell_slots(slot_summary: Optional[dict] = None):
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.render_spell_slots(slot_summary)


def adjust_spell_slot(level: int, delta: int):
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.adjust_spell_slot(level, delta)


def adjust_pact_slot(delta: int):
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.adjust_pact_slot(delta)


def reset_spell_slots(_event=None):
    if SPELLCASTING_MANAGER is not None:
        SPELLCASTING_MANAGER.reset_spell_slots()
    reset_channel_divinity()


def load_inventory_state(state: Optional[dict]):
    """Load inventory from character state."""
    if INVENTORY_MANAGER is not None:
        INVENTORY_MANAGER.load_state(state)


def render_inventory():
    """Render the inventory list."""
    if INVENTORY_MANAGER is not None:
        INVENTORY_MANAGER.render_inventory()


MAX_RESOURCES = 12
MAX_INVENTORY_ITEMS = 50
CURRENCY_ORDER = ["pp", "gp", "ep", "sp", "cp"]

DEFAULT_STATE = {
    "identity": {
        "name": "",
        "class": "Wizard 1",
        "race": "Human",
        "background": "Sage",
        "alignment": "Neutral Good",
        "player_name": "",
        "subclass": "",
    },
    "level": 1,
    "inspiration": 0,
    "spell_ability": "int",
    "abilities": {
        ability: {"score": 10, "save_proficient": False} for ability in ABILITY_ORDER
    },
    "skills": {
        skill: {"proficient": False, "expertise": False, "bonus": 0} for skill in SKILLS
    },
    "combat": {
        "armor_class": 10,
        "speed": 30,
        "max_hp": 8,
        "current_hp": 8,
        "temp_hp": 0,
        "hit_dice": "1d8",
        "hit_dice_available": 0,
        "channel_divinity_available": 0,
        "death_saves_success": 0,
        "death_saves_failure": 0,
    },
    "inventory": {
        "items": [],
        "currency": {key: 0 for key in CURRENCY_ORDER},
    },
    "notes": {
        "features": "",
        "attacks": "",
        "notes": "",
    },
    "feats": [],
    "spells": {key: "" for key in SPELL_FIELDS},
    "spellcasting": {
        "prepared": [],
        "slots_used": {level: 0 for level in range(1, 10)},
        "pact_used": 0,
    },
    "resources": [],
}

def clone_default_state() -> dict:
    """Return a deep copy of the default state template."""
    return copy.deepcopy(DEFAULT_STATE)


def get_element(element_id):
    return document.getElementById(element_id)


def get_text_value(element_id: str) -> str:
    element = get_element(element_id)
    if element is None:
        return ""
    return element.value or ""


def get_numeric_value(element_id: str, default: int = 0) -> int:
    element = get_element(element_id)
    if element is None:
        return default
    raw = element.value
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def get_checkbox(element_id: str) -> bool:
    element = get_element(element_id)
    if element is None:
        return False
    return bool(element.checked)


def set_form_value(element_id: str, value):
    element = get_element(element_id)
    if element is None:
        return
    tag = element.tagName.lower()
    if getattr(element, "type", "").lower() == "checkbox":
        element.checked = bool(value)
    elif tag == "textarea":
        element.value = value or ""
    elif tag == "select":
        element.value = value or ""
    else:
        element.value = value if value is not None else ""


def set_text(element_id: str, value: str):
    element = get_element(element_id)
    if element is None:
        return
    element.innerText = value


def set_html(element_id: str, html: str):
    element = get_element(element_id)
    if element is None:
        return
    element.innerHTML = html


def ability_modifier(score: int) -> int:
    return floor((score - 10) / 2)


def format_bonus(value: int) -> str:
    return f"{value:+d}"


def get_hit_dice_for_class(class_name: str) -> str:
    """Return the hit dice for a given D&D 5e class."""
    class_lower = (class_name or "").lower().strip()
    hit_dice_map = {
        "barbarian": "1d12",
        "fighter": "1d10",
        "paladin": "1d10",
        "ranger": "1d10",
        "bard": "1d8",
        "cleric": "1d8",
        "druid": "1d8",
        "monk": "1d8",
        "rogue": "1d8",
        "warlock": "1d8",
        "sorcerer": "1d6",
        "wizard": "1d6",
    }
    return hit_dice_map.get(class_lower, "1d8")  # Default to 1d8 if unknown


def get_armor_proficiencies_for_class(class_name: str, domain: str = "") -> str:
    """Return armor proficiencies for a given D&D 5e class.
    
    Args:
        class_name: The character's class
        domain: The cleric domain (if applicable)
    """
    class_lower = (class_name or "").lower().strip()
    proficiencies_map = {
        "barbarian": "Light armor, Medium armor, Shields",
        "bard": "Light armor",
        "cleric": "Light armor, Medium armor, Shields",
        "druid": "Light armor, Medium armor, Shields",
        "fighter": "All armor, Shields",
        "monk": "None",
        "paladin": "All armor, Shields",
        "ranger": "Light armor, Medium armor, Shields",
        "rogue": "Light armor",
        "sorcerer": "None",
        "warlock": "Light armor",
        "wizard": "None",
    }
    profs = proficiencies_map.get(class_lower, "None")
    
    # Life Domain clerics get Heavy Armor proficiency
    if class_lower == "cleric" and domain and "life" in domain.lower():
        profs = "Light armor, Medium armor, Heavy armor, Shields"
    
    return profs


def get_weapon_proficiencies_for_class(class_name: str) -> str:
    """Return weapon proficiencies for a given D&D 5e class."""
    class_lower = (class_name or "").lower().strip()
    proficiencies_map = {
        "barbarian": "Simple melee, Martial melee",
        "bard": "Simple melee, Hand crossbows, Longswords, Rapiers, Shortswords",
        "cleric": "Simple melee, Simple ranged",
        "druid": "Clubs, Daggers, Darts, Javelins, Maces, Quarterstaffs, Scimitars, Sickles, Slings, Spears",
        "fighter": "Simple melee, Simple ranged, Martial melee, Martial ranged",
        "monk": "Simple melee, Shortswords",
        "paladin": "Simple melee, Simple ranged, Martial melee, Martial ranged",
        "ranger": "Simple melee, Simple ranged, Martial melee, Martial ranged",
        "rogue": "Hand crossbows, Longswords, Rapiers, Shortswords, Simple melee",
        "sorcerer": "Daggers, Darts, Slings, Quarterstaffs, Light crossbows",
        "warlock": "Simple melee",
        "wizard": "Daggers, Darts, Slings, Quarterstaffs, Light crossbows",
    }
    return proficiencies_map.get(class_lower, "None")


def generate_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def clamp(value: int, minimum: Optional[int] = None, maximum: Optional[int] = None) -> int:
    if minimum is not None and value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum
    return value


def parse_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        lower = value.strip().lower()
        return lower in {"true", "yes", "1"}
    return False


def normalize_class_token(token: Optional[str]) -> str | None:
    if not token:
        return None
    cleaned = token.replace("’", "'")
    cleaned = re.sub(r"\(.*?\)", "", cleaned)
    cleaned = cleaned.replace("-", " ")
    cleaned = " ".join(cleaned.lower().split())
    if not cleaned:
        return None
    for canonical, synonyms in SPELL_CLASS_SYNONYMS.items():
        if cleaned == canonical:
            return canonical
        if cleaned in synonyms:
            return canonical
        for synonym in synonyms:
            if cleaned == synonym:
                return canonical
    for canonical, synonyms in SPELL_CLASS_SYNONYMS.items():
        if cleaned.startswith(canonical):
            return canonical
        for synonym in synonyms:
            if cleaned.startswith(synonym):
                return canonical
    return None


def extract_character_classes(raw_text: Optional[str] = None) -> list[dict]:
    if raw_text is None:
        raw_text = get_text_value("class")
    if not raw_text:
        return []
    segments = re.split(r"[\+/,&]+", raw_text)
    entries: list[dict] = []
    for segment in segments:
        part = segment.strip()
        if not part:
            continue
        lower_part = part.lower()
        level_match = re.search(r"(\d+)", part)
        level = int(level_match.group(1)) if level_match else None
        if level_match:
            name_part = part[: level_match.start()].strip()
        else:
            name_part = part.strip()
        if not name_part:
            name_part = part.strip()
        canonical = normalize_class_token(name_part)
        if canonical is None:
            canonical = normalize_class_token(lower_part)
        if canonical is None:
            continue
        entries.append({
            "key": canonical,
            "level": level,
            "raw": lower_part,
        })
    return entries


def determine_progression_key(class_key: str, raw_text: str) -> str:
    base = CLASS_CASTING_PROGRESSIONS.get(class_key, "none")
    lowered = raw_text or ""
    if class_key == "fighter":
        if "eldritch" in lowered or "arcane archer" in lowered:
            return "third"
        return "none"
    if class_key == "rogue":
        if "arcane trickster" in lowered:
            return "third"
        return "none"
    return base


def get_progression_table(progression_key: str) -> list[int]:
    return SPELLCASTING_PROGRESSION_TABLES.get(
        progression_key, SPELLCASTING_PROGRESSION_TABLES["none"]
    )


def compute_spellcasting_profile(
    raw_text: Optional[str] = None,
    fallback_level: Optional[int] = None,
) -> dict:
    entries = extract_character_classes(raw_text)
    if fallback_level is None:
        fallback_level = get_numeric_value("level", 1)
    fallback_level = max(1, int(fallback_level or 1))

    allowed_classes: list[str] = []
    max_spell_level = -1
    has_progression = False

    for entry in entries:
        class_key = entry["key"]
        class_level = entry["level"] if entry["level"] is not None else fallback_level
        class_level = max(1, min(int(class_level or fallback_level), 20))
        progression = determine_progression_key(class_key, entry["raw"])
        if progression == "none":
            continue
        has_progression = True
        table = get_progression_table(progression)
        level_cap = table[class_level] if class_level < len(table) else table[-1]
        if class_key not in allowed_classes:
            allowed_classes.append(class_key)
        if level_cap > max_spell_level:
            max_spell_level = level_cap

    if not has_progression:
        max_spell_level = -1
    elif max_spell_level < 0:
        max_spell_level = 0

    return {
        "entries": entries,
        "allowed_classes": allowed_classes,
        "max_spell_level": max_spell_level,
    }

def get_spell_by_slug(slug: Optional[str]) -> dict | None:
    if not slug:
        return None
    spell_map = SPELL_LIBRARY_STATE.get("spell_map") or {}
    if slug in spell_map:
        spell = spell_map[slug]
    else:
        spell = None
        for s in SPELL_LIBRARY_STATE.get("spells", []):
            if s.get("slug") == slug:
                spell = s
                break
    
    # Try normalizing slug by removing source suffixes (e.g., "-a5e" for Level Up Advanced 5e)
    if spell is None and "-a5e" in slug:
        normalized_slug = slug.replace("-a5e", "")
        if normalized_slug in spell_map:
            spell = spell_map[normalized_slug]
        else:
            for s in SPELL_LIBRARY_STATE.get("spells", []):
                if s.get("slug") == normalized_slug:
                    spell = s
                    break
    
    # Normalize spell record: ensure level_int is set from level field
    if spell and "level_int" not in spell and "level" in spell:
        spell["level_int"] = spell.get("level", 0)
    
    return spell


def handle_add_spell_click(event, slug: str):
    if event is not None:
        event.stopPropagation()
        event.preventDefault()
    
    # Get the button element to check if add will succeed
    button_el = event.target if event else None
    
    # Try to add the spell
    result_before = len(SPELLCASTING_MANAGER.prepared)
    add_spell_to_spellbook(slug)
    result_after = len(SPELLCASTING_MANAGER.prepared)
    
    # If spell wasn't added, apply red blink animation
    if result_before == result_after and button_el:
        button_el.classList.add("deny-blink")
        # Remove animation class after it completes to allow re-triggering
        def remove_anim():
            try:
                button_el.classList.remove("deny-blink")
            except:
                pass
        document.defaultView.setTimeout(remove_anim, 600)


def handle_remove_spell_click(event, slug: str):
    if event is not None:
        event.stopPropagation()
        event.preventDefault()
    remove_spell_from_spellbook(slug)


def handle_slot_button(event, level: int, delta: int):
    if event is not None:
        event.stopPropagation()
        event.preventDefault()
    adjust_spell_slot(level, delta)


def handle_pact_slot_button(event, delta: int):
    if event is not None:
        event.stopPropagation()
        event.preventDefault()
    adjust_pact_slot(delta)


def compute_proficiency(level: int) -> int:
    level = max(1, min(20, level))
    return 2 + (level - 1) // 4


# Armor type mapping - for AC calculations
ARMOR_TYPES = {
    "light": ["leather", "studded leather", "studded"],
    "medium": ["hide", "chain shirt", "scale mail", "breastplate", "half plate"],
    "heavy": ["plate", "chain mail", "splint", "splint armor"],
}

# D&D 5e standard armor AC values (from PHB)
ARMOR_AC_VALUES = {
    "leather": 11,
    "studded leather": 12,
    "studded": 12,
    "hide": 12,
    "chain shirt": 13,
    "scale mail": 14,
    "breastplate": 14,
    "half plate": 15,
    "plate": 18,
    "chain mail": 16,
    "splint": 17,
    "splint armor": 17,
}


def get_armor_type(armor_name: str) -> str:
    """Determine armor type (light, medium, heavy) from armor name."""
    name_lower = armor_name.lower()
    for armor_type, names in ARMOR_TYPES.items():
        for name_pattern in names:
            if name_pattern in name_lower:
                return armor_type
    return "unknown"


def get_armor_ac(armor_name: str) -> int:
    """Get standard D&D 5e AC value for armor by name. Returns None if not standard armor."""
    name_lower = armor_name.lower()
    for armor_pattern, ac_value in ARMOR_AC_VALUES.items():
        if armor_pattern in name_lower:
            return ac_value
    return None


def generate_ac_tooltip() -> tuple[int, str]:
    """
    Generate AC tooltip showing breakdown of components.
    Returns: (ac_value, tooltip_html)
    
    D&D 5e AC Rules:
    - No armor: 10 + DEX modifier
    - Light armor: AC + DEX modifier
    - Medium armor: AC + DEX modifier (max +2)
    - Heavy armor: AC (no DEX modifier)
    """
    dex_score = get_numeric_value("dex-score", 10)
    dex_mod = ability_modifier(dex_score)
    
    # Check for armor
    armor_ac = None
    armor_name = None
    armor_type = None
    if INVENTORY_MANAGER is not None:
        for item in INVENTORY_MANAGER.items:
            if item.get("category") == "Armor" and item.get("qty", 0) > 0:
                try:
                    notes_str = item.get("notes", "")
                    if notes_str and notes_str.startswith("{"):
                        extra_props = json.loads(notes_str)
                        ac_val = extra_props.get("armor_class", extra_props.get("ac"))
                        if ac_val:
                            armor_ac = int(ac_val)
                            armor_name = item.get("name", "Unknown Armor")
                            armor_type = get_armor_type(armor_name)
                            break
                except:
                    pass
    
    # Build breakdown
    rows = []
    if armor_ac is not None:
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">{escape(armor_name)}</span><span class="tooltip-value">{armor_ac}</span></div>')
        
        if armor_type == "heavy":
            # Heavy armor: AC is fixed, no DEX modifier
            rows.append(f'<div class="tooltip-row"><span class="tooltip-label">DEX modifier</span><span class="tooltip-value">—</span><span style="font-size: 0.8rem; color: #94a3b8;">(heavy armor, no DEX)</span></div>')
            base_ac = armor_ac
        elif armor_type == "medium":
            # Medium armor: AC + DEX (capped at +2)
            dex_applied = min(dex_mod, 2)
            rows.append(f'<div class="tooltip-row"><span class="tooltip-label">DEX modifier</span><span class="tooltip-value">{format_bonus(dex_applied)}</span><span style="font-size: 0.8rem; color: #94a3b8;">(max +2)</span></div>')
            base_ac = armor_ac + dex_applied
        else:
            # Light armor or unknown: AC + full DEX
            rows.append(f'<div class="tooltip-row"><span class="tooltip-label">DEX modifier</span><span class="tooltip-value">{format_bonus(dex_mod)}</span></div>')
            base_ac = armor_ac + dex_mod
    else:
        # No armor
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">Base AC</span><span class="tooltip-value">10</span></div>')
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">DEX modifier</span><span class="tooltip-value">{format_bonus(dex_mod)}</span></div>')
        base_ac = 10 + dex_mod
    
    # Add item modifiers (skip armor-only items)
    item_ac_mod = 0
    item_mods = []
    if INVENTORY_MANAGER is not None:
        for item in INVENTORY_MANAGER.items:
            try:
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                    # Skip armor-only items - they affect AC differently in calculate_armor_class
                    if extra_props.get("armor_only", False):
                        continue
                    ac_mod = extra_props.get("ac_modifier", 0)
                    if ac_mod:
                        ac_mod = int(ac_mod)
                        item_ac_mod += ac_mod
                        item_mods.append((item.get("name", "Unknown"), ac_mod))
            except:
                pass
    
    if item_mods:
        rows.append('<div style="margin-top: 0.4rem; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 0.4rem;"></div>')
        for item_name, mod_val in item_mods:
            rows.append(f'<div class="tooltip-row"><span class="tooltip-label">{escape(item_name)}</span><span class="tooltip-value">{format_bonus(mod_val)}</span></div>')
    
    total_ac = base_ac + item_ac_mod
    tooltip_html = f'<div class="stat-tooltip multiline">{"".join(rows)}</div>'
    return max(1, total_ac), tooltip_html


def generate_save_tooltip(ability: str, ability_score: int, proficient: bool, proficiency: int) -> tuple[int, str]:
    """Generate tooltip for ability save. Returns: (save_total, tooltip_html)"""
    mod = ability_modifier(ability_score)
    save_bonus = mod + (proficiency if proficient else 0)
    
    rows = []
    rows.append(f'<div class="tooltip-row"><span class="tooltip-label">Ability mod ({ability.upper()})</span><span class="tooltip-value">{format_bonus(mod)}</span></div>')
    
    if proficient:
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">Proficiency</span><span class="tooltip-value">{format_bonus(proficiency)}</span></div>')
    
    # Add saves modifiers from items
    item_saves_mod = 0
    if INVENTORY_MANAGER is not None:
        for item in INVENTORY_MANAGER.items:
            try:
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                    saves_mod = extra_props.get("saves_modifier", 0)
                    if saves_mod:
                        item_saves_mod += int(saves_mod)
            except:
                pass
    
    if item_saves_mod:
        rows.append('<div style="margin-top: 0.4rem; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 0.4rem;"></div>')
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">Item modifiers</span><span class="tooltip-value">{format_bonus(item_saves_mod)}</span></div>')
    
    save_total = save_bonus + item_saves_mod
    tooltip_html = f'<div class="stat-tooltip multiline">{"".join(rows)}</div>'
    return save_total, tooltip_html


def generate_skill_tooltip(skill_key: str, ability_scores: dict, proficiency: int, race_bonuses: dict) -> str:
    """Generate tooltip for skill bonus."""
    ability_key = SKILLS.get(skill_key, {}).get("ability", "")
    ability_score = ability_scores.get(ability_key, 10)
    race_bonus = race_bonuses.get(ability_key, 0)
    total_score = ability_score + race_bonus
    
    mod = ability_modifier(total_score)
    proficient = get_checkbox(f"{skill_key}-prof")
    expertise = get_checkbox(f"{skill_key}-exp")
    
    rows = []
    rows.append(f'<div class="tooltip-row"><span class="tooltip-label">{ability_key.upper()} mod</span><span class="tooltip-value">{format_bonus(mod)}</span></div>')
    
    if race_bonus:
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">Race bonus</span><span class="tooltip-value">{format_bonus(race_bonus)}</span></div>')
    
    if expertise:
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">Expertise</span><span class="tooltip-value">{format_bonus(proficiency * 2)}</span></div>')
    elif proficient:
        rows.append(f'<div class="tooltip-row"><span class="tooltip-label">Proficiency</span><span class="tooltip-value">{format_bonus(proficiency)}</span></div>')
    
    return f'<div class="stat-tooltip multiline">{"".join(rows)}</div>'


def calculate_armor_class() -> int:
    """
    Calculate AC based on armor type, DEX modifier, and item modifiers.
    D&D 5e AC Rules:
    - 10 + DEX if no armor
    - Light Armor: Armor AC + DEX modifier
    - Medium Armor: Armor AC + DEX modifier (max +2)
    - Heavy Armor: Armor AC (no DEX modifier)
    Plus any AC modifiers from equipped items
    """
    # Get DEX modifier
    dex_score = get_numeric_value("dex-score", 10)
    dex_mod = ability_modifier(dex_score)
    
    # Check for armor in inventory
    armor_ac = None
    armor_name = None
    armor_type = None
    
    if INVENTORY_MANAGER is not None:
        for item in INVENTORY_MANAGER.items:
            category = item.get("category", "")
            if category == "Armor" and item.get("qty", 0) > 0:
                # Found an armor item - try to get its AC
                try:
                    notes_str = item.get("notes", "")
                    if notes_str and notes_str.startswith("{"):
                        extra_props = json.loads(notes_str)
                        ac_val = extra_props.get("armor_class", extra_props.get("ac"))
                        if ac_val:
                            armor_ac = int(ac_val)
                            armor_name = item.get("name", "Unknown Armor")
                            armor_type = get_armor_type(armor_name)
                            break  # Use first armor found
                except:
                    pass
    
    # Calculate base AC
    if armor_ac is not None:
        if armor_type == "heavy":
            # Heavy armor: AC is fixed, no DEX modifier
            base_ac = armor_ac
        elif armor_type == "medium":
            # Medium armor: AC + DEX (max +2)
            base_ac = armor_ac + min(dex_mod, 2)
        else:
            # Light armor or unknown: AC + DEX (no cap)
            base_ac = armor_ac + dex_mod
    else:
        # No armor - use 10 + DEX
        base_ac = 10 + dex_mod
    
    # Add AC modifiers from items
    # armor-only items add to AC but not to saves (e.g. +1 breastplate)
    # regular items add to both AC and saves (e.g. Ring of Protection)
    item_ac_mod = 0
    if INVENTORY_MANAGER is not None:
        for item in INVENTORY_MANAGER.items:
            try:
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                    ac_mod = extra_props.get("ac_modifier", 0)
                    if ac_mod:
                        item_ac_mod += int(ac_mod)
            except:
                pass
    
    return max(1, base_ac + item_ac_mod)


def _compute_skill_entry(
    skill_key: str,
    ability_scores: dict[str, int],
    proficiency_bonus: int,
    race_bonuses: dict[str, int] = None,
) -> tuple[bool, bool, int]:
    if race_bonuses is None:
        race_bonuses = {}
    ability_key = SKILLS.get(skill_key, {}).get("ability", "")
    ability_score = ability_scores.get(ability_key, 10) + race_bonuses.get(ability_key, 0)
    base_modifier = ability_modifier(ability_score)
    proficient = get_checkbox(f"{skill_key}-prof")
    expertise = get_checkbox(f"{skill_key}-exp")
    multiplier = 2 if expertise else 1 if proficient else 0
    total = base_modifier + multiplier * proficiency_bonus
    return proficient, expertise, total


def gather_scores() -> dict:
    return {ability: get_numeric_value(f"{ability}-score", 10) for ability in ABILITY_ORDER}


def snapshot_character_from_form() -> Character:
    identity = {
        "name": get_text_value("name"),
        "class": get_text_value("class"),
        "race": get_text_value("race"),
        "background": get_text_value("background"),
        "alignment": get_text_value("alignment"),
        "player_name": get_text_value("player_name"),
        "domain": get_text_value("domain"),
    }

    abilities = {}
    for ability in ABILITY_ORDER:
        abilities[ability] = {
            "score": get_numeric_value(f"{ability}-score", 10),
            "save_proficient": get_checkbox(f"{ability}-save-prof"),
        }

    data = {
        "identity": identity,
        "level": get_numeric_value("level", 1),
        "inspiration": get_numeric_value("inspiration", 0),
        "spell_ability": get_text_value("spell_ability") or "int",
        "abilities": abilities,
    }

    return CharacterFactory.from_dict(data)


def reset_channel_divinity(event=None):
    """Reset Channel Divinity uses to proficiency bonus."""
    level = get_numeric_value("level", 1)
    proficiency = compute_proficiency(level)
    set_form_value("channel_divinity_available", str(proficiency))
    update_calculations()
    schedule_auto_export()


def update_calculations(*_args):
    scores = gather_scores()
    level = get_numeric_value("level", 1)
    proficiency = compute_proficiency(level)
    race = get_text_value("race")
    race_bonuses = get_race_ability_bonuses(race)
    
    # Get and normalize class name
    class_name = (get_text_value("class") or "").lower()
    
    # Update hit dice based on class (show die type, not quantity)
    hit_dice_type = get_hit_dice_for_class(class_name)
    set_form_value("hit_dice", hit_dice_type)
    
    # Update proficiencies based on class - render as table
    domain = get_text_value("domain")
    armor_prof_text = get_armor_proficiencies_for_class(class_name, domain)
    weapon_prof_text = get_weapon_proficiencies_for_class(class_name)
    
    # Parse and render armor proficiencies as table rows
    armor_profs = [p.strip() for p in armor_prof_text.split(",") if p.strip()]
    armor_tbody = get_element("armor-proficiencies")
    if armor_tbody:
        armor_tbody.innerHTML = ""
        tr = document.createElement("tr")
        for prof in armor_profs:
            td = document.createElement("td")
            div = document.createElement("div")
            div.className = "proficiency-item armor"
            div.textContent = prof
            td.appendChild(div)
            tr.appendChild(td)
        armor_tbody.appendChild(tr)
    
    # Parse and render weapon proficiencies as table rows
    weapon_profs = [p.strip() for p in weapon_prof_text.split(",") if p.strip()]
    weapon_tbody = get_element("weapon-proficiencies")
    if weapon_tbody:
        weapon_tbody.innerHTML = ""
        tr = document.createElement("tr")
        for prof in weapon_profs:
            td = document.createElement("td")
            div = document.createElement("div")
            div.className = "proficiency-item weapon"
            div.textContent = prof
            td.appendChild(div)
            tr.appendChild(td)
        weapon_tbody.appendChild(tr)
    
    # Auto-sync hit dice remaining with level (only if it's currently empty/0)
    current_hit_dice_available = get_numeric_value("hit_dice_available", 0)
    if current_hit_dice_available == 0:
        set_form_value("hit_dice_available", level)

    set_text("proficiency-bonus", format_bonus(proficiency))

    for ability, score in scores.items():
        # Calculate race bonus and total
        race_bonus = race_bonuses.get(ability, 0)
        total_score = score + race_bonus
        
        # Update display
        if race_bonus > 0:
            set_text(f"{ability}-race", f"+{race_bonus}")
        else:
            set_text(f"{ability}-race", "—")
        set_text(f"{ability}-total", str(total_score))
        
        # Calculate modifier and save from total
        mod = ability_modifier(total_score)
        set_text(f"{ability}-mod", format_bonus(mod))
        proficient = get_checkbox(f"{ability}-save-prof")
        save_total, save_tooltip = generate_save_tooltip(ability, total_score, proficient, proficiency)
        save_elem = get_element(f"{ability}-save")
        if save_elem:
            save_elem.innerHTML = f'<span class="stat-value">{format_bonus(save_total)}{save_tooltip}</span>'

    dex_mod = ability_modifier(scores["dex"] + race_bonuses.get("dex", 0))
    # Initiative tooltip: just DEX modifier
    initiative_tooltip = f'<div class="stat-tooltip"><div class="tooltip-row"><span class="tooltip-label">DEX modifier</span><span class="tooltip-value">{format_bonus(dex_mod)}</span></div></div>'
    initiative_elem = get_element("initiative")
    if initiative_elem:
        initiative_elem.innerHTML = f'<span class="stat-value">{format_bonus(dex_mod)}{initiative_tooltip}</span>'

    # Calculate and update Armor Class with tooltip
    ac, ac_tooltip = generate_ac_tooltip()
    armor_class_elem = get_element("armor_class")
    if armor_class_elem:
        armor_class_elem.innerHTML = f'<span class="stat-value">{ac}{ac_tooltip}</span>'

    # Calculate concentration save (1d20 + CON modifier vs DC 10)
    con_mod = ability_modifier(scores["con"] + race_bonuses.get("con", 0))
    con_tooltip = f'<div class="stat-tooltip"><div class="tooltip-row"><span class="tooltip-label">CON modifier</span><span class="tooltip-value">{format_bonus(con_mod)}</span></div><div class="tooltip-row"><span class="tooltip-label">DC</span><span class="tooltip-value">10</span></div></div>'
    conc_save_elem = get_element("concentration-save")
    if conc_save_elem:
        conc_save_elem.innerHTML = f'<span class="stat-value">1d20 {format_bonus(con_mod)} vs DC 10{con_tooltip}</span>'

    skill_totals = {}
    for skill_key in SKILLS:
        _, _, total = _compute_skill_entry(skill_key, scores, proficiency, race_bonuses)
        skill_totals[skill_key] = total
        skill_tooltip = generate_skill_tooltip(skill_key, scores, proficiency, race_bonuses)
        skill_elem = get_element(f"{skill_key}-total")
        if skill_elem:
            skill_elem.innerHTML = f'<span class="stat-value">{format_bonus(total)}{skill_tooltip}</span>'

    # Passive Perception
    passive_perception = 10 + skill_totals.get("perception", 0)
    perception_total = skill_totals.get("perception", 0)
    passive_tooltip = f'<div class="stat-tooltip multiline"><div class="tooltip-row"><span class="tooltip-label">Base</span><span class="tooltip-value">10</span></div><div class="tooltip-row"><span class="tooltip-label">Perception bonus</span><span class="tooltip-value">{format_bonus(perception_total)}</span></div></div>'
    passive_elem = get_element("passive-perception")
    if passive_elem:
        passive_elem.innerHTML = f'<span class="stat-value">{passive_perception}{passive_tooltip}</span>'

    # Derive spell ability from class
    class_spell_ability_map = {
        "bard": "cha",
        "cleric": "wis",
        "druid": "wis",
        "monk": "wis",
        "paladin": "cha",
        "ranger": "wis",
        "sorcerer": "cha",
        "warlock": "cha",
        "wizard": "int",
    }
    spell_ability = class_spell_ability_map.get(class_name.lower() if class_name else "", "int")
    spell_score = scores.get(spell_ability, 10) + race_bonuses.get(spell_ability, 0)
    spell_mod = ability_modifier(spell_score)
    spell_save_dc = 8 + proficiency + spell_mod
    spell_attack = proficiency + spell_mod
    
    # Spell Save DC tooltip
    spell_dc_tooltip = f'<div class="stat-tooltip multiline"><div class="tooltip-row"><span class="tooltip-label">Base</span><span class="tooltip-value">8</span></div><div class="tooltip-row"><span class="tooltip-label">Proficiency</span><span class="tooltip-value">{format_bonus(proficiency)}</span></div><div class="tooltip-row"><span class="tooltip-label">{spell_ability.upper()} modifier</span><span class="tooltip-value">{format_bonus(spell_mod)}</span></div></div>'
    spell_dc_elem = get_element("spell-save-dc")
    if spell_dc_elem:
        spell_dc_elem.innerHTML = f'<span class="stat-value">{spell_save_dc}{spell_dc_tooltip}</span>'
    
    # Spell Attack tooltip
    spell_attack_tooltip = f'<div class="stat-tooltip multiline"><div class="tooltip-row"><span class="tooltip-label">Proficiency</span><span class="tooltip-value">{format_bonus(proficiency)}</span></div><div class="tooltip-row"><span class="tooltip-label">{spell_ability.upper()} modifier</span><span class="tooltip-value">{format_bonus(spell_mod)}</span></div></div>'
    spell_attack_elem = get_element("spell-attack")
    if spell_attack_elem:
        spell_attack_elem.innerHTML = f'<span class="stat-value">{format_bonus(spell_attack)}{spell_attack_tooltip}</span>'

    # Calculate max prepared spells (class_name already lowercased above)
    if class_name == "cleric":
        max_prepared = level + spell_mod
    elif class_name == "druid":
        max_prepared = level + spell_mod
    elif class_name == "paladin":
        max_prepared = level // 2 + spell_mod
    elif class_name == "ranger":
        max_prepared = level // 2 + spell_mod
    elif class_name == "wizard":
        max_prepared = level + spell_mod
    elif class_name == "warlock":
        max_prepared = level  # Warlocks know spells, always max prepared
    elif class_name == "bard":
        max_prepared = level + spell_mod
    elif class_name == "sorcerer":
        max_prepared = level + spell_mod
    else:
        max_prepared = 0  # Other classes don't prepare spells
    
    max_prepared = max(0, max_prepared)  # Never negative
    
    # Count only user-prepared spells (exclude domain bonus spells and cantrips)
    domain = get_text_value("domain")
    domain_bonus_slugs = set(get_domain_bonus_spells(domain, level)) if domain else set()
    if SPELLCASTING_MANAGER is not None:
        prepared_count = SPELLCASTING_MANAGER.get_prepared_non_cantrip_count(domain_bonus_slugs)
    else:
        prepared_count = 0
    
    # Build counter display with calculation tooltip
    counter_display = f"{prepared_count} / {max_prepared}"
    
    # Create tooltip showing calculation
    if class_name and class_name.lower() in ["cleric", "druid", "paladin", "ranger", "wizard", "bard", "sorcerer"]:
        if class_name.lower() == "paladin" or class_name.lower() == "ranger":
            calc_tooltip = f"Max: {max_prepared} = ⌊Level/2⌋ + {spell_ability.upper()} modifier ({level}÷2 + {spell_mod})"
            calc_hint = f"Max prepared spells: ⌊{level}/2⌋ + {spell_mod} ({spell_ability}) = {max_prepared}"
        else:
            calc_tooltip = f"Max: {max_prepared} = Level + {spell_ability.upper()} modifier ({level} + {spell_mod})"
            calc_hint = f"Max prepared spells: {level} + {spell_mod} ({spell_ability}) = {max_prepared}"
    else:
        calc_tooltip = f"Max: {max_prepared}"
        calc_hint = f"Max prepared spells: {max_prepared}"
    
    counter_elem = get_element("spellbook-prepared-count")
    if counter_elem:
        counter_elem.textContent = counter_display
        counter_elem.title = calc_tooltip
    
    # Update the hint text
    hint_elem = get_element("prepared-calc-hint")
    if hint_elem:
        hint_elem.textContent = calc_hint
    
    # Debug logging
    console.log(f"DEBUG: update_calculations() spell counter update")
    console.log(f"  class_name: {class_name}")
    console.log(f"  level: {level}")
    console.log(f"  spell_ability: {spell_ability}")
    console.log(f"  spell_score: {spell_score}")
    console.log(f"  spell_mod: {spell_mod}")
    console.log(f"  max_prepared: {max_prepared}")
    console.log(f"  prepared_count: {prepared_count}")
    console.log(f"  display: {counter_display}")
    console.log(f"  prepared_slug_set: {list(get_prepared_slug_set())}")
    console.log(f"  domain_bonus_slugs: {list(domain_bonus_slugs)}")

    # Update HP progress bar
    current_hp = get_numeric_value("current_hp", 0)
    max_hp = get_numeric_value("max_hp", 0)
    temp_hp = get_numeric_value("temp_hp", 0)
    
    if max_hp > 0:
        hp_percentage = max(0, min(100, int((current_hp / max_hp) * 100)))
        if temp_hp > 0:
            hp_label = f"({current_hp} / {max_hp} +{temp_hp})"
            # Calculate temp HP bar as overflow: show only the portion beyond current HP
            temp_hp_percentage = max(0, min(100, int((temp_hp / max_hp) * 100)))
        else:
            hp_label = f"({current_hp} / {max_hp})"
            temp_hp_percentage = 0
    else:
        hp_percentage = 0
        hp_label = f"({current_hp} / 0)"
        temp_hp_percentage = 0
    
    hp_bar_fill = get_element("hp-bar-fill")
    if hp_bar_fill:
        hp_bar_fill.style.width = f"{hp_percentage}%"
        # Round right edge only when temp HP is 0 (not adjacent to purple bar)
        if temp_hp_percentage > 0:
            hp_bar_fill.style.borderRadius = "0.5rem 0 0 0.5rem"
        else:
            hp_bar_fill.style.borderRadius = "0.5rem"
        
        # Calculate color: Red (0%) -> Yellow (50%) -> Green (100%)
        # Use HSL for easier color transitions
        if hp_percentage <= 50:
            # Red to Yellow: 0% -> 50%
            hue = 60 * (hp_percentage / 50)  # 0 (red) to 60 (yellow)
            saturation = 100
            lightness = 40
        else:
            # Yellow to Green: 50% -> 100%
            hue = 60 + (60 * ((hp_percentage - 50) / 50))  # 60 (yellow) to 120 (green)
            saturation = 100
            lightness = 40
        
        hp_bar_fill.style.background = f"hsl({hue}, {saturation}%, {lightness}%)"
    
    hp_bar_temp = get_element("hp-bar-temp")
    if hp_bar_temp:
        hp_bar_temp.style.width = f"{temp_hp_percentage}%"
        hp_bar_temp.style.left = f"{hp_percentage}%"
    
    set_text("hp-bar-label", hp_label)

    # Update hit dice pips display
    hit_dice_type = get_text_value("hit_dice")
    hit_dice_available = get_numeric_value("hit_dice_available", 0)
    hit_dice_cap = max(0, get_numeric_value("level", 1))
    
    if hit_dice_cap > 0:
        hd_label = f"{hit_dice_type} ({hit_dice_available} / {hit_dice_cap})"
    else:
        hd_label = f"{hit_dice_type} (0 / 0)"
    
    # Generate pip elements
    hd_pips_container = get_element("hd-pips-container")
    if hd_pips_container:
        # Clear existing pips
        hd_pips_container.innerHTML = ""
        
        # Create pips
        for i in range(hit_dice_cap):
            pip = document.createElement("div")
            pip.className = "hd-pip"
            if i < hit_dice_available:
                pip.classList.add("available")
            hd_pips_container.appendChild(pip)
    
    set_text("hd-bar-label", hd_label)

    # Update Channel Divinity display with pips
    level = get_numeric_value("level", 1)
    proficiency = compute_proficiency(level)
    channel_divinity_available = get_numeric_value("channel_divinity_available", 0)
    
    cd_pips_container = get_element("cd-pips-container")
    if cd_pips_container:
        # Clear existing pips
        cd_pips_container.innerHTML = ""
        
        # Create pips
        for i in range(proficiency):
            pip = document.createElement("div")
            pip.className = "cd-pip"
            if i < channel_divinity_available:
                pip.classList.add("available")
            cd_pips_container.appendChild(pip)

    update_equipment_totals()

    slot_summary = compute_spell_slot_summary(
        compute_spellcasting_profile()
    )
    render_spell_slots(slot_summary)
    update_header_display()
    
    # Render class features and feats
    render_class_features()
    render_feats()
    render_spellbook()


def collect_character_data() -> dict:
    ability_scores: dict[str, int] = {}
    data = {
        "identity": {
            "name": get_text_value("name"),
            "class": get_text_value("class"),
            "race": get_text_value("race"),
            "background": get_text_value("background"),
            "alignment": get_text_value("alignment"),
            "player_name": get_text_value("player_name"),
            "domain": get_text_value("domain"),
        },
        "level": get_numeric_value("level", 1),
        "inspiration": get_numeric_value("inspiration", 0),
        "spell_ability": get_text_value("spell_ability") or "int",
        "abilities": {},
        "skills": {},
        "combat": {
            "armor_class": calculate_armor_class(),
            "speed": get_numeric_value("speed", 30),
            "max_hp": get_numeric_value("max_hp", 8),
            "current_hp": get_numeric_value("current_hp", 8),
            "temp_hp": get_numeric_value("temp_hp", 0),
            "hit_dice": get_text_value("hit_dice"),
            "hit_dice_available": get_numeric_value("hit_dice_available", 0),
            "death_saves_success": sum(1 for i in range(1, 4) if get_checkbox(f"death_saves_success_{i}")),
            "death_saves_failure": sum(1 for i in range(1, 4) if get_checkbox(f"death_saves_failure_{i}")),
        },
        "notes": {
            "equipment": get_text_value("equipment"),
            "features": get_text_value("features"),
            "attacks": get_text_value("attacks"),
            "notes": get_text_value("notes"),
        },
        "inventory": {
            # items collected from the inventory manager
            "items": INVENTORY_MANAGER.items if (INVENTORY_MANAGER is not None) else [],
            "currency": {key: get_numeric_value(f"currency-{key}", 0) for key in CURRENCY_ORDER},
        },
        "spells": {
            key: get_text_value(element_id) for key, element_id in SPELL_FIELDS.items()
        },
    }

    for ability in ABILITY_ORDER:
        score_value = get_numeric_value(f"{ability}-score", 10)
        ability_scores[ability] = score_value
        data["abilities"][ability] = {
            "score": score_value,
            "save_proficient": get_checkbox(f"{ability}-save-prof"),
        }

    proficiency_value = compute_proficiency(data["level"])
    for skill in SKILLS:
        prof_flag, exp_flag, total = _compute_skill_entry(skill, ability_scores, proficiency_value)
        data["skills"][skill] = {
            "proficient": get_checkbox(f"{skill}-prof"),
            "expertise": get_checkbox(f"{skill}-exp"),
            "bonus": total,
        }

    data["spellcasting"] = SPELLCASTING_MANAGER.export_state() if (SPELLCASTING_MANAGER is not None) else {}

    # Determine if this will be a Cleric character
    class_text = data["identity"].get("class", "")
    class_tokens = Character._extract_class_tokens(class_text)
    is_cleric = "cleric" in class_tokens if class_tokens else False
    
    # For Cleric, sync domain to subclass since they're mapped together
    if is_cleric:
        domain_value = data["identity"].get("domain", "")
        console.log(f"DEBUG: Cleric domain collected from form: '{domain_value}'")
        data["identity"]["subclass"] = domain_value

    character = CharacterFactory.from_dict(data)
    return character.to_dict()


def populate_form(data: dict):
    # Suppress auto-exports during bulk form updates to avoid performance issues
    # Access the flag from the export_management module
    previous_suppression = False
    if _export_mgmt is not None:
        previous_suppression = _export_mgmt._AUTO_EXPORT_SUPPRESS
        _export_mgmt._AUTO_EXPORT_SUPPRESS = True
    try:
        character = CharacterFactory.from_dict(data)
        normalized = character.to_dict()

        # Normalize class: extract just the class name from "Class Level" format
        class_text = character.class_text.strip()
        if class_text:
            # Extract the first word as the class name (handles "Wizard 5" -> "Wizard")
            class_name = class_text.split()[0]
            set_form_value("class", class_name)
        else:
            set_form_value("class", "")
        
        set_form_value("name", character.name)
        set_form_value("race", character.race)
        set_form_value("background", character.background)
        set_form_value("alignment", character.alignment)
        set_form_value("player_name", character.player_name)
        set_form_value("domain", character.domain)

        set_form_value("level", character.level)
        set_form_value("inspiration", character.inspiration)
        set_form_value("spell_ability", character.spell_ability)

        for ability in ABILITY_ORDER:
            set_form_value(f"{ability}-score", character.attributes[ability])
            set_form_value(f"{ability}-save-prof", character.attributes.is_proficient(ability))

        for skill in SKILLS:
            skill_state = normalized.get("skills", {}).get(skill, {})
            set_form_value(f"{skill}-prof", skill_state.get("proficient", False))
            set_form_value(f"{skill}-exp", skill_state.get("expertise", False))

        combat = normalized.get("combat", {})
        set_form_value("armor_class", combat.get("armor_class", 10))
        set_form_value("speed", combat.get("speed", 30))
        set_form_value("max_hp", combat.get("max_hp", 8))
        set_form_value("current_hp", combat.get("current_hp", 8))
        set_form_value("temp_hp", combat.get("temp_hp", 0))
        set_form_value("hit_dice", combat.get("hit_dice", ""))
        set_form_value("hit_dice_available", combat.get("hit_dice_available", 0))
        
        # Load death saves as checkboxes
        death_success = combat.get("death_saves_success", 0)
        for i in range(1, 4):
            set_form_value(f"death_saves_success_{i}", i <= death_success)
        death_failure = combat.get("death_saves_failure", 0)
        for i in range(1, 4):
            set_form_value(f"death_saves_failure_{i}", i <= death_failure)

        notes = normalized.get("notes", {})
        set_form_value("equipment", notes.get("equipment", ""))
        set_form_value("features", notes.get("features", ""))
        set_form_value("attacks", notes.get("attacks", ""))
        set_form_value("notes", notes.get("notes", ""))

        spells = normalized.get("spells", {})
        for key, element_id in SPELL_FIELDS.items():
            set_form_value(element_id, spells.get(key, ""))

        load_spellcasting_state(normalized.get("spellcasting"))

        # Load inventory BEFORE update_calculations so totals can be calculated correctly
        load_inventory_state(normalized)
        render_inventory()

        # NOW update calculations (which calls update_equipment_totals)
        update_calculations()

        # populate currency
        inv = normalized.get("inventory", {})
        currency = inv.get("currency", {})
        for key in CURRENCY_ORDER:
            set_form_value(f"currency-{key}", currency.get(key, 0))

        # NOTE: Old equipment table code removed - using new InventoryManager system instead
        # items = get_equipment_items_from_data(normalized)
        # render_equipment_table(items)
        # update_equipment_totals()
    finally:
        if _export_mgmt is not None:
            _export_mgmt._AUTO_EXPORT_SUPPRESS = previous_suppression


def format_money(value: float) -> str:
    try:
        return f"{value:.2f}"
    except Exception:
        return str(value)


def format_weight(value: float) -> str:
    try:
        return f"{value:.2f}"
    except Exception:
        return str(value)


def format_spell_level_label(level_int: int) -> str:
    if level_int <= 0:
        return "Cantrip"
    remainder = level_int % 100
    if 10 <= remainder <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(level_int % 10, "th")
    return f"{level_int}{suffix}-level"


def _coerce_spell_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(part) for part in value if part)
    return str(value)


def _make_paragraphs(text: str) -> str:
    if not text:
        return ""
    paragraphs = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped:
            paragraphs.append(f"<p>{escape(stripped)}</p>")
    return "".join(paragraphs)


def sanitize_spell_record(raw: dict) -> Optional[dict]:
    name = raw.get("name") or "Unknown Spell"
    slug_source = raw.get("slug") or name
    slug = re.sub(r"[^a-z0-9]+", "-", slug_source.lower()).strip("-")

    level_value = raw.get("level_int")
    if level_value is None:
        level_value = raw.get("level")
    level_int = parse_int(level_value, 0)
    level_label = format_spell_level_label(level_int)

    # Handle multiple class field formats:
    # 1. dnd_class: "Bard, Sorcerer, Wizard" (Open5e standard)
    # 2. spell_lists: ["bard", "sorcerer", "wizard"] (Open5e alternative)
    # 3. classes: ["Wizard", "Sorcerer"] (custom format or other sources)
    classes_field = raw.get("dnd_class") or ""
    
    if not classes_field:
        # Try spell_lists field (Open5e provides this)
        spell_lists = raw.get("spell_lists")
        if isinstance(spell_lists, list) and spell_lists:
            classes_field = ", ".join(str(c) for c in spell_lists)
        elif not classes_field:
            # Try classes field as fallback (list or string format)
            classes_raw_input = raw.get("classes")
            if isinstance(classes_raw_input, list):
                classes_field = ", ".join(str(c) for c in classes_raw_input)
            elif isinstance(classes_raw_input, str):
                classes_field = classes_raw_input
            else:
                classes_field = ""

    
    classes_raw = [token.strip() for token in re.split(r"[;,/]+", classes_field) if token.strip()]
    classes: list[str] = []
    for token in classes_raw:
        canonical = normalize_class_token(token)
        if canonical and canonical in SUPPORTED_SPELL_CLASSES and canonical not in classes:
            classes.append(canonical)
    if not classes:
        return None
    classes_display = [SPELL_CLASS_DISPLAY_NAMES.get(c, c.title()) for c in classes]

    school = (raw.get("school") or "").title()
    casting_time = raw.get("casting_time") or ""
    range_text = raw.get("range") or ""
    components = raw.get("components") or ""
    material = raw.get("material") or ""
    duration = raw.get("duration") or ""
    ritual = is_truthy(raw.get("ritual"))
    concentration = is_truthy(raw.get("concentration"))

    desc_text = _coerce_spell_text(raw.get("desc"))
    higher_text = _coerce_spell_text(raw.get("higher_level"))
    desc_html = _make_paragraphs(desc_text)
    higher_html = _make_paragraphs(higher_text)
    description_html = desc_html
    if higher_html:
        description_html += "<p class=\"spell-section-title\">At Higher Levels</p>" + higher_html

    source = raw.get("document__title") or raw.get("document__slug") or raw.get("document") or ""

    search_fields = [
        name,
        classes_field,
        desc_text,
        higher_text,
        school,
        casting_time,
        range_text,
        components,
        material,
        duration,
        source,
    ]
    search_blob = " ".join(part for part in search_fields if part).lower()

    result = {
        "slug": slug,
        "name": name,
        "level_int": level_int,
        "level_label": level_label,
        "school": school,
        "casting_time": casting_time,
        "range": range_text,
        "components": components,
        "material": material,
        "duration": duration,
        "ritual": ritual,
        "concentration": concentration,
        "classes": classes,
        "classes_display": classes_display,
        "description_html": description_html,
        "search_blob": search_blob,
        "source": source,
    }
    
    # Apply any known corrections to this spell
    return apply_spell_corrections(result)


def sanitize_spell_list(raw_spells: list[dict]) -> list[dict]:
    sanitized: list[dict] = []
    seen_slugs: set[str] = set()
    rejected_count = 0
    
    # Debug: Check what SPELL_CLASS_SYNONYMS contains at runtime
    if len(raw_spells) > 0:
        if len(SPELL_CLASS_SYNONYMS) == 0:
            console.warn(f"PySheet: WARNING! SPELL_CLASS_SYNONYMS is EMPTY! This will cause all spells to be rejected!")
        if len(SUPPORTED_SPELL_CLASSES) == 0:
            console.warn(f"PySheet: WARNING! SUPPORTED_SPELL_CLASSES is EMPTY! This will cause all spells to be rejected!")
    
    for spell in raw_spells:
        record = sanitize_spell_record(spell)
        if record is not None:
            slug = record.get("slug")
            # Skip if we've already seen this spell slug
            if slug not in seen_slugs:
                sanitized.append(record)
                seen_slugs.add(slug)
        else:
            rejected_count += 1
    
    # Debug logging if all spells were rejected
    if rejected_count == len(raw_spells) and rejected_count > 0:
        console.warn(f"PySheet: All {rejected_count} spells rejected during sanitization!")
        if len(raw_spells) > 0:
            first_spell = raw_spells[0]
            console.warn(f"  First spell: {first_spell.get('name', 'Unknown')}")
            console.warn(f"  Classes field: {first_spell.get('classes')}")
            console.warn(f"  Type of classes: {type(first_spell.get('classes'))}")
            console.warn(f"  dnd_class field: {first_spell.get('dnd_class')}")
            console.warn(f"  SPELL_CLASS_SYNONYMS: {SPELL_CLASS_SYNONYMS}")
            console.warn(f"  SUPPORTED_SPELL_CLASSES: {SUPPORTED_SPELL_CLASSES}")
    
    sanitized.sort(key=lambda item: (item["level_int"], item["name"].lower()))
    return sanitized


def rehydrate_cached_spell(record: dict) -> Optional[dict]:
    classes = []
    for token in record.get("classes", []):
        canonical = normalize_class_token(token)
        if canonical and canonical in SUPPORTED_SPELL_CLASSES and canonical not in classes:
            classes.append(canonical)
    if not classes:
        return None
    classes_display = record.get("classes_display") or [
        SPELL_CLASS_DISPLAY_NAMES.get(c, c.title()) for c in classes
    ]
    return {
        "slug": record.get("slug", ""),
        "name": record.get("name", "Unknown Spell"),
        "level_int": parse_int(record.get("level_int"), 0),
        "level_label": record.get("level_label", format_spell_level_label(parse_int(record.get("level_int"), 0))),
        "school": record.get("school", ""),
        "casting_time": record.get("casting_time", ""),
        "range": record.get("range", ""),
        "components": record.get("components", ""),
        "material": record.get("material", ""),
        "duration": record.get("duration", ""),
        "ritual": bool(record.get("ritual", False)),
        "concentration": bool(record.get("concentration", False)),
        "classes": classes,
        "classes_display": classes_display,
        "description_html": record.get("description_html", ""),
        "search_blob": (record.get("search_blob", "") or "").lower(),
        "source": record.get("source", ""),
    }


def load_spell_cache() -> list[dict] | None:
    cached = window.localStorage.getItem(SPELL_LIBRARY_STORAGE_KEY)
    if not cached:
        return None
    try:
        payload = json.loads(cached)
    except Exception as exc:
        console.warn(f"PySheet: failed to parse spell cache ({exc})")
        return None
    if payload.get("version") != SPELL_CACHE_VERSION:
        return None
    spells = payload.get("spells")
    if not isinstance(spells, list):
        return None
    rehydrated: list[dict] = []
    seen_slugs: set[str] = set()
    for record in spells:
        try:
            if not isinstance(record, dict):
                continue
            hydrated = rehydrate_cached_spell(record)
            if hydrated is not None:
                slug = hydrated.get("slug")
                # Deduplicate by slug from cache
                if slug and slug not in seen_slugs:
                    rehydrated.append(hydrated)
                    seen_slugs.add(slug)
        except Exception as exc:
            console.warn(f"PySheet: skipping cached spell due to error ({exc})")
    if not rehydrated:
        return None
    rehydrated.sort(key=lambda item: (item["level_int"], item["name"].lower()))
    return rehydrated


def save_spell_cache(spells: list[dict]) -> None:
    payload = {"version": SPELL_CACHE_VERSION, "spells": spells}
    try:
        window.localStorage.setItem(SPELL_LIBRARY_STORAGE_KEY, json.dumps(payload))
    except Exception as exc:
        console.warn(f"PySheet: unable to store spell cache ({exc})")


async def fetch_open5e_spells() -> list[dict]:
    spells: list[dict] = []
    url = OPEN5E_SPELLS_ENDPOINT
    pages = 0
    while url and pages < OPEN5E_MAX_PAGES:
        response = await pyfetch(url)
        if not response.ok:
            raise RuntimeError(f"Open5e request failed ({response.status})")
        data = await response.json()
        results = data.get("results", [])
        if isinstance(results, list):
            spells.extend(results)
        url = data.get("next")
        pages += 1
    return spells


def update_spell_library_status(message: str):
    status_el = get_element("spell-library-status")
    if status_el is not None:
        status_el.innerText = message


def populate_spell_class_filter(spells: list[dict] | None):
    select_el = get_element("spell-class-filter")
    if select_el is None:
        return
    available_classes: set[str] = set()
    if spells:
        for spell in spells:
            for class_key in spell.get("classes", []):
                if class_key in SUPPORTED_SPELL_CLASSES:
                    available_classes.add(class_key)

    if not available_classes:
        available_classes.update(CharacterFactory.supported_classes())

    current_value = select_el.value if hasattr(select_el, "value") else ""

    options = ["<option value=\"\">Any class</option>"]
    ordered_classes = [
        class_key
        for class_key in CharacterFactory.supported_classes()
        if class_key in available_classes
    ]
    for class_key in ordered_classes:
        label = SPELL_CLASS_DISPLAY_NAMES.get(class_key, class_key.title())
        options.append(
            f"<option value=\"{escape(class_key)}\">{escape(label)}</option>"
        )

    select_el.innerHTML = "".join(options)
    if current_value and current_value in ordered_classes:
        select_el.value = current_value
    elif current_value == "":
        select_el.value = ""
    SPELL_LIBRARY_STATE["class_options"] = ordered_classes


def build_spell_card_html(spell: dict, allowed_classes: set[str] | None = None) -> str:
    allowed_set: set[str] = set(allowed_classes or set())
    slug = spell.get("slug", "")
    prepared = is_spell_prepared(slug)
    spell_classes = set(spell.get("classes", []))
    can_add = prepared or not allowed_set or bool(spell_classes.intersection(allowed_set))
    
    # Check if this is a domain bonus spell (cannot be removed)
    domain = get_text_value("domain")
    character_level = get_numeric_value("level", 1)
    is_domain_bonus = slug in get_domain_bonus_spells(domain, character_level) if domain else False
    can_remove = prepared and not is_domain_bonus

    meta_parts: list[str] = []
    level_label = spell.get("level_label")
    if level_label:
        meta_parts.append(level_label)
    school = spell.get("school")
    if school:
        meta_parts.append(school)
    meta_text = " · ".join(part for part in meta_parts if part)

    tags = []
    if not prepared and not can_add:
        tags.append("<span class=\"spell-tag unavailable\">Unavailable</span>")
    if spell.get("ritual"):
        tags.append("<span class=\"spell-tag\">Ritual</span>")
    if spell.get("concentration"):
        tags.append("<span class=\"spell-tag\">Concentration</span>")
    if is_domain_bonus and prepared:
        tags.append("<span class=\"spell-tag domain-bonus\">Domain Bonus</span>")
    tags_html = "".join(tags)

    action = "remove" if can_remove else "add" if not prepared else None
    action_label = "Remove" if can_remove else "Add" if not prepared else None
    button_classes = ["spell-action"]
    if prepared:
        button_classes.append("selected")
    if is_domain_bonus and prepared:
        button_classes.append("locked")
    if not prepared and not can_add:
        button_classes.append("locked")
    button_class_attr = " ".join(button_classes)
    disabled_attr = " disabled" if (not prepared and not can_add) or (is_domain_bonus and prepared) else ""
    
    title_text = ""
    if is_domain_bonus and prepared:
        title_text = "Domain bonus spells cannot be removed"
    elif not prepared and not can_add:
        title_text = "Not available to current class"
    title_attr = f" title=\"{title_text}\"" if title_text else ""
    
    action_button = (
        f"<button type=\"button\" class=\"{button_class_attr}\" "
        f"data-spell-action=\"{action}\" data-spell-slug=\"{escape(slug)}\"{disabled_attr}{title_attr}>{action_label}</button>"
        if slug and action and action_label
        else ""
    )

    properties = []
    casting_time = spell.get("casting_time")
    if casting_time:
        properties.append(
            f"<div><dt>Casting Time</dt><dd>{escape(casting_time)}</dd></div>"
        )
    range_text = spell.get("range")
    if range_text:
        properties.append(f"<div><dt>Range</dt><dd>{escape(range_text)}</dd></div>")
    components = spell.get("components")
    material = spell.get("material")
    if components:
        comp_text = escape(components)
        if material:
            comp_text = f"{comp_text} ({escape(material)})"
        properties.append(f"<div><dt>Components</dt><dd>{comp_text}</dd></div>")
    duration = spell.get("duration")
    if duration:
        properties.append(f"<div><dt>Duration</dt><dd>{escape(duration)}</dd></div>")
    properties_html = ""
    if properties:
        properties_html = "<dl class=\"spell-properties\">" + "".join(properties) + "</dl>"

    classes_display = spell.get("classes_display", [])
    classes_html = ""
    if classes_display:
        classes_html = (
            "<div class=\"spell-classes\"><strong>Classes: </strong>"
            + escape(", ".join(classes_display))
            + "</div>"
        )

    description_html = spell.get("description_html") or ""
    if description_html:
        description_html = f"<div class=\"spell-text\">{description_html}</div>"

    body_html = (
        "<div class=\"spell-body\">"
        + properties_html
        + classes_html
        + description_html
        + "</div>"
    )

    summary_parts = [
        "<summary>",
        "<div class=\"spell-summary\">",
        f"<span class=\"spell-name\">{escape(spell.get('name', 'Spell'))}</span>",
    ]
    if meta_text:
        summary_parts.append(f"<span class=\"spell-meta\">{escape(meta_text)}</span>")
    
    # Add mnemonics for key spell properties
    mnemonics = []
    if spell.get("concentration"):
        mnemonics.append("<span class=\"spell-mnemonic\" title=\"Concentration\">Conc.</span>")
    if spell.get("ritual"):
        mnemonics.append("<span class=\"spell-mnemonic\" title=\"Ritual\">Rit.</span>")
    if is_domain_bonus and prepared:
        mnemonics.append("<span class=\"spell-mnemonic domain\" title=\"Domain Bonus\">Dom.</span>")
    
    # Add range mnemonic
    range_text = spell.get("range", "").lower()
    if range_text:
        if "self" in range_text:
            range_label = "Self"
        elif "touch" in range_text:
            range_label = "Touch"
        elif "sight" in range_text:
            range_label = "Sight"
        elif "unlimited" in range_text:
            range_label = "∞"
        else:
            # Extract number from range (e.g., "60 feet" -> "60ft")
            import re
            match = re.search(r'(\d+)\s*(?:feet|ft)', range_text)
            if match:
                range_label = f"{match.group(1)}ft"
            else:
                range_label = None
        
        if range_label:
            mnemonics.append(f"<span class=\"spell-mnemonic range\" title=\"Range: {escape(spell.get('range', ''))}\">{escape(range_label)}</span>")
    
    if mnemonics:
        summary_parts.append(f"<span class=\"spell-mnemonics\">{''.join(mnemonics)}</span>")
    
    summary_parts.append("</div>")
    summary_parts.append("</summary>")
    
    # Add tags and action button after summary
    summary_parts.append(f"<div class=\"spell-tags\">{tags_html}</div>" if tags_html else "")
    summary_parts.append(f"<div class=\"spell-summary-actions\">{action_button}</div>" if action_button else "")
    
    summary_html = "".join(summary_parts)

    class_list = ["spell-card"]
    if prepared:
        class_list.append("selected")
    classes_attr = " ".join(class_list)

    return (
        f"<details class=\"{classes_attr}\" data-spell-slug=\"{escape(slug)}\">"
        + summary_html
        + body_html
        + "</details>"
    )


def update_header_display():
    character = snapshot_character_from_form()
    set_text("character-header-name", character.display_name())
    set_text("character-header-summary", character.header_summary())


def render_spell_results(
    spells: list[dict], allowed_classes: set[str] | None = None
) -> tuple[int, bool, int]:
    results_el = get_element("spell-library-results")
    if results_el is None:
        return 0, False, 0
    if not spells:
        results_el.innerHTML = (
            "<div class=\"spell-library-empty\">No spells match your filters.</div>"
        )
        return 0, False, 0
    limited = spells[:MAX_SPELL_RENDER]
    cards_html = "".join(
        build_spell_card_html(spell, allowed_classes) for spell in limited
    )
    truncated = len(spells) > MAX_SPELL_RENDER
    if truncated:
        cards_html += (
            f"<div class=\"spell-library-empty\">Showing first {MAX_SPELL_RENDER} spells. Refine your filters for more precise results.</div>"
        )
    results_el.innerHTML = cards_html
    attach_spell_card_handlers(results_el)
    return len(limited), truncated, len(spells)


def attach_spell_card_handlers(container):
    if container is None:
        return
    buttons = container.querySelectorAll("button[data-spell-action]")
    for button in buttons:
        if getattr(button, "disabled", False):
            continue
        slug = button.getAttribute("data-spell-slug") or ""
        action = (button.getAttribute("data-spell-action") or "").lower()
        if not slug or action not in {"add", "remove"}:
            continue
        proxy = create_proxy(
            lambda event, s=slug, a=action: handle_spell_card_action(event, a, s)
        )
        button.addEventListener("click", proxy)
        _EVENT_PROXIES.append(proxy)


def handle_spell_card_action(event, action: str, slug: str):
    if action == "add":
        handle_add_spell_click(event, slug)
    elif action == "remove":
        handle_remove_spell_click(event, slug)


def apply_spell_filters(auto_select: bool = False):
    profile = compute_spellcasting_profile()
    profile_signature = ",".join(profile["allowed_classes"]) + f"|{profile['max_spell_level']}"
    if profile_signature != SPELL_LIBRARY_STATE.get("last_profile_signature"):
        SPELL_LIBRARY_STATE["last_profile_signature"] = profile_signature
        if not auto_select:
            auto_select = True

    if not SPELL_LIBRARY_STATE.get("loaded"):
        update_spell_library_status("Spells not loaded yet. Click \"Load Spells\" to fetch the Open5e SRD.")
        return

    search_el = get_element("spell-search")
    level_el = get_element("spell-level-filter")
    class_el = get_element("spell-class-filter")

    search_term = ""
    if search_el is not None:
        search_term = search_el.value.strip().lower()

    level_filter = None
    if level_el is not None and level_el.value.strip() != "":
        level_filter = parse_int(level_el.value, None)

    selected_class = ""
    if class_el is not None:
        selected_class = class_el.value.strip()

    allowed_classes = [
        cls for cls in profile["allowed_classes"] if cls in SUPPORTED_SPELL_CLASSES
    ]
    max_spell_level = profile["max_spell_level"]

    class_options = SPELL_LIBRARY_STATE.get("class_options", [])
    if selected_class and selected_class not in class_options:
        selected_class = ""

    if auto_select and class_el is not None and allowed_classes:
        if selected_class not in allowed_classes:
            for class_key in allowed_classes:
                if class_key in class_options or class_el.querySelector(f"option[value='{class_key}']") is not None:
                    class_el.value = class_key
                    selected_class = class_key
                    break

    filtered: list[dict] = []
    spells = SPELL_LIBRARY_STATE.get("spells", [])
    allowed_set = set(allowed_classes)
    for spell in spells:
        # Filter by allowed sources
        source = spell.get("source", "")
        if not is_spell_source_allowed(source):
            continue
        
        spell_level = spell.get("level_int", 0)
        if max_spell_level is not None and spell_level > max_spell_level:
            continue
        spell_classes = set(spell.get("classes", []))
        if selected_class:
            if selected_class not in spell_classes:
                continue
        elif allowed_set:
            if not spell_classes.intersection(allowed_set):
                continue
        if level_filter is not None and spell_level != level_filter:
            continue
        if search_term and search_term not in spell.get("search_blob", ""):
            continue
        filtered.append(spell)

    displayed, truncated, total_filtered = render_spell_results(filtered, allowed_set)

    if allowed_classes:
        class_caption = ", ".join(
            SPELL_CLASS_DISPLAY_NAMES.get(c, c.title()) for c in allowed_classes
        )
    else:
        class_caption = "Any class"

    if selected_class:
        class_caption = SPELL_CLASS_DISPLAY_NAMES.get(selected_class, selected_class.title())

    if max_spell_level is None:
        level_caption = "all spell levels"
    elif max_spell_level < 0:
        level_caption = "no spellcasting"
    elif max_spell_level == 0:
        level_caption = "cantrips only"
    else:
        level_caption = f"spell level ≤ {max_spell_level}"

    if total_filtered == 0:
        status_message = f"No spells match your character filters ({class_caption}, {level_caption})."
    else:
        status_message = f"Showing {displayed} of {total_filtered} spells ({class_caption}, {level_caption})."
        if truncated:
            status_message += " Refine your search to see more results."

    update_spell_library_status(status_message)


async def load_spell_library(_event=None):
    console.log(f"DEBUG: load_spell_library() started, SPELLCASTING_MANAGER={SPELLCASTING_MANAGER}")
    if SPELL_LIBRARY_STATE.get("loading"):
        console.log("DEBUG: load_spell_library() - already loading, returning")
        return

    button = get_element("spells-load-btn")
    if button is not None:
        button.disabled = True
    SPELL_LIBRARY_STATE["loading"] = True
    update_spell_library_status("Loading spells from Open5e...")

    try:
        cached_spells = load_spell_cache()
        if cached_spells:
            set_spell_library_data(cached_spells)
            SPELL_LIBRARY_STATE["loaded"] = True
            populate_spell_class_filter(cached_spells)
            sync_prepared_spells_with_library()
            apply_spell_filters(auto_select=True)
            # Auto-populate domain spells now that spell library is loaded from cache
            _populate_domain_spells_on_load()
            update_spell_library_status("Loaded spells from cache. Filters apply to your current class and level.")
            return

        status_message = "Loaded latest Open5e SRD spells."
        raw_spells = None
        fetch_error = None
        try:
            console.log("PySheet: Fetching spells from Open5e...")
            raw_spells = await fetch_open5e_spells()
            console.log(f"PySheet: Open5e fetch returned {len(raw_spells) if raw_spells else 0} spells")
        except Exception as exc:
            fetch_error = exc
            console.warn(f"PySheet: Open5e fetch failed: {exc}")
        
        if not raw_spells:
            console.warn(f"PySheet: No spells from Open5e, using fallback ({len(LOCAL_SPELLS_FALLBACK)} spells)")
            if fetch_error is not None:
                console.warn(f"PySheet: fallback spell list in use ({fetch_error})")
            raw_spells = LOCAL_SPELLS_FALLBACK
            status_message = "Loaded built-in Bard and Cleric spell list."
        else:
            # Check if target spells already exist in Open5e
            open5e_slugs = {spell.get("slug") for spell in raw_spells if spell.get("slug")}
            target_slugs_test = {"toll-the-dead", "word-of-radiance"}
            already_present = target_slugs_test & open5e_slugs
            if already_present:
                console.log(f"PySheet: Target spells already in Open5e: {already_present}")
            
            # Merge in fallback spells that aren't in Open5e
            console.log(f"PySheet: Merging fallback spells into Open5e list...")
            existing_slugs = {spell.get("slug") for spell in raw_spells if spell.get("slug")}
            console.log(f"PySheet: Open5e has {len(existing_slugs)} unique slugs")
            merge_count = 0
            merged_slugs = []
            for fallback_spell in LOCAL_SPELLS_FALLBACK:
                fallback_slug = fallback_spell.get("slug")
                if fallback_slug not in existing_slugs:
                    raw_spells.append(fallback_spell)
                    merge_count += 1
                    merged_slugs.append(fallback_slug)
            console.log(f"PySheet: Merged {merge_count} fallback spells: {merged_slugs}")
            console.log(f"PySheet: Total after merge: {len(raw_spells)}")

        console.log(f"DEBUG: Calling sanitize_spell_list with {len(raw_spells)} spells")
        sanitized = sanitize_spell_list(raw_spells)
        console.log(f"DEBUG: sanitize_spell_list returned {len(sanitized)} spells")
        if not sanitized and raw_spells is not LOCAL_SPELLS_FALLBACK:
            console.warn("PySheet: remote spell list missing supported classes; using fallback list.")
            raw_spells = LOCAL_SPELLS_FALLBACK
            status_message = "Loaded built-in Bard and Cleric spell list."
            sanitized = sanitize_spell_list(raw_spells)
        if not sanitized:
            raise RuntimeError("No spells available for supported classes.")
        
        set_spell_library_data(sanitized)
        SPELL_LIBRARY_STATE["loaded"] = True
        populate_spell_class_filter(sanitized)
        sync_prepared_spells_with_library()
        if raw_spells is not LOCAL_SPELLS_FALLBACK:
            save_spell_cache(sanitized)
        apply_spell_filters(auto_select=True)
        # Auto-populate domain spells now that spell library is loaded
        _populate_domain_spells_on_load()
        update_spell_library_status(status_message)
    except Exception as exc:
        console.error(f"PySheet: failed to load spell library - {exc}")
        update_spell_library_status("Unable to load spells. Check your connection and try again.")
    finally:
        SPELL_LIBRARY_STATE["loading"] = False
        if button is not None:
            button.disabled = False


def handle_spell_filter_change(_event=None):
    apply_spell_filters(auto_select=False)


async def fetch_open5e_weapons():
    """Fetch weapons list from Open5e API."""
    try:
        response = await pyfetch("https://api.open5e.com/weapons/?limit=1000")
        if not response.ok:
            return None
        data = await response.json()
        return data.get("results", [])
    except Exception as exc:
        console.error(f"PySheet: failed to fetch weapons from Open5e - {exc}")
        return None


def set_weapon_library_data(weapons: list):
    """Populate weapon library state and build searchable index."""
    WEAPON_LIBRARY_STATE["weapons"] = weapons or []
    WEAPON_LIBRARY_STATE["weapon_map"] = {}
    for weapon in weapons:
        weapon_name = (weapon.get("name") or "").lower()
        if weapon_name:
            WEAPON_LIBRARY_STATE["weapon_map"][weapon_name] = weapon


def search_weapons(query: str = "") -> list:
    """Filter weapons by name prefix match (case-insensitive)."""
    if not query:
        return []
    query_lower = query.lower().strip()
    if not query_lower:
        return []
    return [w for w in WEAPON_LIBRARY_STATE.get("weapons", []) 
            if (w.get("name") or "").lower().startswith(query_lower)]


def update_weapon_library_status(message: str):
    """Update weapon library status message."""
    status_el = get_element("weapons-library-status")
    if status_el is not None:
        status_el.innerText = message


async def load_weapon_library(_event=None):
    """Load weapons from Open5e API."""
    if WEAPON_LIBRARY_STATE.get("loading"):
        return

    WEAPON_LIBRARY_STATE["loading"] = True
    update_weapon_library_status("Loading weapons...")

    try:
        raw_weapons = await fetch_open5e_weapons()
        if not raw_weapons:
            raise RuntimeError("No weapons available from Open5e API.")
        
        set_weapon_library_data(raw_weapons)
        
        num_weapons = len(raw_weapons)
        update_weapon_library_status(f"Loaded {num_weapons} weapons. Start typing to search.")
        
    except Exception as exc:
        console.error(f"PySheet: failed to load weapon library - {exc}")
        update_weapon_library_status("Unable to load weapons. Check your connection.")
    finally:
        WEAPON_LIBRARY_STATE["loading"] = False


def populate_weapon_dropdown(weapons: list = None):
    """Populate the weapon dropdown with available weapons."""
    if weapons is None:
        weapons = []
    
    dropdown = get_element("weapon-dropdown")
    if dropdown is None:
        return
    
    dropdown.innerHTML = ""
    for idx, weapon in enumerate(weapons[:20]):  # Limit to 20 results
        option = document.createElement("div")
        option.classList.add("weapon-option")
        option.setAttribute("data-weapon-index", str(idx))
        name = weapon.get("name", "Unknown")
        damage = weapon.get("damage", "")
        damage_str = f" ({escape(damage)})" if damage else ""
        option.innerHTML = f"{escape(name)}{damage_str}"
        
        def make_click_handler(w):
            def on_click(evt):
                add_equipped_weapon(w)
                close_weapon_dropdown()
                clear_weapon_search()
            return on_click
        
        # Use create_proxy to wrap the handler
        handler = create_proxy(make_click_handler(weapon))
        option.addEventListener("click", handler)
        _EVENT_PROXIES.append(handler)
        dropdown.appendChild(option)


def clear_weapon_search():
    """Clear weapon search input."""
    search_input = get_element("weapon-search")
    if search_input is not None:
        search_input.value = ""


def filter_weapon_dropdown(query: str = ""):
    """Filter dropdown options by search query."""
    results = search_weapons(query)
    populate_weapon_dropdown(results)
    
    dropdown = get_element("weapon-dropdown")
    if dropdown is not None:
        if results:
            dropdown.classList.add("active")
        else:
            dropdown.classList.remove("active")


def handle_weapon_search(event=None):
    """Handle weapon search input changes with arrow key navigation."""
    search_input = get_element("weapon-search")
    if search_input is None:
        return
    
    if event and event.type == "keydown":
        key = event.key
        if key == "ArrowDown" or key == "ArrowUp":
            event.preventDefault()
            navigate_weapon_options(key == "ArrowDown")
            return
        elif key == "Enter":
            event.preventDefault()
            select_highlighted_weapon()
            return
    
    query = search_input.value or ""
    filter_weapon_dropdown(query)


def navigate_weapon_options(move_down: bool = True):
    """Navigate weapon dropdown with arrow keys."""
    dropdown = get_element("weapon-dropdown")
    if dropdown is None or not dropdown.classList.contains("active"):
        return
    
    options = dropdown.querySelectorAll(".weapon-option")
    if not options:
        return
    
    highlighted = dropdown.querySelector(".weapon-option.highlighted")
    
    if not highlighted:
        # Highlight first or last based on direction
        if move_down:
            options[0].classList.add("highlighted")
        else:
            options[len(options) - 1].classList.add("highlighted")
    else:
        idx = int(highlighted.getAttribute("data-weapon-index") or 0)
        highlighted.classList.remove("highlighted")
        
        if move_down:
            next_idx = min(idx + 1, len(options) - 1)
        else:
            next_idx = max(idx - 1, 0)
        
        if next_idx < len(options):
            options[next_idx].classList.add("highlighted")


def select_highlighted_weapon():
    """Select the highlighted weapon from dropdown."""
    dropdown = get_element("weapon-dropdown")
    if dropdown is None:
        return
    
    highlighted = dropdown.querySelector(".weapon-option.highlighted")
    if highlighted:
        highlighted.click()


def open_weapon_dropdown():
    """Show weapon dropdown."""
    dropdown = get_element("weapon-dropdown")
    if dropdown is not None:
        dropdown.classList.add("active")


def close_weapon_dropdown():
    """Hide weapon dropdown."""
    dropdown = get_element("weapon-dropdown")
    if dropdown is not None:
        dropdown.classList.remove("active")


def get_equipped_weapons() -> list[dict]:
    """Get list of currently equipped weapons from localStorage."""
    try:
        storage_key = "dnd_character_data"
        stored = window.localStorage.getItem(storage_key)
        if stored:
            import json
            char_data = json.loads(stored)
            return char_data.get("equipped_weapons", [])
    except:
        pass
    return []


def render_equipped_weapons():
    """Render equipped weapons as cards."""
    equipped_list = get_element("weapons-list")
    empty_state = get_element("weapons-empty-state")
    
    if equipped_list is None or empty_state is None:
        return
    
    weapons = get_equipped_weapons()
    
    if not weapons:
        equipped_list.innerHTML = ""
        empty_state.style.display = "block"
        return
    
    empty_state.style.display = "none"
    equipped_list.innerHTML = ""
    
    for weapon in weapons:
        weapon_id = weapon.get("name", "").replace(" ", "_").replace("/", "_")
        
        card = document.createElement("div")
        card.classList.add("weapon-card")
        card.setAttribute("id", f"weapon-card-{weapon_id}")
        
        name = weapon.get("name", "Unknown")
        damage = weapon.get("damage", "")
        to_hit = weapon.get("to_hit", "")
        damage_type = weapon.get("damage_type", "")
        weapon_type = weapon.get("weapon_type", "")
        weight = weapon.get("weight", "")
        cost = weapon.get("cost", "")
        
        # Main display: to-hit and damage
        # Format to-hit - show only if available, otherwise show damage bonus if available
        if to_hit:
            to_hit_str = f"+{to_hit}" if isinstance(to_hit, (int, float)) else str(to_hit)
        else:
            bonus = weapon.get("bonus", "") or weapon.get("attack_bonus", "")
            to_hit_str = f"+{bonus}" if bonus else "-"
        
        damage_str = damage if damage else "-"
        
        card.innerHTML = f'''
        <div class="weapon-card-header">
            <strong>{escape(name)}</strong>
            <span class="weapon-stat-compact">{escape(damage_str)}</span>
            <button class="weapon-card-edit" data-weapon-id="{escape(weapon_id)}" type="button">✎</button>
            <button class="weapon-card-remove" data-weapon-id="{escape(weapon_id)}" type="button">✕</button>
        </div>
        '''
        
        # Create details div separately
        details_div = document.createElement("div")
        details_div.classList.add("weapon-card-details")
        details_div.setAttribute("id", f"details-{escape(weapon_id)}")
        
        # Build details - shows additional info when expanded
        details_lines = []
        details_lines.append(f"<div class='weapon-detail-row'><strong>Type:</strong> {escape(weapon_type)}</div>")
        if damage_type:
            details_lines.append(f"<div class='weapon-detail-row'><strong>Damage Type:</strong> {escape(damage_type)}</div>")
        if weight:
            details_lines.append(f"<div class='weapon-detail-row'><strong>Weight:</strong> {escape(weight)} lbs</div>")
        if cost:
            details_lines.append(f"<div class='weapon-detail-row'><strong>Cost:</strong> {escape(cost)}</div>")
        
        details_html = "".join(details_lines)
        details_div.innerHTML = details_html
        card.appendChild(details_div)
        # Click to expand/collapse details
        def make_expand_handler(wid):
            def on_click(evt):
                details = get_element(f"details-{wid}")
                if details:
                    details.classList.toggle("expanded")
            return on_click
        
        card_element = card
        handler = create_proxy(make_expand_handler(weapon_id))
        card_element.addEventListener("click", handler)
        _EVENT_PROXIES.append(handler)
        
        # Edit button
        edit_btn = card.querySelector(".weapon-card-edit")
        if edit_btn is not None:
            def make_edit_handler(w):
                def on_click(evt):
                    evt.stopPropagation()  # Don't trigger expand/collapse
                    edit_equipped_weapon(w)
                return on_click
            # Use create_proxy to wrap the handler
            edit_handler = create_proxy(make_edit_handler(weapon))
            edit_btn.addEventListener("click", edit_handler)
            _EVENT_PROXIES.append(edit_handler)
        
        # Remove button
        remove_btn = card.querySelector(".weapon-card-remove")
        if remove_btn is not None:
            def make_remove_handler(wid):
                def on_click(evt):
                    evt.stopPropagation()  # Don't trigger expand/collapse
                    remove_equipped_weapon(wid)
                    render_equipped_weapons()
                return on_click
            # Use create_proxy to wrap the handler
            remove_handler = create_proxy(make_remove_handler(weapon_id))
            remove_btn.addEventListener("click", remove_handler)
            _EVENT_PROXIES.append(remove_handler)
        
        equipped_list.appendChild(card)


def add_equipped_weapon(weapon: dict):
    """Add weapon to equipped list."""
    if not weapon:
        return
    
    weapon_name = weapon.get("name", "")
    if not weapon_name:
        return
    
    try:
        # Get current data from localStorage
        storage_key = "dnd_character_data"
        char_data = {
            "equipped_weapons": []
        }
        
        # Load from localStorage if available
        try:
            stored = window.localStorage.getItem(storage_key)
            if stored:
                import json
                char_data = json.loads(stored)
        except Exception as e:
            pass
        
        # Check if already equipped
        if "equipped_weapons" not in char_data:
            char_data["equipped_weapons"] = []
        
        equipped = char_data.get("equipped_weapons", [])
        if any(w.get("name") == weapon_name for w in equipped):
            return
        
        # Add weapon
        char_data["equipped_weapons"].append(weapon)
        
        # Save to localStorage
        try:
            import json
            window.localStorage.setItem(storage_key, json.dumps(char_data))
        except Exception as e:
            pass
        
        render_equipped_weapons()
        schedule_auto_export()
    except Exception as exc:
        console.error(f"PySheet: failed to add weapon - {exc}")


def remove_equipped_weapon(weapon_id: str):
    """Remove weapon from equipped list."""
    try:
        # Load from localStorage
        storage_key = "dnd_character_data"
        char_data = {"equipped_weapons": []}
        
        try:
            stored = window.localStorage.getItem(storage_key)
            if stored:
                import json
                char_data = json.loads(stored)
        except:
            pass
        
        equipped = char_data.get("equipped_weapons", [])
        char_data["equipped_weapons"] = [
            w for w in equipped 
            if w.get("name", "").replace(" ", "_").replace("/", "_") != weapon_id
        ]
        
        # Save to localStorage
        try:
            import json
            window.localStorage.setItem(storage_key, json.dumps(char_data))
        except:
            pass
        
        render_equipped_weapons()
        schedule_auto_export()
    except Exception as exc:
        console.error(f"PySheet: failed to remove weapon - {exc}")


def edit_equipped_weapon(weapon: dict):
    """Show edit dialog for weapon."""
    if not weapon:
        return
    
    name = weapon.get("name", "Unknown")
    damage = weapon.get("damage", "")
    damage_type = weapon.get("damage_type", "")
    weapon_type = weapon.get("weapon_type", "")
    
    # Show all available fields in a formatted way
    dialog_text = f"""Weapon Details for: {name}

Damage: {damage or 'N/A'}
Damage Type: {damage_type or 'N/A'}
Type: {weapon_type or 'N/A'}

Full API Data:
{str(weapon)}"""
    
    # Use alert for now - shows all the data
    window.alert(dialog_text)


def _create_equipment_row(item: dict) -> any:
    """Return a DOM <tr> element for the given item dict."""
    try:
        tbody = get_element("equipment-table-body")
        if tbody is None:
            console.log("ERROR in _create_equipment_row: tbody is None")
            return None
        
        tr = document.createElement("tr")
        tr.setAttribute("data-item-id", item.get("id", generate_id("item")))
        tr.className = "equipment-item-row"

        # Create a details element for expandable view
        details = document.createElement("details")
        details.style.cursor = "pointer"
        
        summary = document.createElement("summary")
        summary.style.listStyle = "none"
        summary.style.display = "flex"
        summary.style.justifyContent = "space-between"
        summary.style.alignItems = "center"
        summary.style.padding = "0.75rem"
        summary.style.borderRadius = "0.5rem"
        summary.style.backgroundColor = "rgba(30, 41, 59, 0.5)"
        summary.style.cursor = "pointer"
        summary.style.userSelect = "none"
        
        # Item name and summary
        nameDiv = document.createElement("div")
        nameDiv.style.fontWeight = "600"
        nameDiv.style.color = "#cbd5f5"
        nameDiv.textContent = f"{item.get('name', 'Unknown')} (x{int(item.get('qty', 1))})"
        
        costWeightDiv = document.createElement("div")
        costWeightDiv.style.fontSize = "0.85rem"
        costWeightDiv.style.color = "#94a3b8"
        costWeightDiv.textContent = f"{format_money(item.get('cost', 0))} | {format_weight(item.get('weight', 0))}"
        
        summary.appendChild(nameDiv)
        summary.appendChild(costWeightDiv)
        details.appendChild(summary)
        
        # Expandable details section
        detailsContent = document.createElement("div")
        detailsContent.style.padding = "1rem"
        detailsContent.style.borderTop = "1px solid rgba(148, 163, 184, 0.2)"
        detailsContent.style.marginTop = "0.5rem"
        
        # Input fields in a grid
        fieldsGrid = document.createElement("div")
        fieldsGrid.style.display = "grid"
        fieldsGrid.style.gridTemplateColumns = "1fr 1fr"
        fieldsGrid.style.gap = "1rem"
        fieldsGrid.style.marginBottom = "1rem"
        
        # Name field
        nameField = _create_equipment_field("Name", "name", item)
        # Qty field
        qtyField = _create_equipment_field("Qty", "qty", item)
        # Cost field
        costField = _create_equipment_field("Cost (ea)", "cost", item)
        # Weight field
        weightField = _create_equipment_field("Weight (ea)", "weight", item)
        
        fieldsGrid.appendChild(nameField)
        fieldsGrid.appendChild(qtyField)
        fieldsGrid.appendChild(costField)
        fieldsGrid.appendChild(weightField)
        
        detailsContent.appendChild(fieldsGrid)
        
        # Notes field (full width)
        notesField = _create_equipment_field("Notes", "notes", item)
        notesField.style.gridColumn = "1 / -1"
        detailsContent.appendChild(notesField)
        
        # Remove button
        removeBtn = document.createElement("button")
        removeBtn.className = "equipment-remove"
        removeBtn.type = "button"
        removeBtn.textContent = "Remove"
        removeBtn.style.marginTop = "1rem"
        removeBtn.style.padding = "0.5rem 1rem"
        removeBtn.style.backgroundColor = "rgba(239, 68, 68, 0.2)"
        removeBtn.style.color = "#fca5a5"
        removeBtn.style.border = "1px solid rgba(239, 68, 68, 0.5)"
        removeBtn.style.borderRadius = "0.375rem"
        removeBtn.style.cursor = "pointer"
        removeBtn.addEventListener("click", create_proxy(lambda e, iid=item.get("id"): remove_equipment_item(iid)))
        _EVENT_PROXIES.append(removeBtn)
        
        detailsContent.appendChild(removeBtn)
        details.appendChild(detailsContent)
        
        # Add to tr
        td = document.createElement("td")
        td.colSpan = 6
        td.style.padding = "0"
        td.appendChild(details)
        tr.appendChild(td)
        
        console.log(f"_create_equipment_row: created row for {item.get('name')}")
        return tr
    except Exception as e:
        console.log(f"ERROR in _create_equipment_row: {e}")
        return None


def _create_equipment_field(label: str, field_name: str, item: dict):
    """Create a labeled input field for equipment item"""
    container = document.createElement("div")
    
    labelEl = document.createElement("label")
    labelEl.style.display = "flex"
    labelEl.style.flexDirection = "column"
    labelEl.style.gap = "0.5rem"
    
    span = document.createElement("span")
    span.style.fontSize = "0.85rem"
    span.style.color = "#94a3b8"
    span.textContent = label
    labelEl.appendChild(span)
    
    if field_name == "qty":
        inp = document.createElement("input")
        inp.type = "number"
        inp.min = "0"
        inp.value = str(int(item.get(field_name, 0)))
    elif field_name == "cost":
        inp = document.createElement("input")
        inp.type = "number"
        inp.step = "0.01"
        inp.min = "0"
        inp.value = format_money(item.get(field_name, 0))
    elif field_name == "weight":
        inp = document.createElement("input")
        inp.type = "number"
        inp.step = "0.01"
        inp.min = "0"
        inp.value = format_weight(item.get(field_name, 0))
    else:
        inp = document.createElement("input")
        inp.type = "text"
        inp.value = str(item.get(field_name, ""))
    
    inp.setAttribute("data-item-field", field_name)
    inp.style.padding = "0.5rem"
    inp.style.borderRadius = "0.375rem"
    inp.style.border = "1px solid rgba(148, 163, 184, 0.3)"
    inp.style.backgroundColor = "rgba(15, 23, 42, 0.8)"
    inp.style.color = "#cbd5f5"
    
    item_id = item.get("id")
    proxy = create_proxy(lambda e, iid=item_id: handle_equipment_input(e, iid))
    inp.addEventListener("input", proxy)
    _EVENT_PROXIES.append(proxy)
    
    labelEl.appendChild(inp)
    container.appendChild(labelEl)
    return container


def render_equipment_table(items: list[dict]):
    tbody = get_element("equipment-table-body")
    # Get wrapper by class since it doesn't have an id
    wrapper = document.querySelector(".equipment-table-wrapper")
    empty_state = get_element("equipment-empty-state")
    if tbody is None or wrapper is None or empty_state is None:
        console.log(f"ERROR in render_equipment_table: tbody={tbody is not None}, wrapper={wrapper is not None}, empty_state={empty_state is not None}")
        return
    # clear
    tbody.innerHTML = ""
    if not items:
        wrapper.classList.remove("has-items")
        empty_state.style.display = "block"
        return
    wrapper.classList.add("has-items")
    empty_state.style.display = "none"
    
    console.log(f"render_equipment_table: processing {len(items)} items")
    for item in items:
        console.log(f"Creating row for: {item.get('name')}")
        row = _create_equipment_row(item)
        if row is None:
            console.log(f"ERROR: _create_equipment_row returned None for {item.get('name')}")
            continue
        tbody.appendChild(row)
        console.log(f"Appended row to tbody")

    # attach listeners to inputs and remove buttons
    rows = tbody.querySelectorAll("tr[data-item-id]")
    console.log(f"Found {len(rows)} rows in DOM after render")
    for row in rows:
        item_id = row.getAttribute("data-item-id")
        inputs = row.querySelectorAll("input[data-item-field]")
        for inp in inputs:
            proxy = create_proxy(lambda e, iid=item_id: handle_equipment_input(e, iid))
            inp.addEventListener("input", proxy)
            _EVENT_PROXIES.append(proxy)
        remove_btn = row.querySelector(".equipment-remove")
        if remove_btn is not None:
            proxy_rm = create_proxy(lambda e, iid=item_id: remove_equipment_item(iid))
            remove_btn.addEventListener("click", proxy_rm)
            _EVENT_PROXIES.append(proxy_rm)


def get_equipment_items_from_data(data: dict) -> list:
    inv = data.get("inventory") or {}
    items = inv.get("items") or []
    # ensure shape
    sanitized = []
    for it in items:
        # Parse cost and weight - they might be strings like "5 gp" or "8 lb"
        cost_val = it.get("cost", 0.0)
        if isinstance(cost_val, str):
            # Extract numeric value from strings like "5 gp"
            match = re.search(r'(\d+(?:\.\d+)?)', cost_val.lower())
            cost_val = float(match.group(1)) if match else 0.0
        else:
            cost_val = float(cost_val) if cost_val else 0.0
        
        weight_val = it.get("weight", 0.0)
        if isinstance(weight_val, str):
            # Extract numeric value from strings like "8 lb"
            match = re.search(r'(\d+(?:\.\d+)?)', weight_val.lower())
            weight_val = float(match.group(1)) if match else 0.0
        else:
            weight_val = float(weight_val) if weight_val else 0.0
        
        sanitized.append({
            "id": it.get("id") or generate_id("item"),
            "name": it.get("name", ""),
            "qty": int(it.get("qty", 1)),
            "cost": cost_val,
            "weight": weight_val,
            "notes": it.get("notes", ""),
        })
    return sanitized


def add_equipment_item(_event=None):
    """Equipment items are added through inline cards in the equipment library"""
    pass


def add_custom_item(_event=None):
    """Show the custom item modal"""
    modal = get_element("custom-item-modal")
    if modal:
        modal.style.display = "flex"
        # Focus on name field
        name_input = get_element("custom-item-name")
        if name_input:
            name_input.value = ""
            name_input.focus()


def add_custom_item(_event=None):
    """Show the custom item modal"""
    modal = get_element("custom-item-modal")
    if modal:
        modal.style.display = "flex"
        # Focus on name field
        name_input = get_element("custom-item-name")
        if name_input:
            name_input.value = ""
            name_input.focus()
        # Clear URL field
        url_input = get_element("custom-item-url")
        if url_input:
            url_input.value = ""
        # Clear status
        status = get_element("custom-item-fetch-status")
        if status:
            status.style.display = "none"


def fetch_custom_item_from_url_handler(event=None):
    """PyScript event handler for Get Data button"""
    url_input = get_element("custom-item-url")
    if not url_input:
        return
    
    url = url_input.value.strip()
    if not url:
        return
    
    fetch_custom_item_from_url(url)


def fetch_custom_item_from_url(url: str):
    """Fetch and parse custom item data from URL"""
    if not url or not url.strip():
        return
    
    status = get_element("custom-item-fetch-status")
    if status:
        status.textContent = "⏳ Fetching..."
        status.style.display = "block"
    
    try:
        def on_response(response):
            if response.ok:
                def on_text(html):
                    parse_custom_item_html(html)
                response.text().then(on_text)
            else:
                if status:
                    status.textContent = f"❌ Failed to fetch ({response.status})"
                    status.style.display = "block"
                console.error(f"PySheet: Failed to fetch {url}: {response.status}")
        
        def on_error(err):
            if status:
                status.textContent = "❌ Network error"
                status.style.display = "block"
            console.error(f"PySheet: Network error: {err}")
        
        window.fetch(url).then(on_response).catch(on_error)
    except Exception as e:
        if status:
            status.textContent = f"❌ Error: {str(e)[:50]}"
            status.style.display = "block"
        console.error(f"PySheet: Error fetching custom item: {e}")


def parse_custom_item_html(html: str):
    """Parse custom item data from HTML and populate form fields"""
    try:
        import re
        
        # Extract item name - look for h1 first, but avoid generic titles
        name = ""
        
        # Try h1 first (usually the main heading)
        h1_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        if h1_match:
            potential_name = h1_match.group(1).strip()
            # Skip if it's just "D&D 5th Edition" or similar generic text
            if not re.match(r'^D&D.*Edition|^Compendium', potential_name, re.IGNORECASE):
                name = potential_name
        
        # If no valid h1, try h2
        if not name:
            h2_match = re.search(r'<h2[^>]*>([^<]+)</h2>', html)
            if h2_match:
                name = h2_match.group(1).strip()
        
        # Clean up common patterns
        name = re.sub(r'\s*(?:- D&D|D&D 5e|5e|compendium).*', '', name, flags=re.IGNORECASE).strip()
        
        # If still no name, try to extract from a meta tag or structured data
        if not name:
            meta_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\']([^"\']+)["\']', html)
            if meta_match:
                name = meta_match.group(1).strip()
                name = re.sub(r'\s*(?:- D&D|D&D 5e|5e|compendium).*', '', name, flags=re.IGNORECASE).strip()
        
        # Extract damage
        damage = ""
        damage_match = re.search(r'[Dd]amage[:\s]*(\d+d\d+(?:\+\d+)?)', html)
        if damage_match:
            damage = damage_match.group(1)
        
        # Extract damage type
        damage_type = ""
        dtype_match = re.search(r'[Dd]amage\s+[Tt]ype[:\s]*([A-Za-z]+)', html)
        if dtype_match:
            damage_type = dtype_match.group(1)
        
        # Extract weight
        weight = ""
        weight_match = re.search(r'[Ww]eight[:\s]*([0-9.]+\s*(?:lb|lbs|kg)\.?)', html)
        if weight_match:
            weight = weight_match.group(1)
        
        # Extract cost
        cost = ""
        cost_match = re.search(r'[Cc]ost[:\s]*([0-9.]+\s*(?:gp|sp|cp|varies))', html)
        if cost_match:
            cost = cost_match.group(1)
        
        # Extract AC (for armor)
        ac = ""
        ac_match = re.search(r'(?:AC|armor\s+class)[:\s]*(\d+|1[0-9]|10\+[Dd]ex)', html)
        if ac_match:
            ac = ac_match.group(1)
        
        # Extract rarity/properties
        properties = ""
        rarity_match = re.search(r'[Rr]arity[:\s]*([A-Za-z]+)', html)
        if rarity_match:
            properties = rarity_match.group(1)
        
        # Update form fields
        if name:
            name_input = get_element("custom-item-name")
            if name_input:
                name_input.value = name
        
        if damage:
            damage_input = get_element("custom-item-damage")
            if damage_input:
                damage_input.value = damage
        
        if damage_type:
            dtype_input = get_element("custom-item-damage-type")
            if dtype_input:
                dtype_input.value = damage_type
        
        if weight:
            weight_input = get_element("custom-item-weight")
            if weight_input:
                weight_input.value = weight
        
        if cost:
            cost_input = get_element("custom-item-cost")
            if cost_input:
                cost_input.value = cost
        
        if ac:
            ac_input = get_element("custom-item-ac")
            if ac_input:
                ac_input.value = ac
        
        if properties:
            props_input = get_element("custom-item-properties")
            if props_input:
                props_input.value = properties
        
        # Show success message
        status = get_element("custom-item-fetch-status")
        if status:
            status.textContent = f"✅ Loaded: {name}"
            status.style.display = "block"
        
        console.log(f"PySheet: Populated custom item form from URL")
        
    except Exception as e:
        status = get_element("custom-item-fetch-status")
        if status:
            status.textContent = f"⚠️ Partial data loaded (parsing issue)"
            status.style.display = "block"
        console.error(f"PySheet: Error parsing custom item HTML: {e}")


def clear_equipment_list(_event=None):
    """Clear all equipment from the inventory"""
    if INVENTORY_MANAGER is None or len(INVENTORY_MANAGER.items) == 0:
        return
    INVENTORY_MANAGER.items = []
    INVENTORY_MANAGER.render_inventory()
    schedule_auto_export()


def update_inventory_totals():
    """Update total weight and cost displays"""
    if INVENTORY_MANAGER is None:
        return
    total_weight = INVENTORY_MANAGER.get_total_weight()
    weight_el = get_element("equipment-total-weight")
    if weight_el:
        weight_el.textContent = f"{total_weight:.1f} lb"
    # TODO: Add cost calculation if needed


def get_equipment_items_from_dom() -> list:
    """Legacy function - now returns from INVENTORY_MANAGER"""
    if INVENTORY_MANAGER is None:
        return []
    return INVENTORY_MANAGER.items


def fetch_equipment_from_open5e():
    """Fetch equipment data from Open5e API and cache locally"""
    global EQUIPMENT_LIBRARY_STATE
    import json
    
    # Check localStorage cache first
    try:
        cache_key = "dnd_equipment_cache_v10"
        cached = window.localStorage.getItem(cache_key)
        if cached:
            cache_data = json.loads(cached)
            console.log(f"PySheet: Loaded {len(cache_data)} items from cache")
            # Only use cache if it has a reasonable number of items (more than just common items)
            if len(cache_data) > 20:
                EQUIPMENT_LIBRARY_STATE["equipment"] = cache_data
                return
            else:
                console.log(f"PySheet: Cache too small ({len(cache_data)} items), using fallback")
        else:
            console.log("PySheet: No cache found in localStorage")
    except Exception as e:
        console.log(f"PySheet: Cache load error: {str(e)}")
    
    # Use comprehensive fallback of common D&D 5e items
    console.log("PySheet: Using comprehensive fallback equipment list")
    EQUIPMENT_LIBRARY_STATE["equipment"] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in [
        # Melee Weapons (common PHB weapons)
        Weapon("Mace", damage="1d6", damage_type="bludgeoning", cost="5 gp", weight="4 lb."),
        Weapon("Longsword", damage="1d8", damage_type="slashing", cost="15 gp", weight="3 lb."),
        Weapon("Shortsword", damage="1d6", damage_type="piercing", cost="10 gp", weight="2 lb."),
        Weapon("Rapier", damage="1d8", damage_type="piercing", cost="25 gp", weight="2 lb."),
        Weapon("Dagger", damage="1d4", damage_type="piercing", cost="2 gp", weight="1 lb."),
        Weapon("Greataxe", damage="1d12", damage_type="slashing", cost="30 gp", weight="7 lb."),
        Weapon("Greatsword", damage="2d6", damage_type="slashing", cost="50 gp", weight="6 lb."),
        Weapon("Warhammer", damage="1d8", damage_type="bludgeoning", cost="15 gp", weight="2 lb."),
        Weapon("Morningstar", damage="1d8", damage_type="piercing", cost="15 gp", weight="4 lb."),
        Weapon("Pike", damage="1d10", damage_type="piercing", cost="5 gp", weight="18 lb."),
        Weapon("Spear", damage="1d6", damage_type="piercing", cost="1 gp", weight="3 lb."),
        Weapon("Club", damage="1d4", damage_type="bludgeoning", cost="0.1 gp", weight="2 lb."),
        Weapon("Quarterstaff", damage="1d6", damage_type="bludgeoning", cost="0.2 gp", weight="4 lb."),
        Weapon("Falchion", damage="1d8", damage_type="slashing", cost="20 gp", weight="4 lb."),
        
        # Ranged Weapons
        Weapon("Longbow", damage="1d8", damage_type="piercing", range_text="150/600", cost="50 gp", weight="3 lb."),
        Weapon("Shortbow", damage="1d6", damage_type="piercing", range_text="80/320", cost="25 gp", weight="2 lb."),
        Weapon("Crossbow, light", damage="1d8", damage_type="piercing", range_text="80/320", cost="25 gp", weight="5 lb."),
        Weapon("Crossbow, heavy", damage="1d10", damage_type="piercing", range_text="100/400", cost="50 gp", weight="18 lb."),
        Weapon("Sling", damage="1d4", damage_type="bludgeoning", range_text="30/120", cost="0.1 gp", weight="0 lb."),
        
        # Armor
        Armor("Leather", armor_class=11, cost="5 gp", weight="10 lb."),
        Armor("Studded Leather", armor_class=12, cost="45 gp", weight="13 lb."),
        Armor("Hide", armor_class=12, cost="10 gp", weight="12 lb."),
        Armor("Chain Shirt", armor_class=13, cost="50 gp", weight="20 lb."),
        Armor("Scale Mail", armor_class=14, cost="50 gp", weight="45 lb."),
        Armor("Breastplate", armor_class=14, cost="400 gp", weight="20 lb."),
        Armor("Half Plate", armor_class=15, cost="750 gp", weight="40 lb."),
        Armor("Ring Mail", armor_class=14, cost="30 gp", weight="40 lb."),
        Armor("Chain Mail", armor_class=16, cost="75 gp", weight="55 lb."),
        Armor("Splint", armor_class=17, cost="200 gp", weight="60 lb."),
        Armor("Plate", armor_class=18, cost="1500 gp", weight="65 lb."),
        
        # Shields
        Shield("Shield", ac_bonus="+2", cost="10 gp", weight="6 lb."),
        
        # Starter Packs
        Equipment("Explorer's Pack", cost="10 gp", weight="59 lb."),
        Equipment("Adventurer's Pack", cost="5 gp", weight="54 lb."),
        Equipment("Burglar's Pack", cost="16 gp", weight="44 lb."),
        Equipment("Diplomat's Pack", cost="39 gp", weight="46 lb."),
        Equipment("Dungeoneer's Pack", cost="12 gp", weight="61 lb."),
        Equipment("Entertainer's Pack", cost="40 gp", weight="38 lb."),
        Equipment("Priest's Pack", cost="19 gp", weight="24 lb."),
        Equipment("Scholar's Pack", cost="40 gp", weight="10 lb."),
        
        # Adventuring Gear
        Equipment("Rope (50 feet)", cost="1 gp", weight="10 lb."),
        Equipment("Torch", cost="0.01 gp", weight="1 lb."),
        Equipment("Lantern (Bullseye)", cost="12 gp", weight="2 lb."),
        Equipment("Lantern (Hooded)", cost="5 gp", weight="2 lb."),
        Equipment("Backpack", cost="2 gp", weight="5 lb."),
        Equipment("Bedroll", cost="0.1 gp", weight="10 lb."),
        Equipment("Tent", cost="2 gp", weight="20 lb."),
        Equipment("Grappling Hook", cost="2 gp", weight="4 lb."),
        Equipment("Caltrops (20)", cost="1 gp", weight="2 lb."),
        Equipment("Chalk (1 piece)", cost="0.01 gp", weight="0.01 lb."),
        Equipment("Waterskin", cost="0.5 gp", weight="1 lb."),
        Equipment("Hempen Rope (50 feet)", cost="1 gp", weight="10 lb."),
        Equipment("Silk Rope (50 feet)", cost="10 gp", weight="5 lb."),
        Equipment("Crowbar", cost="2 gp", weight="5 lb."),
        Equipment("Hammer", cost="1 gp", weight="3 lb."),
        Equipment("Piton", cost="0.05 gp", weight="0.25 lb."),
        Equipment("Tinderbox", cost="0.5 gp", weight="1 lb."),
        Equipment("Candle", cost="0.01 gp", weight="0.1 lb."),
        Equipment("Mess Kit", cost="0.2 gp", weight="1 lb."),
        Equipment("Component Pouch", cost="25 gp", weight="2 lb."),
        Equipment("Spellcasting Focus", cost="5-15 gp", weight="varies"),
        Equipment("Holy Water (Flask)", cost="25 gp", weight="1 lb."),
        Equipment("Mirror (steel)", cost="5 gp", weight="0.5 lb."),
        Equipment("Rations (1 day)", cost="0.5 gp", weight="2 lb."),
        Equipment("Trail Rations (1 day)", cost="0.5 gp", weight="2 lb."),
        Equipment("Pouch", cost="0.5 gp", weight="1 lb."),
        Equipment("Money Pouch", cost="5 gp", weight="1 lb."),
        Equipment("Map or Scroll Case", cost="1 gp", weight="0.5 lb."),
        Equipment("Magnifying Glass", cost="100 gp", weight="0 lb."),
        Equipment("Playing Cards", cost="0.5 gp", weight="0 lb."),
        Equipment("Dice Set", cost="0.1 gp", weight="0 lb."),
        Equipment("Dominoes", cost="0.5 gp", weight="1 lb."),
        Equipment("Ink (1 oz bottle)", cost="10 gp", weight="0 lb."),
        Equipment("Ink Pen", cost="0.02 gp", weight="0 lb."),
        Equipment("Parchment", cost="0.1 gp", weight="0 lb."),
        Equipment("Paper", cost="0.2 gp", weight="0 lb."),
        Equipment("Spyglass", cost="1000 gp", weight="1 lb."),
        Equipment("Thieves' Tools", cost="25 gp", weight="1 lb."),
        Equipment("Healer's Kit", cost="5 gp", weight="3 lb."),
        Equipment("Herbalism Kit", cost="5 gp", weight="3 lb."),
        Equipment("Disguise Kit", cost="25 gp", weight="3 lb."),
        Equipment("Forgery Kit", cost="15 gp", weight="5 lb."),
        Equipment("Climber's Kit", cost="25 gp", weight="12 lb."),
        Equipment("Artisan's Tools", cost="5 gp", weight="5 lb."),
        Equipment("Instrument (String)", cost="25 gp", weight="1 lb."),
        Equipment("Lute", cost="35 gp", weight="2 lb."),
        Equipment("Flute", cost="2 gp", weight="1 lb."),
        Equipment("Drum", cost="6 gp", weight="3 lb."),
        Equipment("Tambourine", cost="2 gp", weight="1 lb."),
        Equipment("Pan Pipes", cost="12 gp", weight="2 lb."),
        Equipment("Vial", cost="1 gp", weight="0 lb."),
        Equipment("Potion of Healing", cost="50 gp", weight="0.5 lb."),
        Equipment("Potion of Greater Healing", cost="100 gp", weight="0.5 lb."),
        Equipment("Everburning Lantern", cost="varies", weight="2 lb."),
        Equipment("Antitoxin (vial)", cost="50 gp", weight="0 lb."),
        Equipment("Oil (1-pint bottle)", cost="0.1 gp", weight="1 lb."),
        Equipment("Perfume (vial)", cost="5 gp", weight="0 lb."),
        Equipment("Soap", cost="0.02 gp", weight="0 lb."),
        Equipment("Sack", cost="0.01 gp", weight="0.5 lb."),
        Equipment("Barrel", cost="0.2 gp", weight="70 lb."),
        Equipment("Basket", cost="0.04 gp", weight="1 lb."),
        Equipment("Bottle", cost="0.02 gp", weight="1 lb."),
        Equipment("Box", cost="0.1 gp", weight="2 lb."),
        Equipment("Carpet (6 sq ft)", cost="2 gp", weight="100 lb."),
        Equipment("Chest", cost="5 gp", weight="25 lb."),
        Equipment("Clothes, Common", cost="0.5 gp", weight="3 lb."),
        Equipment("Clothes, Costume", cost="5 gp", weight="4 lb."),
        Equipment("Clothes, Fine", cost="15 gp", weight="6 lb."),
        Equipment("Clothes, Traveler's", cost="2 gp", weight="4 lb."),
        Equipment("Dragonchess Set", cost="1 gp", weight="0.5 lb."),
        Equipment("Lock", cost="10 gp", weight="1 lb."),
        Equipment("Manacles", cost="2 gp", weight="6 lb."),
        Equipment("Mirror, Pocket", cost="5 gp", weight="0.5 lb."),
        
        # Magical Items (common)
        Equipment("Ring of Protection +1", cost="varies", weight="0 lb."),
        Equipment("Amulet of Health", cost="varies", weight="0 lb."),
        Equipment("Cloak of Protection", cost="varies", weight="1 lb."),
        Equipment("Wand of Magic Missiles", cost="varies", weight="1 lb."),
        Equipment("Staff of Fire", cost="varies", weight="4 lb."),
        Equipment("Magic Item", cost="varies", weight="0 lb."),
    ]]


def load_equipment_library(_event=None):
    """Load equipment library from cached data or Open5e API"""
    if EQUIPMENT_LIBRARY_STATE.get("loading"):
        return

    button = get_element("equipment-load-btn")
    if button is not None:
        button.disabled = True
    
    EQUIPMENT_LIBRARY_STATE["loading"] = True
    update_equipment_library_status("Loading equipment...")

    try:
        # Fetch and cache equipment data
        fetch_equipment_from_open5e()
        
        equipment_list = EQUIPMENT_LIBRARY_STATE.get("equipment", [])
        if equipment_list:
            EQUIPMENT_LIBRARY_STATE["loaded"] = True
            update_equipment_library_status(f"Loaded {len(equipment_list)} items. Search to filter results.")
            console.log(f"PySheet: Equipment library loaded with {len(equipment_list)} items")
        else:
            update_equipment_library_status("No equipment items loaded. Try again.")
            console.warn("PySheet: Equipment library is empty")
    except Exception as exc:
        console.error(f"PySheet: Error loading equipment: {exc}")
        update_equipment_library_status("Error loading equipment. Please try again.")
    finally:
        EQUIPMENT_LIBRARY_STATE["loading"] = False
        if button is not None:
            button.disabled = False


def update_equipment_library_status(message: str):
    """Update the equipment library status message"""
    status_div = get_element("equipment-library-status")
    if status_div:
        status_div.textContent = message


def populate_equipment_results(search_term: str = ""):
    """Populate equipment search results from Open5e"""
    results_div = get_element("equipment-library-results")
    if not results_div:
        console.error("PySheet: equipment-library-results element not found")
        return
    
    # Ensure we have equipment data - only fetch if not already loaded
    if not EQUIPMENT_LIBRARY_STATE.get("equipment"):
        console.log("PySheet: No equipment data, calling fetch_equipment_from_open5e")
        fetch_equipment_from_open5e()
    
    search_term = search_term.lower().strip()
    filtered = []
    seen_names = set()
    
    equipment_list = EQUIPMENT_LIBRARY_STATE.get("equipment", [])
    console.log(f"PySheet: Searching in {len(equipment_list)} equipment items for '{search_term}'")
    
    # Filter from EQUIPMENT_LIBRARY_STATE and deduplicate by name
    for item in equipment_list:
        name = item.get("name", "")
        if search_term == "" or search_term in name.lower():
            # Only add if we haven't seen this exact name before
            if name not in seen_names:
                filtered.append(item)
                seen_names.add(name)
    
    # Limit to 30 results
    limited = filtered[:30]
    
    if not limited:
        results_div.innerHTML = '<div class="equipment-library-empty">No items found. Try searching for sword, armor, rope, potion, etc.</div>'
        return
    
    # Build HTML from cards
    cards_html = "".join(build_equipment_card_html(item) for item in limited)
    truncated = len(filtered) > 30
    if truncated:
        cards_html += f'<div class="equipment-library-empty">Showing first 30 items. Refine your search for more precise results.</div>'
    
    results_div.innerHTML = cards_html
    attach_equipment_card_handlers(results_div)


def build_equipment_card_html(item: Union[dict, 'Equipment']) -> str:
    """Build HTML for an equipment card similar to spell cards"""
    # Handle both dict and Equipment object
    if isinstance(item, dict):
        name = item.get("name", "Unknown")
        cost = item.get("cost", "Unknown")
        weight = item.get("weight", "Unknown")
        damage = item.get("damage", "")
        damage_type = item.get("damage_type", "")
        range_text = item.get("range", "")
        properties = item.get("properties", "")
        ac_string = item.get("ac", "")
        armor_class = item.get("armor_class", "")
    else:
        # Equipment object
        name = item.name
        cost = item.cost or "Unknown"
        weight = item.weight or "Unknown"
        damage = getattr(item, 'damage', "")
        damage_type = getattr(item, 'damage_type', "")
        range_text = getattr(item, 'range', "")
        properties = getattr(item, 'properties', "")
        ac_string = getattr(item, 'ac_bonus', "")
        armor_class = getattr(item, 'armor_class', "")
    
    # Convert to strings to handle numeric values
    if armor_class and not isinstance(armor_class, str):
        armor_class = str(armor_class)
    
    # Build details list
    details = []
    if cost and cost != "Unknown":
        details.append(escape(str(cost)))
    if weight and weight != "Unknown":
        details.append(escape(str(weight)))
    details_text = " · ".join(details)
    
    # Build specs (damage, AC, range, etc)
    specs = []
    if damage:
        specs.append(escape(str(damage)))
    if damage_type:
        specs.append(f"({escape(str(damage_type))})")
    if armor_class:
        specs.append(f"AC {escape(str(armor_class))}")
    if ac_string:
        specs.append(f"AC {escape(str(ac_string))}")
    if range_text:
        specs.append(escape(str(range_text)))
    specs_text = " · ".join(specs) if specs else ""
    
    # Add button
    button_html = (
        f'<button type="button" class="equipment-action" '
        f'data-equipment-name="{escape(str(name))}" '
        f'data-equipment-cost="{escape(str(cost))}" '
        f'data-equipment-weight="{escape(str(weight))}" '
        f'data-equipment-damage="{escape(str(damage))}" '
        f'data-equipment-damage-type="{escape(str(damage_type))}" '
        f'data-equipment-range="{escape(str(range_text))}" '
        f'data-equipment-properties="{escape(str(properties))}" '
        f'data-equipment-ac="{escape(str(ac_string))}" '
        f'data-equipment-armor-class="{escape(str(armor_class))}">Add</button>'
    )
    
    return (
        f'<div class="equipment-card" data-equipment-name="{escape(str(name))}">'
        f'  <div class="equipment-summary">'
        f'    <div class="equipment-header">'
        f'      <span class="equipment-name">{escape(str(name))}</span>'
        f'      {button_html}'
        f'    </div>'
        f'    <div class="equipment-details">{details_text}</div>'
        + (f'    <div class="equipment-specs">{specs_text}</div>' if specs_text else '')
        + f'  </div>'
        f'</div>'
    )


def attach_equipment_card_handlers(container):
    """Attach click handlers to equipment add buttons"""
    if container is None:
        return
    
    buttons = container.querySelectorAll("button.equipment-action")
    for button in buttons:
        name = button.getAttribute("data-equipment-name") or ""
        cost = button.getAttribute("data-equipment-cost") or ""
        weight = button.getAttribute("data-equipment-weight") or ""
        damage = button.getAttribute("data-equipment-damage") or ""
        damage_type = button.getAttribute("data-equipment-damage-type") or ""
        range_text = button.getAttribute("data-equipment-range") or ""
        properties = button.getAttribute("data-equipment-properties") or ""
        ac_string = button.getAttribute("data-equipment-ac") or ""
        armor_class = button.getAttribute("data-equipment-armor-class") or ""
        
        proxy = create_proxy(
            lambda event, n=name, c=cost, w=weight, d=damage, dt=damage_type, r=range_text, p=properties, ac=ac_string, acv=armor_class: 
                submit_open5e_item(n, c, w, d, dt, r, p, ac, acv)
        )
        button.addEventListener("click", proxy)
        _EVENT_PROXIES.append(proxy)


def _handle_equipment_click(event):
    """Handle clicks on equipment result items - add directly to inventory"""
    target = event.target
    # Walk up the DOM to find the result item div
    while target and not target.getAttribute("data-name"):
        target = target.parentElement
    
    if target and target.getAttribute("data-name"):
        name = target.getAttribute("data-name")
        cost = target.getAttribute("data-cost") or ""
        weight = target.getAttribute("data-weight") or ""
        # Only include optional fields if they exist
        damage = target.getAttribute("data-damage") or ""
        damage_type = target.getAttribute("data-damage-type") or ""
        range_text = target.getAttribute("data-range") or ""
        properties = target.getAttribute("data-properties") or ""
        ac_string = target.getAttribute("data-ac-string") or ""
        armor_class = target.getAttribute("data-armor-class") or ""
        console.log(f"Equipment clicked: {name}")
        
        # Special handling for Magic Item importer
        if name == "Magic Item":
            show_magic_item_import_modal()
        else:
            # Add directly to inventory with only non-empty properties
            submit_open5e_item(name, cost, weight, damage, damage_type, range_text, properties, ac_string, armor_class)




def show_magic_item_import_modal():
    """Handle magic item import"""
    INVENTORY_MANAGER.add_item("Unnamed Magic Item", cost="", weight="", qty=1, category="Magic Items", notes="", source="custom")
    INVENTORY_MANAGER.render_inventory()
    schedule_auto_export()


def show_equipment_details(name: str, cost: str, weight: str):
    """Equipment details deprecated - use inline cards"""
    pass


def select_equipment_item(name: str, cost: str, weight: str):
    """Add selected item to equipment table"""
    console.log(f"select_equipment_item called: {name}, {cost}, {weight}")
    
    tbody = get_element("equipment-table-body")
    if tbody is None:
        console.log("ERROR: equipment-table-body not found")
        return
    
    # Parse cost and weight (they might be strings like "10 gp" or "2 lbs")
    import re
    cost_numeric = 0.0
    weight_numeric = 0.0
    
    # Extract numeric value from cost string
    cost_match = re.search(r'(\d+(?:\.\d+)?)', str(cost))
    if cost_match:
        cost_numeric = float(cost_match.group(1))
    
    # Extract numeric value from weight string
    weight_match = re.search(r'(\d+(?:\.\d+)?)', str(weight))
    if weight_match:
        weight_numeric = float(weight_match.group(1))
    
    console.log(f"Parsed: cost={cost_numeric}, weight={weight_numeric}")
    
    new_item = {"id": generate_id("item"), "name": name, "qty": 1, "cost": cost_numeric, "weight": weight_numeric, "notes": ""}
    existing = get_equipment_items_from_dom()
    console.log(f"Existing items: {len(existing)}")
    items = existing + [new_item]
    console.log(f"Total items after add: {len(items)}")
    console.log(f"New item: {new_item}")
    
    render_equipment_table(items)
    console.log("render_equipment_table called")
    
    # Verify it was added
    verify_items = get_equipment_items_from_dom()
    console.log(f"Items in DOM after render: {len(verify_items)}")
    if verify_items:
        console.log(f"Last item: {verify_items[-1]}")
    
    update_equipment_totals()
    console.log("Totals updated")
    
    schedule_auto_export()
    console.log("Export scheduled")
    
    schedule_auto_export()


def update_equipment_totals():
    """Update total weight and cost from equipment table (legacy) or inventory"""
    # Try to get items from the new inventory system first
    if hasattr(INVENTORY_MANAGER, 'items') and INVENTORY_MANAGER.items:
        total_weight = INVENTORY_MANAGER.get_total_weight()
        total_cost = 0.0
        for item in INVENTORY_MANAGER.items:
            # Parse cost - could be "5 gp" or just "5"
            cost_str = str(item.get("cost", "0")).lower()
            cost_match = re.search(r'(\d+(?:\.\d+)?)', cost_str)
            cost = float(cost_match.group(1)) if cost_match else 0.0
            qty = float(item.get("qty", 1))
            total_cost += cost * qty
    else:
        # Fallback to old equipment table
        items = get_equipment_items_from_dom()
        total_weight = 0.0
        total_cost = 0.0
        for it in items:
            try:
                q = float(it.get("qty", 0))
                # Parse weight - could be "8 lb" or just "8"
                w_str = str(it.get("weight", "0")).lower()
                w_match = re.search(r'(\d+(?:\.\d+)?)', w_str)
                w = float(w_match.group(1)) if w_match else 0.0
                # Parse cost - could be "5 gp" or just "5"
                c_str = str(it.get("cost", "0")).lower()
                c_match = re.search(r'(\d+(?:\.\d+)?)', c_str)
                c = float(c_match.group(1)) if c_match else 0.0
                total_weight += q * w
                total_cost += q * c
            except (ValueError, TypeError):
                continue
    
    set_text("equipment-total-weight", format_weight(total_weight))
    set_text("equipment-total-cost", format_money(total_cost))


def submit_custom_item(_event=None):
    """Handle custom item form submission"""
    name_input = get_element("custom-item-name")
    category_select = get_element("custom-item-category")
    cost_input = get_element("custom-item-cost")
    weight_input = get_element("custom-item-weight")
    qty_input = get_element("custom-item-qty")
    notes_textarea = get_element("custom-item-notes")
    damage_input = get_element("custom-item-damage")
    damage_type_input = get_element("custom-item-damage-type")
    range_input = get_element("custom-item-range")
    ac_input = get_element("custom-item-ac")
    properties_input = get_element("custom-item-properties")
    
    name = name_input.value.strip() if name_input else ""
    if not name:
        console.warn("PySheet: Item name is required")
        return
    
    console.log(f"PySheet: Adding custom item: {name}")
    
    category = category_select.value if category_select else ""
    cost = cost_input.value.strip() if cost_input else ""
    weight = weight_input.value.strip() if weight_input else ""
    qty = parse_int(qty_input.value if qty_input else 1, 1)
    damage = damage_input.value.strip() if damage_input else ""
    damage_type = damage_type_input.value.strip() if damage_type_input else ""
    range_text = range_input.value.strip() if range_input else ""
    ac = ac_input.value.strip() if ac_input else ""
    properties = properties_input.value.strip() if properties_input else ""
    notes = notes_textarea.value.strip() if notes_textarea else ""
    
    # Build extra properties dict
    extra_props = {}
    if damage:
        extra_props["damage"] = damage
    if damage_type:
        extra_props["damage_type"] = damage_type
    if range_text:
        extra_props["range"] = range_text
    if ac:
        extra_props["armor_class"] = ac
    elif category == "Armor":
        # Auto-detect standard D&D 5e armor AC values by name
        detected_ac = get_armor_ac(name)
        if detected_ac:
            extra_props["armor_class"] = detected_ac
    if properties:
        extra_props["properties"] = properties
    if notes:
        extra_props["notes"] = notes
    
    # Store as JSON in notes field
    final_notes = json.dumps(extra_props) if extra_props else ""
    
    # Add to inventory
    console.log(f"PySheet: Adding to inventory manager: name={name}, qty={qty}, category={category}")
    if INVENTORY_MANAGER is not None:
        INVENTORY_MANAGER.add_item(name, cost=cost, weight=weight, qty=qty, category=category, notes=final_notes, source="custom")
    
        console.log(f"PySheet: Total items in inventory: {len(INVENTORY_MANAGER.items)}")
    
        # Render inventory
        INVENTORY_MANAGER.render_inventory()
        console.log("PySheet: Inventory rendered")
    
    # Close modal
    modal = get_element("custom-item-modal")
    if modal:
        modal.style.display = "none"
        console.log("PySheet: Modal closed")
    
    schedule_auto_export()
    console.log("PySheet: Export scheduled")


def submit_open5e_item(name: str, cost: str = "", weight: str = "", damage: str = "", damage_type: str = "", 
                       range_text: str = "", properties: str = "", ac_string: str = "", armor_class: str = ""):
    """Add an Open5e item to inventory with all properties"""
    # Build a properties dict to store extra info as JSON in notes
    extra_props = {}
    if damage:
        extra_props["damage"] = damage
    if damage_type:
        extra_props["damage_type"] = damage_type
    if range_text:
        extra_props["range"] = range_text
    if properties:
        extra_props["properties"] = properties
    if ac_string:
        extra_props["ac_string"] = ac_string
    if armor_class:
        extra_props["armor_class"] = armor_class
    
    # Store properties as JSON in notes field
    notes = json.dumps(extra_props) if extra_props else ""
    
    INVENTORY_MANAGER.add_item(name, cost=cost, weight=weight, qty=1, category="", notes=notes, source="open5e")
    INVENTORY_MANAGER.render_inventory()
    schedule_auto_export()


# Class Features & Feats functions

CLASS_FEATURES_DATABASE = {
    "cleric": {
        1: [
            {"name": "Spellcasting", "description": "You can cast cleric spells using your choice of Wisdom or Intelligence (typically Wisdom) as your spellcasting ability modifier."},
            {"name": "Channel Divinity (DC)", "description": "You can use your action and expend one spell slot to invoke devastating divine magic. You know one Channel Divinity option. You gain more options at higher levels."},
        ],
        2: [
            {"name": "Channel Divinity", "description": "You can now use your Channel Divinity twice between rests."},
        ],
        3: [],
        5: [
            {"name": "Destroy Undead", "description": "When a creature you can see within 30 feet of you drops to 0 hit points, you can use your reaction to destroy it and render it unable to be raised from the dead. You can use this feature a number of times equal to your Wisdom modifier (minimum of 1)."},
        ],
        6: [
            {"name": "Channel Divinity", "description": "You can now use your Channel Divinity three times between rests."},
        ],
        8: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1. You can't increase an ability score above 20 using this feature."},
        ],
        10: [
            {"name": "Divine Intervention", "description": "You can call on your deity for aid. Describing what aid you seek, you make a DC 10 Wisdom check. If you succeed, the deity intervenes. The GM chooses how the intervention occurs."},
        ],
        12: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
        14: [
            {"name": "Improved Divine Intervention", "description": "Your Divine Intervention DC becomes 5 instead of 10 when you reach this level."},
        ],
        16: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
        19: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
    },
    "bard": {
        1: [
            {"name": "Spellcasting", "description": "You know a number of cantrips equal to your Charisma modifier (minimum of 1). You can cast any bard spell you know, provided that you have spell slots available to cast the spell."},
            {"name": "Bardic Inspiration", "description": "You can inspire others through stirring words or music. When another creature that can hear you within 60 feet of you makes an Attack roll, ability check, or damage roll, you can use your reaction to add to that roll."},
        ],
        2: [
            {"name": "Jack of All Trades", "description": "Starting at 2nd level, you can add half your proficiency bonus (round down) to any ability check you make that doesn't already include your proficiency bonus."},
        ],
        3: [],
        5: [
            {"name": "Bardic Inspiration Die Increases", "description": "Your Bardic Inspiration die becomes a d8."},
        ],
        6: [
            {"name": "Expertise Expansion", "description": "You can choose two more of your skill proficiencies to gain expertise."},
        ],
        8: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
        10: [
            {"name": "Bardic Inspiration Die Increases", "description": "Your Bardic Inspiration die becomes a d10."},
        ],
        12: [
            {"name": "Ability Score Improvement", "description": "You can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1."},
        ],
    },
}

# Domain-specific features for clerics
DOMAIN_FEATURES_DATABASE = {
    "life": {
        1: [
            {"name": "Bonus Proficiency", "description": "You gain proficiency with heavy armor."},
            {"name": "Disciple of Life", "description": "Your healing spells are more effective. Whenever you use a spell to restore hit points to a creature, that creature regains additional hit points equal to 2 + the spell's level."},
        ],
        2: [
            {"name": "Channel Divinity: Preserve Life", "description": "As an action, you can expend a use of your Channel Divinity to restore hit points to any number of creatures that you can see within 30 feet of you. You restore a number of hit points equal to five times your cleric level. Distribute these hit points among the creatures as you choose, but no creature can regain more than half of its maximum hit points at once."},
        ],
        6: [
            {"name": "Blessed Healer", "description": "The healing spells you cast on others can heal you as well. When you cast a healing spell whose target is not you, you regain hit points equal to 2 + the spell's level."},
        ],
        8: [
            {"name": "Divine Strike", "description": "Once on each of your turns when you hit a creature with a weapon attack, you can cause the attack to deal an extra 1d8 radiant damage to the target. When you reach 14th level, the extra damage increases to 2d8."},
        ],
        17: [
            {"name": "Supreme Healing", "description": "When you would normally roll one or more dice to restore hit points with a spell, you instead use the highest number possible for each die. For example, instead of restoring 2d6 hit points to a creature, you restore 12."},
        ],
    },
}

DOMAIN_BONUS_SPELLS = {
    "life": {
        1: ["cure-wounds", "bless"],
        3: ["lesser-restoration", "spiritual-weapon"],
        5: ["beacon-of-hope", "revivify"],
        7: ["guardian-of-faith", "death-ward"],
        9: ["mass-cure-wounds", "raise-dead"],
    },
}

def get_class_features_for_level(class_name: str, current_level: int) -> list:
    """Get all class features up to the current level."""
    class_key = class_name.lower().strip() if class_name else ""
    features_by_level = CLASS_FEATURES_DATABASE.get(class_key, {})
    
    all_features = []
    for level in sorted(features_by_level.keys()):
        if level <= current_level:
            all_features.extend(features_by_level[level])
    return all_features


def get_domain_features_for_level(domain_name: str, current_level: int) -> list:
    """Get all domain-specific features up to the current level."""
    domain_key = domain_name.lower().strip() if domain_name else ""
    features_by_level = DOMAIN_FEATURES_DATABASE.get(domain_key, {})
    
    all_features = []
    for level in sorted(features_by_level.keys()):
        if level <= current_level:
            all_features.extend(features_by_level[level])
    return all_features


def get_domain_bonus_spells(domain_name: str, current_level: int) -> list[str]:
    """Get all domain bonus spell slugs available up to the current level."""
    domain_key = domain_name.lower().strip() if domain_name else ""
    spells_by_level = DOMAIN_BONUS_SPELLS.get(domain_key, {})
    
    bonus_spells = []
    for level in sorted(spells_by_level.keys()):
        if level <= current_level:
            bonus_spells.extend(spells_by_level[level])
    return bonus_spells


def render_class_features():
    """Render class features organized by level."""
    container = get_element("class-features-container")
    if container is None:
        return
    
    # Get current class, level, and domain
    class_name = get_text_value("class")
    level = get_numeric_value("level", 1)
    domain = get_text_value("domain")
    
    if not class_name:
        container.innerHTML = '<div class="class-features-empty">Select a class to see its features.</div>'
        return
    
    class_key = class_name.lower().strip()
    features_by_level = CLASS_FEATURES_DATABASE.get(class_key, {})
    
    if not features_by_level:
        container.innerHTML = '<div class="class-features-empty">No class features database for ' + escape(class_name) + '.</div>'
        return
    
    html_parts = []
    
    # Add class features (only up to current level)
    for level_num in sorted(features_by_level.keys()):
        if level_num > level:
            continue  # Skip features above current level
        
        level_features = features_by_level[level_num]
        unlocked = "expanded"  # Always expanded since only showing unlocked features
        
        html_parts.append(f'''<div class="class-feature-level">
            <div class="class-feature-level-header {unlocked}" onclick="this.nextElementSibling.classList.toggle('expanded'); this.classList.toggle('expanded')">
                <span><span class="level-indicator">Level {level_num}</span></span>
                <span style="font-size: 0.8rem; color: #94a3b8;">{len(level_features)} feature(s)</span>
            </div>
            <div class="class-feature-level-content {unlocked}">''')
        
        for feat in level_features:
            name = escape(feat.get("name", "Unknown"))
            desc = escape(feat.get("description", ""))
            html_parts.append(f'''<div class="class-feature-item">
                <div class="class-feature-name">{name}</div>
                <div class="class-feature-description">{desc}</div>
            </div>''')
        
        html_parts.append('''</div>
        </div>''')
    
    # Add domain features if applicable (only up to current level)
    if domain and class_key == "cleric":
        domain_features_by_level = DOMAIN_FEATURES_DATABASE.get(domain.lower().strip(), {})
        if domain_features_by_level:
            for level_num in sorted(domain_features_by_level.keys()):
                if level_num > level:
                    continue  # Skip features above current level
                
                level_features = domain_features_by_level[level_num]
                unlocked = "expanded"  # Always expanded since only showing unlocked features
                
                domain_title = escape(domain.title())
                html_parts.append(f'''<div class="class-feature-level">
                <div class="class-feature-level-header {unlocked}" onclick="this.nextElementSibling.classList.toggle('expanded'); this.classList.toggle('expanded')">
                    <span><span class="level-indicator">{domain_title} Domain - Level {level_num}</span></span>
                    <span style="font-size: 0.8rem; color: #94a3b8;">{len(level_features)} feature(s)</span>
                </div>
                <div class="class-feature-level-content {unlocked}">''')
                
                for feat in level_features:
                    name = escape(feat.get("name", "Unknown"))
                    desc = escape(feat.get("description", ""))
                    html_parts.append(f'''<div class="class-feature-item">
                    <div class="class-feature-name">{name}</div>
                    <div class="class-feature-description">{desc}</div>
                </div>''')
                
                html_parts.append('''</div>
            </div>''')
    
    container.innerHTML = "".join(html_parts)


def render_feats():
    """Render user-added feats and custom abilities."""
    feats_container = get_element("feats-list")
    if feats_container is None:
        return
    
    # Collect feats from character data
    stored_data = window.localStorage.getItem(LOCAL_STORAGE_KEY)
    feats = []
    if stored_data:
        try:
            data = json.loads(stored_data)
            feats = data.get("feats", [])
        except:
            pass
    
    if not feats:
        feats_container.innerHTML = '<div class="feats-empty">No feats added yet. Use the form below to add your first feat!</div>'
        return
    
    # Sort feats by level gained
    feats = sorted(feats, key=lambda f: f.get("level_gained", 1))
    
    html_parts = []
    for feat in feats:
        feat_id = feat.get("id", "")
        name = escape(feat.get("name", "Unknown"))
        level = feat.get("level_gained", 1)
        desc = escape(feat.get("description", ""))
        
        html_parts.append(f'''<div class="feat-card" data-feat-id="{feat_id}">
            <div class="feat-card-header">
                <div class="feat-info">
                    <div class="feat-name">{name}</div>
                    <div class="feat-level">Gained at Level {level}</div>
                    {f'<div class="feat-description">{desc}</div>' if desc else ''}
                </div>
                <div class="feat-actions">
                    <button class="feat-action-btn" onclick="remove_feat('{feat_id}')">Remove</button>
                </div>
            </div>
        </div>''')
    
    feats_container.innerHTML = "".join(html_parts)


def add_feat(_event=None):
    """Add a new feat to the character."""
    name = get_element("feat-name-input")
    level_el = get_element("feat-level-input")
    desc = get_element("feat-description-input")
    
    if name is None or not name.value.strip():
        console.warn("Feat name is required")
        return
    
    # Load existing feats
    stored_data = window.localStorage.getItem(LOCAL_STORAGE_KEY)
    data = {}
    if stored_data:
        try:
            data = json.loads(stored_data)
        except:
            pass
    
    feats = data.get("feats", [])
    
    # Add new feat
    new_feat = {
        "id": str(uuid.uuid4()),
        "name": name.value.strip(),
        "level_gained": int(level_el.value or 1) if level_el else 1,
        "description": desc.value.strip() if desc else "",
    }
    
    feats.append(new_feat)
    data["feats"] = feats
    
    # Save
    window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
    
    # Clear form
    if name:
        name.value = ""
    if level_el:
        level_el.value = "1"
    if desc:
        desc.value = ""
    
    render_feats()


def remove_feat(feat_id: str):
    """Remove a feat by ID."""
    stored_data = window.localStorage.getItem(LOCAL_STORAGE_KEY)
    if not stored_data:
        return
    
    try:
        data = json.loads(stored_data)
        feats = data.get("feats", [])
        feats = [f for f in feats if f.get("id") != feat_id]
        data["feats"] = feats
        window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
        render_feats()
    except:
        pass


# Export/Import functions now imported from export_management.py
# Functions: save_character, show_storage_info, cleanup_exports, export_character, reset_character, handle_import


def handle_input_event(event=None):
    # Debug: log domain changes
    if event is not None and hasattr(event, "target"):
        target_id = getattr(event.target, "id", "")
        if target_id == "domain":
            value = getattr(event.target, "value", "")
            console.log(f"DEBUG: domain input event fired! New value: {value}")
            # Auto-populate domain spells when domain is selected
            if value and SPELL_LIBRARY_STATE.get("loaded"):
                level = get_numeric_value("level", 1)
                domain_spells = get_domain_bonus_spells(value, level)
                console.log(f"DEBUG: handle_input_event - Adding {len(domain_spells)} domain spells: {domain_spells}")
                added_count = 0
                for spell_slug in domain_spells:
                    if not SPELLCASTING_MANAGER.is_spell_prepared(spell_slug):
                        console.log(f"DEBUG: Adding domain spell from input event: {spell_slug}")
                        SPELLCASTING_MANAGER.add_spell(spell_slug)
                        added_count += 1
                console.log(f"DEBUG: Added {added_count} domain spells from input event")
            else:
                console.log(f"DEBUG: Skipped domain spell add - value={value}, loaded={SPELL_LIBRARY_STATE.get('loaded')}")
        # Auto-check proficiency if expertise is checked
        elif target_id.endswith("-exp") and event.target.checked:
            skill_name = target_id[:-4]  # Remove "-exp" suffix
            prof_id = f"{skill_name}-prof"
            set_form_value(prof_id, True)
    
    update_calculations()
    if SPELL_LIBRARY_STATE.get("loaded"):
        target_id = ""
        if event is not None and hasattr(event, "target"):
            target = event.target
            target_id = getattr(target, "id", "")
        auto = target_id in {"class", "level"}
        apply_spell_filters(auto_select=auto)
    schedule_auto_export()


def handle_adjust_button(event=None):
    """Handle health/resource adjustment buttons."""
    if event is None or not hasattr(event, "target"):
        return
    
    button = event.target
    target_id = button.getAttribute("data-adjust-target")
    if not target_id:
        return
    
    # Get current value
    current = get_numeric_value(target_id, 0)
    new_value = current
    
    # Handle delta adjustment
    delta_str = button.getAttribute("data-adjust-delta")
    if delta_str:
        try:
            delta = int(delta_str)
            new_value = current + delta
        except ValueError:
            return
    
    # Handle set to value (from field)
    set_id = button.getAttribute("data-adjust-set-id")
    if set_id:
        new_value = get_numeric_value(set_id, 0)
    
    # Handle set to direct value
    set_val = button.getAttribute("data-adjust-set")
    if set_val is not None and set_val != "":
        try:
            new_value = int(set_val)
        except ValueError:
            pass
    
    # Apply min/max constraints
    min_val_str = button.getAttribute("data-adjust-min")
    if min_val_str:
        try:
            min_val = int(min_val_str)
            new_value = max(new_value, min_val)
        except ValueError:
            pass
    
    max_id = button.getAttribute("data-adjust-max-id")
    if max_id:
        max_val = get_numeric_value(max_id, 0)
        new_value = min(new_value, max_val)
    
    # Handle max by proficiency (for Channel Divinity)
    max_by = button.getAttribute("data-adjust-max-by")
    if max_by == "proficiency":
        level = get_numeric_value("level", 1)
        proficiency = compute_proficiency(level)
        new_value = min(new_value, proficiency)
    
    # Set the new value
    set_form_value(target_id, str(new_value))
    update_calculations()
    schedule_auto_export()


def register_event_listeners():
    nodes = document.querySelectorAll("[data-character-input]")
    for element in nodes:
        proxy_input = create_proxy(handle_input_event)
        element.addEventListener("input", proxy_input)
        _EVENT_PROXIES.append(proxy_input)
        element_type = getattr(element, "type", "").lower()
        if element_type == "checkbox" or element.tagName.lower() == "select":
            proxy_change = create_proxy(handle_input_event)
            element.addEventListener("change", proxy_change)
            _EVENT_PROXIES.append(proxy_change)

    # Register adjust button handlers
    adjust_buttons = document.querySelectorAll("[data-adjust-target]")
    for button in adjust_buttons:
        proxy_adjust = create_proxy(handle_adjust_button)
        button.addEventListener("click", proxy_adjust)
        _EVENT_PROXIES.append(proxy_adjust)

    import_input = get_element("import-file")
    if import_input is not None:
        proxy_import = create_proxy(handle_import)
        import_input.addEventListener("change", proxy_import)
        _EVENT_PROXIES.append(proxy_import)

    spell_search = get_element("spell-search")
    if spell_search is not None:
        proxy_spell_search = create_proxy(handle_spell_filter_change)
        spell_search.addEventListener("input", proxy_spell_search)
        _EVENT_PROXIES.append(proxy_spell_search)

    spell_level_filter = get_element("spell-level-filter")
    if spell_level_filter is not None:
        proxy_spell_level = create_proxy(handle_spell_filter_change)
        spell_level_filter.addEventListener("change", proxy_spell_level)
        _EVENT_PROXIES.append(proxy_spell_level)

    spell_class_filter = get_element("spell-class-filter")
    if spell_class_filter is not None:
        if not SPELL_LIBRARY_STATE.get("loaded"):
            populate_spell_class_filter(None)
        proxy_spell_class = create_proxy(handle_spell_filter_change)
        spell_class_filter.addEventListener("change", proxy_spell_class)
        _EVENT_PROXIES.append(proxy_spell_class)

    # Register Channel Divinity reset button
    reset_btn = get_element("reset-channel-divinity")
    if reset_btn is not None:
        proxy_reset = create_proxy(reset_channel_divinity)
        reset_btn.addEventListener("click", proxy_reset)
        _EVENT_PROXIES.append(proxy_reset)

    # Register equipment search
    equipment_search = get_element("equipment-search-input")
    if equipment_search is not None:
        proxy_equip_search = create_proxy(lambda e: populate_equipment_results(e.target.value if hasattr(e, 'target') else ""))
        equipment_search.addEventListener("input", proxy_equip_search)
        _EVENT_PROXIES.append(proxy_equip_search)

    # Save character when page is being closed or reloaded
    if window is not None:
        proxy_unload = create_proxy(lambda e: export_character())
        window.addEventListener("beforeunload", proxy_unload)


def load_initial_state():
    stored = window.localStorage.getItem(LOCAL_STORAGE_KEY)
    if stored:
        try:
            data = json.loads(stored)
            populate_form(data)
            return
        except Exception as exc:
            console.warn(f"PySheet: unable to parse stored character, using defaults ({exc})")
    populate_form(clone_default_state())


# Only run module initialization if we're in a PyScript environment (document is not None)
if document is not None:
    register_event_listeners()
    load_initial_state()
    update_calculations()
    render_equipped_weapons()
    # Populate spell class filter with fallback spells on startup
    populate_spell_class_filter(SPELL_LIBRARY_STATE.get("spells"))

# Auto-populate domain spells if domain is set and spell library is loaded
def _populate_domain_spells_on_load():
    console.log(f"DEBUG: _populate_domain_spells_on_load() called, SPELLCASTING_MANAGER={SPELLCASTING_MANAGER}")
    if SPELLCASTING_MANAGER is None:
        console.warn("DEBUG: _populate_domain_spells_on_load - SPELLCASTING_MANAGER is None, skipping")
        console.log(f"DEBUG: SpellcastingManager class={SpellcastingManager}")
        return
    
    domain = get_text_value("domain")
    loaded = SPELL_LIBRARY_STATE.get("loaded")
    console.log(f"DEBUG: _populate_domain_spells_on_load - domain={domain}, loaded={loaded}")
    
    if domain and loaded:
        level = get_numeric_value("level", 1)
        domain_spells = get_domain_bonus_spells(domain, level)
        console.log(f"DEBUG: _populate_domain_spells_on_load - domain={domain}, level={level}, spells={domain_spells}")
        
        prepared_before = len(SPELLCASTING_MANAGER.get_prepared_slug_set())
        for spell_slug in domain_spells:
            if not SPELLCASTING_MANAGER.is_spell_prepared(spell_slug):
                console.log(f"DEBUG: Adding domain spell {spell_slug}")
                SPELLCASTING_MANAGER.add_spell(spell_slug)
            else:
                console.log(f"DEBUG: Domain spell {spell_slug} already prepared")
        prepared_after = len(SPELLCASTING_MANAGER.get_prepared_slug_set())
        console.log(f"DEBUG: Domain spells added: {prepared_after - prepared_before} spells (before={prepared_before}, after={prepared_after})")
        update_calculations()
    else:
        console.log(f"DEBUG: _populate_domain_spells_on_load - skipped (domain={domain}, loaded={loaded})")

# Auto-load weapon library
async def _auto_load_weapons():
    console.log("DEBUG: _auto_load_weapons() started")
    await load_weapon_library()
    console.log("DEBUG: _auto_load_weapons() - weapon library loaded, calling _populate_domain_spells_on_load")
    _populate_domain_spells_on_load()
    console.log("DEBUG: _auto_load_weapons() completed")

# Only start async tasks if we're in a PyScript environment
if document is not None:
    try:
        console.log("DEBUG: Creating async task for _auto_load_weapons")
        asyncio.create_task(_auto_load_weapons())
    except RuntimeError as e:
        # No event loop available (e.g., in test environment)
        console.warn(f"DEBUG: Could not create async task: {e}")
        pass
