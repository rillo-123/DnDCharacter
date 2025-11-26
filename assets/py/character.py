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

from js import Blob, URL, console, document, window
try:
    from pyodide import JsException
except ImportError:  # Pyodide >=0.23 exposes JsException under pyodide.ffi
    from pyodide.ffi import JsException  # type: ignore
from pyodide.ffi import create_proxy
from pyodide.http import open_url, pyfetch
from types import ModuleType

MODULE_DIR = (
    Path(__file__).resolve().parent
    if "__file__" in globals()
    else (Path.cwd() / "assets" / "py")
)
if str(MODULE_DIR) not in sys.path:
    sys.path.append(str(MODULE_DIR))

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

SUPPORTED_SPELL_CLASSES = set(CharacterFactory.supported_classes())

WEAPON_LIBRARY_STATE = {
    "loading": False,
    "weapons": [],
    "weapon_map": {},
}

# Equipment library state - will be fetched from Open5e
EQUIPMENT_LIBRARY_STATE = {
    "loading": False,
    "equipment": [],
    "equipment_map": {},
}

_EVENT_PROXIES: list = []
_EQUIPMENT_RESULT_PROXY = None  # Track the current equipment results listener to remove it


AUTO_EXPORT_DELAY_MS = 2000
AUTO_EXPORT_MAX_EVENTS = 15
_AUTO_EXPORT_TIMER_ID: int | None = None
_AUTO_EXPORT_PROXY = None
_AUTO_EXPORT_SUPPRESS = False
_LAST_AUTO_EXPORT_SNAPSHOT = ""
_LAST_AUTO_EXPORT_DATE = ""
_AUTO_EXPORT_EVENT_COUNT = 0
_AUTO_EXPORT_FILE_HANDLE = None
_AUTO_EXPORT_DISABLED = False
_AUTO_EXPORT_SUPPORT_WARNED = False
_AUTO_EXPORT_DIRECTORY_HANDLE = None
_AUTO_EXPORT_LAST_FILENAME = ""
_AUTO_EXPORT_SETUP_PROMPTED = False


def _normalize_export_basename(candidate: str | None) -> str:
    if not candidate:
        candidate = "character"
    cleaned = re.sub(r"[^A-Za-z0-9]+", "_", candidate.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return "character"
    return cleaned


def _build_export_filename(data: dict, *, now: datetime | None = None) -> str:
    if now is None:
        now = datetime.now()
    raw_name = (data.get("identity", {}).get("name") or "character").strip()
    base_name = _normalize_export_basename(raw_name)
    
    # Get class
    class_name = (data.get("identity", {}).get("class") or "unknown").strip()
    class_part = _normalize_export_basename(class_name)
    
    # Get level
    level_value = 0
    try:
        level_value = int(data.get("level", 0))
    except (TypeError, ValueError):
        level_value = 0
    if level_value <= 0:
        level_value = 0
    
    # Format: <character_name>_<class>_lvl<level_number>_YYYYMMDD_HHMM.json
    timestamp = now.strftime("%Y%m%d_%H%M")
    return f"{base_name}_{class_part}_lvl{level_value}_{timestamp}.json"


# ===================================================================
# Export Directory Pruning
# ===================================================================

MAX_EXPORTS_PER_CHARACTER = 20  # Keep last N exports per character
EXPORT_PRUNE_DAYS = 30  # Remove exports older than this many days


def _extract_character_name_from_filename(filename: str) -> str:
    """Extract character name from export filename.
    
    Handles formats like:
    - enwer_cleric_lvl9_20251120_1234.json (new format)
    - enwer_20251120_lvl_9.json (old format)
    - rillobaby.json
    - character (1).json
    """
    if not filename or not filename.endswith(".json"):
        return ""
    
    # Remove .json
    name_part = filename[:-5]
    
    import re
    # Try new format: <name>_<class>_lvl<level>_YYYYMMDD_HHMM
    match = re.match(r'^(.+?)_[a-z]+_lvl\d+_\d{8}_\d{4}$', name_part)
    if match:
        return match.group(1).lower()
    
    # Try old format: <name>_YYYYMMDD_lvl_<level>
    cleaned = re.sub(r'_\d{8}(_lvl_\d+)?$', '', name_part)
    # Try old format with time: <name>_YYYYMMDD_HHMM
    cleaned = re.sub(r'_\d{8}_\d{4}$', '', cleaned)
    # Remove (N) suffix from duplicates
    cleaned = re.sub(r'\s*\(\d+\)$', '', cleaned)
    
    return cleaned.strip().lower()


def prune_old_exports(directory_handle, max_keep: int = MAX_EXPORTS_PER_CHARACTER):
    """Remove old exports, keeping only the most recent per character.
    
    This is a browser-based version that attempts to prune from the
    directory. Note: Full file listing/deletion may not be available
    in all browsers.
    """
    try:
        # Note: Full directory traversal isn't available in browser File System API
        # This would need backend support or browser extension
        LOGGER.info(f"Export pruning configured: keeping {max_keep} latest per character")
        return True
    except Exception as exc:
        LOGGER.warning(f"Could not prune exports: {exc}")
        return False


async def _prune_old_exports_from_directory(directory_handle):
    """Prune exports older than EXPORT_PRUNE_DAYS from the directory.
    
    Only works if directory_handle supports async iteration (desktop/Chrome).
    """
    if directory_handle is None:
        return
    
    try:
        import re
        cutoff_date = datetime.now() - timedelta(days=EXPORT_PRUNE_DAYS)
        pruned_count = 0
        
        # Attempt to iterate and delete old files
        async for entry in directory_handle.entries():
            if not entry.name.endswith(".json"):
                continue
            
            # Extract timestamp from filename (YYYYMMDD_HHMM format)
            match = re.search(r'_(\d{8})_(\d{4})\.json$', entry.name)
            if not match:
                continue
            
            date_str, time_str = match.groups()
            try:
                file_date = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M")
                if file_date < cutoff_date:
                    # Attempt to remove old file
                    await directory_handle.removeEntry(entry.name)
                    pruned_count += 1
                    LOGGER.info(f"Pruned old export: {entry.name}")
            except (ValueError, JsException):
                continue
        
        if pruned_count > 0:
            LOGGER.info(f"Pruned {pruned_count} exports older than {EXPORT_PRUNE_DAYS} days")
    
    except (AttributeError, JsException):
        # Directory iteration not supported in this browser
        pass
    except Exception as exc:
        LOGGER.warning(f"Error during export pruning: {exc}")


def estimate_export_cleanup():
    """Estimate storage savings from cleanup (browser localStorage only)."""
    try:
        # Get localStorage usage
        stored_logs = window.localStorage.getItem("pysheet_logs") or ""
        stored_spells = window.localStorage.getItem("pysheet_spells") or ""
        stored_chars = window.localStorage.getItem("pysheet_character") or ""
        
        total_size = len(stored_logs) + len(stored_spells) + len(stored_chars)
        
        # Estimate: each full export is ~2-5KB of JSON
        estimated_exports = total_size // 3000
        
        return {
            "total_bytes": total_size,
            "estimated_export_count": estimated_exports,
            "estimated_savings_kb": (estimated_exports * 3) // 1024 if estimated_exports > 20 else 0,
        }
    except Exception as exc:
        LOGGER.warning(f"Could not estimate cleanup: {exc}")
        return None


async def _ensure_directory_write_permission(handle) -> bool:
    if handle is None:
        return False
    query_permission = getattr(handle, "queryPermission", None)
    request_permission = getattr(handle, "requestPermission", None)
    if query_permission is None or request_permission is None:
        return True
    try:
        status = await query_permission({"mode": "readwrite"})
    except JsException as exc:
        console.warn(f"PySheet: directory permission query failed - {exc}")
        status = None
    if status == "granted":
        return True
    if status == "denied":
        return False
    try:
        status = await request_permission({"mode": "readwrite"})
    except JsException as exc:
        console.warn(f"PySheet: directory permission request failed - {exc}")
        return False
    return status == "granted"


def _ensure_auto_export_proxy():
    global _AUTO_EXPORT_PROXY
    if _AUTO_EXPORT_PROXY is None:
        def _auto_export_callback(*_args):
            global _AUTO_EXPORT_TIMER_ID
            _AUTO_EXPORT_TIMER_ID = None
            async def _run_auto_export():
                global _AUTO_EXPORT_EVENT_COUNT
                try:
                    await export_character(auto=True)
                except Exception as exc:
                    console.error(f"PySheet: auto-export failed - {exc}")
                finally:
                    _AUTO_EXPORT_EVENT_COUNT = 0

            try:
                loop = asyncio.get_running_loop()
                loop.create_task(_run_auto_export())
            except RuntimeError:
                asyncio.run(_run_auto_export())
        _AUTO_EXPORT_PROXY = create_proxy(_auto_export_callback)
        _EVENT_PROXIES.append(_AUTO_EXPORT_PROXY)
    return _AUTO_EXPORT_PROXY


def schedule_auto_export():
    global _AUTO_EXPORT_TIMER_ID, _AUTO_EXPORT_EVENT_COUNT
    if _AUTO_EXPORT_SUPPRESS:
        return
    
    _AUTO_EXPORT_EVENT_COUNT = min(_AUTO_EXPORT_EVENT_COUNT + 1, AUTO_EXPORT_MAX_EVENTS)
    
    # Always save to localStorage immediately to preserve data across page refreshes
    try:
        data = collect_character_data()
        window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
    except Exception as exc:
        console.warn(f"PySheet: failed to save to localStorage - {exc}")
    
    # Show recording indicator (red) - even if auto-export is disabled, show that we detected a change
    indicator = document.getElementById("saving-indicator")
    if indicator:
        indicator.classList.remove("saving", "fading")
        indicator.classList.add("recording")
    
    # If auto-export is disabled, don't actually schedule the export timer
    if _AUTO_EXPORT_DISABLED:
        console.log(f"DEBUG: Change detected but auto-export disabled. Recording indicator shown for UX.")
        return
    
    console.log(f"DEBUG: schedule_auto_export called! Event count: {_AUTO_EXPORT_EVENT_COUNT}")
    
    proxy = _ensure_auto_export_proxy()
    if _AUTO_EXPORT_TIMER_ID is not None:
        window.clearTimeout(_AUTO_EXPORT_TIMER_ID)
    remaining = AUTO_EXPORT_MAX_EVENTS - _AUTO_EXPORT_EVENT_COUNT
    interval = AUTO_EXPORT_DELAY_MS
    if remaining <= 0:
        interval = int(AUTO_EXPORT_DELAY_MS * 0.25)
    _AUTO_EXPORT_TIMER_ID = window.setTimeout(proxy, interval)


def _supports_persistent_auto_export() -> bool:
    return bool(
        hasattr(window, "showDirectoryPicker")
        or hasattr(window, "showSaveFilePicker")
    )


async def _ensure_auto_export_directory(auto_trigger: bool = True):
    global _AUTO_EXPORT_DIRECTORY_HANDLE, _AUTO_EXPORT_DISABLED
    if _AUTO_EXPORT_DIRECTORY_HANDLE is not None:
        return _AUTO_EXPORT_DIRECTORY_HANDLE
    if not hasattr(window, "showDirectoryPicker"):
        return None
    try:
        handle = await window.showDirectoryPicker()
    except JsException as exc:
        name = getattr(exc, "name", "")
        if name == "AbortError":
            # User cancelled - don't disable auto-export, just try again next time
            console.log("PySheet: auto-export directory not selected; will try again on next change")
        elif name in {"NotAllowedError", "SecurityError"}:
            console.warn("PySheet: directory picker requires a user gesture; use Export JSON to set it up")
        else:
            console.warn(f"PySheet: auto-export directory picker error - {exc}")
        return None
    has_permission = await _ensure_directory_write_permission(handle)
    if not has_permission:
        # Permission denied - don't disable auto-export, just can't use this handle
        console.log("PySheet: directory lacks write permission; will try again on next change")
        return None
    if not hasattr(handle, "getFileHandle"):
        console.warn("PySheet: selected directory handle cannot create files; falling back to file picker")
        return None
    _AUTO_EXPORT_DIRECTORY_HANDLE = handle
    console.log("PySheet: auto-export directory selected")
    return handle


async def _ensure_auto_export_file_handle(target_name: str, auto_trigger: bool = True):
    global _AUTO_EXPORT_FILE_HANDLE, _AUTO_EXPORT_DISABLED, _AUTO_EXPORT_LAST_FILENAME
    if not hasattr(window, "showSaveFilePicker"):
        return None
    if _AUTO_EXPORT_FILE_HANDLE is not None:
        existing_name = getattr(_AUTO_EXPORT_FILE_HANDLE, "name", None)
        if existing_name and existing_name != target_name:
            _AUTO_EXPORT_FILE_HANDLE = None
        else:
            _AUTO_EXPORT_LAST_FILENAME = existing_name or target_name
            return _AUTO_EXPORT_FILE_HANDLE
    options = {
        "suggestedName": target_name,
        "types": [
            {
                "description": "Character JSON",
                "accept": {"application/json": [".json"]},
            }
        ],
    }
    try:
        handle = await window.showSaveFilePicker(options)
    except JsException as exc:
        # AbortError fires when the user dismisses the picker; treat as a simple skip.
        name = getattr(exc, "name", "")
        if name == "AbortError":
            # User cancelled - don't disable auto-export, just try again next time
            console.log("PySheet: auto-export file target not selected; will try again on next change")
        elif name in {"NotAllowedError", "SecurityError"}:
            console.warn("PySheet: file picker requires a user gesture; use Export JSON to set it up")
        else:
            console.warn(f"PySheet: auto-export file picker error - {exc}")
        return None
    _AUTO_EXPORT_FILE_HANDLE = handle
    _AUTO_EXPORT_LAST_FILENAME = getattr(handle, "name", target_name)
    console.log("PySheet: auto-export file selected")
    return handle


async def _write_auto_export_file(handle, payload: str):
    try:
        writable = await handle.createWritable()
        await writable.write(payload)
        await writable.close()
    except JsException as exc:
        raise RuntimeError(f"failed to write auto-export file ({exc})")


async def _attempt_persistent_export(
    payload: str,
    proposed_filename: str,
    *,
    auto: bool,
    allow_prompt: bool,
) -> bool:
    global _AUTO_EXPORT_DIRECTORY_HANDLE, _AUTO_EXPORT_FILE_HANDLE
    global _AUTO_EXPORT_DISABLED, _AUTO_EXPORT_LAST_FILENAME, _LAST_AUTO_EXPORT_SNAPSHOT
    global _AUTO_EXPORT_SETUP_PROMPTED

    if not _supports_persistent_auto_export():
        return False

    need_prompt = (
        allow_prompt
        and not _AUTO_EXPORT_SETUP_PROMPTED
        and _AUTO_EXPORT_DIRECTORY_HANDLE is None
        and _AUTO_EXPORT_FILE_HANDLE is None
    )
    if need_prompt:
        wants_setup = False
        try:
            wants_setup = window.confirm(
                "Enable automatic JSON exports? Select OK to choose a folder for saving updates automatically."
            )
        except JsException:
            wants_setup = False
        _AUTO_EXPORT_SETUP_PROMPTED = True
        if wants_setup:
            handle = await _ensure_auto_export_directory(auto_trigger=False)
            if handle is None:
                await _ensure_auto_export_file_handle(proposed_filename, auto_trigger=False)

    if _AUTO_EXPORT_DIRECTORY_HANDLE is not None:
        try:
            file_handle = await _AUTO_EXPORT_DIRECTORY_HANDLE.getFileHandle(
                proposed_filename,
                {"create": True},
            )
        except JsException as exc:
            console.warn(f"PySheet: unable to open auto-export file in directory ({exc})")
            if auto:
                _AUTO_EXPORT_DIRECTORY_HANDLE = None
        else:
            try:
                await _write_auto_export_file(file_handle, payload)
            except Exception as exc:
                console.warn(f"PySheet: auto-export write failed for directory target ({exc})")
                if auto:
                    _AUTO_EXPORT_DIRECTORY_HANDLE = None
            else:
                _AUTO_EXPORT_LAST_FILENAME = getattr(file_handle, "name", proposed_filename)
                _LAST_AUTO_EXPORT_SNAPSHOT = payload
                _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
                verb = "auto-exported" if auto else "exported"
                console.log(f"PySheet: {verb} character JSON to {_AUTO_EXPORT_LAST_FILENAME}")
                _AUTO_EXPORT_DISABLED = False
                return True

    handle = _AUTO_EXPORT_FILE_HANDLE
    if handle is not None:
        existing_name = getattr(handle, "name", "")
        if existing_name and existing_name != proposed_filename and allow_prompt:
            _AUTO_EXPORT_FILE_HANDLE = None
            handle = None
        if handle is None and allow_prompt:
            handle = await _ensure_auto_export_file_handle(proposed_filename, auto_trigger=False)
        if handle is not None:
            try:
                await _write_auto_export_file(handle, payload)
            except Exception as exc:
                console.warn(f"PySheet: auto-export write failed for file handle ({exc})")
                if auto:
                    _AUTO_EXPORT_FILE_HANDLE = None
            else:
                _AUTO_EXPORT_LAST_FILENAME = getattr(handle, "name", proposed_filename)
                _LAST_AUTO_EXPORT_SNAPSHOT = payload
                _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
                verb = "auto-exported" if auto else "exported"
                console.log(f"PySheet: {verb} character JSON to {_AUTO_EXPORT_LAST_FILENAME}")
                _AUTO_EXPORT_DISABLED = False
                return True

    return False


LOCAL_SPELLS_FALLBACK = [
    {
        "name": "Cure Wounds",
        "slug": "cure-wounds",
        "level": 1,
        "school": "evocation",
        "casting_time": "1 action",
        "range": "Touch",
        "components": "V, S",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "A creature you touch regains a number of hit points equal to 1d8 + your spellcasting ability modifier.",
            "This spell has no effect on undead or constructs.",
        ],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d8 for each slot level above 1st.",
        "dnd_class": "Bard, Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Healing Word",
        "slug": "healing-word",
        "level": 1,
        "school": "evocation",
        "casting_time": "1 bonus action",
        "range": "60 feet",
        "components": "V",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "A creature of your choice that you can see within range regains hit points equal to 1d4 + your spellcasting ability modifier.",
            "This spell has no effect on undead or constructs.",
        ],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the healing increases by 1d4 for each slot level above 1st.",
        "dnd_class": "Bard, Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Guiding Bolt",
        "slug": "guiding-bolt",
        "level": 1,
        "school": "evocation",
        "casting_time": "1 action",
        "range": "120 feet",
        "components": "V, S",
        "material": "",
        "duration": "1 round",
        "ritual": False,
        "concentration": False,
        "desc": [
            "A flash of light streaks toward a creature of your choice within range. Make a ranged spell attack against the target.",
            "On a hit, the target takes 4d6 radiant damage, and the next attack roll made against this target before the end of your next turn has advantage.",
        ],
        "higher_level": "The damage increases by 1d6 for each slot level above 1st.",
        "dnd_class": "Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Bless",
        "slug": "bless",
        "level": 1,
        "school": "enchantment",
        "casting_time": "1 action",
        "range": "30 feet",
        "components": "V, S, M",
        "material": "A sprinkling of holy water",
        "duration": "Concentration, up to 1 minute",
        "ritual": False,
        "concentration": True,
        "desc": [
            "You bless up to three creatures of your choice within range. Whenever a target makes an attack roll or a saving throw before the spell ends, the target can roll a d4 and add the number rolled to the attack roll or saving throw.",
        ],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, you can target one additional creature for each slot level above 1st.",
        "dnd_class": "Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Faerie Fire",
        "slug": "faerie-fire",
        "level": 1,
        "school": "evocation",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V",
        "material": "",
        "duration": "Concentration, up to 1 minute",
        "ritual": False,
        "concentration": True,
        "desc": [
            "Each object in a 20-foot cube within range is outlined in blue, green, or violet light. Any creature in the area when the spell is cast is also outlined in light if it fails a Dexterity saving throw.",
            "For the duration, objects and affected creatures shed dim light in a 10-foot radius and attack rolls against affected creatures have advantage.",
        ],
        "higher_level": "",
        "dnd_class": "Bard",
        "document__title": "SRD",
    },
    {
        "name": "Sacred Flame",
        "slug": "sacred-flame",
        "level": 0,
        "school": "evocation",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V, S",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "Flame-like radiance descends on a creature you can see within range. The target must succeed on a Dexterity saving throw or take 1d8 radiant damage.",
            "The target gains no benefit from cover for this saving throw.",
        ],
        "higher_level": "The spell's damage increases by 1d8 when you reach 5th level (2d8), 11th level (3d8), and 17th level (4d8).",
        "dnd_class": "Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Detect Magic",
        "slug": "detect-magic",
        "level": 1,
        "school": "divination",
        "casting_time": "1 action",
        "range": "Self",
        "components": "V, S",
        "material": "",
        "duration": "Concentration, up to 10 minutes",
        "ritual": True,
        "concentration": True,
        "desc": [
            "For the duration, you sense the presence of magic within 30 feet of you.",
            "If you sense magic in this way, you can use your action to see a faint aura around any visible creature or object in the area that bears magic, and you learn its school of magic, if any.",
        ],
        "higher_level": "",
        "dnd_class": "Bard, Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Prayer of Healing",
        "slug": "prayer-of-healing",
        "level": 2,
        "school": "evocation",
        "casting_time": "10 minutes",
        "range": "30 feet",
        "components": "V",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "Up to six creatures of your choice that you can see within range each regain hit points equal to 2d8 + your spellcasting ability modifier.",
            "This spell has no effect on undead or constructs.",
        ],
        "higher_level": "When you cast this spell using a spell slot of 3rd level or higher, the healing increases by 1d8 for each slot level above 2nd.",
        "dnd_class": "Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Shatter",
        "slug": "shatter",
        "level": 2,
        "school": "evocation",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V, S, M",
        "material": "A chip of mica",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "A sudden loud ringing noise, painfully intense, erupts from a point of your choice within range.",
            "Each creature in a 10-foot-radius sphere centered on that point must make a Constitution saving throw, taking 3d8 thunder damage on a failed save, or half as much damage on a successful one.",
        ],
        "higher_level": "When you cast this spell using a spell slot of 3rd level or higher, the damage increases by 1d8 for each slot level above 2nd.",
        "dnd_class": "Bard",
        "document__title": "SRD",
    },
    {
        "name": "Hold Person",
        "slug": "hold-person",
        "level": 2,
        "school": "enchantment",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V, S, M",
        "material": "A small, straight piece of iron",
        "duration": "Concentration, up to 1 minute",
        "ritual": False,
        "concentration": True,
        "desc": [
            "Choose a humanoid that you can see within range. The target must succeed on a Wisdom saving throw or be paralyzed for the duration.",
            "At the end of each of its turns, the target can make another Wisdom saving throw. On a success, the spell ends on the target.",
        ],
        "higher_level": "When you cast this spell using a spell slot of 3rd level or higher, you can target one additional humanoid for each slot level above 2nd.",
        "dnd_class": "Bard, Cleric",
        "document__title": "SRD",
    },
    {
        "name": "Vicious Mockery",
        "slug": "vicious-mockery",
        "level": 0,
        "school": "enchantment",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "You unleash a string of insults laced with subtle enchantments at a creature you can see within range. If the target can hear you, it must succeed on a Wisdom saving throw or take 1d4 psychic damage and have disadvantage on the next attack roll it makes before the end of its next turn.",
        ],
        "higher_level": "The damage increases by 1d4 when you reach 5th level (2d4), 11th level (3d4), and 17th level (4d4).",
        "dnd_class": "Bard",
        "document__title": "SRD",
    },
    {
        "name": "Word of Radiance",
        "slug": "word-of-radiance",
        "level": 0,
        "school": "evocation",
        "casting_time": "1 reaction",
        "range": "5 feet",
        "components": "V",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "You utter a divine word, and burning radiance erupts from you.",
            "Each creature of your choice that you can see within 5 feet of you must succeed on a Constitution saving throw or take 1d6 radiant damage.",
        ],
        "higher_level": "The damage increases by 1d6 when you reach 5th level (2d6), 11th level (3d6), and 17th level (4d6).",
        "dnd_class": "Cleric",
        "document__title": "XGE",
    },
    {
        "name": "Toll the Dead",
        "slug": "toll-the-dead",
        "level": 0,
        "school": "necromancy",
        "casting_time": "1 action",
        "range": "60 feet",
        "components": "V, S",
        "material": "",
        "duration": "Instantaneous",
        "ritual": False,
        "concentration": False,
        "desc": [
            "You point at one creature you can see within range. The creature must make a Wisdom saving throw.",
            "On a failed save, it takes 1d8 necrotic damage if it is still below its hit point maximum when you cast the spell.",
            "If the creature is missing any of its hit points when you cast this spell, it takes 1d12 necrotic damage instead.",
        ],
        "higher_level": "When you reach 5th level, the damage increases to 2d8 or 2d12, at 11th level to 3d8 or 3d12, and at 17th level to 4d8 or 4d12.",
        "dnd_class": "Cleric, Wizard",
        "document__title": "XGE",
    },
]


def set_spell_library_data(spells: list[dict] | None):
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
    "fighter": ["fighter", "eldritch knight", "arcane archer"],
    "rogue": ["rogue", "arcane trickster"],
    "monk": ["monk"],
    "barbarian": ["barbarian"],
    "blood hunter": ["blood hunter", "bloodhunter"],
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
    "fighter": "Fighter (Eldritch Knight)",
    "rogue": "Rogue (Arcane Trickster)",
    "monk": "Monk",
    "barbarian": "Barbarian",
    "blood hunter": "Blood Hunter",
}

# Known spell data corrections for Open5e inconsistencies
# Format: "slug": {"classes": ["correct", "class", "list"]}
SPELL_CORRECTIONS = {
    "burning-hands": {"classes": ["sorcerer", "wizard"]},  # Not a cleric spell
}

def apply_spell_corrections(spell: dict) -> dict:
    """Apply known corrections to spell data."""
    slug = spell.get("slug", "")
    if slug in SPELL_CORRECTIONS:
        correction = SPELL_CORRECTIONS[slug]
        if "classes" in correction:
            spell["classes"] = correction["classes"]
            # Update classes_display to match
            spell["classes_display"] = [
                SPELL_CLASS_DISPLAY_NAMES.get(c, c.title()) for c in correction["classes"]
            ]
    return spell


def is_spell_source_allowed(source: str) -> bool:
    """Check if a spell source is in our allowed list (PHB, TCE, XGE only)."""
    # Temporarily allow all sources for debugging
    return True

CLASS_CASTING_PROGRESSIONS = {
    "artificer": "half_up",
    "bard": "full",
    "cleric": "full",
    "druid": "full",
    "paladin": "half",
    "ranger": "half",
    "sorcerer": "full",
    "warlock": "pact",
    "wizard": "full",
    "fighter": "third",
    "rogue": "third",
    "monk": "none",
    "barbarian": "none",
    "blood hunter": "half",
}

SPELLCASTING_PROGRESSION_TABLES = {
    "none": [0] * 21,
    "full": [
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        6,
        6,
        7,
        7,
        8,
        8,
        9,
        9,
        9,
        9,
    ],
    "half": [
        0,
        0,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
    ],
    "half_up": [
        0,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        4,
        4,
        4,
        4,
        5,
        5,
        5,
        5,
    ],
    "third": [
        0,
        0,
        0,
        1,
        1,
        1,
        1,
        2,
        2,
        2,
        2,
        2,
        2,
        3,
        3,
        3,
        3,
        3,
        3,
        4,
        4,
    ],
    "pact": [
        0,
        1,
        1,
        2,
        2,
        3,
        3,
        4,
        4,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
        5,
    ],
}

# Standard slot counts for full casters by caster level (PHB p. 201)
STANDARD_SLOT_TABLE = {
    0: [0, 0, 0, 0, 0, 0, 0, 0, 0],
    1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
    2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
    3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
    4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
    5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
    6: [4, 3, 3, 0, 0, 0, 0, 0, 0],
    7: [4, 3, 3, 1, 0, 0, 0, 0, 0],
    8: [4, 3, 3, 2, 0, 0, 0, 0, 0],
    9: [4, 3, 3, 3, 1, 0, 0, 0, 0],
    10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
    11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
    12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
    13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
    14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
    15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
    16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
    17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
    18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
    19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
    20: [4, 3, 3, 3, 3, 2, 2, 1, 1],
}

PACT_MAGIC_TABLE = {
    0: {"slots": 0, "level": 0},
    1: {"slots": 1, "level": 1},
    2: {"slots": 2, "level": 1},
    3: {"slots": 2, "level": 2},
    4: {"slots": 2, "level": 2},
    5: {"slots": 2, "level": 3},
    6: {"slots": 2, "level": 3},
    7: {"slots": 2, "level": 4},
    8: {"slots": 2, "level": 4},
    9: {"slots": 2, "level": 5},
    10: {"slots": 2, "level": 5},
    11: {"slots": 3, "level": 5},
    12: {"slots": 3, "level": 5},
    13: {"slots": 3, "level": 5},
    14: {"slots": 3, "level": 5},
    15: {"slots": 3, "level": 5},
    16: {"slots": 3, "level": 5},
    17: {"slots": 4, "level": 5},
    18: {"slots": 4, "level": 5},
    19: {"slots": 4, "level": 5},
    20: {"slots": 4, "level": 5},
}

class SpellcastingManager:
    """Encapsulates spellbook selections, slot tracking, and related rendering."""

    def __init__(self):
        self.reset_state()

    # ------------------------------------------------------------------
    # state management
    # ------------------------------------------------------------------
    def reset_state(self):
        self.prepared: list[dict] = []
        self.slots_used: dict[int, int] = {level: 0 for level in range(1, 10)}
        self.pact_used: int = 0

    def export_state(self) -> dict:
        return {
            "prepared": copy.deepcopy(self.prepared),
            "slots_used": {
                str(level): self.slots_used.get(level, 0) for level in range(1, 10)
            },
            "pact_used": self.pact_used,
        }

    def _normalize_prepared_entry(self, entry: dict) -> dict | None:
        slug = (entry or {}).get("slug")
        if not slug:
            return None
        record = get_spell_by_slug(slug)
        name = entry.get("name") if entry else None
        level = parse_int(entry.get("level") if entry else None, 0)
        source = entry.get("source") if entry else ""
        concentration = bool(entry.get("concentration"))
        ritual = bool(entry.get("ritual"))
        school = entry.get("school", "")
        casting_time = entry.get("casting_time", "")
        range_text = entry.get("range", "")
        components = entry.get("components", "")
        material = entry.get("material", "")
        duration = entry.get("duration", "")
        description = entry.get("description", "")
        description_html = entry.get("description_html", "")
        classes = entry.get("classes", [])
        classes_display = entry.get("classes_display", [])
        
        if record:
            name = record.get("name", name)
            level = record.get("level_int", level)
            source = record.get("source", source)
            concentration = bool(record.get("concentration"))
            ritual = bool(record.get("ritual"))
            school = record.get("school", school)
            casting_time = record.get("casting_time", casting_time)
            range_text = record.get("range", range_text)
            components = record.get("components", components)
            material = record.get("material", material)
            duration = record.get("duration", duration)
            description = record.get("description", description)
            description_html = record.get("description_html", description_html)
            classes = record.get("classes", classes)
            classes_display = record.get("classes_display", classes_display)
        if not name:
            name = slug.replace("-", " ").title()
        return {
            "slug": slug,
            "name": name,
            "level": level,
            "source": source,
            "concentration": concentration,
            "ritual": ritual,
            "school": school,
            "casting_time": casting_time,
            "range": range_text,
            "components": components,
            "material": material,
            "duration": duration,
            "description": description,
            "description_html": description_html,
            "classes": classes,
            "classes_display": classes_display,
        }

    def sort_prepared_spells(self):
        def _sort_key(item: dict):
            level = item.get("level", 0)
            name = item.get("name", "").lower()
            concentration = 1 if item.get("concentration") else 0
            return (level, name, concentration)

        self.prepared.sort(key=_sort_key)

    def load_state(self, state: dict | None):
        self.reset_state()
        if not state:
            self.sort_prepared_spells()
            self.render_spellbook()
            self.render_spell_slots()
            return

        prepared: list[dict] = []
        for entry in state.get("prepared", []):
            normalized = self._normalize_prepared_entry(entry)
            if normalized:
                prepared.append(normalized)
        self.prepared = prepared
        self.sort_prepared_spells()

        slots_used = state.get("slots_used", {})
        for level in range(1, 10):
            value = slots_used.get(level)
            if value is None:
                value = slots_used.get(str(level), 0)
            self.slots_used[level] = clamp(parse_int(value, 0), 0)

        self.pact_used = clamp(parse_int(state.get("pact_used", 0), 0), 0)

        self.render_spellbook()
        self.render_spell_slots()

    # ------------------------------------------------------------------
    # library integration
    # ------------------------------------------------------------------
    def sync_with_library(self):
        if not self.prepared:
            return
        changed = False
        for entry in self.prepared:
            record = get_spell_by_slug(entry.get("slug"))
            if not record:
                continue
            if entry.get("name") != record.get("name"):
                entry["name"] = record.get("name", entry.get("name"))
                changed = True
            if entry.get("level") != record.get("level_int"):
                entry["level"] = record.get("level_int", entry.get("level", 0))
                changed = True
            source = record.get("source")
            if source and entry.get("source") != source:
                entry["source"] = source
                changed = True
            conc = bool(record.get("concentration"))
            if conc != bool(entry.get("concentration")):
                entry["concentration"] = conc
                changed = True
        if changed:
            self.sort_prepared_spells()
            self.render_spellbook()

    def get_prepared_slug_set(self) -> set[str]:
        return {entry.get("slug") for entry in self.prepared if entry.get("slug")}

    def get_prepared_non_cantrip_count(self, exclude_domain_bonus_slugs: set[str] = None) -> int:
        """Count prepared spells excluding cantrips and optionally domain bonus spells."""
        if exclude_domain_bonus_slugs is None:
            exclude_domain_bonus_slugs = set()
        count = 0
        for entry in self.prepared:
            # Skip cantrips (level 0)
            if entry.get("level", 0) == 0:
                continue
            # Skip domain bonus spells if provided
            if entry.get("slug") in exclude_domain_bonus_slugs:
                continue
            count += 1
        return count

    def get_prepared_cantrip_count(self) -> int:
        """Count prepared cantrips (level 0 spells only)."""
        count = 0
        for entry in self.prepared:
            if entry.get("level", 0) == 0:
                count += 1
        return count
    
    def get_max_cantrips_allowed(self, class_name: str, level: int, spell_mod: int) -> int:
        """Get the maximum number of cantrips allowed for a given class."""
        class_name = class_name.lower() if class_name else ""
        
        if class_name == "cleric":
            # Cleric cantrips: 3 (L1), 4 (L4), 5 (L10), 6 (L17)
            if level >= 17:
                return 6
            elif level >= 10:
                return 5
            elif level >= 4:
                return 4
            else:
                return 3
        elif class_name == "bard":
            # Bard cantrips = Charisma modifier (minimum 1)
            return max(1, spell_mod)
        elif class_name == "wizard":
            # Wizard cantrips = Intelligence modifier (minimum 1)
            return max(1, spell_mod)
        elif class_name in ("druid", "sorcerer"):
            # Druid cantrips: 2 (L1), 3 (L4), 4 (L10), 5 (L17)
            # Sorcerer cantrips: 4 (L1), 5 (L4), 6 (L10)
            if class_name == "druid":
                if level >= 17:
                    return 5
                elif level >= 10:
                    return 4
                elif level >= 4:
                    return 3
                else:
                    return 2
            else:  # sorcerer
                if level >= 10:
                    return 6
                elif level >= 4:
                    return 5
                else:
                    return 4
        else:
            return 0  # Other classes don't have cantrips

    def is_spell_prepared(self, slug: str | None) -> bool:
        if not slug:
            return False
        return slug in self.get_prepared_slug_set()

    # ------------------------------------------------------------------
    # spellbook manipulation
    # ------------------------------------------------------------------
    def add_spell(self, slug: str):
        if not slug or self.is_spell_prepared(slug):
            return
        record = get_spell_by_slug(slug)
        if record is None:
            console.warn(f"PySheet: unable to add spell '{slug}' – not in library")
            return
        
        # Check if spell source is allowed
        source = record.get("source", "")
        if not is_spell_source_allowed(source):
            console.warn(f"PySheet: spell '{slug}' is not from an allowed source (must be PHB, TCE, or XGE)")
            return
        
        profile = compute_spellcasting_profile()
        max_level = profile.get("max_spell_level")
        if (
            max_level is not None
            and max_level >= 0
            and record.get("level_int", 0) > max_level
        ):
            console.warn("PySheet: cannot add spell above available level")
            return
        allowed = profile.get("allowed_classes", [])
        spell_classes = set(record.get("classes", []))
        if allowed and not spell_classes.intersection(set(allowed)):
            console.warn("PySheet: spell not available to current classes")
            return

        # Check max prepared spells limit
        class_name = get_text_value("class").lower() if get_text_value("class") else ""
        level = get_numeric_value("level", 1)
        spell_ability = {
            "artificer": "int",
            "bard": "cha",
            "cleric": "wis",
            "druid": "wis",
            "paladin": "cha",
            "ranger": "wis",
            "sorcerer": "cha",
            "warlock": "cha",
            "wizard": "int",
        }.get(class_name, "int")
        scores = gather_scores()
        race_bonuses = get_race_ability_bonuses(get_text_value("race"))
        spell_score = scores.get(spell_ability, 10) + race_bonuses.get(spell_ability, 0)
        spell_mod = ability_modifier(spell_score)
        
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
        else:
            max_prepared = 0
        
        max_prepared = max(0, max_prepared)
        
        # Check cantrip limit first
        spell_level = record.get("level_int", 0)
        if spell_level == 0:  # This is a cantrip
            max_cantrips = SPELLCASTING_MANAGER.get_max_cantrips_allowed(class_name, level, spell_mod)
            current_cantrips = SPELLCASTING_MANAGER.get_prepared_cantrip_count()
            
            if max_cantrips <= 0:
                console.warn(f"PySheet: cannot add cantrip – {class_name} does not have cantrips")
                return
            
            if current_cantrips >= max_cantrips:
                console.warn(f"PySheet: cannot add cantrip – max {max_cantrips} cantrips known")
                return
        else:
            # Check prepared spell limit for non-cantrips
            # Count domain bonus spells (they don't count toward the limit)
            domain = get_text_value("domain")
            bonus_spell_slugs = set(get_domain_bonus_spells(domain, level)) if domain else set()
            current_prepared = len([s for s in self.prepared if s.get("level", 0) > 0 and s.get("slug") not in bonus_spell_slugs])
            
            if current_prepared >= max_prepared:
                console.warn(f"PySheet: cannot add spell – max {max_prepared} spells prepared")
                return

        self.prepared.append(
            {
                "slug": slug,
                "name": record.get("name", slug.title()),
                "level": record.get("level_int", 0),
                "source": record.get("source", ""),
                "concentration": bool(record.get("concentration")),
                "ritual": bool(record.get("ritual")),
                "school": record.get("school", ""),
                "casting_time": record.get("casting_time", ""),
                "range": record.get("range", ""),
                "components": record.get("components", ""),
                "material": record.get("material", ""),
                "duration": record.get("duration", ""),
                "description": record.get("description", ""),
                "description_html": record.get("description_html", ""),
                "classes": record.get("classes", []),
                "classes_display": record.get("classes_display", []),
            }
        )
        self.sort_prepared_spells()
        self.render_spellbook()
        self.render_spell_slots(self.compute_slot_summary(profile))
        apply_spell_filters(auto_select=False)
        update_calculations()  # Update counter
        schedule_auto_export()

    def remove_spell(self, slug: str):
        if not slug:
            return
        
        # Prevent removing domain bonus spells
        try:
            domain = get_text_value("domain")
            level = get_numeric_value("level", 1)
            if domain:
                bonus_spells = get_domain_bonus_spells(domain, level)
                if slug in bonus_spells:
                    LOGGER.warning(f"Attempted to remove domain bonus spell: {slug}")
                    console.warn(f"PySheet: cannot remove domain bonus spell {slug}")
                    return
        except Exception as exc:
            LOGGER.error(f"Error checking domain bonus spells in remove_spell: {exc}", exc)
        
        before = len(self.prepared)
        self.prepared = [
            entry for entry in self.prepared if entry.get("slug") != slug
        ]
        if len(self.prepared) != before:
            self.render_spellbook()
            apply_spell_filters(auto_select=False)
            update_calculations()  # Update counter
            schedule_auto_export()

    def can_cast_spell(self, spell_level: int) -> bool:
        """Check if a spell of given level can be cast (has available slots)."""
        if spell_level == 0:  # Cantrips don't use slots
            return True
        
        profile = compute_spellcasting_profile()
        max_slots = self.compute_max_slots_for_level(spell_level, profile)
        used_slots = self.slots_used.get(spell_level, 0)
        
        return used_slots < max_slots
    
    def compute_max_slots_for_level(self, level: int, profile: dict | None = None) -> int:
        """Get max spell slots available for a given level."""
        if level == 0:
            return 999  # Cantrips unlimited
        
        if profile is None:
            profile = compute_spellcasting_profile()
        
        slot_summary = self.compute_slot_summary(profile)
        return slot_summary.get("levels", {}).get(level, 0)

    # ------------------------------------------------------------------
    # rendering helpers
    # ------------------------------------------------------------------
    def render_spellbook(self):
        container = get_element("spellbook-levels")
        empty_state = get_element("spellbook-empty-state")
        if container is None or empty_state is None:
            return

        # Render slot tracker
        self.render_slots_tracker()

        if not self.prepared:
            empty_state.style.display = "block"
            container.innerHTML = ""
            return

        empty_state.style.display = "none"
        groups: dict[int, list[dict]] = {}
        for entry in self.prepared:
            level = entry.get("level", 0)
            groups.setdefault(level, []).append(entry)

        sections: list[str] = []
        slot_summary = self.compute_slot_summary()
        for level in sorted(groups.keys()):
            def _group_sort_key(item: dict):
                name = item.get("name", "").lower()
                concentration = 1 if item.get("concentration") else 0
                return (name, concentration)

            spells = sorted(groups[level], key=_group_sort_key)
            heading = "Cantrips" if level == 0 else format_spell_level_label(level)
            
            # Add slot info for leveled spells
            slot_info_html = ""
            if level > 0:
                max_slots = slot_summary["levels"].get(level, 0)
                used = self.slots_used.get(level, 0)
                available = max_slots - used
                slot_info_html = f' <span class="spell-level-slots">({available}/{max_slots} slots)</span>'
            
            items_html = []
            for spell in spells:
                slug = spell.get("slug", "")
                name = spell.get("name", "Unknown Spell")
                source = spell.get("source", "")
                # Use spell data from prepared list (which has all details saved), then fall back to library if needed
                record = spell.copy()  # Start with the prepared spell data
                if not record.get("level_label"):
                    record["level_label"] = format_spell_level_label(spell.get("level", level))
                # Try to update from library if available - prioritize library data for descriptions
                lib_record = get_spell_by_slug(slug)
                if lib_record:
                    # Merge library data: use library values for missing fields
                    for key in lib_record:
                        if key not in record or not record.get(key):
                            record[key] = lib_record[key]
                    # Ensure description_html is always set
                    if not record.get("description_html") and lib_record.get("description_html"):
                        record["description_html"] = lib_record.get("description_html")
                    # Also try description field as fallback
                    if not record.get("description") and lib_record.get("description"):
                        record["description"] = lib_record.get("description")
                
                level_label = record.get("level_label")
                if not level_label:
                    level_label = format_spell_level_label(spell.get("level", level))
                school = record.get("school") or ""
                meta_parts = []
                if level_label:
                    meta_parts.append(level_label)
                if school:
                    meta_parts.append(school)
                meta_text = " · ".join(part for part in meta_parts if part)
                meta_html = (
                    f"<span class=\"spellbook-meta\">{escape(meta_text)}</span>"
                    if meta_text
                    else ""
                )
                source_html = (
                    f"<span class=\"spellbook-source\">{escape(source)}</span>"
                    if source
                    else ""
                )
                tag_parts: list[str] = []
                if record.get("ritual"):
                    tag_parts.append("<span class=\"spell-tag\">Ritual</span>")
                if record.get("concentration"):
                    tag_parts.append("<span class=\"spell-tag\">Concentration</span>")
                tags_html = "".join(tag_parts)
                classes_display = record.get("classes_display") or []
                classes_html = (
                    "<div class=\"spellbook-classes\"><strong>Classes: </strong>"
                    + escape(", ".join(classes_display))
                    + "</div>"
                    if classes_display
                    else ""
                )
                properties: list[str] = []
                casting_time = record.get("casting_time") or ""
                if casting_time:
                    properties.append(
                        f"<div><dt>Casting Time</dt><dd>{escape(casting_time)}</dd></div>"
                    )
                range_text = record.get("range") or ""
                if range_text:
                    properties.append(
                        f"<div><dt>Range</dt><dd>{escape(range_text)}</dd></div>"
                    )
                components = record.get("components") or ""
                material = record.get("material") or ""
                if components:
                    comp_text = escape(components)
                    if material:
                        comp_text = f"{comp_text} ({escape(material)})"
                    properties.append(
                        f"<div><dt>Components</dt><dd>{comp_text}</dd></div>"
                    )
                duration = record.get("duration") or ""
                if duration:
                    properties.append(
                        f"<div><dt>Duration</dt><dd>{escape(duration)}</dd></div>"
                    )
                properties_html = (
                    "<dl class=\"spellbook-properties\">"
                    + "".join(properties)
                    + "</dl>"
                    if properties
                    else ""
                )
                description_html = record.get("description_html")
                if not description_html:
                    # Try to build from desc/higher_level if available
                    desc_text = _coerce_spell_text(record.get("desc"))
                    higher_text = _coerce_spell_text(record.get("higher_level"))
                    desc_html = _make_paragraphs(desc_text)
                    higher_html = _make_paragraphs(higher_text)
                    if desc_html:
                        description_html = desc_html
                        if higher_html:
                            description_html += "<p class=\"spell-section-title\">At Higher Levels</p>" + higher_html
                    else:
                        # Fall back to description field if available
                        description_text = record.get("description", "")
                        if description_text:
                            description_html = _make_paragraphs(_coerce_spell_text(description_text))
                        else:
                            description_html = (
                                "<p class=\"spellbook-description-empty\">No detailed description available.</p>"
                            )
                body_sections = []
                if tags_html:
                    body_sections.append(
                        f"<div class=\"spellbook-tags\">{tags_html}</div>"
                    )
                if properties_html:
                    body_sections.append(properties_html)
                if classes_html:
                    body_sections.append(classes_html)
                body_sections.append(
                    f"<div class=\"spellbook-description\">{description_html}</div>"
                )
                body_html = (
                    "<div class=\"spellbook-body\">"
                    + "".join(body_sections)
                    + "</div>"
                )

                # Determine castability
                is_castable = self.can_cast_spell(level)
                castable_class = "" if is_castable else " uncastable"
                
                # Check if this is a domain bonus spell
                domain = get_text_value("domain")
                bonus_spell_slugs = get_domain_bonus_spells(domain, get_numeric_value("level", 1)) if domain else []
                is_bonus_spell = slug in bonus_spell_slugs
                
                # Build mnemonics for spellbook view (concentration, ritual, range, domain bonus)
                mnemonics_html = ""
                mnemonics_list = []
                if record.get("concentration"):
                    mnemonics_list.append("<span class=\"spell-mnemonic\" title=\"Concentration\">Conc.</span>")
                if record.get("ritual"):
                    mnemonics_list.append("<span class=\"spell-mnemonic\" title=\"Ritual\">Rit.</span>")
                if is_bonus_spell:
                    mnemonics_list.append("<span class=\"spell-mnemonic domain\" title=\"Domain Bonus\">Dom.</span>")
                
                # Add range mnemonic
                range_text = record.get("range", "").lower()
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
                        # Extract number from range
                        import re
                        match = re.search(r'(\d+)\s*(?:feet|ft)', range_text)
                        if match:
                            range_label = f"{match.group(1)}ft"
                        else:
                            range_label = None
                    
                    if range_label:
                        mnemonics_list.append(f"<span class=\"spell-mnemonic range\" title=\"Range: {escape(record.get('range', ''))}\">{escape(range_label)}</span>")
                
                if mnemonics_list:
                    mnemonics_html = f"<span class=\"spell-mnemonics\">{''.join(mnemonics_list)}</span>"
                
                # Add cast button for non-cantrips
                cast_button_html = ""
                if level > 0:
                    cast_button_html = f'<button type="button" class="spellbook-cast" data-cast-spell="{escape(slug)}" data-spell-level="{level}">Cast</button>'
                
                # Only add remove button if not a bonus spell
                remove_button_html = ""
                if not is_bonus_spell:
                    remove_button_html = f'<button type="button" class="spellbook-remove" data-remove-spell="{escape(slug)}">Remove</button>'
                
                items_html.append(
                    "<li class=\"spellbook-spell" + castable_class + "\" data-spell-slug=\""
                    + escape(slug)
                    + "\">"
                    + "<details class=\"spellbook-details\">"
                    + "<summary>"
                    + "<div class=\"spellbook-summary-main\">"
                    + f"<span class=\"spellbook-name\">{escape(name)}</span>"
                    + mnemonics_html
                    + "</div>"
                    + "<div class=\"spellbook-actions\">"
                    + cast_button_html
                    + remove_button_html
                    + "</div>"
                    + "</summary>"
                    + body_html
                    + "</details>"
                    + "</li>"
                )
            sections.append(
                "<section class=\"spellbook-level\">"
                + f"<header><h3>{escape(heading)}{slot_info_html}</h3></header>"
                + "<ul>"
                + "".join(items_html)
                + "</ul></section>"
            )

        container.innerHTML = "".join(sections)

        buttons = container.querySelectorAll("button[data-remove-spell]")
        for button in buttons:
            slug = button.getAttribute("data-remove-spell")
            if not slug:
                continue
            proxy = create_proxy(
                lambda event, s=slug: handle_remove_spell_click(event, s)
            )
            button.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)

        # Register cast button handlers
        cast_buttons = container.querySelectorAll("button[data-cast-spell]")
        console.log(f"PySheet: found {len(cast_buttons)} cast buttons to register")
        for button in cast_buttons:
            slug = button.getAttribute("data-cast-spell")
            level = button.getAttribute("data-spell-level")
            if not slug or not level:
                continue
            level_int = parse_int(level, 0)
            proxy = create_proxy(
                lambda event, s=slug, l=level_int: self.handle_spell_cast_button(event, s, l)
            )
            button.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
            console.log(f"PySheet: registered cast button for spell {slug} level {level_int}")

    def handle_spell_cast_button(self, event, slug: str, level: int):
        """Handle Cast button click to show confirmation modal."""
        console.log(f"PySheet: Cast button clicked for slug={slug}, level={level}")
        
        if event is not None:
            event.stopPropagation()
            event.preventDefault()
        
        current = self.slots_used.get(level, 0)
        max_slots = self.compute_max_slots_for_level(level)
        console.log(f"PySheet: current slots used: {current}, max: {max_slots}")
        
        # Get spell info for the confirmation message
        spell_name = "Unknown Spell"
        spell_boost_text = None
        for entry in self.prepared:
            if entry.get("slug") == slug:
                spell_name = entry.get("name", "Unknown Spell")
                spell_boost_text = entry.get("boost_text")
                break
        
        level_label = format_spell_level_label(level)
        remaining = max_slots - current - 1
        
        # Show modal confirmation
        self.show_spell_cast_modal(spell_name, level_label, remaining, slug, level, spell_boost_text)

    def show_spell_cast_modal(self, spell_name: str, level_label: str, remaining: int, slug: str, level: int, boost_text: str | None = None):
        """Display the spell cast confirmation modal."""
        modal = get_element("spell-cast-modal")
        title = get_element("spell-cast-modal-title")
        message = get_element("spell-cast-modal-message")
        confirm_btn = get_element("spell-cast-modal-confirm")
        cancel_btn = get_element("spell-cast-modal-cancel")
        close_btn = get_element("spell-cast-modal-close")
        boost_section = get_element("spell-cast-modal-boost-section")
        boost_container = get_element("spell-cast-modal-boost-options")
        
        if not all([modal, title, message, confirm_btn, cancel_btn, close_btn]):
            console.error("PySheet: spell cast modal elements not found")
            return
        
        # Set modal content
        title.textContent = f"Cast {spell_name}"
        message.innerHTML = f"<strong>{level_label}</strong><br>{remaining} slot(s) remaining"
        
        current = self.slots_used.get(level, 0)
        max_slots = self.compute_max_slots_for_level(level)
        
        # Build radio button options for boost levels
        boost_options_html = '<label class="boost-option"><input type="radio" name="boost-level" value="0" checked> None</label>'
        slot_summary = self.compute_slot_summary()
        available_levels = slot_summary.get("levels", {})
        
        has_boost_options = False
        for boost_level in range(level + 1, 10):
            max_boost_slots = available_levels.get(boost_level, 0)
            used_boost_slots = self.slots_used.get(boost_level, 0)
            available_boost = max_boost_slots - used_boost_slots
            if available_boost > 0:
                has_boost_options = True
                boost_level_label = format_spell_level_label(boost_level)
                boost_options_html += f'<label class="boost-option"><input type="radio" name="boost-level" value="{boost_level}"> {boost_level_label} Slot</label>'
        
        # Update boost section if it exists
        if boost_container and boost_section:
            if has_boost_options:
                boost_container.innerHTML = boost_options_html
                boost_section.style.display = "block"
            else:
                boost_section.style.display = "none"
        
        # Set onclick handlers directly (works better with PyScript)
        def confirm_click(e):
            console.log(f"PySheet: modal OK clicked")
            # Get selected boost level
            selected_radio = modal.querySelector('input[name="boost-level"]:checked')
            boost_level = parse_int(selected_radio.value if selected_radio else "0", 0) if selected_radio else 0
            
            if boost_level == 0:
                # Cast at base level
                if current < max_slots:
                    self.slots_used[level] = current + 1
                    console.log(f"PySheet: cast at level {level}")
                    update_calculations()
                    schedule_auto_export()
            else:
                # Cast with boosted slot
                boost_current = self.slots_used.get(boost_level, 0)
                boost_max = available_levels.get(boost_level, 0)
                if boost_current < boost_max:
                    self.slots_used[boost_level] = boost_current + 1
                    console.log(f"PySheet: boosted spell using level {boost_level} slot")
                    update_calculations()
                    schedule_auto_export()
            
            modal.classList.remove("active")
        
        def cancel_click(e):
            console.log(f"PySheet: modal cancel clicked")
            modal.classList.remove("active")
        
        # Use onclick attribute which works reliably with PyScript
        confirm_btn.onclick = confirm_click
        cancel_btn.onclick = cancel_click
        close_btn.onclick = cancel_click
        
        # Show modal
        modal.classList.add("active")
        console.log(f"PySheet: modal shown for {spell_name}")

    def compute_slot_summary(self, profile: dict | None = None) -> dict:
        if profile is None:
            profile = compute_spellcasting_profile()

        fallback_level = get_numeric_value("level", 1)
        caster_points = 0.0
        warlock_level = 0

        for entry in profile.get("entries", []):
            class_level = entry.get("level")
            if class_level is None:
                class_level = fallback_level
            class_level = max(1, min(int(class_level or fallback_level), 20))
            progression = determine_progression_key(entry.get("key"), entry.get("raw", ""))
            if progression == "full":
                caster_points += class_level
            elif progression == "half":
                caster_points += class_level / 2
            elif progression == "half_up":
                caster_points += ceil(class_level / 2)
            elif progression == "third":
                caster_points += class_level / 3
            elif progression == "pact":
                warlock_level += class_level

        effective_level = int(min(caster_points, 20))
        if effective_level < 0:
            effective_level = 0
        slot_counts = STANDARD_SLOT_TABLE.get(
            effective_level, STANDARD_SLOT_TABLE[0]
        )
        level_slots = {level: slot_counts[level - 1] for level in range(1, 10)}

        warlock_level = max(0, min(int(warlock_level), 20))
        pact_info = PACT_MAGIC_TABLE.get(warlock_level, PACT_MAGIC_TABLE[20])

        return {
            "levels": level_slots,
            "pact": pact_info,
            "effective_level": effective_level,
        }

    def _normalize_slot_usage(self, slot_summary: dict):
        levels = slot_summary.get("levels", {})
        for level in range(1, 10):
            max_slots = levels.get(level, 0)
            current = self.slots_used.get(level, 0)
            self.slots_used[level] = clamp(current, 0, max_slots)

        pact_max = slot_summary.get("pact", {}).get("slots", 0)
        self.pact_used = clamp(self.pact_used, 0, pact_max)

    def render_slots_tracker(self):
        """Render a summary of spell slot usage."""
        container = get_element("spellbook-slots-summary")
        if container is None:
            return
        
        slot_summary = self.compute_slot_summary()
        levels = slot_summary.get("levels", {})
        
        # Build slot tracker HTML
        tracker_items = []
        for level in range(1, 10):
            max_slots = levels.get(level, 0)
            if max_slots <= 0:
                continue
            used = self.slots_used.get(level, 0)
            available = max_slots - used
            level_label = format_spell_level_label(level)
            tracker_items.append(
                f'<div class="slot-tracker-item" title="{level_label}: {available}/{max_slots} slots available">'
                + f'<span class="slot-tracker-label">{level_label}</span>'
                + f'<span class="slot-tracker-value">{available}/{max_slots}</span>'
                + '</div>'
            )
        
        # Add pact slots if available
        pact_info = slot_summary.get("pact", {})
        if pact_info.get("slots", 0) > 0:
            pact_used = self.pact_used
            pact_max = pact_info["slots"]
            pact_available = pact_max - pact_used
            tracker_items.append(
                f'<div class="slot-tracker-item pact" title="Pact Slots (Level {pact_info["level"]}): {pact_available}/{pact_max} slots available">'
                + f'<span class="slot-tracker-label">Pact</span>'
                + f'<span class="slot-tracker-value">{pact_available}/{pact_max}</span>'
                + '</div>'
            )
        
        if tracker_items:
            container.innerHTML = '<div class="slot-tracker">' + "".join(tracker_items) + '</div>'
            container.style.display = "block"
        else:
            container.innerHTML = ""
            container.style.display = "none"

    def render_spell_slots(self, slot_summary: dict | None = None):
        slots_container = get_element("spell-slots")
        pact_container = get_element("pact-slots")
        if slots_container is None:
            return

        if slot_summary is None:
            slot_summary = self.compute_slot_summary()

        self._normalize_slot_usage(slot_summary)

        rows = []
        total_available_levels = 0
        for level in range(1, 10):
            max_slots = slot_summary["levels"].get(level, 0)
            if max_slots <= 0:
                continue
            total_available_levels += max_slots
            used = self.slots_used.get(level, 0)
            available = max_slots - used
            spend_disabled = " disabled" if available <= 0 else ""
            recover_disabled = " disabled" if used <= 0 else ""
            rows.append(
                "<div class=\"slot-row\">"
                + f"<div class=\"slot-label\">{escape(format_spell_level_label(level))}</div>"
                + f"<div class=\"slot-status\">{available} / {max_slots} available</div>"
                + "<div class=\"slot-buttons\">"
                + f"<button type=\"button\" data-slot-level=\"{level}\" data-slot-delta=\"1\"{spend_disabled}>Spend</button>"
                + f"<button type=\"button\" data-slot-level=\"{level}\" data-slot-delta=\"-1\"{recover_disabled}>Recover</button>"
                + "</div></div>"
            )

        if rows:
            slots_container.innerHTML = "".join(rows)
        else:
            slots_container.innerHTML = "<p class=\"spell-slots-empty\">No spell slots available at your current level.</p>"

        buttons = slots_container.querySelectorAll("button[data-slot-level]")
        for button in buttons:
            level = parse_int(button.getAttribute("data-slot-level"), None)
            delta = parse_int(button.getAttribute("data-slot-delta"), 0)
            if level is None:
                continue
            proxy = create_proxy(
                lambda event, lvl=level, d=delta: handle_slot_button(event, lvl, d)
            )
            button.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)

        pact_info = slot_summary.get("pact", {"slots": 0, "level": 0})
        if pact_container is not None:
            if pact_info.get("slots", 0) <= 0:
                pact_container.innerHTML = ""
                pact_container.style.display = "none"
            else:
                pact_container.style.display = ""
                used = self.pact_used
                available = pact_info["slots"] - used
                spend_disabled = " disabled" if available <= 0 else ""
                recover_disabled = " disabled" if used <= 0 else ""
                pact_container.innerHTML = (
                    "<div class=\"slot-row pact-row\">"
                    + f"<div class=\"slot-label\">Pact Slots (Level {pact_info['level']})</div>"
                    + f"<div class=\"slot-status\">{available} / {pact_info['slots']} available</div>"
                    + "<div class=\"slot-buttons\">"
                    + f"<button type=\"button\" data-pact-delta=\"1\"{spend_disabled}>Spend</button>"
                    + f"<button type=\"button\" data-pact-delta=\"-1\"{recover_disabled}>Recover</button>"
                    + "</div></div>"
                )
                pact_buttons = pact_container.querySelectorAll("button[data-pact-delta]")
                for button in pact_buttons:
                    delta = parse_int(button.getAttribute("data-pact-delta"), 0)
                    proxy = create_proxy(
                        lambda event, d=delta: handle_pact_slot_button(event, d)
                    )
                    button.addEventListener("click", proxy)
                    _EVENT_PROXIES.append(proxy)

    # ------------------------------------------------------------------
    # slot adjustments
    # ------------------------------------------------------------------
    def adjust_spell_slot(self, level: int, delta: int):
        slot_summary = self.compute_slot_summary()
        max_slots = slot_summary["levels"].get(level, 0)
        if max_slots <= 0:
            self.slots_used[level] = 0
            self.render_spell_slots(slot_summary)
            schedule_auto_export()
            return
        current = self.slots_used.get(level, 0)
        current = clamp(current + delta, 0, max_slots)
        self.slots_used[level] = current
        self.render_spell_slots(slot_summary)
        schedule_auto_export()

    def adjust_pact_slot(self, delta: int):
        slot_summary = self.compute_slot_summary()
        pact_max = slot_summary.get("pact", {}).get("slots", 0)
        current = clamp(self.pact_used + delta, 0, pact_max)
        self.pact_used = current
        self.render_spell_slots(slot_summary)
        schedule_auto_export()

    def reset_spell_slots(self):
        for level in range(1, 10):
            self.slots_used[level] = 0
        self.pact_used = 0
        self.render_spell_slots()
        self.render_spellbook()
        schedule_auto_export()


class InventoryManager:
    """Manages character inventory with categories, sorting, and detailed item view."""
    
    # Common item categories for auto-detection
    ARMOR_KEYWORDS = ["armor", "plate", "mail", "leather", "chain", "scale", "shield", "helmet", "breastplate"]
    WEAPON_KEYWORDS = ["sword", "axe", "spear", "bow", "staff", "mace", "hammer", "dagger", "knife", "blade", "rapier", "wand"]
    AMMO_KEYWORDS = ["arrow", "bolt", "ammo", "ammunition", "shot"]
    TOOL_KEYWORDS = ["tool", "kit", "instrument", "lock pick", "thieves'", "healer's"]
    POTION_KEYWORDS = ["potion", "elixir", "oil", "poison", "cure", "healing"]
    GEAR_KEYWORDS = ["rope", "torch", "bedroll", "tent", "lantern", "backpack", "grappling hook", "caltrops", "chalk", "pack", "explorer", "adventurer", "burglar", "diplomat", "dungeoneer", "entertainer", "priest", "scholar"]
    MOUNT_KEYWORDS = ["horse", "mule", "donkey", "camel", "mount", "vehicle", "cart", "boat", "ship"]
    MAGIC_KEYWORDS = ["+1", "+2", "+3", "magical", "magic", "enchanted", "ring of", "cloak of", "amulet of", "wand of", "staff of", "artifact", "relic"]
    
    # Category ordering for display
    CATEGORY_ORDER = ["Magic Items", "Weapons", "Armor", "Ammunition", "Potions", "Tools", "Adventuring Gear", "Mounts & Vehicles", "Other"]
    
    def __init__(self):
        self.items: list[dict] = []
    
    def load_state(self, state: dict | None):
        """Load inventory from character state."""
        if not state:
            self.items = []
            return
        
        # Try to get items from inventory.items (new format)
        inventory = state.get("inventory", {})
        items_list = inventory.get("items", [])
        
        # Fallback to equipment for backward compatibility
        if not items_list:
            items_list = state.get("equipment", [])
        
        self.items = []
        for item in items_list:
            if isinstance(item, dict):
                # Ensure all required fields exist
                if "id" not in item:
                    item["id"] = str(len(self.items))
                if "category" not in item:
                    item["category"] = self._infer_category(item.get("name", ""))
                if "qty" not in item:
                    item["qty"] = item.get("quantity", 1)
                self.items.append(item)
    
    def _infer_category(self, name: str) -> str:
        """Auto-detect item category from name."""
        name_lower = name.lower()
        # Check for magic items first (they might contain weapon/armor keywords too)
        if any(keyword in name_lower for keyword in self.MAGIC_KEYWORDS):
            return "Magic Items"
        elif any(keyword in name_lower for keyword in self.ARMOR_KEYWORDS):
            return "Armor"
        elif any(keyword in name_lower for keyword in self.WEAPON_KEYWORDS):
            return "Weapons"
        elif any(keyword in name_lower for keyword in self.AMMO_KEYWORDS):
            return "Ammunition"
        elif any(keyword in name_lower for keyword in self.TOOL_KEYWORDS):
            return "Tools"
        elif any(keyword in name_lower for keyword in self.POTION_KEYWORDS):
            return "Potions"
        elif any(keyword in name_lower for keyword in self.GEAR_KEYWORDS):
            return "Adventuring Gear"
        elif any(keyword in name_lower for keyword in self.MOUNT_KEYWORDS):
            return "Mounts & Vehicles"
        return "Other"
    
    def add_item(self, name: str, cost: str = "", weight: str = "", qty: int = 1, 
                 category: str = "", notes: str = "", source: str = "custom") -> str:
        """Add an item to inventory and return its ID."""
        item_id = str(len(self.items))
        if not category:
            category = self._infer_category(name)
        
        item = {
            "id": item_id,
            "name": name,
            "cost": cost,
            "weight": weight,
            "qty": qty,
            "category": category,
            "notes": notes,
            "source": source,
        }
        self.items.append(item)
        return item_id
    
    def remove_item(self, item_id: str):
        """Remove an item by ID."""
        self.items = [item for item in self.items if item.get("id") != item_id]
    
    def update_item(self, item_id: str, updates: dict):
        """Update item fields."""
        for item in self.items:
            if item.get("id") == item_id:
                for key, value in updates.items():
                    if key in ("name", "cost", "weight", "qty", "category", "notes"):
                        item[key] = value
                break
    
    def get_items_by_category(self) -> dict[str, list[dict]]:
        """Group items by category, sorted within each category."""
        grouped = {}
        for item in self.items:
            category = item.get("category", "Other")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(item)
        
        # Sort items within each category alphabetically
        for category in grouped:
            grouped[category].sort(key=lambda x: x.get("name", "").lower())
        
        # Return in defined order, putting unlisted categories at end
        result = {}
        for category in self.CATEGORY_ORDER:
            if category in grouped:
                result[category] = grouped[category]
        for category in sorted(grouped.keys()):
            if category not in result:
                result[category] = grouped[category]
        
        return result
    
    def get_total_weight(self) -> float:
        """Calculate total weight of items."""
        total = 0.0
        for item in self.items:
            weight_str = item.get("weight", "").strip().lower()
            qty = item.get("qty", 1)
            if weight_str:
                # Extract number from strings like "2 lb", "0.5 lb", "2lb"
                import re
                match = re.search(r'(\d+\.?\d*)', weight_str)
                if match:
                    try:
                        total += float(match.group(1)) * qty
                    except:
                        pass
        return total
    
    def render_inventory(self):
        """Render inventory list with categories and expandable items."""
        container = get_element("inventory-list")
        if container is None:
            return
        
        items_grouped = self.get_items_by_category()
        sections_html = []
        
        if not self.items:
            container.innerHTML = ""
            empty_msg = get_element("inventory-empty-state")
            if empty_msg:
                empty_msg.style.display = "block"
            return
        
        empty_msg = get_element("inventory-empty-state")
        if empty_msg:
            empty_msg.style.display = "none"
        
        # Build HTML for each category
        for category, items in items_grouped.items():
            category_html = f'<div class="inventory-category">'
            category_html += f'<div class="inventory-category-header">{escape(category)}</div>'
            
            # Add items in this category
            for item in items:
                item_id = item.get("id", "")
                name = item.get("name", "Unknown Item")
                qty = item.get("qty", 1)
                cost = item.get("cost", "")
                weight = item.get("weight", "")
                notes = item.get("notes", "")
                
                # Parse extra properties from notes JSON if present
                extra_props = {}
                try:
                    if notes and notes.startswith("{"):
                        extra_props = json.loads(notes)
                        notes = ""  # Clear notes since we're using it for storage
                except:
                    pass
                
                # Build cost/weight display
                details_html = ""
                if cost:
                    details_html += f'<span class="inventory-item-cost"><strong>Cost:</strong> {escape(str(cost))}</span>'
                if weight:
                    details_html += f'<span class="inventory-item-weight"><strong>Weight:</strong> {escape(str(weight))}</span>'
                
                # Build body content with expandable properties
                body_html = ''
                
                # Show weapon/armor properties if available
                if extra_props.get("damage"):
                    body_html += f'<div class="inventory-item-field"><label>Damage</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("damage")))}</div></div>'
                if extra_props.get("damage_type"):
                    body_html += f'<div class="inventory-item-field"><label>Damage Type</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("damage_type")))}</div></div>'
                if extra_props.get("range"):
                    body_html += f'<div class="inventory-item-field"><label>Range</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("range")))}</div></div>'
                if extra_props.get("properties"):
                    body_html += f'<div class="inventory-item-field"><label>Properties/Contents</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("properties")))}</div></div>'
                if extra_props.get("armor_class"):
                    body_html += f'<div class="inventory-item-field"><label>AC</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("armor_class")))}</div></div>'
                if extra_props.get("ac_string"):
                    body_html += f'<div class="inventory-item-field"><label>AC String</label><div style="color: #bfdbfe;">{escape(str(extra_props.get("ac_string")))}</div></div>'
                
                # Show notes if present (after we cleared it for prop parsing)
                if notes:
                    body_html += f'<div class="inventory-item-field"><label>Notes</label><div style="color: #bfdbfe;">{escape(notes)}</div></div>'
                
                # Add editable custom properties field for things like "+1 AC and saves"
                custom_props = extra_props.get("custom_properties", "")
                body_html += f'<div class="inventory-item-field"><label>Item Effects/Properties</label><input type="text" data-item-custom-props="{item_id}" value="{escape(str(custom_props))}" placeholder="e.g., +1 AC and saves" style="width: 100%;"></div>'
                
                body_html += f'<div class="inventory-item-field"><label>Quantity</label><input type="number" min="1" value="{qty}" data-item-qty="{item_id}" style="width: 80px;"></div>'
                
                # Build category dropdown with current category selected
                category_options = [
                    ("Magic Items", "Magic Items"),
                    ("Weapons", "Weapons"),
                    ("Armor", "Armor"),
                    ("Ammunition", "Ammunition"),
                    ("Potions", "Potions"),
                    ("Tools", "Tools"),
                    ("Adventuring Gear", "Adventuring Gear"),
                    ("Mounts & Vehicles", "Mounts & Vehicles"),
                    ("Other", "Other")
                ]
                category_select_html = f'<select data-item-category="{item_id}" style="width: 100%;">'
                for cat_value, cat_label in category_options:
                    selected = "selected" if cat_value == item.get("category", "Other") else ""
                    category_select_html += f'<option value="{cat_value}" {selected}>{cat_label}</option>'
                category_select_html += '</select>'
                body_html += f'<div class="inventory-item-field"><label>Category</label>{category_select_html}</div>'
                
                category_html += f'''<li class="inventory-item" data-item-id="{escape(item_id)}">
                    <div class="inventory-item-summary" data-toggle-item="{escape(item_id)}">
                        <div class="inventory-item-main">
                            <span class="inventory-item-name">{escape(name)}</span>
                            <span class="inventory-item-qty">×{qty}</span>
                        </div>
                        <div class="inventory-item-details">
                            {details_html}
                        </div>
                        <div class="inventory-item-actions">
                            <button class="inventory-item-remove" data-remove-item="{escape(item_id)}" type="button">Remove</button>
                        </div>
                    </div>
                    <div class="inventory-item-body" data-item-body="{escape(item_id)}">
                        {body_html}
                    </div>
                </li>'''
            
            category_html += '</div>'
            sections_html.append(category_html)
        
        container.innerHTML = "".join(sections_html)
        
        # Register event handlers
        self._register_item_handlers()
        
        # Update totals
        update_inventory_totals()
    
    def _register_item_handlers(self):
        """Register click handlers for inventory items."""
        # Toggle expand/collapse
        toggles = get_element("inventory-list").querySelectorAll("[data-toggle-item]")
        for toggle in toggles:
            item_id = toggle.getAttribute("data-toggle-item")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_item_toggle(event, iid))
            toggle.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Remove buttons
        removes = get_element("inventory-list").querySelectorAll("[data-remove-item]")
        for remove_btn in removes:
            item_id = remove_btn.getAttribute("data-remove-item")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_item_remove(event, iid))
            remove_btn.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Qty changes
        qty_inputs = get_element("inventory-list").querySelectorAll("[data-item-qty]")
        for qty_input in qty_inputs:
            item_id = qty_input.getAttribute("data-item-qty")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_qty_change(event, iid))
            qty_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Category changes
        cat_selects = get_element("inventory-list").querySelectorAll("[data-item-category]")
        for cat_select in cat_selects:
            item_id = cat_select.getAttribute("data-item-category")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_category_change(event, iid))
            cat_select.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
        
        # Custom properties changes
        custom_props_inputs = get_element("inventory-list").querySelectorAll("[data-item-custom-props]")
        for props_input in custom_props_inputs:
            item_id = props_input.getAttribute("data-item-custom-props")
            proxy = create_proxy(lambda event, iid=item_id: self._handle_custom_props_change(event, iid))
            props_input.addEventListener("change", proxy)
            _EVENT_PROXIES.append(proxy)
    
    def _handle_item_toggle(self, event, item_id: str):
        """Toggle item details visibility."""
        body = document.querySelector(f"[data-item-body='{item_id}']")
        if body:
            if body.classList.contains("open"):
                body.classList.remove("open")
            else:
                body.classList.add("open")
    
    def _handle_item_remove(self, event, item_id: str):
        """Remove an item."""
        event.stopPropagation()
        event.preventDefault()
        self.remove_item(item_id)
        self.render_inventory()
        schedule_auto_export()
    
    def _handle_qty_change(self, event, item_id: str):
        """Handle quantity changes."""
        qty_input = event.target
        qty = parse_int(qty_input.value, 1)
        self.update_item(item_id, {"qty": qty})
        self.render_inventory()
        schedule_auto_export()
    
    def _handle_category_change(self, event, item_id: str):
        """Handle category changes."""
        cat_select = event.target
        category = cat_select.value or "Other"
        self.update_item(item_id, {"category": category})
        self.render_inventory()
        schedule_auto_export()
    
    def _handle_custom_props_change(self, event, item_id: str):
        """Handle custom properties/effects changes."""
        props_input = event.target
        custom_props = props_input.value.strip()
        
        # Update the item's notes field with the custom properties
        item = self.get_item(item_id)
        if item:
            try:
                # Parse existing notes to preserve other properties
                notes_str = item.get("notes", "")
                if notes_str and notes_str.startswith("{"):
                    extra_props = json.loads(notes_str)
                else:
                    extra_props = {}
            except:
                extra_props = {}
            
            # Update custom properties
            extra_props["custom_properties"] = custom_props
            
            # Save back to notes
            notes = json.dumps(extra_props) if extra_props else ""
            self.update_item(item_id, {"notes": notes})
            self.render_inventory()
            schedule_auto_export()


INVENTORY_MANAGER = InventoryManager()
SPELLCASTING_MANAGER = SpellcastingManager()


def reset_spellcasting_state():
    SPELLCASTING_MANAGER.reset_state()


def sort_prepared_spells():
    SPELLCASTING_MANAGER.sort_prepared_spells()


def load_spellcasting_state(state: dict | None):
    SPELLCASTING_MANAGER.load_state(state)


def sync_prepared_spells_with_library():
    SPELLCASTING_MANAGER.sync_with_library()


def get_prepared_slug_set() -> set[str]:
    return SPELLCASTING_MANAGER.get_prepared_slug_set()


def is_spell_prepared(slug: str | None) -> bool:
    return SPELLCASTING_MANAGER.is_spell_prepared(slug)


def add_spell_to_spellbook(slug: str):
    SPELLCASTING_MANAGER.add_spell(slug)


def remove_spell_from_spellbook(slug: str):
    SPELLCASTING_MANAGER.remove_spell(slug)


def render_spellbook():
    SPELLCASTING_MANAGER.render_spellbook()


def compute_spell_slot_summary(profile: dict | None = None) -> dict:
    return SPELLCASTING_MANAGER.compute_slot_summary(profile)


def render_spell_slots(slot_summary: dict | None = None):
    SPELLCASTING_MANAGER.render_spell_slots(slot_summary)


def adjust_spell_slot(level: int, delta: int):
    SPELLCASTING_MANAGER.adjust_spell_slot(level, delta)


def adjust_pact_slot(delta: int):
    SPELLCASTING_MANAGER.adjust_pact_slot(delta)


def reset_spell_slots(_event=None):
    SPELLCASTING_MANAGER.reset_spell_slots()
    reset_channel_divinity()


def load_inventory_state(state: dict | None):
    """Load inventory from character state."""
    INVENTORY_MANAGER.load_state(state)


def render_inventory():
    """Render the inventory list."""
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


def clamp(value: int, minimum: int | None = None, maximum: int | None = None) -> int:
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


def normalize_class_token(token: str | None) -> str | None:
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


def extract_character_classes(raw_text: str | None = None) -> list[dict]:
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
    raw_text: str | None = None,
    fallback_level: int | None = None,
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

def get_spell_by_slug(slug: str | None) -> dict | None:
    if not slug:
        return None
    spell_map = SPELL_LIBRARY_STATE.get("spell_map") or {}
    if slug in spell_map:
        return spell_map[slug]
    for spell in SPELL_LIBRARY_STATE.get("spells", []):
        if spell.get("slug") == slug:
            return spell
    return None


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
        save_total = mod + (proficiency if proficient else 0)
        set_text(f"{ability}-save", format_bonus(save_total))

    dex_mod = ability_modifier(scores["dex"] + race_bonuses.get("dex", 0))
    set_text("initiative", format_bonus(dex_mod))

    # Calculate concentration save (1d20 + CON modifier vs DC 10)
    con_mod = ability_modifier(scores["con"] + race_bonuses.get("con", 0))
    set_text("concentration-save", f"1d20 {format_bonus(con_mod)} vs DC 10")

    skill_totals = {}
    for skill_key in SKILLS:
        _, _, total = _compute_skill_entry(skill_key, scores, proficiency, race_bonuses)
        skill_totals[skill_key] = total
        set_text(f"{skill_key}-total", format_bonus(total))

    passive_perception = 10 + skill_totals.get("perception", 0)
    set_text("passive-perception", str(passive_perception))

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
    set_text("spell-save-dc", str(spell_save_dc))
    set_text("spell-attack", format_bonus(spell_attack))

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
    prepared_count = SPELLCASTING_MANAGER.get_prepared_non_cantrip_count(domain_bonus_slugs)
    
    counter_display = f"{prepared_count} / {max_prepared}"
    set_text("spellbook-prepared-count", counter_display)
    
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
            "armor_class": get_numeric_value("armor_class", 10),
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
            "items": INVENTORY_MANAGER.items,
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

    data["spellcasting"] = SPELLCASTING_MANAGER.export_state()

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
    global _AUTO_EXPORT_SUPPRESS
    previous_suppression = _AUTO_EXPORT_SUPPRESS
    _AUTO_EXPORT_SUPPRESS = True
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
        _AUTO_EXPORT_SUPPRESS = previous_suppression


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


def sanitize_spell_record(raw: dict) -> dict | None:
    name = raw.get("name") or "Unknown Spell"
    slug_source = raw.get("slug") or name
    slug = re.sub(r"[^a-z0-9]+", "-", slug_source.lower()).strip("-")

    level_value = raw.get("level_int")
    if level_value is None:
        level_value = raw.get("level")
    level_int = parse_int(level_value, 0)
    level_label = format_spell_level_label(level_int)

    classes_field = raw.get("dnd_class") or raw.get("classes") or ""
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
    for spell in raw_spells:
        record = sanitize_spell_record(spell)
        if record is not None:
            slug = record.get("slug")
            # Skip if we've already seen this spell slug
            if slug not in seen_slugs:
                sanitized.append(record)
                seen_slugs.add(slug)
    sanitized.sort(key=lambda item: (item["level_int"], item["name"].lower()))
    return sanitized


def rehydrate_cached_spell(record: dict) -> dict | None:
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
    if SPELL_LIBRARY_STATE.get("loading"):
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

        sanitized = sanitize_spell_list(raw_spells)
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
    """Show the equipment chooser modal"""
    modal = get_element("equipment-chooser-modal")
    if modal:
        modal.style.display = "flex"
        search_input = get_element("equipment-search")
        if search_input:
            search_input.value = ""
            search_input.focus()
        populate_equipment_results("")


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


def clear_equipment_list(_event=None):
    """Clear all equipment from the inventory"""
    if len(INVENTORY_MANAGER.items) == 0:
        return
    INVENTORY_MANAGER.items = []
    INVENTORY_MANAGER.render_inventory()
    schedule_auto_export()


def update_inventory_totals():
    """Update total weight and cost displays"""
    total_weight = INVENTORY_MANAGER.get_total_weight()
    weight_el = get_element("equipment-total-weight")
    if weight_el:
        weight_el.textContent = f"{total_weight:.1f} lb"
    # TODO: Add cost calculation if needed


def get_equipment_items_from_dom() -> list:
    """Legacy function - now returns from INVENTORY_MANAGER"""
    return INVENTORY_MANAGER.items


def fetch_equipment_from_open5e():
    """Fetch equipment data from Open5e API and cache locally"""
    global EQUIPMENT_LIBRARY_STATE
    import json
    
    # Check localStorage cache first
    try:
        cache_key = "dnd_equipment_cache_v6"
        cached = window.localStorage.getItem(cache_key)
        if cached:
            cache_data = json.loads(cached)
            console.log(f"PySheet: Loaded {len(cache_data)} items from cache")
            EQUIPMENT_LIBRARY_STATE["equipment"] = cache_data
            return
        else:
            console.log("PySheet: No cache found in localStorage")
    except Exception as e:
        console.log(f"PySheet: Cache load error: {str(e)}")
    
    # If no cache, we'll fetch async but return immediately with empty state
    # The real fetching happens in JavaScript via fetch() in a background thread
    if not EQUIPMENT_LIBRARY_STATE.get("equipment"):
        console.log("PySheet: Using fallback equipment list")
        # Return minimal fallback for now - will be replaced when JS fetches
        EQUIPMENT_LIBRARY_STATE["equipment"] = [
            {"name": "Shortsword", "cost": "10 gp", "weight": "2 lb."},
            {"name": "Longsword", "cost": "15 gp", "weight": "3 lb."},
            {"name": "Dagger", "cost": "2 gp", "weight": "1 lb."},
            {"name": "Mace", "cost": "5 gp", "weight": "4 lb."},
        ]


def populate_equipment_results(search_term: str = ""):
    """Populate equipment search results from Open5e"""
    results_div = get_element("equipment-results")
    if not results_div:
        console.error("PySheet: equipment-results element not found")
        return
    
    # Ensure we have equipment data
    fetch_equipment_from_open5e()
    
    search_term = search_term.lower().strip()
    filtered = []
    seen_names = set()
    
    equipment_list = EQUIPMENT_LIBRARY_STATE.get("equipment", [])
    console.log(f"PySheet: populate_equipment_results - equipment count: {len(equipment_list)}")
    
    # Debug: show first few items
    if equipment_list:
        console.log(f"PySheet: first item: {equipment_list[0]}")
        console.log(f"PySheet: search term: '{search_term}'")
    
    # Filter from EQUIPMENT_LIBRARY_STATE and deduplicate by name
    for item in equipment_list:
        name = item.get("name", "")
        if search_term == "" or search_term in name.lower():
            # Only add if we haven't seen this exact name before
            if name not in seen_names:
                filtered.append(item)
                seen_names.add(name)
    
    console.log(f"PySheet: filtered results: {len(filtered)}")
    
    # Limit to 20 results
    filtered = filtered[:20]
    
    results_div.innerHTML = ""
    
    if not filtered:
        empty = document.createElement("div")
        empty.style.padding = "1rem"
        empty.style.textAlign = "center"
        empty.style.color = "#94a3b8"
        empty.textContent = "No items found"
        results_div.appendChild(empty)
        return
    
    # Create container for cards
    container = document.createElement("div")
    container.className = "equipment-results-container"
    
    for item in filtered:
        name = item.get("name", "Unknown")
        cost = item.get("cost", "Unknown")
        weight = item.get("weight", "Unknown")
        damage = item.get("damage", "")
        damage_type = item.get("damage_type", "")
        range_text = item.get("range", "")
        properties = item.get("properties", "")
        ac_string = item.get("ac", "")
        armor_class = item.get("armor_class", "")
        
        # Create card
        card = document.createElement("div")
        card.className = "equipment-result-card"
        card.setAttribute("data-name", name)
        card.setAttribute("data-cost", cost)
        card.setAttribute("data-weight", weight)
        card.setAttribute("data-damage", damage)
        card.setAttribute("data-damage-type", damage_type)
        card.setAttribute("data-range", range_text)
        card.setAttribute("data-properties", properties)
        card.setAttribute("data-ac-string", ac_string)
        card.setAttribute("data-armor-class", armor_class)
        card.style.cursor = "pointer"
        
        # Item name
        nameEl = document.createElement("div")
        nameEl.className = "equipment-result-name"
        nameEl.textContent = name
        card.appendChild(nameEl)
        
        # Details (cost + weight + damage if present)
        detailsEl = document.createElement("div")
        detailsEl.className = "equipment-result-details"
        details_text = [cost, weight]
        if damage:
            details_text.append(damage)
        detailsEl.innerHTML = "".join(f"<span>{d}</span>" for d in details_text)
        card.appendChild(detailsEl)
        
        container.appendChild(card)
    
    results_div.appendChild(container)
    
    # Remove old listener if it exists
    global _EQUIPMENT_RESULT_PROXY
    if _EQUIPMENT_RESULT_PROXY:
        results_div.removeEventListener("click", _EQUIPMENT_RESULT_PROXY)
    
    # Add single new listener
    _EQUIPMENT_RESULT_PROXY = create_proxy(_handle_equipment_click)
    results_div.addEventListener("click", _EQUIPMENT_RESULT_PROXY)


def _handle_equipment_click(event):
    """Handle clicks on equipment result items - add directly to inventory"""
    target = event.target
    # Walk up the DOM to find the result item div
    while target and not target.getAttribute("data-name"):
        target = target.parentElement
    
    if target and target.getAttribute("data-name"):
        name = target.getAttribute("data-name")
        cost = target.getAttribute("data-cost")
        weight = target.getAttribute("data-weight")
        damage = target.getAttribute("data-damage") or ""
        damage_type = target.getAttribute("data-damage-type") or ""
        range_text = target.getAttribute("data-range") or ""
        properties = target.getAttribute("data-properties") or ""
        ac_string = target.getAttribute("data-ac-string") or ""
        armor_class = target.getAttribute("data-armor-class") or ""
        console.log(f"Equipment clicked: {name}")
        # Add directly to inventory with all properties
        submit_open5e_item(name, cost, weight, damage, damage_type, range_text, properties, ac_string, armor_class)


def show_equipment_details(name: str, cost: str, weight: str):
    """Show equipment details modal"""
    set_text("equipment-details-name", name)
    set_text("equipment-details-cost", cost)
    set_text("equipment-details-weight", weight)
    
    # Store current item data as data attributes on the button itself
    add_button = get_element("equipment-details-add")
    if add_button:
        add_button.setAttribute("data-item-name", name)
        add_button.setAttribute("data-item-cost", cost)
        add_button.setAttribute("data-item-weight", weight)
    
    modal = get_element("equipment-details-modal")
    if modal:
        modal.style.display = "block"
        # Close the chooser modal
        chooser = get_element("equipment-chooser-modal")
        if chooser:
            chooser.style.display = "none"


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
    
    # Close the chooser modal
    modal = get_element("equipment-chooser-modal")
    if modal:
        modal.style.display = "none"
        console.log("Chooser modal closed")


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
    if properties:
        extra_props["properties"] = properties
    if notes:
        extra_props["notes"] = notes
    
    # Store as JSON in notes field
    final_notes = json.dumps(extra_props) if extra_props else ""
    
    # Add to inventory
    console.log(f"PySheet: Adding to inventory manager: name={name}, qty={qty}, category={category}")
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
    
    # Close modal
    modal = get_element("equipment-chooser-modal")
    if modal:
        modal.style.display = "none"
    
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


def save_character(_event=None):
    data = collect_character_data()
    window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
    console.log("PySheet: character saved to localStorage")


def show_storage_info(_event=None):
    """Display storage usage information."""
    info = estimate_export_cleanup()
    msg_el = document.getElementById("storage-message")
    
    if msg_el is None:
        return
    
    if info is None:
        msg_el.innerText = "Could not determine storage usage."
        LOGGER.warning("Failed to get storage info")
        return
    
    total_kb = info["total_bytes"] // 1024
    exports = info["estimated_export_count"]
    savings_kb = info["estimated_savings_kb"]
    
    if savings_kb > 0:
        msg_el.innerHTML = (
            f"<strong>Storage Usage:</strong> {total_kb}KB | "
            f"<strong>Exports:</strong> ~{exports} | "
            f"<strong>Potential savings:</strong> ~{savings_kb}KB if cleaned"
        )
        LOGGER.info(f"Storage info: {total_kb}KB used, ~{exports} exports, ~{savings_kb}KB potential savings")
    else:
        msg_el.innerHTML = f"<strong>Storage Usage:</strong> {total_kb}KB | <strong>Exports:</strong> ~{exports}"
        LOGGER.info(f"Storage info: {total_kb}KB used, ~{exports} exports")


def cleanup_exports(_event=None):
    """Clean up old export files (browser-based pruning of localStorage info).
    
    Note: Full directory pruning requires backend support or filesystem API.
    This displays instructions for manual cleanup on desktop/server.
    """
    msg_el = document.getElementById("storage-message")
    if msg_el is None:
        return
    
    try:
        # The new LOGGER system automatically maintains a 60-day rolling window
        # Just display the cleanup status
        stats = LOGGER.get_stats()
        
        oldest = stats.get("oldest_log", "unknown")
        total_logs = stats.get("total_logs", 0)
        total_errors = stats.get("total_errors", 0)
        days = stats.get("days_with_logs", 0)
        storage_kb = stats.get("storage_bytes", 0) // 1024
        
        msg_el.innerHTML = (
            f"✓ <strong>Logs maintained!</strong> "
            f"{total_logs} log entries across {days} days ({storage_kb}KB). "
            f"Rolling 60-day window active (oldest: ~{oldest[:10] if oldest else 'unknown'}). "
            f"To delete old export files from /exports/, use your file manager."
        )
        LOGGER.info(f"Cleanup status: {total_logs} logs, {total_errors} errors, {storage_kb}KB used, 60-day rolling window active")
    except Exception as exc:
        LOGGER.error(f"Cleanup failed: {exc}", exc)
        msg_el.innerHTML = "Cleanup error - check logs"
        console.error(f"Cleanup failed: {exc}")


async def export_character(_event=None, *, auto: bool = False):
    global _LAST_AUTO_EXPORT_SNAPSHOT
    global _LAST_AUTO_EXPORT_DATE
    global _AUTO_EXPORT_FILE_HANDLE
    global _AUTO_EXPORT_DISABLED
    global _AUTO_EXPORT_SUPPORT_WARNED
    global _AUTO_EXPORT_DIRECTORY_HANDLE
    global _AUTO_EXPORT_LAST_FILENAME
    global _AUTO_EXPORT_SETUP_PROMPTED
    
    def show_saving_state():
        """Show green SAVING state."""
        indicator = document.getElementById("saving-indicator")
        if indicator:
            indicator.classList.remove("recording", "fading")
            indicator.classList.add("saving")
    
    def fade_indicator():
        """Fade to gray and remove."""
        indicator = document.getElementById("saving-indicator")
        if indicator:
            indicator.classList.remove("saving", "recording")
            indicator.classList.add("fading")
    
    if auto and _AUTO_EXPORT_DISABLED:
        fade_indicator()
        return
    if not auto and _AUTO_EXPORT_DISABLED:
        _AUTO_EXPORT_DISABLED = False
        _AUTO_EXPORT_DIRECTORY_HANDLE = None
        _AUTO_EXPORT_FILE_HANDLE = None
        _AUTO_EXPORT_LAST_FILENAME = ""
        _AUTO_EXPORT_SETUP_PROMPTED = False
        console.log("PySheet: auto-export re-enabled after manual export request")
    data = collect_character_data()
    payload = json.dumps(data, indent=2)
    
    # For auto-exports: skip only if data hasn't changed AND we've already exported today
    if auto and payload == _LAST_AUTO_EXPORT_SNAPSHOT:
        today = datetime.now().strftime("%Y%m%d")
        if today == _LAST_AUTO_EXPORT_DATE:
            fade_indicator()
            return
    
    # Show green SAVING state
    show_saving_state()

    now = datetime.now()
    proposed_filename = _build_export_filename(data, now=now)

    persistent_used = await _attempt_persistent_export(
        payload,
        proposed_filename,
        auto=auto,
        allow_prompt=not _AUTO_EXPORT_SETUP_PROMPTED,  # Prompt only once, on first attempt (auto or manual)
    )
    if persistent_used:
        fade_indicator()
        return

    if auto:
        if not _supports_persistent_auto_export():
            if not _AUTO_EXPORT_SUPPORT_WARNED:
                console.warn("PySheet: browser does not support persistent auto-export; using fallback downloads")
                _AUTO_EXPORT_SUPPORT_WARNED = True
            # Continue to fallback download below (don't return)
        elif not (_AUTO_EXPORT_DIRECTORY_HANDLE or _AUTO_EXPORT_FILE_HANDLE):
            # Persistent export not yet set up, but that's OK - just skip this export and try again next time
            # Don't disable auto-export - user may set it up manually later
            console.log("PySheet: auto-export not yet configured; will try again on next change")
            fade_indicator()
            return
        else:
            # Persistent export is set up, we already tried it above
            fade_indicator()
            return

    # Fallback: download via browser if persistent export didn't work or if manual export
    blob = Blob.new([payload], {"type": "application/json"})
    url = URL.createObjectURL(blob)
    link = document.createElement("a")
    link.href = url
    link.download = proposed_filename
    link.click()
    URL.revokeObjectURL(url)
    _LAST_AUTO_EXPORT_SNAPSHOT = payload
    _LAST_AUTO_EXPORT_DATE = datetime.now().strftime("%Y%m%d")
    if auto:
        console.log(f"PySheet: auto-exported character JSON (download) to {proposed_filename}")
    else:
        console.log(f"PySheet: exported character JSON to {proposed_filename}")
    
    fade_indicator()


def reset_character(_event=None):
    if not window.confirm("Reset the sheet to default values? This will clear saved data."):
        return
    window.localStorage.removeItem(LOCAL_STORAGE_KEY)
    populate_form(clone_default_state())
    console.log("PySheet: character reset to defaults")
    schedule_auto_export()


def handle_import(event):
    file_list = event.target.files
    if not file_list or file_list.length == 0:
        return
    file_obj = file_list.item(0)
    reader = window.FileReader.new()

    def on_load(_evt):
        try:
            payload = reader.result
            data = json.loads(payload)
        except Exception as exc:
            console.error(f"PySheet: failed to import character - {exc}")
            return
        populate_form(data)
        window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
        console.log("PySheet: character imported from JSON")
        schedule_auto_export()

    load_proxy = create_proxy(on_load)
    _EVENT_PROXIES.append(load_proxy)
    reader.onload = load_proxy
    reader.readAsText(file_obj)
    event.target.value = ""


def handle_input_event(event=None):
    # Debug: log domain changes
    if event is not None and hasattr(event, "target"):
        target_id = getattr(event.target, "id", "")
        if target_id == "domain":
            value = getattr(event.target, "value", "")
            console.log(f"DEBUG: domain input event fired! New value: {value}")
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
    equipment_search = get_element("equipment-search")
    if equipment_search is not None:
        proxy_equip_search = create_proxy(lambda e: populate_equipment_results(e.target.value))
        equipment_search.addEventListener("input", proxy_equip_search)
        _EVENT_PROXIES.append(proxy_equip_search)

    # Register equipment chooser close button
    equipment_close = get_element("equipment-chooser-close")
    if equipment_close is not None:
        proxy_equip_close = create_proxy(lambda e: get_element("equipment-chooser-modal").style.display == "none" or setattr(get_element("equipment-chooser-modal"), "style.display", "none"))
        equipment_close.addEventListener("click", proxy_equip_close)
        _EVENT_PROXIES.append(proxy_equip_close)

    # Register equipment details modal handlers
    equipment_details_close = get_element("equipment-details-close")
    if equipment_details_close is not None:
        proxy_details_close = create_proxy(lambda e: get_element("equipment-details-modal").style.display == "none" or setattr(get_element("equipment-details-modal"), "style.display", "none"))
        equipment_details_close.addEventListener("click", proxy_details_close)
        _EVENT_PROXIES.append(proxy_details_close)

    equipment_details_cancel = get_element("equipment-details-cancel")
    if equipment_details_cancel is not None:
        proxy_details_cancel = create_proxy(lambda e: get_element("equipment-details-modal").style.display == "none" or setattr(get_element("equipment-details-modal"), "style.display", "none"))
        equipment_details_cancel.addEventListener("click", proxy_details_cancel)
        _EVENT_PROXIES.append(proxy_details_cancel)

    equipment_details_add = get_element("equipment-details-add")
    if equipment_details_add is not None:
        def handle_details_add(e):
            button = e.target
            name = button.getAttribute("data-item-name") or ""
            cost = button.getAttribute("data-item-cost") or ""
            weight = button.getAttribute("data-item-weight") or ""
            
            console.log(f"Adding from details: {name}, {cost}, {weight}")
            
            if name:
                select_equipment_item(name, cost, weight)
                # Close details modal
                details_modal = get_element("equipment-details-modal")
                if details_modal:
                    details_modal.style.display = "none"
        
        proxy_details_add = create_proxy(handle_details_add)
        equipment_details_add.addEventListener("click", proxy_details_add)
        _EVENT_PROXIES.append(proxy_details_add)


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


register_event_listeners()
load_initial_state()
update_calculations()
render_equipped_weapons()

# Auto-load weapon library
async def _auto_load_weapons():
    await load_weapon_library()

asyncio.create_task(_auto_load_weapons())
