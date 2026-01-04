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
from math import floor
from pathlib import Path
from typing import Union, Optional

try:
    from tooltip_values import WeaponToHitValue
except ImportError:
    # In case tooltip_values not available (fallback)
    WeaponToHitValue = None

try:
    import export_management
except ImportError:
    # export_management may not be available in test environments
    export_management = None

try:
    from js import console, document, window
except ImportError:
    # Mock for testing environments
    class _MockConsole:
        @staticmethod
        def log(*args): pass
        @staticmethod
        def warn(*args): pass
        @staticmethod
        def error(*args): pass
    
    console = _MockConsole()
    document = None
    window = None
# VERY FIRST DEBUG MESSAGE - if this doesn't appear, Python didn't load
if document is not None:
    try:
        console.log("[DEBUG-START] character.py module loading...")
    except:
        pass

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
    else (Path.cwd() / "static" / "assets" / "py")
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
    from character_models import (
        Character,
        CharacterFactory,
        DEFAULT_ABILITY_KEYS,
        get_class_armor_proficiencies,
        get_class_hit_die,
        get_class_weapon_proficiencies,
        get_race_ability_bonuses,
    )
except ModuleNotFoundError:
    module_candidates = [
        MODULE_DIR / "character_models.py",
        Path.cwd() / "static" / "assets" / "py" / "character_models.py",
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
                # Register before exec so dataclass decorators resolve __module__ properly
                sys.modules["character_models"] = module
                exec(source, module.__dict__)
            Character = module.Character
            CharacterFactory = module.CharacterFactory
            DEFAULT_ABILITY_KEYS = module.DEFAULT_ABILITY_KEYS
            get_class_armor_proficiencies = module.get_class_armor_proficiencies
            get_class_hit_die = module.get_class_hit_die
            get_class_weapon_proficiencies = module.get_class_weapon_proficiencies
            get_race_ability_bonuses = module.get_race_ability_bonuses
            loaded = True
            break
        except Exception:
            continue
    if not loaded:
        # Final HTTP fallback for Pyodide/static builds
        try:
            source = open_url("assets/py/character_models.py").read()
            module = ModuleType("character_models")
            # Register before exec so dataclass decorators can resolve __module__
            sys.modules["character_models"] = module
            exec(source, module.__dict__)
            Character = module.Character
            CharacterFactory = module.CharacterFactory
            DEFAULT_ABILITY_KEYS = module.DEFAULT_ABILITY_KEYS
            get_class_armor_proficiencies = module.get_class_armor_proficiencies
            get_class_hit_die = module.get_class_hit_die
            get_class_weapon_proficiencies = module.get_class_weapon_proficiencies
            get_race_ability_bonuses = module.get_race_ability_bonuses
            console.log("DEBUG: character_models loaded via HTTP fallback")
        except Exception as e:
            console.error(f"DEBUG: character_models HTTP fallback failed: {e}")
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
    console.log(f"DEBUG: spell_data import succeeded - CLASS_CASTING_PROGRESSIONS keys: {list(CLASS_CASTING_PROGRESSIONS.keys())}")
except ImportError as e:
    console.log(f"DEBUG: spell_data import failed: {e}")
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

# Manual HTTP fetch for spellcasting module (workaround for Pyodide path resolution)
def _load_module_from_http_sync(module_name: str, url: str, _retry: bool = True):
    """Load a Python module from HTTP URL synchronously using open_url.

    This helper will attempt to auto-resolve simple missing-module errors by
    fetching the missing dependency module from the assets HTTP path and retrying once.
    """
    try:
        console.log(f"DEBUG: [HTTP] Starting load_module_from_http_sync")
        console.log(f"DEBUG: [HTTP] module_name = {module_name}")
        console.log(f"DEBUG: [HTTP] url = {url}")
        console.log(f"DEBUG: [HTTP] open_url available = {open_url is not None}")

        if open_url is None:
            raise RuntimeError("open_url is None")

        console.log(f"DEBUG: [HTTP] Calling open_url({url})")
        response = open_url(url)
        console.log(f"DEBUG: [HTTP] open_url returned")

        source = response.read()
        console.log(f"DEBUG: [HTTP] Read {len(source)} bytes")

        module = ModuleType(module_name)
        module.__file__ = url  # Help modules that log __file__
        # Register before exec so intra-module lookups (e.g., dataclasses __module__) succeed
        sys.modules[module_name] = module
        console.log(f"DEBUG: [HTTP] Created ModuleType and registered in sys.modules")

        try:
            exec(source, module.__dict__)
            console.log(f"DEBUG: [HTTP] exec() completed")
            console.log(f"DEBUG: [HTTP] SUCCESS")
            return module
        except Exception as inner_exc:
            # If a ModuleNotFoundError occurred during exec, attempt to fetch that missing module
            msg = str(inner_exc)
            console.error(f"DEBUG: [HTTP] exec() ERROR: {type(inner_exc).__name__}: {msg}")
            import re
            m = re.search(r"No module named '([^']+)'", msg)
            if m and _retry:
                missing = m.group(1)
                console.log(f"DEBUG: [HTTP] Detected missing dependency: {missing}; attempting to fetch it and retry")
                try:
                    dep_url = f"http://localhost:8080/assets/py/{missing}.py"
                    dep_mod = _load_module_from_http_sync(missing, dep_url, _retry=False)
                    if dep_mod is not None:
                        console.log(f"DEBUG: [HTTP] Successfully loaded dependency {missing}; retrying exec of {module_name}")
                        # Retry exec now that dependency is registered
                        exec(source, module.__dict__)
                        console.log(f"DEBUG: [HTTP] exec() completed on retry")
                        console.log(f"DEBUG: [HTTP] SUCCESS (after dependency fetch)")
                        return module
                    else:
                        console.error(f"DEBUG: [HTTP] Failed to load dependency module: {missing}")
                except Exception as e2:
                    console.error(f"DEBUG: [HTTP] Error while fetching dependency {missing}: {e2}")
            # If we get here, re-raise to be logged by the outer except
            raise

    except Exception as e:
        console.error(f"DEBUG: [HTTP] EXCEPTION: {type(e).__name__}")
        console.error(f"DEBUG: [HTTP] Message: {str(e)}")
        import traceback
        for line in traceback.format_exc().split('\n'):
            if line.strip():
                console.error(f"DEBUG: [HTTP] {line}")
        return None

def _ensure_manager_loaded(module_name: str, attr_name: str, http_url: str | None = None):
    """Attempt to import <module_name> and return the attribute <attr_name>.
    On ImportError, retry by inserting static/assets/py into sys.path, and
    finally attempt an HTTP fallback using _load_module_from_http_sync if
    http_url is provided. Raises ImportError if all attempts fail.
    """
    try:
        module = __import__(module_name)
        if hasattr(module, attr_name):
            return getattr(module, attr_name)
    except Exception as e:
        console.warn(f"DEBUG: {module_name} import failed: {e}")
        # Retry by inserting assets/py into sys.path
        try:
            assets_py = Path.cwd() / "static" / "assets" / "py"
            if str(assets_py) not in sys.path:
                sys.path.insert(0, str(assets_py))
                console.log(f"DEBUG: Added {assets_py} to sys.path[0]")
            module = __import__(module_name)
            if hasattr(module, attr_name):
                console.log(f"DEBUG: {module_name} imported after path insertion")
                return getattr(module, attr_name)
        except Exception as e2:
            console.warn(f"DEBUG: {module_name} retry failed: {e2}")
            # Try HTTP fallback if a URL was provided
            if http_url is not None:
                console.log(f"DEBUG: Attempting HTTP fallback for {module_name}")
                mod = _load_module_from_http_sync(module_name, http_url)
                if mod is not None and hasattr(mod, attr_name):
                    console.log(f"DEBUG: {module_name} loaded via HTTP fallback")
                    return getattr(mod, attr_name)
            raise ImportError(f"{module_name} could not be loaded")

# Try standard import first
try:
    from spellcasting import SpellcastingManager, SPELL_LIBRARY_STATE, set_spell_library_data, load_spell_library
    console.log("DEBUG: spellcasting module imported successfully on first try")
except ImportError as e:
    console.log("DEBUG: *** FALLBACK 1 TRIGGERED ***")
    # Fallback 1: Try adding assets/py to sys.path and retry
    console.warn(f"DEBUG: spellcasting module import failed: {e}")
    console.log("DEBUG: Attempting retry with explicit path insertion")
    
    try:
        assets_py = Path.cwd() / "static" / "assets" / "py"
        if str(assets_py) not in sys.path:
            sys.path.insert(0, str(assets_py))
            console.log(f"DEBUG: Added {assets_py} to sys.path[0]")
        
        from spellcasting import SpellcastingManager, SPELL_LIBRARY_STATE, set_spell_library_data, load_spell_library
        console.log("DEBUG: spellcasting module imported successfully on retry")
    except ImportError as e2:
        # Fallback 2: Try HTTP fetch with open_url
        console.error(f"DEBUG: spellcasting module import failed on retry: {e2}")
        console.log("DEBUG: *** FALLBACK 2: HTTP FETCH ***")
        
        try:
            # First, manually load spell_data via HTTP (needed by spellcasting)
            console.log("DEBUG: [Fallback2] Loading spell_data")
            spell_data_module = _load_module_from_http_sync("spell_data", "http://localhost:8080/assets/py/spell_data.py")
            console.log(f"DEBUG: [Fallback2] spell_data_module = {spell_data_module}")
            if spell_data_module is not None:
                LOCAL_SPELLS_FALLBACK = getattr(spell_data_module, "LOCAL_SPELLS_FALLBACK", LOCAL_SPELLS_FALLBACK)
                SPELL_CLASS_SYNONYMS = getattr(spell_data_module, "SPELL_CLASS_SYNONYMS", SPELL_CLASS_SYNONYMS)
                SPELL_CLASS_DISPLAY_NAMES = getattr(spell_data_module, "SPELL_CLASS_DISPLAY_NAMES", SPELL_CLASS_DISPLAY_NAMES)
                SPELL_CORRECTIONS = getattr(spell_data_module, "SPELL_CORRECTIONS", SPELL_CORRECTIONS)
                apply_spell_corrections = getattr(spell_data_module, "apply_spell_corrections", apply_spell_corrections)
                is_spell_source_allowed = getattr(spell_data_module, "is_spell_source_allowed", is_spell_source_allowed)
                CLASS_CASTING_PROGRESSIONS = getattr(spell_data_module, "CLASS_CASTING_PROGRESSIONS", CLASS_CASTING_PROGRESSIONS)
                SPELLCASTING_PROGRESSION_TABLES = getattr(spell_data_module, "SPELLCASTING_PROGRESSION_TABLES", SPELLCASTING_PROGRESSION_TABLES)
                STANDARD_SLOT_TABLE = getattr(spell_data_module, "STANDARD_SLOT_TABLE", STANDARD_SLOT_TABLE)
                PACT_MAGIC_TABLE = getattr(spell_data_module, "PACT_MAGIC_TABLE", PACT_MAGIC_TABLE)
                console.log(f"DEBUG: [Fallback2] Loaded spell_data constants: fallback_spells={len(LOCAL_SPELLS_FALLBACK)}")
            
            # Then load spellcasting via HTTP
            console.log("DEBUG: [Fallback2] Loading spellcasting")
            spellcasting_module = _load_module_from_http_sync("spellcasting", "http://localhost:8080/assets/py/spellcasting.py")
            console.log(f"DEBUG: [Fallback2] spellcasting_module = {spellcasting_module}")
            
            if spellcasting_module is not None:
                console.log("DEBUG: [Fallback2] Extracting attributes from spellcasting_module")
                SpellcastingManager = spellcasting_module.SpellcastingManager
                SPELL_LIBRARY_STATE = spellcasting_module.SPELL_LIBRARY_STATE
                set_spell_library_data = spellcasting_module.set_spell_library_data
                load_spell_library = spellcasting_module.load_spell_library
                console.log("DEBUG: spellcasting module loaded via HTTP successfully")
            else:
                raise ImportError("HTTP fetch returned None")
        except Exception as e3:
            # Fallback 3: All imports fail - use stubs
            console.error(f"DEBUG: spellcasting module import failed on HTTP fetch: {e3}")
            console.error(f"DEBUG: Using stub functions")
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
    console.log("DEBUG: equipment_management import succeeded on first try")
except ImportError as e:
    console.log("DEBUG: equipment_management import failed, attempting HTTP fallback")
    console.warn(f"DEBUG: equipment_management import failed: {e}")
    try:
        equipment_module = _load_module_from_http_sync(
            "equipment_management",
            "http://localhost:8080/assets/py/equipment_management.py",
        )
        InventoryManager = getattr(equipment_module, "InventoryManager", None)
        Item = getattr(equipment_module, "Item", None)
        Weapon = getattr(equipment_module, "Weapon", None)
        Armor = getattr(equipment_module, "Armor", None)
        Shield = getattr(equipment_module, "Shield", None)
        Equipment = getattr(equipment_module, "Equipment", None)
        format_money = getattr(equipment_module, "format_money", lambda x: str(x))
        format_weight = getattr(equipment_module, "format_weight", lambda x: str(x))
        get_armor_type = getattr(equipment_module, "get_armor_type", lambda x: "unknown")
        get_armor_ac = getattr(equipment_module, "get_armor_ac", lambda x: None)
        ARMOR_TYPES = getattr(equipment_module, "ARMOR_TYPES", {})
        ARMOR_AC_VALUES = getattr(equipment_module, "ARMOR_AC_VALUES", {})
        console.log("DEBUG: equipment_management module loaded via HTTP successfully")
    except Exception as e2:
        console.error(f"DEBUG: equipment_management HTTP fallback failed: {e2}")
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
    )
    _export_mgmt = sys.modules.get("export_management")
    if _export_mgmt is not None:
        # Provide a back-reference so export_management can reach this module in Pyodide
        _export_mgmt.CHARACTER_MODULE = sys.modules.get(__name__)
    # Explicitly expose imported handlers to PyScript's event system
    # PyScript's py-click needs these to be in the module's global namespace
    globals()['save_character'] = save_character
    globals()['reset_character'] = reset_character
    globals()['show_storage_info'] = show_storage_info
    globals()['cleanup_exports'] = cleanup_exports
    console.log("DEBUG: export_management module imported successfully on first try")
    console.log("DEBUG: Button handlers exposed to PyScript event system")
except ImportError as e:
    console.log("DEBUG: *** EXPORT_MGMT FALLBACK TRIGGERED ***")
    console.warn(f"DEBUG: export_management import failed: {e}")
    try:
        export_mgmt_module = _load_module_from_http_sync(
            "export_management",
            "http://localhost:8080/assets/py/export_management.py",
        )
        save_character = getattr(export_mgmt_module, "save_character", lambda *a, **kw: None)
        export_character = getattr(export_mgmt_module, "export_character", lambda *a, **kw: None)
        reset_character = getattr(export_mgmt_module, "reset_character", lambda *a, **kw: None)
        handle_import = getattr(export_mgmt_module, "handle_import", lambda *a, **kw: None)
        show_storage_info = getattr(export_mgmt_module, "show_storage_info", lambda *a, **kw: None)
        cleanup_exports = getattr(export_mgmt_module, "cleanup_exports", lambda *a, **kw: None)
        _export_mgmt = export_mgmt_module
        try:
            _export_mgmt.CHARACTER_MODULE = sys.modules.get(__name__)
        except Exception:
            pass
        # Explicitly expose imported handlers to PyScript's event system
        globals()['save_character'] = save_character
        globals()['reset_character'] = reset_character
        globals()['show_storage_info'] = show_storage_info
        globals()['cleanup_exports'] = cleanup_exports
        console.log("DEBUG: export_management module loaded via HTTP successfully")
        console.log("DEBUG: Button handlers exposed to PyScript event system (HTTP fallback)")
    except Exception as e2:
        console.error(f"DEBUG: export_management fallback failed: {e2}")
        # Fallbacks for non-modular environments
        save_character = lambda *a, **kw: None
        export_character = lambda *a, **kw: None
        reset_character = lambda *a, **kw: None
        handle_import = lambda *a, **kw: None
        show_storage_info = lambda *a, **kw: None
        cleanup_exports = lambda *a, **kw: None
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
        data = {
            "name": self.name,
            "entity_type": self.entity_type,
            "description": self.description,
        }
        if self.properties:
            data["properties"] = self.properties.copy()
        return data
    
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
        # Keep weapon-specific properties separate so Entity.properties stays a dict
        self.weapon_properties = properties
    
    def to_dict(self) -> dict:
        d = super().to_dict()
        if self.damage:
            d["damage"] = self.damage
        if self.damage_type:
            d["damage_type"] = self.damage_type
        if self.range:
            d["range"] = self.range
        if self.weapon_properties:
            d["properties"] = self.weapon_properties
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

# SPELL_LIBRARY_STATE is now imported from spellcasting.py - don't redefine it here
# This prevents duplicate state management

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
_DOMAIN_SPELL_SYNCING = False

# Module references for lazy loading (initialized on first use)
_EXPORT_MODULE_REF = None
_EQUIPMENT_MODULE_REF = None



# Export/Import functions moved to export_management.py
# Imported above with fallback stubs


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
        
        # If spell_data import failed, try to get CLASS_CASTING_PROGRESSIONS from spellcasting module
        if not CLASS_CASTING_PROGRESSIONS:
            try:
                import spellcasting as sc_module
                if hasattr(sc_module, 'CLASS_CASTING_PROGRESSIONS'):
                    globals()['CLASS_CASTING_PROGRESSIONS'] = sc_module.CLASS_CASTING_PROGRESSIONS
                    console.log(f"DEBUG: Populated CLASS_CASTING_PROGRESSIONS from spellcasting module: {list(CLASS_CASTING_PROGRESSIONS.keys())}")
                if hasattr(sc_module, 'SPELLCASTING_PROGRESSION_TABLES'):
                    globals()['SPELLCASTING_PROGRESSION_TABLES'] = sc_module.SPELLCASTING_PROGRESSION_TABLES
                    console.log(f"DEBUG: Populated SPELLCASTING_PROGRESSION_TABLES from spellcasting module")
            except Exception as e:
                console.log(f"DEBUG: Could not populate spell progression tables from spellcasting: {e}")
        
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
    """Reset spell slots and channel divinity on long rest.
    
    Called by Long Rest button to restore all expended spell slots
    and channel divinity uses at the end of a long rest.
    """
    console.log("DEBUG: reset_spell_slots() called")
    try:
        if SPELLCASTING_MANAGER is not None:
            SPELLCASTING_MANAGER.reset_spell_slots()
        reset_channel_divinity()
        trigger_auto_export("reset_spell_slots")
    except Exception as e:
        print(f"ERROR in reset_spell_slots: {e}")


def load_inventory_state(state: Optional[dict]):
    """Load inventory from character state."""
    if INVENTORY_MANAGER is not None:
        INVENTORY_MANAGER.load_state(state)


def render_inventory():
    """Render the inventory list."""
    if INVENTORY_MANAGER is not None:
        INVENTORY_MANAGER.render_inventory()


def render_weapons_grid():
    """Render equipped weapons as a grid table in the Skills tab."""
    if INVENTORY_MANAGER is None:
        return
    
    # Get all equipped weapons from inventory
    equipped_weapons = []
    for item in INVENTORY_MANAGER.items:
        category = item.get("category", "")
        # Check if weapon - "Weapons" is the primary category, but also check for "weapon" just in case
        is_weapon = category in ["Weapons", "weapon", "weapons"]
        if item.get("equipped") and is_weapon:
            equipped_weapons.append(item)
    
    weapons_grid = get_element("weapons-grid")
    empty_state = get_element("weapons-empty-state")
    
    if not weapons_grid:
        return
    
    if not equipped_weapons:
        # Show empty state
        weapons_grid.innerHTML = ""
        if empty_state:
            empty_state.style.display = "table-row"
        return
    
    # Hide empty state
    if empty_state:
        empty_state.style.display = "none"
    
    # Get character stats for to-hit calculation
    scores = gather_scores()
    level = get_numeric_value("level", 1)
    proficiency = compute_proficiency(level)
    race_bonuses = get_race_ability_bonuses(get_text_value("race"))
    
    weapons_grid.innerHTML = ""
    
    for weapon in equipped_weapons:
        tr = document.createElement("tr")
        
        # Extract weapon properties - handle both Open5e API format and custom format
        weapon_bonus = 0
        weapon_damage = None
        weapon_damage_type = ""
        weapon_range = "Melee"
        weapon_properties_list = []
        weapon_properties_str = ""
        
        # DEBUG: Log what we're working with
        console.log(f"DEBUG render_weapons_grid: Processing '{weapon.get('name')}'")
        console.log(f"  - notes field content: {weapon.get('notes')}")
        
        # First, always try to parse properties from notes JSON (this is where they're stored)
        try:
            notes_str = weapon.get("notes", "")
            if notes_str and notes_str.startswith("{"):
                extra_props = json.loads(notes_str)
                console.log(f"  ✓ Successfully parsed notes JSON: {extra_props}")
                # Get all values from notes
                if "damage" in extra_props:
                    weapon_damage = extra_props["damage"]
                if "damage_type" in extra_props:
                    weapon_damage_type = extra_props["damage_type"]
                if "range" in extra_props:
                    weapon_range = extra_props["range"]
                if "properties" in extra_props:
                    weapon_properties_str = extra_props["properties"]
                if "bonus" in extra_props:
                    weapon_bonus = extra_props["bonus"]
                console.log(f"  ✓ FINAL VALUES: damage={weapon_damage}, type={weapon_damage_type}, range={weapon_range}, properties={weapon_properties_str}")
        except Exception as e:
            console.error(f"  ✗ Failed to parse notes JSON: {e}")
            pass
        
        # Fallback: Try to get damage from direct properties (backward compat)
        if not weapon_damage:
            if weapon.get("damage_dice"):
                weapon_damage = weapon.get("damage_dice")
            elif weapon.get("damage"):
                weapon_damage = weapon.get("damage")
        
        # Parse properties from Open5e format (list) if we still don't have them
        if not weapon_properties_str:
            props = weapon.get("properties", [])
            if isinstance(props, list) and props:
                weapon_properties_list = props
            # Look for range in properties (e.g., "ammunition (range 30/120)")
            for prop in props:
                if isinstance(prop, str):
                    prop_lower = prop.lower()
                    if "range" in prop_lower or "ammunition" in prop_lower:
                        # Extract range if it exists in the property
                        if "(" in prop and ")" in prop:
                            weapon_range = prop[prop.find("(")+1:prop.find(")")]
                        else:
                            weapon_range = prop
                        break
        
        # Convert properties list to string
        if weapon_properties_list and not weapon_properties_str:
            weapon_properties_str = ", ".join(weapon_properties_list)
        
        # Determine if ranged weapon
        is_ranged = False
        if weapon_properties_list:
            for prop in weapon_properties_list:
                if isinstance(prop, str) and ("ranged" in prop.lower() or "ammunition" in prop.lower()):
                    is_ranged = True
                    break
        
        # If no range info found and it's not ranged, keep as Melee
        if not is_ranged and weapon_range == "Melee":
            # Check if it's a ranged weapon by category
            weapon_category = weapon.get("category", "").lower()
            if "ranged" in weapon_category or "bow" in weapon_category or "crossbow" in weapon_category:
                is_ranged = True
        
        # Default damage if not found
        if not weapon_damage:
            weapon_damage = "1d4"
        
        # Column 1: Weapon name (with bonus if applicable)
        name_td = document.createElement("td")
        name_text = weapon.get("name", "Unknown")
        
        if weapon_bonus and weapon_bonus > 0:
            name_text = f"{name_text} +{weapon_bonus}"
        name_td.textContent = name_text
        tr.appendChild(name_td)
        
        # Column 2: To Hit bonus
        to_hit_td = document.createElement("td")
        # Determine ability based on weapon properties
        use_finesse = False
        if weapon_properties_list:
            for prop in weapon_properties_list:
                if isinstance(prop, str) and "finesse" in prop.lower():
                    use_finesse = True
                    break
        elif weapon_properties_str:
            use_finesse = "finesse" in weapon_properties_str.lower()
        
        str_score = scores.get("str", 10) + race_bonuses.get("str", 0)
        dex_score = scores.get("dex", 10) + race_bonuses.get("dex", 0)
        
        # For ranged weapons, use DEX if higher; for melee, use STR unless finesse
        if is_ranged:
            ability_mod = ability_modifier(dex_score)
        elif use_finesse and dex_score > str_score:
            ability_mod = ability_modifier(dex_score)
        else:
            ability_mod = ability_modifier(str_score)
        
        to_hit = ability_mod + proficiency + weapon_bonus
        to_hit_td.textContent = format_bonus(to_hit)
        tr.appendChild(to_hit_td)
        
        # Column 3: Damage
        damage_td = document.createElement("td")
        damage_text = f"{weapon_damage}"
        if weapon_damage_type:
            damage_text += f" {weapon_damage_type}"
        if weapon_bonus and weapon_bonus > 0:
            damage_text += f" +{weapon_bonus}"
        damage_td.textContent = damage_text
        tr.appendChild(damage_td)
        
        # Column 4: Range
        range_td = document.createElement("td")
        range_td.textContent = weapon_range
        tr.appendChild(range_td)
        
        # Column 5: Properties
        props_td = document.createElement("td")
        properties_text = weapon_properties_str if weapon_properties_str else "—"
        props_td.textContent = properties_text
        tr.appendChild(props_td)
        
        weapons_grid.appendChild(tr)
    
    weapons_grid = get_element("weapons-grid")
    empty_state = get_element("weapons-empty-state")
    
    if not weapons_grid:
        return
    
    if not equipped_weapons:
        # Show empty state
        weapons_grid.innerHTML = ""
        if empty_state:
            empty_state.style.display = "table-row"
        return
    
    # Hide empty state
    if empty_state:
        empty_state.style.display = "none"
    
    # Get character stats for to-hit calculation
    scores = gather_scores()
    level = get_numeric_value("level", 1)
    proficiency = compute_proficiency(level)
    
    weapons_grid.innerHTML = ""
    
    for weapon in equipped_weapons:
        tr = document.createElement("tr")
        
        # Column 1: Weapon name (with bonus if applicable)
        name_td = document.createElement("td")
        name_text = weapon.get("name", "Unknown")
        bonus = 0
        try:
            notes_str = weapon.get("notes", "")
            if notes_str and notes_str.startswith("{"):
                extra_props = json.loads(notes_str)
                bonus = extra_props.get("bonus", 0)
        except:
            bonus = 0
        
        if bonus and bonus > 0:
            name_text = f"{name_text} +{bonus}"
        name_td.textContent = name_text
        tr.appendChild(name_td)
        
        # Column 2: To Hit bonus
        to_hit_td = document.createElement("td")
        # Try to calculate based on weapon properties
        # For now, use DEX or STR based on weapon properties
        weapon_properties = weapon.get("properties", "").lower()
        use_finesse = "finesse" in weapon_properties
        str_score = scores.get("str", 10) + get_race_ability_bonuses(get_text_value("race")).get("str", 0)
        dex_score = scores.get("dex", 10) + get_race_ability_bonuses(get_text_value("race")).get("dex", 0)
        
        # Default to STR, but use DEX if finesse and DEX is higher
        if use_finesse and dex_score > str_score:
            ability_mod = ability_modifier(dex_score)
        else:
            ability_mod = ability_modifier(str_score)
        
        to_hit = ability_mod + proficiency + bonus
        to_hit_td.textContent = format_bonus(to_hit)
        tr.appendChild(to_hit_td)
        
        # Column 3: Damage
        damage_td = document.createElement("td")
        damage_dice = weapon.get("damage", "1d4")
        damage_type = weapon.get("damage_type", "bludgeoning")
        damage_text = f"{damage_dice} {damage_type}"
        if bonus and bonus > 0:
            damage_text += f" +{bonus}"
        damage_td.textContent = damage_text
        tr.appendChild(damage_td)
        
        # Column 4: Range
        range_td = document.createElement("td")
        range_text = weapon.get("range_text", "Melee")
        range_td.textContent = range_text
        tr.appendChild(range_td)
        
        # Column 5: Properties
        props_td = document.createElement("td")
        properties_text = weapon.get("properties", "")
        if not properties_text:
            properties_text = "—"
        props_td.textContent = properties_text
        tr.appendChild(props_td)
        
        weapons_grid.appendChild(tr)
    # Update equipped items display
    render_equipped_attack_grid()


def add_resource(_event=None):
    """Add a new resource tracker to the character."""
    console.log("DEBUG: add_resource() called")
    try:
        # Get resource list element
        resource_list = document.getElementById("resource-list")
        if resource_list is None:
            print("ERROR: resource-list element not found")
            return
        
        # Get current character state
        from assets.py.state_manager import state_manager
        if state_manager is None or state_manager.state is None:
            print("ERROR: state_manager not initialized")
            return
        
        # Get or initialize resources list
        resources = state_manager.state.get("resources", [])
        if not isinstance(resources, list):
            resources = []
        
        # Check if we've hit the max resources limit
        if len(resources) >= MAX_RESOURCES:
            print(f"ERROR: Maximum {MAX_RESOURCES} resources reached")
            return
        
        # Create a new resource with default values
        new_resource = {
            "name": f"Resource {len(resources) + 1}",
            "max_value": 1,
            "current_value": 1,
            "type": "resource"
        }
        
        # Add to state
        resources.append(new_resource)
        state_manager.state["resources"] = resources
        
        # Save the state
        state_manager.save()
        
        # Render the updated resource list
        render_resources()
        
        print(f"Added new resource: {new_resource['name']}")
        
    except Exception as e:
        print(f"ERROR in add_resource: {e}")


def render_resources():
    """Render the resource trackers list."""
    console.log("DEBUG: render_resources() called")
    try:
        from assets.py.state_manager import state_manager
        
        resource_list = document.getElementById("resource-list")
        if resource_list is None:
            print("ERROR: resource-list element not found")
            return
        
        # Clear existing content
        resource_list.innerHTML = ""
        
        if state_manager is None or state_manager.state is None:
            return
        
        resources = state_manager.state.get("resources", [])
        if not resources:
            resource_list.innerHTML = "<p class='hint'>No resources yet. Click 'Add Resource' to create one.</p>"
            return
        
        # Render each resource
        for idx, resource in enumerate(resources):
            name = resource.get("name", f"Resource {idx + 1}")
            max_val = resource.get("max_value", 1)
            current_val = resource.get("current_value", max_val)
            
            # Create resource row
            row = document.createElement("div")
            row.className = "resource-row"
            
            # Create HTML for this resource
            row.innerHTML = f"""
            <div class="resource-item">
                <label>{name}</label>
                <div class="resource-controls">
                    <input type="number" class="resource-current" 
                           value="{current_val}" 
                           data-index="{idx}"
                           min="0" max="{max_val}">
                    <span class="resource-max">/ {max_val}</span>
                    <button class="resource-delete-btn" data-index="{idx}">Delete</button>
                </div>
            </div>
            """
            resource_list.appendChild(row)
        
    except Exception as e:
        print(f"ERROR in render_resources: {e}")


def _export_character_wrapper(_event=None):
    """Synchronous wrapper for async export_character function.
    
    PyScript's py-click attribute only works with synchronous functions,
    so this wrapper schedules the async function properly.
    """
    console.log("DEBUG: _export_character_wrapper() called")
    try:
        # Create an async context and schedule the export
        import asyncio
        # Schedule the async function in the event loop
        asyncio.create_task(export_character(_event))
    except Exception as e:
        print(f"ERROR in _export_character_wrapper: {e}")


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
    # Defensive wrapper: test environments may provide a minimal MockDocument
    getter = getattr(document, 'getElementById', None)
    if not getter:
        return None
    return getter(element_id)


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
    return get_class_hit_die(class_name)


def get_armor_proficiencies_for_class(class_name: str, domain: str = "") -> str:
    """Return armor proficiencies for a given D&D 5e class.
    
    Args:
        class_name: The character's class
        domain: The cleric domain (if applicable)
    """
    profs = get_class_armor_proficiencies(class_name, domain)
    return ", ".join(profs)


def get_weapon_proficiencies_for_class(class_name: str) -> str:
    """Return weapon proficiencies for a given D&D 5e class."""
    profs = get_class_weapon_proficiencies(class_name)
    return ", ".join(profs)


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
    console.log(f"DEBUG: determine_progression_key() - class_key={class_key}, CLASS_CASTING_PROGRESSIONS={CLASS_CASTING_PROGRESSIONS}, base={base}")
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
    # Return the progression table for the key, or an empty dict if not found
    return SPELLCASTING_PROGRESSION_TABLES.get(progression_key, {})


def compute_spellcasting_profile(
    raw_text: Optional[str] = None,
    fallback_level: Optional[int] = None,
) -> dict:
    entries = extract_character_classes(raw_text)
    console.log(f"DEBUG: compute_spellcasting_profile() - entries={entries}")
    if fallback_level is None:
        fallback_level = get_numeric_value("level", 1)
    fallback_level = max(1, int(fallback_level or 1))
    console.log(f"DEBUG: compute_spellcasting_profile() - fallback_level={fallback_level}")

    allowed_classes: list[str] = []
    max_spell_level = -1
    has_progression = False

    for entry in entries:
        class_key = entry["key"]
        class_level = entry["level"] if entry["level"] is not None else fallback_level
        class_level = max(1, min(int(class_level or fallback_level), 20))
        progression = determine_progression_key(class_key, entry["raw"])
        console.log(f"DEBUG: compute_spellcasting_profile() - processing class_key={class_key}, class_level={class_level}, progression={progression}")
        if progression == "none":
            console.log(f"DEBUG: compute_spellcasting_profile() - progression is 'none', skipping")
            continue
        has_progression = True
        table = get_progression_table(progression)
        
        # table is a dict where keys are character levels and values are spell level dicts
        # e.g., table[9] = {1: 4, 2: 3, 3: 3, 4: 3, 5: 1} means level 9 has spells up to level 5
        level_slots = table.get(class_level, {})
        if not level_slots and table:
            # If exact level not found, use the last available level
            level_slots = table.get(max(table.keys()), {})
        
        # Get the maximum spell level available (highest key in the slots dict)
        if level_slots:
            level_cap = max(level_slots.keys())
        else:
            level_cap = 0
        
        console.log(f"DEBUG: compute_spellcasting_profile() - table keys={list(table.keys())[:3]}, class_level={class_level}, level_slots={level_slots}, level_cap={level_cap}")
        if class_key not in allowed_classes:
            allowed_classes.append(class_key)
        if level_cap > max_spell_level:
            max_spell_level = level_cap

    if not has_progression:
        max_spell_level = -1
    elif max_spell_level < 0:
        max_spell_level = 0

    console.log(f"DEBUG: compute_spellcasting_profile() - result: allowed_classes={allowed_classes}, max_spell_level={max_spell_level}")
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
        try:
            remove_anim_proxy = create_proxy(remove_anim)
            _EVENT_PROXIES.append(remove_anim_proxy)
            if document is not None and getattr(document, "defaultView", None) is not None:
                document.defaultView.setTimeout(remove_anim_proxy, 600)
            elif window is not None and hasattr(window, "setTimeout"):
                window.setTimeout(remove_anim_proxy, 600)
        except Exception:
            try:
                remove_anim()
            except Exception:
                pass


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
    
    # Add item modifiers including shields
    item_ac_mod = 0
    shield_bonus = 0
    item_mods = []
    if INVENTORY_MANAGER is not None:
        for item in INVENTORY_MANAGER.items:
            try:
                # Only process equipped items
                if not item.get("equipped"):
                    continue
                    
                item_name = item.get("name", "").lower()
                category = item.get("category", "").lower()
                notes_str = item.get("notes", "")
                extra_props = {}
                
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                
                # Check if this is a shield
                is_shield = ("shield" in item_name or category == "shield")
                
                if is_shield:
                    # Shields: +2 base bonus + magical bonus
                    bonus_val = int(extra_props.get("bonus", 0))
                    shield_bonus_val = 2 + bonus_val
                    shield_bonus += shield_bonus_val
                    item_mods.append((item.get("name", "Unknown"), shield_bonus_val, True))  # True = is_shield
                else:
                    # Other items: ac_modifier
                    if extra_props.get("armor_only", False):
                        continue
                    ac_mod = extra_props.get("ac_modifier", 0)
                    if ac_mod:
                        ac_mod = int(ac_mod)
                        item_ac_mod += ac_mod
                        item_mods.append((item.get("name", "Unknown"), ac_mod, False))  # False = not shield
            except:
                pass
    
    if item_mods:
        rows.append('<div style="margin-top: 0.4rem; border-top: 1px solid rgba(148, 163, 184, 0.2); padding-top: 0.4rem;"></div>')
        for item_name, mod_val, is_shield_item in item_mods:
            if is_shield_item:
                rows.append(f'<div class="tooltip-row"><span class="tooltip-label">{escape(item_name)}</span><span class="tooltip-value">{format_bonus(mod_val)}</span></div>')
            else:
                rows.append(f'<div class="tooltip-row"><span class="tooltip-label">{escape(item_name)}</span><span class="tooltip-value">{format_bonus(mod_val)}</span></div>')
    
    total_ac = base_ac + shield_bonus + item_ac_mod
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
    
    Priority: Equipped items first, then any items found
    """
    # Get DEX modifier
    dex_score = get_numeric_value("dex-score", 10)
    dex_mod = ability_modifier(dex_score)
    
    print(f"[AC-CALC] Starting AC calculation: DEX {dex_score} (mod {dex_mod})")
    
    # Check for equipped armor in inventory (priority)
    armor_ac = None
    armor_name = None
    armor_type = None
    
    if INVENTORY_MANAGER is not None:
        # First, look for equipped armor
        for item in INVENTORY_MANAGER.items:
            if item.get("equipped") and is_equipable(item):
                item_name = item.get("name", "").lower()
                
                # Check if it's armor (exclude weapons)
                armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "armor"]
                weapon_keywords = ["sword", "axe", "bow", "spear", "mace", "staff", "dagger", "rapier", "crossbow", "club", "flail", "hammer", "lance", "pike", "scimitar"]
                
                is_armor = any(kw in item_name for kw in armor_keywords)
                is_weapon = any(kw in item_name for kw in weapon_keywords)
                
                if is_armor and not is_weapon:
                    # Found equipped armor
                    try:
                        notes_str = item.get("notes", "")
                        if notes_str and notes_str.startswith("{"):
                            extra_props = json.loads(notes_str)
                            ac_val = extra_props.get("armor_class", extra_props.get("ac"))
                            if ac_val:
                                armor_ac = int(ac_val)
                                armor_name = item.get("name", "Unknown Armor")
                                armor_type = get_armor_type(armor_name)
                                print(f"[AC-CALC] Found armor: {armor_name}, AC={armor_ac}, type={armor_type}")
                                break  # Use first equipped armor found
                    except:
                        pass
        
        # If no equipped armor found, look for any armor
        if armor_ac is None:
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
                                print(f"[AC-CALC] Found armor (fallback): {armor_name}, AC={armor_ac}, type={armor_type}")
                                break  # Use first armor found
                    except:
                        pass
    
    # Calculate base AC
    if armor_ac is not None:
        if armor_type == "heavy":
            # Heavy armor: AC is fixed, no DEX modifier
            base_ac = armor_ac
            print(f"[AC-CALC] Heavy armor: base_ac={base_ac} (no DEX)")
        elif armor_type == "medium":
            # Medium armor: AC + DEX (max +2, never subtract)
            dex_to_add = max(0, min(dex_mod, 2))  # Clamp: 0 to +2
            base_ac = armor_ac + dex_to_add
            print(f"[AC-CALC] Medium armor: {armor_ac} + DEX {dex_to_add} (capped) = {base_ac}")
        else:
            # Light armor: AC + DEX (no cap, but never subtract)
            dex_to_add = max(0, dex_mod)  # Never go below 0
            base_ac = armor_ac + dex_to_add
            print(f"[AC-CALC] Light armor: {armor_ac} + DEX {dex_to_add} = {base_ac}")
    else:
        # No armor - use 10 + DEX (can be negative if DEX is very low)
        base_ac = 10 + dex_mod
        print(f"[AC-CALC] No armor: 10 + DEX {dex_mod} = {base_ac}")
    
    # Add AC modifiers from equipped items
    # Shields add +2 base bonus + magical bonus
    # AC modifiers from other items add to AC (e.g. Ring of Protection)
    item_ac_mod = 0
    shield_bonus = 0
    if INVENTORY_MANAGER is not None:
        for item in INVENTORY_MANAGER.items:
            try:
                # Only process equipped items
                if item.get("equipped"):
                    item_name = item.get("name", "").lower()
                    category = item.get("category", "").lower()
                    notes_str = item.get("notes", "")
                    extra_props = {}
                    
                    if notes_str and notes_str.startswith("{"):
                        extra_props = json.loads(notes_str)
                    
                    # Check if this is a shield
                    is_shield = ("shield" in item_name or category == "shield")
                    
                    if is_shield:
                        # Shields: +2 base bonus + magical bonus
                        bonus_val = extra_props.get("bonus", 0)
                        shield_bonus += 2 + bonus_val
                        print(f"[AC-CALC] Found shield: {item.get('name')}, bonus={2 + bonus_val}")
                    else:
                        # Other items: ac_modifier
                        ac_mod = extra_props.get("ac_modifier", 0)
                        if ac_mod:
                            item_ac_mod += int(ac_mod)
                            print(f"[AC-CALC] AC modifier from {item.get('name')}: {ac_mod}")
            except:
                pass
    
    final_ac = max(1, base_ac + shield_bonus + item_ac_mod)
    print(f"[AC-CALC] FINAL AC: {base_ac} (base) + {shield_bonus} (shields) + {item_ac_mod} (mods) = {final_ac}")
    return final_ac


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
    trigger_auto_export("reset_channel_divinity")

def _update_ability_scores_and_saves(scores, race_bonuses, proficiency):
    """Update ability scores, modifiers, and saving throws display."""
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


def _update_skills_and_passive(scores, proficiency, race_bonuses):
    """Update skill bonuses and passive perception display."""
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


def _update_spell_casting_stats(class_name, scores, race_bonuses, level, proficiency):
    """Update spell save DC, spell attack, and max prepared spells."""
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

    # Calculate max prepared spells
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
    
    return spell_ability, spell_mod, spell_score, spell_save_dc, spell_attack, max_prepared


def _update_hp_display(current_hp, max_hp, temp_hp):
    """Update HP bar fill and temp HP overlay."""
    if max_hp > 0:
        hp_percentage = max(0, min(100, int((current_hp / max_hp) * 100)))
        if temp_hp > 0:
            hp_label = f"({current_hp} / {max_hp} +{temp_hp})"
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
        if hp_percentage <= 50:
            hue = 60 * (hp_percentage / 50)
            saturation = 100
            lightness = 40
        else:
            hue = 60 + (60 * ((hp_percentage - 50) / 50))
            saturation = 100
            lightness = 40
        
        hp_bar_fill.style.background = f"hsl({hue}, {saturation}%, {lightness}%)"
    
    hp_bar_temp = get_element("hp-bar-temp")
    if hp_bar_temp:
        hp_bar_temp.style.width = f"{temp_hp_percentage}%"
        hp_bar_temp.style.left = f"{hp_percentage}%"
    
    set_text("hp-bar-label", hp_label)


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

    # Update ability scores and saves
    _update_ability_scores_and_saves(scores, race_bonuses, proficiency)

    # Update initiative
    dex_mod = ability_modifier(scores["dex"] + race_bonuses.get("dex", 0))
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

    # Update skills and passive perception
    _update_skills_and_passive(scores, proficiency, race_bonuses)

    # Update spell casting stats and prepare spells counter
    spell_ability, spell_mod, spell_score, spell_save_dc, spell_attack, max_prepared = _update_spell_casting_stats(
        class_name, scores, race_bonuses, level, proficiency
    )
    
    # Count only user-prepared spells (exclude domain bonus spells and cantrips)
    domain = get_text_value("domain")
    if SPELL_LIBRARY_STATE.get("loaded"):
        _ensure_domain_spells_in_spellbook(reason="calc_sync")
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
    _update_hp_display(current_hp, max_hp, temp_hp)

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
            "channel_divinity_available": get_numeric_value("channel_divinity_available", 0),
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
    console.log("[POPULATE] populate_form() called")
    previous_suppression = False
    if _export_mgmt is not None:
        previous_suppression = _export_mgmt._AUTO_EXPORT_SUPPRESS
        _export_mgmt._AUTO_EXPORT_SUPPRESS = True
    console.log("[POPULATE] Auto-export suppression enabled")
    try:
        console.log("[POPULATE] Creating character from dict...")
        character = CharacterFactory.from_dict(data)
        console.log(f"[POPULATE] Character created: {character.name} ({character.class_text})")
        normalized = character.to_dict()
        console.log("[POPULATE] Character normalized")

        # Normalize class: extract just the class name from "Class Level" format
        class_text = character.class_text.strip()
        if class_text:
            # Extract the first word as the class name (handles "Wizard 5" -> "Wizard")
            class_name = class_text.split()[0]
            set_form_value("class", class_name)
        else:
            set_form_value("class", "")
        
        console.log("[POPULATE] Setting identity fields...")
        set_form_value("name", character.name)
        set_form_value("race", character.race)
        set_form_value("background", character.background)
        set_form_value("alignment", character.alignment)
        set_form_value("player_name", character.player_name)
        set_form_value("domain", character.domain)
        console.log(f"[POPULATE] Identity set, domain: {character.domain}")

        set_form_value("level", character.level)
        set_form_value("inspiration", character.inspiration)
        set_form_value("spell_ability", character.spell_ability)
        console.log("[POPULATE] Basic stats set")

        console.log("[POPULATE] Setting ability scores...")
        for ability in ABILITY_ORDER:
            set_form_value(f"{ability}-score", character.attributes[ability])
            set_form_value(f"{ability}-save-prof", character.attributes.is_proficient(ability))
        console.log("[POPULATE] Ability scores set")

        console.log("[POPULATE] Setting skills...")
        for skill in SKILLS:
            skill_state = normalized.get("skills", {}).get(skill, {})
            set_form_value(f"{skill}-prof", skill_state.get("proficient", False))
            set_form_value(f"{skill}-exp", skill_state.get("expertise", False))
        console.log("[POPULATE] Skills set")

        console.log("[POPULATE] Setting combat data...")
        combat = normalized.get("combat", {})
        set_form_value("armor_class", combat.get("armor_class", 10))
        set_form_value("speed", combat.get("speed", 30))
        set_form_value("max_hp", combat.get("max_hp", 8))
        set_form_value("current_hp", combat.get("current_hp", 8))
        set_form_value("temp_hp", combat.get("temp_hp", 0))
        set_form_value("hit_dice", combat.get("hit_dice", ""))
        set_form_value("hit_dice_available", combat.get("hit_dice_available", 0))
        set_form_value("channel_divinity_available", combat.get("channel_divinity_available", 0))
        
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
        console.log("[POPULATE] Notes set")

        console.log("[POPULATE] Setting spell fields...")
        spells = normalized.get("spells", {})
        for key, element_id in SPELL_FIELDS.items():
            set_form_value(element_id, spells.get(key, ""))

        console.log("[POPULATE] Loading spellcasting state...")
        load_spellcasting_state(normalized.get("spellcasting"))
        console.log("[POPULATE] Spellcasting state loaded")

        # Load inventory BEFORE update_calculations so totals can be calculated correctly
        console.log("[POPULATE] Loading inventory...")
        load_inventory_state(normalized)
        render_inventory()
        console.log("[POPULATE] Inventory loaded and rendered")

        # NOW update calculations (which calls update_equipment_totals)
        console.log("[POPULATE] Updating calculations...")
        update_calculations()
        console.log("[POPULATE] Calculations updated")

        # populate currency
        console.log("[POPULATE] Setting currency...")
        inv = normalized.get("inventory", {})
        currency = inv.get("currency", {})
        for key in CURRENCY_ORDER:
            set_form_value(f"currency-{key}", currency.get(key, 0))
        console.log("[POPULATE] Currency set")

        # NOTE: Old equipment table code removed - using new InventoryManager system instead
        # items = get_equipment_items_from_data(normalized)
        # render_equipment_table(items)
        # update_equipment_totals()
        console.log("[POPULATE] populate_form() COMPLETED SUCCESSFULLY")
    except Exception as e:
        console.error(f"[POPULATE] ERROR in populate_form: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        console.log("[POPULATE] Restoring auto-export suppression")
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


def _build_spell_tags_and_action_button(spell: dict, prepared: bool, is_domain_bonus: bool, can_add: bool, can_remove: bool, slug: str) -> tuple[str, str, str]:
    """Build spell tags and action button HTML. Returns (tags_html, action_button_html, button_classes_str)."""
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
    
    return tags_html, action_button, button_class_attr


def _build_spell_properties_html(spell: dict) -> str:
    """Build spell properties definition list HTML."""
    properties = []
    casting_time = spell.get("casting_time")
    if casting_time:
        properties.append(f"<div><dt>Casting Time</dt><dd>{escape(casting_time)}</dd></div>")
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
    
    if properties:
        return "<dl class=\"spell-properties\">" + "".join(properties) + "</dl>"
    return ""


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

    # Build meta text (level and school)
    meta_parts: list[str] = []
    level_label = spell.get("level_label")
    if level_label:
        meta_parts.append(level_label)
    school = spell.get("school")
    if school:
        meta_parts.append(school)
    meta_text = " · ".join(part for part in meta_parts if part)

    # Build tags and action button
    tags_html, action_button, button_class_attr = _build_spell_tags_and_action_button(
        spell, prepared, is_domain_bonus, can_add, can_remove, slug
    )

    # Build properties definition list
    properties_html = _build_spell_properties_html(spell)

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
    # Detect saving throw requirement (must *require* a save, not just mention it)
    try:
        import re
        # Only match if the spell text says the target "must" make a save or "fails" one
        # This filters out spells like Bless that just mention saving throws as optional outcomes
        # Matches patterns like:
        #   "must succeed on a Dexterity saving throw"
        #   "must make a Wisdom saving throw"
        #   "if it fails a Dexterity saving throw"
        save_regex = re.compile(r"(?:must\s+(?:succeed\s+on\s+|make\s+)(?:a|an)\s+|if\s+it\s+fails\s+(?:a|an)\s+)(strength|dexterity|constitution|intelligence|wisdom|charisma)\s+saving throw", re.IGNORECASE)
        text_blobs = []
        for field in ("dc", "saving_throw", "desc", "higher_level", "description", "description_html"):
            value = spell.get(field)
            if isinstance(value, (list, tuple)):
                value = " ".join(str(v) for v in value)
            if value:
                text_blobs.append(str(value))
        save_ability = None
        save_required = False
        for blob in text_blobs:
            match = save_regex.search(blob)
            if match:
                save_required = True
                ability = match.group(1).lower()
                ability_map = {
                    "strength": "STR",
                    "dexterity": "DEX",
                    "constitution": "CON",
                    "intelligence": "INT",
                    "wisdom": "WIS",
                    "charisma": "CHA",
                }
                save_ability = ability_map.get(ability)
                break
        if save_required and save_ability:
            label = f"Save: {save_ability}"
            title = f"Requires {save_ability} saving throw"
            mnemonics.append(f"<span class=\"spell-mnemonic save\" title=\"{escape(title)}\">{escape(label)}</span>")
    except Exception as exc:
        console.warn(f"DEBUG: save mnemonic detection failed for {slug}: {exc}")
    
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
    console.log(f"DEBUG: render_spell_results() called with {len(spells)} spells")
    results_el = get_element("spell-library-results")
    console.log(f"DEBUG: render_spell_results() - results_el found: {results_el is not None}")
    if results_el is None:
        console.warn("DEBUG: render_spell_results() - spell-library-results element not found!")
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
    console.log(f"DEBUG: apply_spell_filters() called with auto_select={auto_select}")
    _ensure_spell_library_seeded(reason="apply_filters")
    profile = compute_spellcasting_profile()
    profile_signature = ",".join(profile["allowed_classes"]) + f"|{profile['max_spell_level']}"
    if profile_signature != SPELL_LIBRARY_STATE.get("last_profile_signature"):
        SPELL_LIBRARY_STATE["last_profile_signature"] = profile_signature
        if not auto_select:
            auto_select = True

    if not SPELL_LIBRARY_STATE.get("loaded"):
        console.log("DEBUG: apply_spell_filters() - spells not loaded yet, returning")
        update_spell_library_status("Spells not loaded yet. Click \"Load Spells\" to fetch the Open5e SRD.")
        return

    console.log("DEBUG: apply_spell_filters() - spells loaded, getting DOM elements...")
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
    console.log(f"DEBUG: apply_spell_filters() - spells={len(spells)}, allowed_classes={allowed_classes}, selected_class='{selected_class}', allowed_set={allowed_set}")
    
    source_filtered = 0
    level_filtered = 0
    class_filtered = 0
    search_filtered = 0
    
    for spell in spells:
        # Filter by allowed sources
        source = spell.get("source", "")
        if not is_spell_source_allowed(source):
            source_filtered += 1
            continue
        
        spell_level = spell.get("level_int", 0)
        if max_spell_level is not None and spell_level > max_spell_level:
            level_filtered += 1
            continue
        spell_classes = set(spell.get("classes", []))
        if selected_class:
            if selected_class not in spell_classes:
                class_filtered += 1
                continue
        elif allowed_set:
            if not spell_classes.intersection(allowed_set):
                class_filtered += 1
                continue
        if level_filter is not None and spell_level != level_filter:
            level_filtered += 1
            continue
        if search_term and search_term not in spell.get("search_blob", ""):
            search_filtered += 1
            continue
        filtered.append(spell)
    
    console.log(f"DEBUG: Spell filtering breakdown - source_filtered={source_filtered}, level_filtered={level_filtered}, class_filtered={class_filtered}, search_filtered={search_filtered}, passed={len(filtered)}")
    console.log(f"DEBUG: apply_spell_filters() - filtered {len(filtered)} spells, calling render_spell_results")
    displayed, truncated, total_filtered = render_spell_results(filtered, allowed_set)
    console.log(f"DEBUG: apply_spell_filters() - render_spell_results returned: displayed={displayed}, truncated={truncated}, total={total_filtered}")

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


def _load_spell_library_wrapper(_event=None):
    """Synchronous wrapper for async load_spell_library function.
    
    PyScript's py-click attribute only works with synchronous functions,
    so this wrapper schedules the async function properly.
    """
    console.log("DEBUG: _load_spell_library_wrapper() called")
    try:
        import asyncio
        asyncio.create_task(load_spell_library(_event))
    except Exception as e:
        console.log(f"ERROR in _load_spell_library_wrapper: {e}")


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
        console.log("DEBUG: load_spell_library() - checking cache...")
        cached_spells = load_spell_cache()
        console.log(f"DEBUG: load_spell_library() - cached_spells = {type(cached_spells)}, len = {len(cached_spells) if cached_spells else 0}")
        if cached_spells:
            console.log(f"DEBUG: load_spell_library() - loading from cache, {len(cached_spells)} spells")
            set_spell_library_data(cached_spells)
            SPELL_LIBRARY_STATE["loaded"] = True
            populate_spell_class_filter(cached_spells)
            console.log("DEBUG: load_spell_library() - populated class filter, calling sync_prepared_spells_with_library")
            sync_prepared_spells_with_library()
            console.log("DEBUG: load_spell_library() - calling apply_spell_filters")
            apply_spell_filters(auto_select=True)
            console.log("DEBUG: load_spell_library() - calling _populate_domain_spells_on_load")
            # Auto-populate domain spells now that spell library is loaded from cache
            _populate_domain_spells_on_load()
            update_spell_library_status("Loaded spells from cache. Filters apply to your current class and level.")
            console.log("DEBUG: load_spell_library() - cache loading complete!")
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
        
        console.log(f"DEBUG: load_spell_library() - raw_spells check: raw_spells={bool(raw_spells)}, len={len(raw_spells) if raw_spells else 0}")
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
    """Render equipped weapons as table rows - delegates to render_equipped_attack_grid."""
    render_equipped_attack_grid()
    


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


def is_equipable(item: dict) -> bool:
    """Check if item can be equipped (armor or weapon)."""
    item_type = (item.get("type") or "").lower()
    item_name = (item.get("name") or "").lower()
    
    # Check explicit type field
    armor_types = ["armor", "light armor", "medium armor", "heavy armor", "shield"]
    weapon_types = ["weapon", "melee weapon", "ranged weapon", "simple melee", "simple ranged", "martial melee", "martial ranged"]
    
    if item_type in armor_types or item_type in weapon_types:
        return True
    
    # Heuristic: check name for common patterns
    armor_keywords = ["plate", "leather", "chain", "hide", "scale", "mail", "breastplate", "armor", "shield"]
    weapon_keywords = ["sword", "axe", "bow", "spear", "mace", "staff", "dagger", "rapier", "longsword", "shortsword", "greataxe", "greatsword", "crossbow", "shield", "club", "flail", "hammer", "lance", "pike", "scimitar"]
    
    for keyword in armor_keywords:
        if keyword in item_name:
            return True
    for keyword in weapon_keywords:
        if keyword in item_name:
            return True
    
    return False


def calculate_weapon_tohit(item: dict) -> int:
    """Calculate attack bonus for a weapon."""
    # Get proficiency and ability modifiers
    level = get_numeric_value("level", 1)
    proficiency = compute_proficiency(level)
    
    # Determine relevant ability (STR for melee, DEX for ranged typically)
    # For simplicity, use STR unless it's explicitly a ranged weapon
    item_type = (item.get("type") or "").lower()
    item_name = (item.get("name") or "").lower()
    
    ranged_keywords = ["bow", "crossbow", "ranged"]
    is_ranged = any(kw in item_name or kw in item_type for kw in ranged_keywords)
    
    ability_key = "dex" if is_ranged else "str"
    ability_score = get_numeric_value(f"{ability_key}-score", 10)
    ability_mod = ability_modifier(ability_score)
    
    # Add proficiency bonus - all equipped weapons get proficiency
    # (in a full implementation, would check class proficiencies)
    to_hit = ability_mod + proficiency
    
    # Detect bonus from notes JSON or equipment enrichment
    weapon_bonus = 0
    try:
        enriched = _enrich_weapon_item(item)
        weapon_bonus = enriched.get("bonus", 0) or 0
    except Exception:
        weapon_bonus = 0
    
    # If no bonus yet, try to parse from name like "+1 Sword"
    if not weapon_bonus:
        import re
        match = re.search(r'\+(\d+)', item.get("name", ""))
        if match:
            weapon_bonus = int(match.group(1))
    
    to_hit += weapon_bonus
    return to_hit


def create_unequip_handler(item_id, weapon_name):
    """Create a closure for unequip button that remembers the item_id."""
    def unequip_weapon():
        """Unequip a weapon from inventory."""
        if INVENTORY_MANAGER is None:
            console.log("[UNEQUIP] INVENTORY_MANAGER is None")
            return
        
        # Find and unequip the item
        for item in INVENTORY_MANAGER.items:
            if item.get("id") == item_id:
                item["equipped"] = False
                console.log(f"[UNEQUIP] Unequipped: {weapon_name}")
                # Re-render the weapons grid
                render_equipped_attack_grid()
                # Update calculations
                update_calculations()
                # Auto-export
                save_to_localstorage()
                return
        
        console.log(f"[UNEQUIP] Item not found: id={item_id}")
    
    return unequip_weapon


def _enrich_weapon_item(item: dict) -> dict:
    """Return a copy of item with damage/range/properties enriched from notes or equipment library."""
    enriched = dict(item)
    # Extract from explicit fields
    dmg = enriched.get("damage", "")
    dmg_type = enriched.get("damage_type", "")
    range_text = enriched.get("range_text", "") or enriched.get("range", "")
    props = enriched.get("weapon_properties", "") or enriched.get("properties", "")

    # Try notes JSON
    bonus = enriched.get("bonus", 0) or 0
    try:
        notes_str = enriched.get("notes", "")
        if notes_str and isinstance(notes_str, str) and notes_str.startswith("{"):
            notes_data = json.loads(notes_str)
            if not dmg and notes_data.get("damage"):
                dmg = notes_data.get("damage")
            if not dmg_type and notes_data.get("damage_type"):
                dmg_type = notes_data.get("damage_type")
            if not range_text and notes_data.get("range"):
                range_text = notes_data.get("range")
            if not props and notes_data.get("properties"):
                p = notes_data.get("properties")
                if isinstance(p, list):
                    props = ", ".join(str(x) for x in p)
                else:
                    props = p
            # Extract bonus if present in notes JSON
            if not bonus and notes_data.get("bonus"):
                try:
                    bonus = int(notes_data.get("bonus"))
                except Exception:
                    bonus = notes_data.get("bonus")
    except Exception:
        pass

    # If still missing fields, try to look up in equipment library by normalized name
    if (not dmg or not dmg_type or not range_text or not props) and EQUIPMENT_LIBRARY_STATE.get("equipment"):
        try:
            name_norm = (enriched.get("name", "") or "").lower().replace(',', '').strip()
            import re
            for eq in EQUIPMENT_LIBRARY_STATE.get("equipment", []):
                eq_name_raw = (eq.get("name", "") or "")
                eq_name = eq_name_raw.lower().replace(',', '').strip()
                # Tokenize names to allow matching 'Light Crossbow' <-> 'Crossbow, light'
                name_tokens = set(re.findall(r"\w+", name_norm))
                eq_tokens = set(re.findall(r"\w+", eq_name))
                match = False
                if name_tokens and eq_tokens:
                    # Exact token set match or subset match
                    if name_tokens == eq_tokens or name_tokens.issubset(eq_tokens) or eq_tokens.issubset(name_tokens):
                        match = True
                # Fallback substring checks
                if not match:
                    if name_norm in eq_name or eq_name in name_norm:
                        match = True
                if match:
                    console.log(f"[ENRICH] Found library match for {enriched.get('name')}: {eq_name_raw}")
                    if not dmg:
                        dmg = eq.get("damage") or eq.get("damage_dice") or dmg
                    if not dmg_type:
                        dmg_type = eq.get("damage_type") or dmg_type
                    if not range_text:
                        range_text = eq.get("range") or range_text
                    if not props:
                        p = eq.get("properties", "")
                        if isinstance(p, list):
                            # Convert list to comma-separated string
                            props = ", ".join(str(x) for x in p)
                            # Try to extract range info from properties strings like 'ammunition (range 80/320)'
                            try:
                                import re
                                if not range_text:
                                    for prop in p:
                                        if isinstance(prop, str):
                                            m = re.search(r"\(([^)]+)\)", prop)
                                            if m:
                                                # common Open5e property format: 'ammunition (range 80/320)'
                                                candidate = m.group(1).strip()
                                                # normalize candidate to remove leading 'range ' if present
                                                if candidate.lower().startswith("range"):
                                                    candidate = candidate.split(None, 1)[1] if len(candidate.split(None, 1)) > 1 else candidate
                                                range_text = candidate
                                                break
                            except Exception:
                                pass
                        else:
                            props = p

                    # If fields still missing, try to parse notes JSON (Equipment.to_dict() stores extras in notes)
                    try:
                        notes_str = eq.get("notes", "")
                        if notes_str and isinstance(notes_str, str) and notes_str.startswith("{"):
                            notes_data = json.loads(notes_str)
                            if not dmg:
                                dmg = notes_data.get("damage") or notes_data.get("damage_dice") or dmg
                            if not dmg_type:
                                dmg_type = notes_data.get("damage_type") or dmg_type
                            if not range_text:
                                range_text = notes_data.get("range") or notes_data.get("range_text") or range_text
                            if not props:
                                p2 = notes_data.get("properties", "")
                                if isinstance(p2, list):
                                    props = ", ".join(str(x) for x in p2)
                                else:
                                    props = p2
                            # Extract bonus from equipment notes if present
                            if not bonus and notes_data.get("bonus"):
                                try:
                                    bonus = int(notes_data.get("bonus"))
                                except Exception:
                                    bonus = notes_data.get("bonus")
                    except Exception:
                        # ignore malformed notes
                        pass

                    # If still missing fields, try the builtin equipment list as a final fallback
                    if (not dmg or not dmg_type or not range_text or not props):
                        try:
                            builtin = _find_builtin_equipment_match(enriched.get('name', ''))
                            if builtin:
                                if not dmg:
                                    dmg = builtin.get('damage') or builtin.get('damage_dice') or dmg
                                if not dmg_type:
                                    dmg_type = builtin.get('damage_type') or dmg_type
                                if not range_text:
                                    range_text = builtin.get('range_text') or builtin.get('range') or range_text
                                if not props:
                                    p3 = builtin.get('properties', '')
                                    if isinstance(p3, list):
                                        props = ", ".join(str(x) for x in p3)
                                    else:
                                        props = p3
                                # Extract bonus from builtin if provided
                                if not bonus and builtin.get('bonus'):
                                    try:
                                        bonus = int(builtin.get('bonus'))
                                    except Exception:
                                        bonus = builtin.get('bonus')
                        except Exception:
                            pass

                    console.log(f"[ENRICH] Applied damage={dmg}, type={dmg_type}, range={range_text}, props={props}")
                    break
        except Exception as e:
            console.log(f"[ENRICH] Error during library lookup: {e}")
            pass

    # Assign back to enriched dict under expected keys
    if dmg:
        enriched["damage"] = dmg
    if dmg_type:
        enriched["damage_type"] = dmg_type
    if range_text:
        enriched["range_text"] = range_text
    if props:
        enriched["weapon_properties"] = props
    # Ensure bonus from notes, equipment library or builtin fallback is present on enriched dict
    if bonus and bonus != 0:
        enriched["bonus"] = bonus

    # Final fallback: if still missing critical fields, try builtin equipment lookup even if the
    # global EQUIPMENT_LIBRARY_STATE hasn't been populated. This covers cases where the app
    # hasn't loaded the cached equipment list yet (avoids showing empty damage for common items).
    try:
        if (not dmg or not dmg_type or not range_text or not props):
            builtin = _find_builtin_equipment_match(enriched.get('name', ''))
            if builtin:
                if not dmg:
                    dmg = builtin.get('damage') or builtin.get('damage_dice') or dmg
                if not dmg_type:
                    dmg_type = builtin.get('damage_type') or dmg_type
                if not range_text:
                    range_text = builtin.get('range_text') or builtin.get('range') or range_text
                if not props:
                    p3 = builtin.get('properties', '')
                    if isinstance(p3, list):
                        props = ", ".join(str(x) for x in p3)
                    else:
                        props = p3
                # Propagate back to enriched dict
                if dmg:
                    enriched["damage"] = dmg
                if dmg_type:
                    enriched["damage_type"] = dmg_type
                if range_text:
                    enriched["range_text"] = range_text
                if props:
                    enriched["weapon_properties"] = props
                # In case builtin includes a bonus value
                if not bonus and builtin.get('bonus'):
                    try:
                        enriched['bonus'] = int(builtin.get('bonus'))
                    except Exception:
                        enriched['bonus'] = builtin.get('bonus')
    except Exception:
        # Be conservative — if anything goes wrong, don't interfere with enrichment
        pass

    return enriched


def render_equipped_attack_grid():
    """Render grid of equipped weapons and armor in Skills tab right pane."""
    console.log("[RENDER WEAPONS] render_equipped_attack_grid() called")
    
    if INVENTORY_MANAGER is None:
        console.log("[RENDER WEAPONS] INVENTORY_MANAGER is None, returning")
        return
    
    # Get equipped WEAPONS only (not armor) from inventory
    equipped_items = []
    for item in INVENTORY_MANAGER.items:
        category = item.get("category", "")
        # Only show weapons, not armor or other equipment (case-insensitive)
        is_weapon = category.lower() in ["weapons", "weapon"]
        if item.get("equipped") and is_weapon:
            equipped_items.append(item)
            console.log(f"[RENDER WEAPONS] Found equipped weapon: {item.get('name')} (category={category})")
    
    console.log(f"[RENDER WEAPONS] Total equipped weapons: {len(equipped_items)}")
    
    # Find or create container in right pane
    weapons_section = get_element("weapons-grid")
    if weapons_section is None:
        console.log("[RENDER WEAPONS] ERROR: weapons-grid container not found")
        return
    
    # Clear existing weapon rows (but NOT the empty state row)
    # Remove all rows except the empty state row
    rows_to_remove = []
    for row in weapons_section.querySelectorAll("tr"):
        if row.id != "weapons-empty-state":
            rows_to_remove.append(row)
    for row in rows_to_remove:
        row.remove()
    
    if not equipped_items:
        empty_state = get_element("weapons-empty-state")
        if empty_state:
            empty_state.style.display = "table-row"
        return
    
    # Hide empty state
    empty_state = get_element("weapons-empty-state")
    if empty_state:
        empty_state.style.display = "none"
    
    # Build table rows (weapons_section is the tbody)
    for item in equipped_items:
        console.log(f"[RENDER WEAPONS] Building row for: {item.get('name')}")
        try:
            tr = document.createElement("tr")
            
            # Column 1: Weapon name
            name_td = document.createElement("td")
            name_td.textContent = item.get("name", "Unknown")
            tr.appendChild(name_td)
            
            # Column 2: To Hit bonus (with styled tooltip)
            to_hit_td = document.createElement("td")
            
            # Calculate weapon to-hit and breakdown for tooltip
            level = get_numeric_value("level", 1)
            proficiency = compute_proficiency(level)
            item_name = (item.get("name") or "").lower()
            ranged_keywords = ["bow", "crossbow", "ranged"]
            is_ranged = any(kw in item_name for kw in ranged_keywords)
            ability_key = "dex" if is_ranged else "str"
            ability_score = get_numeric_value(f"{ability_key}-score", 10)
            ability_mod = ability_modifier(ability_score)
            weapon_bonus = 0
            enriched = _enrich_weapon_item(item)
            weapon_bonus = enriched.get("bonus", 0) or 0
            if not weapon_bonus:
                match = re.search(r'\+(\d+)', item.get("name", ""))
                if match:
                    weapon_bonus = int(match.group(1))
            
            # Calculate to-hit value
            to_hit = calculate_weapon_tohit(item)
            to_hit_bonus_text = format_bonus(to_hit)
            
            # Generate tooltip using WeaponToHitValue entity
            tooltip_html = ""
            if WeaponToHitValue:
                try:
                    w2h = WeaponToHitValue(
                        weapon_name=item.get("name", ""),
                        ability=ability_key,
                        ability_mod=ability_mod,
                        proficiency=proficiency,
                        weapon_bonus=weapon_bonus
                    )
                    tooltip_html = w2h.generate_tooltip_html()
                except Exception as e:
                    console.log(f"[RENDER WEAPONS] Error creating tooltip for {item.get('name')}: {e}")
            else:
                # Fallback text tooltip
                ability_name = "DEX" if is_ranged else "STR"
                bonus_text = f" + {weapon_bonus}" if weapon_bonus > 0 else ""
                tooltip = f"{ability_mod:+d} ({ability_name}) + {proficiency:+d} (Prof){bonus_text}"
                # Create simple tooltip without styling
                tooltip_html = f'<div class="stat-tooltip"><div class="tooltip-row"><span class="tooltip-label">To Hit</span><span class="tooltip-value">{tooltip}</span></div></div>'
            
            # Set innerHTML with value + tooltip (matching saves pattern)
            to_hit_td.innerHTML = f'<span class="stat-value">{to_hit_bonus_text}{tooltip_html}</span>'
            tr.appendChild(to_hit_td)
            
            # Column 3: Damage - check notes JSON and equipment library for weapon properties and bonus
            dmg_td = document.createElement("td")
            # Enrich item with any missing weapon metadata from notes/ library
            enriched_item = _enrich_weapon_item(item)
            dmg = enriched_item.get("damage", "")
            dmg_type = enriched_item.get("damage_type", "")
            dmg_bonus = enriched_item.get("bonus", 0) or item.get("bonus", 0)
            
            # Notes fallback (already handled by _enrich_weapon_item) - keep compatibility
            # if needed, additional parsing could go here
            
            # If still no bonus, check weapon name for "+X" pattern (handles "+1 Mace" or "Sword +1")
            if not dmg_bonus or dmg_bonus == 0:
                match = re.search(r'\+(\d+)', item.get("name", ""))
                if match:
                    dmg_bonus = int(match.group(1))
            
            dmg_text = dmg
            if dmg_text and dmg_type:
                dmg_text = f"{dmg_text} {dmg_type}"
            if dmg_bonus and dmg_bonus > 0 and dmg_text:
                dmg_text = f"{dmg_text} +{dmg_bonus}"
            dmg_td.textContent = dmg_text if dmg_text else "—"
            tr.appendChild(dmg_td)
            
            # Column 4: Range - prefer enriched value
            range_td = document.createElement("td")
            range_text = enriched_item.get("range_text", "") or enriched_item.get("range", "")
            range_td.textContent = range_text if range_text else "—"
            tr.appendChild(range_td)
            
            # Column 5: Properties - prefer enriched weapon_properties
            prop_td = document.createElement("td")
            props = enriched_item.get("weapon_properties", "") or enriched_item.get("properties", "")
            # Convert list to string if needed
            if isinstance(props, list):
                props = ", ".join(str(p) for p in props)
            prop_td.textContent = props if props else "—"
            tr.appendChild(prop_td)
            
            weapons_section.appendChild(tr)
            console.log(f"[RENDER WEAPONS] Successfully added row for: {item.get('name')}")
        except Exception as e:
            console.log(f"[RENDER WEAPONS] ERROR rendering {item.get('name')}: {e}")


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
        
        # Left section: Item name and summary
        leftDiv = document.createElement("div")
        leftDiv.style.display = "flex"
        leftDiv.style.flexDirection = "column"
        leftDiv.style.gap = "0.25rem"
        
        nameDiv = document.createElement("div")
        nameDiv.style.fontWeight = "600"
        nameDiv.style.color = "#cbd5f5"
        nameDiv.textContent = f"{item.get('name', 'Unknown')} (x{int(item.get('qty', 1))})"
        
        costWeightDiv = document.createElement("div")
        costWeightDiv.style.fontSize = "0.85rem"
        costWeightDiv.style.color = "#94a3b8"
        costWeightDiv.textContent = f"{format_money(item.get('cost', 0))} | {format_weight(item.get('weight', 0))}"
        
        leftDiv.appendChild(nameDiv)
        leftDiv.appendChild(costWeightDiv)
        
        # Right section: Equipped checkbox (only for armor/weapons)
        rightDiv = document.createElement("div")
        rightDiv.style.display = "flex"
        rightDiv.style.alignItems = "center"
        rightDiv.style.gap = "0.5rem"
        
        if is_equipable(item):
            equippedLabel = document.createElement("label")
            equippedLabel.style.display = "flex"
            equippedLabel.style.alignItems = "center"
            equippedLabel.style.gap = "0.5rem"
            equippedLabel.style.cursor = "pointer"
            equippedLabel.style.userSelect = "none"
            equippedLabel.style.color = "#94a3b8"
            
            equippedCheckbox = document.createElement("input")
            equippedCheckbox.type = "checkbox"
            equippedCheckbox.className = "equipment-equipped-check"
            equippedCheckbox.checked = bool(item.get("equipped", False))
            equippedCheckbox.style.cursor = "pointer"
            
            equippedText = document.createElement("span")
            equippedText.textContent = "Equipped"
            equippedText.style.fontSize = "0.85rem"
            
            equippedLabel.appendChild(equippedCheckbox)
            equippedLabel.appendChild(equippedText)
            rightDiv.appendChild(equippedLabel)
            
            # Store reference to checkbox for event handling
            item["_checkbox_element"] = equippedCheckbox
        
        summary.appendChild(leftDiv)
        summary.appendChild(rightDiv)
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
        
        # Handle equipped checkbox
        equipped_check = row.querySelector(".equipment-equipped-check")
        if equipped_check is not None:
            proxy_equip = create_proxy(lambda e, iid=item_id: handle_equipment_equipped(e, iid))
            equipped_check.addEventListener("change", proxy_equip)
            _EVENT_PROXIES.append(proxy_equip)


def handle_equipment_equipped(event=None, item_id: str = None):
    """Handle when an item's equipped checkbox is toggled."""
    if INVENTORY_MANAGER is None or item_id is None:
        return
    
    # Find item in inventory and update equipped flag
    for item in INVENTORY_MANAGER.items:
        if item.get("id") == item_id:
            checkbox = event.target if event else None
            if checkbox:
                item["equipped"] = bool(checkbox.checked)
            console.log(f"DEBUG: Equipment {item.get('name')} equipped={item.get('equipped')}")
            break
    
    # Recalculate AC
    update_calculations()
    
    # Re-render attack grid
    render_equipped_attack_grid()
    
    # Auto-save
def handle_equipment_input(event=None, item_id: str = None):
    """Handle when an equipment field is edited."""
    if INVENTORY_MANAGER is None or item_id is None or event is None:
        return
    
    field_name = event.target.getAttribute("data-item-field")
    new_value = event.target.value
    
    # Find item and update field
    for item in INVENTORY_MANAGER.items:
        if item.get("id") == item_id:
            if field_name == "qty":
                item[field_name] = int(new_value) if new_value else 0
            elif field_name in ["cost", "weight"]:
                item[field_name] = float(new_value) if new_value else 0.0
            else:
                item[field_name] = new_value
            break
    
    # Update totals display
    update_equipment_totals()
    
    # Auto-save
def remove_equipment_item(item_id: str):
    """Remove an item from inventory."""
    if INVENTORY_MANAGER is None or item_id is None:
        return
    
    # Remove item from inventory
    INVENTORY_MANAGER.items = [item for item in INVENTORY_MANAGER.items if item.get("id") != item_id]
    
    # Re-render table
    render_inventory()
    
    # Recalculate AC and update display
    update_calculations()
    
    # Re-render attack grid
    render_equipped_attack_grid()
    
    # Auto-save
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
    console.log("DEBUG: add_equipment_item() called")
    pass


def add_custom_item(_event=None):
    """Show the custom item modal"""
    console.log("DEBUG: add_custom_item() called")
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
    console.log("DEBUG: fetch_custom_item_from_url_handler() called")
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
    console.log("DEBUG: clear_equipment_list() called")
    if INVENTORY_MANAGER is None or len(INVENTORY_MANAGER.items) == 0:
        return
    INVENTORY_MANAGER.items = []
    INVENTORY_MANAGER.render_inventory()
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
    EQUIPMENT_LIBRARY_STATE["equipment"] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in _get_builtin_equipment_list()]


def _get_builtin_equipment_list():
    """Return builtin equipment as a list of objects (Weapon/Armor/Equipment/etc)."""
    return [
        # Melee Weapons (common PHB weapons)
        Weapon("Mace", damage="1d6", damage_type="bludgeoning", cost="5 gp", weight="4 lb."),
        Weapon("Longsword", damage="1d8", damage_type="slashing", cost="15 gp", weight="3 lb."),
        Weapon("Shortsword", damage="1d6", damage_type="piercing", cost="10 gp", weight="2 lb."),
        Weapon("Rapier", damage="1d8", damage_type="piercing", cost="25 gp", weight="2 lb.", properties="finesse"),
        Weapon("Dagger", damage="1d4", damage_type="piercing", cost="2 gp", weight="1 lb.", properties="finesse, light"),
        Weapon("Greataxe", damage="1d12", damage_type="slashing", cost="30 gp", weight="7 lb."),
        Weapon("Greatsword", damage="2d6", damage_type="slashing", cost="50 gp", weight="6 lb."),
        Weapon("Warhammer", damage="1d8", damage_type="bludgeoning", cost="15 gp", weight="2 lb."),
        Weapon("Morningstar", damage="1d8", damage_type="piercing", cost="15 gp", weight="4 lb."),
        Weapon("Pike", damage="1d10", damage_type="piercing", cost="5 gp", weight="18 lb."),
        Weapon("Spear", damage="1d6", damage_type="piercing", cost="1 gp", weight="3 lb.", properties="finesse, versatile"),
        Weapon("Club", damage="1d4", damage_type="bludgeoning", cost="0.1 gp", weight="2 lb."),
        Weapon("Quarterstaff", damage="1d6", damage_type="bludgeoning", cost="0.2 gp", weight="4 lb.", properties="versatile"),
        Weapon("Falchion", damage="1d8", damage_type="slashing", cost="20 gp", weight="4 lb."),
        
        # Ranged Weapons
        Weapon("Longbow", damage="1d8", damage_type="piercing", range_text="150/600 ft.", cost="50 gp", weight="3 lb.", properties="ammunition, heavy, two-handed"),
        Weapon("Shortbow", damage="1d6", damage_type="piercing", range_text="80/320 ft.", cost="25 gp", weight="2 lb.", properties="ammunition, two-handed"),
        Weapon("Crossbow, light", damage="1d8", damage_type="piercing", range_text="80/320 ft.", cost="25 gp", weight="5 lb.", properties="ammunition, loading"),
        Weapon("Crossbow, heavy", damage="1d10", damage_type="piercing", range_text="100/400 ft.", cost="50 gp", weight="18 lb.", properties="ammunition, heavy, loading, two-handed"),
        Weapon("Sling", damage="1d4", damage_type="bludgeoning", range_text="30/120 ft.", cost="0.1 gp", weight="0 lb.", properties="ammunition"),
        
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
    ]


def _find_builtin_equipment_match(name: str):
    """Find a builtin equipment dict matching name using token/set or substring heuristics."""
    try:
        import re
        name_norm = (name or "").lower().replace(',', '').strip()
        name_tokens = set(re.findall(r"\w+", name_norm))
        for itm in _get_builtin_equipment_list():
            itm_dict = itm.to_dict() if hasattr(itm, 'to_dict') else itm
            eq_name_raw = itm_dict.get('name', '')
            eq_name = eq_name_raw.lower().replace(',', '').strip()
            eq_tokens = set(re.findall(r"\w+", eq_name))
            match = False
            if name_tokens and eq_tokens:
                if name_tokens == eq_tokens or name_tokens.issubset(eq_tokens) or eq_tokens.issubset(name_tokens):
                    match = True
            if not match:
                if name_norm in eq_name or eq_name in name_norm:
                    match = True
            if match:
                return itm_dict
    except Exception:
        pass
    return None


def load_equipment_library(_event=None):
    """Load equipment library from cached data or Open5e API"""
    console.log("DEBUG: load_equipment_library() called")
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
        
        # Handle both custom format (damage, damage_type) and Open5e format (damage_dice)
        damage = item.get("damage", "") or item.get("damage_dice", "")
        damage_type = item.get("damage_type", "")
        
        # Handle both custom format (range) and Open5e format (properties array with range in it)
        range_text = item.get("range", "")
        if not range_text:
            # Try to extract range from properties array
            props = item.get("properties", [])
            if isinstance(props, list):
                for prop in props:
                    if isinstance(prop, str) and ("range" in prop.lower() or "ammunition" in prop.lower()):
                        # Extract range info from property
                        if "(" in prop and ")" in prop:
                            range_text = prop[prop.find("(")+1:prop.find(")")]
                        else:
                            range_text = prop
                        break
        
        # Format properties
        properties = item.get("properties", "")
        if isinstance(properties, list):
            # Convert list to comma-separated string
            properties = ", ".join(str(p) for p in properties if p)
        
        ac_string = item.get("ac", "") or item.get("ac_string", "")
        armor_class = item.get("armor_class", "")
        
        # If data not found in direct properties, check the notes JSON (from Weapon.to_dict())
        if not damage or not damage_type or not range_text:
            try:
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    notes_data = json.loads(notes_str)
                    console.log(f"DEBUG build_equipment_card: {name} - parsed notes: {notes_data}")
                    if not damage and "damage" in notes_data:
                        damage = notes_data["damage"]
                    if not damage_type and "damage_type" in notes_data:
                        damage_type = notes_data["damage_type"]
                    if not range_text and "range" in notes_data:
                        range_text = notes_data["range"]
                    if not properties and "properties" in notes_data:
                        props = notes_data["properties"]
                        if isinstance(props, list):
                            properties = ", ".join(str(p) for p in props if p)
                        else:
                            properties = props
                    console.log(f"DEBUG build_equipment_card: {name} - extracted damage={damage}, type={damage_type}, range={range_text}")
            except Exception as e:
                console.error(f"DEBUG build_equipment_card: Failed to parse notes for {name}: {e}")
                pass
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
    console.log("Export scheduled")
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
    console.log("PySheet: Export scheduled")


def submit_open5e_item(name: str, cost: str = "", weight: str = "", damage: str = "", damage_type: str = "", 
                       range_text: str = "", properties: str = "", ac_string: str = "", armor_class: str = ""):
    """Add an Open5e item to inventory with all properties"""
    global INVENTORY_MANAGER
    if INVENTORY_MANAGER is None:
        if InventoryManager is None:
            console.warn("PySheet: INVENTORY_MANAGER is not initialized; cannot add Open5e item")
            return
        try:
            INVENTORY_MANAGER = InventoryManager()
            console.log("DEBUG: submit_open5e_item created INVENTORY_MANAGER on-demand")
        except Exception as exc:
            console.warn(f"PySheet: Unable to create INVENTORY_MANAGER: {exc}")
            return
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
    console.log("DEBUG: submit_open5e_item calling schedule_auto_export()")
    console.log("DEBUG: submit_open5e_item completed schedule_auto_export()")


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
        1: ["bless", "cure-wounds"],
        3: ["lesser-restoration", "spiritual-weapon"],
        5: ["beacon-of-hope", "revivify"],
        7: ["death-ward", "guardian-of-faith"],
        9: ["mass-cure-wounds", "raise-dead"],
    },
    "knowledge": {
        1: ["detect-magic", "bless"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "insect-plague"],
    },
    "tempest": {
        1: ["faerie-fire", "shatter"],
        3: ["hold-person", "confusion"],
        5: ["insect-plague", "mass-cure-wounds"],
    },
    "trickery": {
        1: ["faerie-fire", "vicious-mockery"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "insect-plague"],
    },
    "war": {
        1: ["bless", "guiding-bolt"],
        3: ["hold-person", "shatter"],
        5: ["insect-plague", "raise-dead"],
    },
    "light": {
        1: ["guiding-bolt", "sacred-flame"],
        3: ["shatter", "hold-person"],
        5: ["insect-plague", "mass-cure-wounds"],
    },
    "nature": {
        1: ["faerie-fire", "detect-magic"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "insect-plague"],
    },
    "forge": {
        1: ["detect-magic", "bless"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "insect-plague"],
    },
    "grave": {
        1: ["bless", "detect-magic"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "raise-dead"],
    },
    "death": {
        1: ["bless", "detect-magic"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "raise-dead"],
    },
    "arcana": {
        1: ["detect-magic", "bless"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "insect-plague"],
    },
    "city": {
        1: ["detect-magic", "faerie-fire"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "insect-plague"],
    },
    "order": {
        1: ["bless", "guiding-bolt"],
        3: ["hold-person", "shatter"],
        5: ["confusion", "insect-plague"],
    },
    "peace": {
        1: ["bless", "detect-magic"],
        3: ["healing-word", "prayer-of-healing"],
        5: ["mass-cure-wounds", "raise-dead"],
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
    console.log(f"DEBUG: get_domain_bonus_spells - domain_name='{domain_name}', domain_key='{domain_key}', spells_by_level={spells_by_level}")
    
    bonus_spells = []
    for level in sorted(spells_by_level.keys()):
        if level <= current_level:
            bonus_spells.extend(spells_by_level[level])
            console.log(f"DEBUG: get_domain_bonus_spells - adding spells for level {level}: {spells_by_level[level]}")
    
    console.log(f"DEBUG: get_domain_bonus_spells - returning {len(bonus_spells)} total spells: {bonus_spells}")
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
    console.log("DEBUG: add_feat() called")
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
            console.log(f"DEBUG: domain input event fired! New value: {value}, SPELLCASTING_MANAGER={SPELLCASTING_MANAGER is not None}")
            _ensure_domain_spells_in_spellbook(reason="domain_change")
        elif target_id == "level":
            # Ensure newly unlocked domain spells are added when leveling up
            _ensure_domain_spells_in_spellbook(reason="level_change")
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

def initialize_module_references():
    """Lazy load module references for export and equipment management."""
    global _EXPORT_MODULE_REF, _EQUIPMENT_MODULE_REF
    
    if _EXPORT_MODULE_REF is None:
        _EXPORT_MODULE_REF = sys.modules.get('export_management')
        if not _EXPORT_MODULE_REF and export_management is not None:
            _EXPORT_MODULE_REF = export_management
        if _EXPORT_MODULE_REF:
            # Verify the module has the functions we need
            if not hasattr(_EXPORT_MODULE_REF, 'schedule_auto_export'):
                _EXPORT_MODULE_REF = None
    
    if _EQUIPMENT_MODULE_REF is None:
        _EQUIPMENT_MODULE_REF = sys.modules.get('equipment_management')

def trigger_auto_export(source: str = "auto"):
    """Trigger auto-export with fallback logic. Tries direct import first, then module reference."""
    try:
        # Try direct import first
        if export_management is not None:
            export_management.schedule_auto_export()
            return True
    except Exception as e:
        console.warn(f"DEBUG: Direct export_management call failed ({source}): {e}")
    
    try:
        # Fallback: try module reference
        initialize_module_references()
        if _EXPORT_MODULE_REF is not None and hasattr(_EXPORT_MODULE_REF, 'schedule_auto_export'):
            _EXPORT_MODULE_REF.schedule_auto_export()
            return True
    except Exception as e:
        console.error(f"ERROR in trigger_auto_export ({source}): {e}")
    
    return False

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
    trigger_auto_export("handle_adjust_button")

def handle_currency_button(event):
    """Handle currency adjustment buttons (±10, ±100)"""
    try:
        button = event.target
        currency_type = button.getAttribute("data-currency")
        amount_str = button.getAttribute("data-amount")
        
        if not currency_type or not amount_str:
            return
        
        # Get the input element for this currency type
        input_elem = get_element(f"currency-{currency_type}")
        if not input_elem:
            return
        
        # Get current value and amount adjustment
        current = get_numeric_value(f"currency-{currency_type}", 0)
        amount = int(amount_str)
        new_value = max(0, current + amount)  # Don't allow negative currency
        
        # Set the new value
        set_form_value(f"currency-{currency_type}", str(new_value))
        update_calculations()
        trigger_auto_export("handle_currency_button")
    except Exception as e:
        console.error(f"ERROR in handle_currency_button: {e}")

def register_event_listeners():
    console.log("[DEBUG] register_event_listeners() called - starting event registration")
    # In test environments document is often a lightweight mock; be defensive
    if not hasattr(document, 'querySelectorAll'):
        console.warn("[DEBUG] document.querySelectorAll not available - skipping event registration in non-PyScript environment")
        return

    nodes = document.querySelectorAll("[data-character-input]")
    console.log(f"[DEBUG] Found {len(nodes)} character input elements")
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

    # Register currency button handlers
    currency_buttons = document.querySelectorAll(".currency-btn")
    for button in currency_buttons:
        proxy_currency = create_proxy(handle_currency_button)
        button.addEventListener("click", proxy_currency)
        _EVENT_PROXIES.append(proxy_currency)

    import_input = get_element("import-file")
    if import_input is not None:
        console.log("[DEBUG] import-file element found, registering event listener")
        console.log(f"[DEBUG] import-file element tag: {import_input.tagName}, type: {getattr(import_input, 'type', 'N/A')}")
        
        # Create a Python wrapper function that catches the event and calls handle_import
        def import_event_wrapper(evt):
            try:
                console.log("[DEBUG] import_event_wrapper called!")
                console.log(f"[DEBUG] event type: {evt.type}, target: {evt.target}")
                handle_import(evt)
            except Exception as e:
                console.error(f"[DEBUG] import_event_wrapper error: {e}")
                import traceback
                traceback.print_exc()
        
        # Create proxy from wrapper
        proxy_import = create_proxy(import_event_wrapper)
        
        # Register on change event
        import_input.addEventListener("change", proxy_import)
        console.log("[DEBUG] 'change' event listener registered via wrapper")
        _EVENT_PROXIES.append(proxy_import)
        
        console.log("[DEBUG] All import event listeners registered successfully")
    else:
        console.warn("[DEBUG] import-file element NOT FOUND in DOM")

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
    console.log("[DEBUG] load_initial_state() called")
    # Be defensive: in tests window may be a minimal mock without localStorage
    stored = None
    if hasattr(window, 'localStorage') and hasattr(window.localStorage, 'getItem'):
        try:
            stored = window.localStorage.getItem(LOCAL_STORAGE_KEY)
        except Exception as exc:
            console.warn(f"DEBUG: window.localStorage.getItem raised an exception: {exc}")

    if stored:
        try:
            data = json.loads(stored)
            console.log("[DEBUG] Loaded character from localStorage")
            populate_form(data)
            # Populate domain spells after character is fully loaded
            if SPELL_LIBRARY_STATE.get("loaded"):
                console.log("DEBUG: Character loaded from storage - calling _populate_domain_spells_on_load")
                _populate_domain_spells_on_load()
            return
        except Exception as exc:
            console.warn(f"PySheet: unable to parse stored character, using defaults ({exc})")
    console.log("[DEBUG] No stored character, using defaults")
    populate_form(clone_default_state())


# Spell library safety: ensure fallback data is seeded if map is empty
def _ensure_spell_library_seeded(reason: str = "unspecified"):
    if SPELL_LIBRARY_STATE.get("spell_map"):
        return
    console.log(f"DEBUG: _ensure_spell_library_seeded(reason={reason}) - seeding fallback spells")
    set_spell_library_data(LOCAL_SPELLS_FALLBACK)
    SPELL_LIBRARY_STATE["loaded"] = True


# Auto-populate domain spells if domain is set and spell library is loaded
def _ensure_domain_spells_in_spellbook(reason: str = "unspecified"):
    """Ensure all domain bonus spells up to current level are prepared."""
    global _DOMAIN_SPELL_SYNCING
    if _DOMAIN_SPELL_SYNCING:
        return
    _DOMAIN_SPELL_SYNCING = True
    console.log(f"DEBUG: _ensure_domain_spells_in_spellbook(reason={reason})")
    _ensure_spell_library_seeded(reason="domain_sync")
    if SPELLCASTING_MANAGER is None:
        console.warn("DEBUG: _ensure_domain_spells_in_spellbook - SPELLCASTING_MANAGER is None, skipping")
        console.log(f"DEBUG: SpellcastingManager class={SpellcastingManager}")
        _DOMAIN_SPELL_SYNCING = False
        return

    domain = get_text_value("domain")
    loaded = SPELL_LIBRARY_STATE.get("loaded")
    level = get_numeric_value("level", 1)
    console.log(f"DEBUG: _ensure_domain_spells_in_spellbook - domain={domain}, level={level}, loaded={loaded}")

    if not domain or not loaded:
        console.log(f"DEBUG: _ensure_domain_spells_in_spellbook - skipped (domain={domain}, loaded={loaded})")
        return

    domain_spells = get_domain_bonus_spells(domain, level)
    console.log(f"DEBUG: _ensure_domain_spells_in_spellbook - spells={domain_spells}")

    prepared_before = len(SPELLCASTING_MANAGER.get_prepared_slug_set())
    added_count = 0
    flagged_count = 0
    for spell_slug in domain_spells:
        if not SPELLCASTING_MANAGER.is_spell_prepared(spell_slug):
            console.log(f"DEBUG: Adding domain spell {spell_slug}")
            SPELLCASTING_MANAGER.add_spell(spell_slug, is_domain_bonus=True)
            added_count += 1
        else:
            # Ensure already-prepared domain spells are flagged as domain bonus
            updated = False
            for entry in getattr(SPELLCASTING_MANAGER, "prepared", []):
                if entry.get("slug") == spell_slug and not entry.get("is_domain_bonus"):
                    entry["is_domain_bonus"] = True
                    updated = True
                    flagged_count += 1
                    console.log(f"DEBUG: Flagged existing spell as domain bonus: {spell_slug}")
                    break
            if not updated:
                console.log(f"DEBUG: Domain spell {spell_slug} already prepared and flagged")
    prepared_after = len(SPELLCASTING_MANAGER.get_prepared_slug_set())
    console.log(f"DEBUG: Domain spells added: {added_count} new spells, flagged={flagged_count} existing (before={prepared_before}, after={prepared_after}, total in list={len(domain_spells)})")
    if added_count > 0 or flagged_count > 0:
        SPELLCASTING_MANAGER.render_spellbook()
        update_calculations()
    _DOMAIN_SPELL_SYNCING = False


def _populate_domain_spells_on_load():
    # Backward-compatible wrapper used during initialization
    _ensure_domain_spells_in_spellbook(reason="initial_load")


# Only run module initialization if we're in a PyScript environment (document is not None)
if document is not None:
    console.log("[DEBUG] === PySheet initialization starting ===")
    console.log("[DEBUG] Calling register_event_listeners()")
    register_event_listeners()
    console.log("[DEBUG] Calling load_initial_state()")
    load_initial_state()
    console.log("[DEBUG] Calling update_calculations()")
    update_calculations()
    
    # Initialize weapons and armor managers

    # Manager pre-load helper is defined at module level (_ensure_manager_loaded)
    # Use that helper to ensure the manager is available before initialization.
    try:
        # Ensure weapons manager is available
        initialize_weapons_manager = _ensure_manager_loaded(
            "weapons_manager",
            "initialize_weapons_manager",
            "http://localhost:8080/assets/py/weapons_manager.py",
        )

        # Ensure armor manager is available (allow HTTP fallback)
        initialize_armor_manager = _ensure_manager_loaded(
            "armor_manager",
            "initialize_armor_manager",
            "http://localhost:8080/assets/py/armor_manager.py",
        )

        console.log("[DEBUG] Initializing weapons and armor managers")
        # Get character stats for managers
        level = get_numeric_value("level", 1)
        char_stats = {
            "str": get_numeric_value("str", 10),
            "dex": get_numeric_value("dex", 10),
            "proficiency": compute_proficiency(level)
        }
        weapons_mgr = initialize_weapons_manager(INVENTORY_MANAGER, char_stats)
        weapons_mgr.render()
        armor_mgr = initialize_armor_manager(INVENTORY_MANAGER, char_stats)
        armor_mgr.render()
        console.log("[DEBUG] Weapons and armor managers initialized and rendered")
    except Exception as e:
        console.error(f"[DEBUG] Error initializing managers: {e}")
        # Fallback to old method
        console.log("[DEBUG] Falling back to render_equipped_weapons()")
        render_equipped_weapons()
    
    # Populate spell class filter with fallback spells on startup
    console.log("[DEBUG] Populating spell class filter")
    populate_spell_class_filter(SPELL_LIBRARY_STATE.get("spells"))
    console.log("[DEBUG] === PySheet initialization complete ===")


# Auto-load weapon library
async def _auto_load_weapons():
    console.log("DEBUG: _auto_load_weapons() started")
    await load_weapon_library()
    console.log("DEBUG: _auto_load_weapons() - weapon library loaded")
    # Also load the equipment library into Python (reads from localStorage or fallback)
    try:
        console.log("DEBUG: _auto_load_weapons() - loading equipment library into Python")
        load_equipment_library()
        console.log(f"DEBUG: _auto_load_weapons() - equipment library size = {len(EQUIPMENT_LIBRARY_STATE.get('equipment', []))}")
        # Re-render the weapons grid so any enriched values are applied
        console.log("DEBUG: _auto_load_weapons() - re-rendering equipped attack grid to apply enrichment")
        render_equipped_attack_grid()
    except Exception as e:
        console.warn(f"DEBUG: _auto_load_weapons() - equipment load or render failed: {e}")
    # Give SPELLCASTING_MANAGER a chance to fully initialize
    await asyncio.sleep(0.1)
    console.log("DEBUG: _auto_load_weapons() - calling _populate_domain_spells_on_load")
    _populate_domain_spells_on_load()
    console.log("DEBUG: _auto_load_weapons() completed")

# Only start async tasks if we're in a PyScript environment
if document is not None:
    try:
        console.log("DEBUG: Creating async task for _auto_load_weapons")
        # Only create the coroutine and schedule it if an event loop is running.
        # Creating the coroutine first and then calling create_task() can raise
        # RuntimeError and leave the coroutine un-awaited, which yields the
        # "coroutine was never awaited" RuntimeWarning. Use get_running_loop()
        # to check for an active loop before creating/scheduling the coroutine.
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            console.warn("DEBUG: No running event loop; skipping _auto_load_weapons scheduling")
        else:
            loop.create_task(_auto_load_weapons())
    except Exception as e:
        console.warn(f"DEBUG: Could not schedule _auto_load_weapons: {e}")
