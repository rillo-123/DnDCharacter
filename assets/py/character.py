"""PyScript driver for the PySheet D&D 5e character web app."""

import asyncio
import copy
import importlib.util
import json
import re
import sys
import uuid
from datetime import datetime
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
    from character_models import Character, CharacterFactory, DEFAULT_ABILITY_KEYS
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
            loaded = True
            break
        except Exception:
            continue
    if not loaded:
        raise

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
SPELL_LIBRARY_STORAGE_KEY = "pysheet.spells.v1"
SPELL_CACHE_VERSION = 3
SPELL_LIBRARY_STATE = {
    "loaded": False,
    "loading": False,
    "spells": [],
    "class_options": list(CharacterFactory.supported_classes()),
    "last_profile_signature": "",
    "spell_map": {},
}

SUPPORTED_SPELL_CLASSES = set(CharacterFactory.supported_classes())

_EVENT_PROXIES: list = []


AUTO_EXPORT_DELAY_MS = 2000
AUTO_EXPORT_MAX_EVENTS = 15
_AUTO_EXPORT_TIMER_ID: int | None = None
_AUTO_EXPORT_PROXY = None
_AUTO_EXPORT_SUPPRESS = False
_LAST_AUTO_EXPORT_SNAPSHOT = ""
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
    date_stamp = now.strftime("%Y%m%d")
    level_value = 0
    try:
        level_value = int(data.get("level", 0))
    except (TypeError, ValueError):
        level_value = 0
    if level_value <= 0:
        level_value = 0
    level_part = f"lvl_{level_value}"
    return f"{base_name}_{date_stamp}_{level_part}.json"


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
    if _AUTO_EXPORT_SUPPRESS or _AUTO_EXPORT_DISABLED:
        return
    _AUTO_EXPORT_EVENT_COUNT = min(_AUTO_EXPORT_EVENT_COUNT + 1, AUTO_EXPORT_MAX_EVENTS)
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
            if auto_trigger:
                console.log("PySheet: auto-export directory not selected; disabling auto-export until manual export")
                _AUTO_EXPORT_DISABLED = True
        elif name in {"NotAllowedError", "SecurityError"}:
            console.warn("PySheet: directory picker requires a user gesture; use Export JSON to set it up")
            if auto_trigger:
                _AUTO_EXPORT_DISABLED = True
        else:
            console.warn(f"PySheet: auto-export directory picker error - {exc}")
        return None
    has_permission = await _ensure_directory_write_permission(handle)
    if not has_permission:
        console.log("PySheet: directory lacks write permission; disabling auto-export until manual export")
        if auto_trigger:
            _AUTO_EXPORT_DISABLED = True
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
            if auto_trigger:
                console.log("PySheet: auto-export file target not selected; disabling auto-export until manual export")
                _AUTO_EXPORT_DISABLED = True
        elif name in {"NotAllowedError", "SecurityError"}:
            console.warn("PySheet: file picker requires a user gesture; use Export JSON to set it up")
            if auto_trigger:
                _AUTO_EXPORT_DISABLED = True
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
]


def set_spell_library_data(spells: list[dict] | None):
    spell_list = spells or []
    SPELL_LIBRARY_STATE["spells"] = spell_list
    SPELL_LIBRARY_STATE["spell_map"] = {
        spell.get("slug"): spell
        for spell in spell_list
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
        if record:
            name = record.get("name", name)
            level = record.get("level_int", level)
            source = record.get("source", source)
            concentration = bool(record.get("concentration"))
        if not name:
            name = slug.replace("-", " ").title()
        return {
            "slug": slug,
            "name": name,
            "level": level,
            "source": source,
            "concentration": concentration,
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

        self.prepared.append(
            {
                "slug": slug,
                "name": record.get("name", slug.title()),
                "level": record.get("level_int", 0),
                "source": record.get("source", ""),
                "concentration": bool(record.get("concentration")),
            }
        )
        self.sort_prepared_spells()
        self.render_spellbook()
        self.render_spell_slots(self.compute_slot_summary(profile))
        apply_spell_filters(auto_select=False)
        schedule_auto_export()

    def remove_spell(self, slug: str):
        if not slug:
            return
        before = len(self.prepared)
        self.prepared = [
            entry for entry in self.prepared if entry.get("slug") != slug
        ]
        if len(self.prepared) != before:
            self.render_spellbook()
            apply_spell_filters(auto_select=False)
            schedule_auto_export()

    # ------------------------------------------------------------------
    # rendering helpers
    # ------------------------------------------------------------------
    def render_spellbook(self):
        container = get_element("spellbook-levels")
        empty_state = get_element("spellbook-empty-state")
        if container is None or empty_state is None:
            return

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
        for level in sorted(groups.keys()):
            def _group_sort_key(item: dict):
                name = item.get("name", "").lower()
                concentration = 1 if item.get("concentration") else 0
                return (name, concentration)

            spells = sorted(groups[level], key=_group_sort_key)
            heading = "Cantrips" if level == 0 else format_spell_level_label(level)
            items_html = []
            for spell in spells:
                slug = spell.get("slug", "")
                name = spell.get("name", "Unknown Spell")
                source = spell.get("source", "")
                record = get_spell_by_slug(slug) or {}
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

                items_html.append(
                    "<li class=\"spellbook-spell\" data-spell-slug=\""
                    + escape(slug)
                    + "\">"
                    + "<details class=\"spellbook-details\">"
                    + "<summary>"
                    + "<div class=\"spellbook-summary-main\">"
                    + f"<span class=\"spellbook-name\">{escape(name)}</span>"
                    + meta_html
                    + source_html
                    + "</div>"
                    + f"<button type=\"button\" class=\"spellbook-remove\" data-remove-spell=\"{escape(slug)}\">Remove</button>"
                    + "</summary>"
                    + body_html
                    + "</details>"
                    + "</li>"
                )
            sections.append(
                "<section class=\"spellbook-level\">"
                + f"<header><h3>{escape(heading)}</h3></header>"
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

    def render_spell_slots(self, slot_summary: dict | None = None):
        slots_container = get_element("spell-slots")
        pact_container = get_element("pact-slots")
        reset_button = get_element("spell-slots-reset")
        if slots_container is None or reset_button is None:
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

        any_slots = total_available_levels > 0 or pact_info.get("slots", 0) > 0
        reset_button.disabled = not any_slots

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
        schedule_auto_export()


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
        "hit_dice": "1d6",
        "hit_dice_available": 1,
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
    add_spell_to_spellbook(slug)


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
) -> tuple[bool, bool, int]:
    ability_key = SKILLS.get(skill_key, {}).get("ability", "")
    ability_score = ability_scores.get(ability_key, 10)
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


def update_calculations(*_args):
    scores = gather_scores()
    level = get_numeric_value("level", 1)
    proficiency = compute_proficiency(level)

    set_text("proficiency-bonus", format_bonus(proficiency))

    for ability, score in scores.items():
        mod = ability_modifier(score)
        set_text(f"{ability}-mod", format_bonus(mod))
        proficient = get_checkbox(f"{ability}-save-prof")
        save_total = mod + (proficiency if proficient else 0)
        set_text(f"{ability}-save", format_bonus(save_total))

    dex_mod = ability_modifier(scores["dex"])
    set_text("initiative", format_bonus(dex_mod))

    skill_totals = {}
    for skill_key in SKILLS:
        _, _, total = _compute_skill_entry(skill_key, scores, proficiency)
        skill_totals[skill_key] = total
        set_text(f"{skill_key}-total", format_bonus(total))

    passive_perception = 10 + skill_totals.get("perception", 0)
    set_text("passive-perception", str(passive_perception))

    spell_ability = get_text_value("spell_ability") or "int"
    spell_mod = ability_modifier(scores.get(spell_ability, 10))
    spell_save_dc = 8 + proficiency + spell_mod
    spell_attack = proficiency + spell_mod
    set_text("spell-save-dc", str(spell_save_dc))
    set_text("spell-attack", format_bonus(spell_attack))

    current_hp = get_numeric_value("current_hp", 0)
    max_hp = get_numeric_value("max_hp", 0)
    temp_hp = get_numeric_value("temp_hp", 0)
    if max_hp > 0:
        hp_status = f"{current_hp} / {max_hp}"
    else:
        hp_status = str(current_hp)
    if temp_hp > 0:
        hp_status = f"{hp_status} (+{temp_hp} temp)"
    set_text("hp-status", hp_status)

    hit_dice_available = get_numeric_value("hit_dice_available", 0)
    hit_dice_cap = max(0, get_numeric_value("level", 1))
    if hit_dice_cap > 0:
        hit_dice_status = f"{hit_dice_available} / {hit_dice_cap}"
    else:
        hit_dice_status = str(hit_dice_available)
    set_text("hit-dice-status", hit_dice_status)

    update_equipment_totals()

    slot_summary = compute_spell_slot_summary(
        compute_spellcasting_profile()
    )
    render_spell_slots(slot_summary)
    update_header_display()


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
            "death_saves_success": get_numeric_value("death_saves_success", 0),
            "death_saves_failure": get_numeric_value("death_saves_failure", 0),
        },
        "notes": {
            "equipment": get_text_value("equipment"),
            "features": get_text_value("features"),
            "attacks": get_text_value("attacks"),
            "notes": get_text_value("notes"),
        },
        "inventory": {
            # items collected from the equipment table DOM
            "items": [],
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
            "proficient": prof_flag,
            "expertise": exp_flag,
            "bonus": total,
        }

    # collect equipment items from the table
    items = []
    tbody = get_element("equipment-table-body")
    if tbody is not None:
        rows = tbody.querySelectorAll("tr[data-item-id]")
        for row in rows:
            item_id = row.getAttribute("data-item-id")
            name_el = row.querySelector("input[data-item-field='name']")
            qty_el = row.querySelector("input[data-item-field='qty']")
            cost_el = row.querySelector("input[data-item-field='cost']")
            weight_el = row.querySelector("input[data-item-field='weight']")
            notes_el = row.querySelector("input[data-item-field='notes']")
            item = {
                "id": item_id,
                "name": name_el.value if name_el is not None else "",
                "qty": parse_int(qty_el.value if qty_el is not None else 0, 0),
                "cost": parse_float(cost_el.value if cost_el is not None else 0.0, 0.0),
                "weight": parse_float(weight_el.value if weight_el is not None else 0.0, 0.0),
                "notes": notes_el.value if notes_el is not None else "",
            }
            items.append(item)
    data["inventory"]["items"] = items

    data["spellcasting"] = SPELLCASTING_MANAGER.export_state()

    character = CharacterFactory.from_dict(data)
    return character.to_dict()


def populate_form(data: dict):
    global _AUTO_EXPORT_SUPPRESS
    previous_suppression = _AUTO_EXPORT_SUPPRESS
    _AUTO_EXPORT_SUPPRESS = True
    try:
        character = CharacterFactory.from_dict(data)
        normalized = character.to_dict()

        set_form_value("name", character.name)
        set_form_value("class", character.class_text)
        set_form_value("race", character.race)
        set_form_value("background", character.background)
        set_form_value("alignment", character.alignment)
        set_form_value("player_name", character.player_name)

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
        set_form_value("death_saves_success", combat.get("death_saves_success", 0))
        set_form_value("death_saves_failure", combat.get("death_saves_failure", 0))

        notes = normalized.get("notes", {})
        set_form_value("equipment", notes.get("equipment", ""))
        set_form_value("features", notes.get("features", ""))
        set_form_value("attacks", notes.get("attacks", ""))
        set_form_value("notes", notes.get("notes", ""))

        spells = normalized.get("spells", {})
        for key, element_id in SPELL_FIELDS.items():
            set_form_value(element_id, spells.get(key, ""))

        load_spellcasting_state(normalized.get("spellcasting"))
        update_calculations()

        # populate currency and equipment
        inv = normalized.get("inventory", {})
        currency = inv.get("currency", {})
        for key in CURRENCY_ORDER:
            set_form_value(f"currency-{key}", currency.get(key, 0))

        items = get_equipment_items_from_data(normalized)
        render_equipment_table(items)
        update_equipment_totals()
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

    return {
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


def sanitize_spell_list(raw_spells: list[dict]) -> list[dict]:
    sanitized: list[dict] = []
    for spell in raw_spells:
        record = sanitize_spell_record(spell)
        if record is not None:
            sanitized.append(record)
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
    for record in spells:
        try:
            if not isinstance(record, dict):
                continue
            hydrated = rehydrate_cached_spell(record)
            if hydrated is not None:
                rehydrated.append(hydrated)
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
    tags_html = "".join(tags)

    action = "remove" if prepared else "add"
    action_label = "Remove" if prepared else "Add"
    button_classes = ["spell-action"]
    if prepared:
        button_classes.append("selected")
    if not prepared and not can_add:
        button_classes.append("locked")
    button_class_attr = " ".join(button_classes)
    disabled_attr = " disabled" if not prepared and not can_add else ""
    title_attr = " title=\"Not available to current class\"" if not prepared and not can_add else ""
    action_button = (
        f"<button type=\"button\" class=\"{button_class_attr}\" "
        f"data-spell-action=\"{action}\" data-spell-slug=\"{escape(slug)}\"{disabled_attr}{title_attr}>{action_label}</button>"
        if slug
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
    summary_parts.append("</div>")
    if tags_html:
        summary_parts.append(f"<div class=\"spell-tags\">{tags_html}</div>")
    if action_button:
        summary_parts.append(
            f"<div class=\"spell-summary-actions\">{action_button}</div>"
        )
    summary_parts.append("</summary>")
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
            raw_spells = await fetch_open5e_spells()
        except Exception as exc:
            fetch_error = exc
        if not raw_spells:
            if fetch_error is not None:
                console.warn(f"PySheet: fallback spell list in use ({fetch_error})")
            raw_spells = LOCAL_SPELLS_FALLBACK
            status_message = "Loaded built-in Bard and Cleric spell list."

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


def _create_equipment_row(item: dict) -> any:
    """Return a DOM <tr> element for the given item dict."""
    tbody = get_element("equipment-table-body")
    if tbody is None:
        return None
    tr = document.createElement("tr")
    tr.setAttribute("data-item-id", item.get("id", generate_id("item")))

    def mk_cell(html_content):
        td = document.createElement("td")
        td.innerHTML = html_content
        return td

    # name
    name_html = f"<input data-item-field='name' type='text' value=\"{escape(item.get('name',''))}\" />"
    tr.appendChild(mk_cell(name_html))

    # qty
    qty_html = f"<input data-item-field='qty' type='number' min='0' value=\"{int(item.get('qty',1))}\" />"
    tr.appendChild(mk_cell(qty_html))

    # cost
    cost_html = f"<input data-item-field='cost' type='number' step='0.01' min='0' value=\"{format_money(item.get('cost',0))}\" />"
    tr.appendChild(mk_cell(cost_html))

    # weight
    weight_html = f"<input data-item-field='weight' type='number' step='0.01' min='0' value=\"{format_weight(item.get('weight',0))}\" />"
    tr.appendChild(mk_cell(weight_html))

    # notes
    notes_html = f"<input data-item-field='notes' type='text' value=\"{escape(item.get('notes',''))}\" />"
    tr.appendChild(mk_cell(notes_html))

    # remove button
    remove_html = "<button class='equipment-remove' type='button'>Remove</button>"
    tr.appendChild(mk_cell(remove_html))

    return tr


def render_equipment_table(items: list[dict]):
    tbody = get_element("equipment-table-body")
    wrapper = get_element("equipment-table-wrapper")
    empty_state = get_element("equipment-empty-state")
    if tbody is None or wrapper is None or empty_state is None:
        return
    # clear
    tbody.innerHTML = ""
    if not items:
        wrapper.classList.remove("has-items")
        empty_state.style.display = "block"
        return
    wrapper.classList.add("has-items")
    empty_state.style.display = "none"
    for item in items:
        row = _create_equipment_row(item)
        if row is None:
            continue
        tbody.appendChild(row)

    # attach listeners to inputs and remove buttons
    rows = tbody.querySelectorAll("tr[data-item-id]")
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
        sanitized.append({
            "id": it.get("id") or generate_id("item"),
            "name": it.get("name", ""),
            "qty": int(it.get("qty", 0)),
            "cost": float(it.get("cost", 0.0)),
            "weight": float(it.get("weight", 0.0)),
            "notes": it.get("notes", ""),
        })
    return sanitized


def add_equipment_item(_event=None):
    tbody = get_element("equipment-table-body")
    if tbody is None:
        return
    new_item = {"id": generate_id("item"), "name": "", "qty": 1, "cost": 0.0, "weight": 0.0, "notes": ""}
    items = [new_item]
    # append existing items
    existing = get_equipment_items_from_dom()
    items = existing + items
    render_equipment_table(items)
    update_equipment_totals()
    schedule_auto_export()


def get_equipment_items_from_dom() -> list:
    tbody = get_element("equipment-table-body")
    result = []
    if tbody is None:
        return result
    rows = tbody.querySelectorAll("tr[data-item-id]")
    for row in rows:
        item_id = row.getAttribute("data-item-id")
        name_el = row.querySelector("input[data-item-field='name']")
        qty_el = row.querySelector("input[data-item-field='qty']")
        cost_el = row.querySelector("input[data-item-field='cost']")
        weight_el = row.querySelector("input[data-item-field='weight']")
        notes_el = row.querySelector("input[data-item-field='notes']")
        item = {
            "id": item_id,
            "name": name_el.value if name_el is not None else "",
            "qty": parse_int(qty_el.value if qty_el is not None else 0, 0),
            "cost": parse_float(cost_el.value if cost_el is not None else 0.0, 0.0),
            "weight": parse_float(weight_el.value if weight_el is not None else 0.0, 0.0),
            "notes": notes_el.value if notes_el is not None else "",
        }
        result.append(item)
    return result


def handle_equipment_input(event, item_id=None):
    # any change to equipment updates totals
    update_equipment_totals()
    schedule_auto_export()


def remove_equipment_item(item_id: str):
    tbody = get_element("equipment-table-body")
    if tbody is None:
        return
    row = tbody.querySelector(f"tr[data-item-id='{item_id}']")
    if row is not None:
        tbody.removeChild(row)
    update_equipment_totals()
    schedule_auto_export()


def update_equipment_totals():
    items = get_equipment_items_from_dom()
    total_weight = 0.0
    total_cost = 0.0
    for it in items:
        q = float(it.get("qty", 0))
        w = float(it.get("weight", 0.0))
        c = float(it.get("cost", 0.0))
        total_weight += q * w
        total_cost += q * c
    set_text("equipment-total-weight", format_weight(total_weight))
    set_text("equipment-total-cost", format_money(total_cost))



def save_character(_event=None):
    data = collect_character_data()
    window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
    console.log("PySheet: character saved to localStorage")


async def export_character(_event=None, *, auto: bool = False):
    global _LAST_AUTO_EXPORT_SNAPSHOT
    global _AUTO_EXPORT_FILE_HANDLE
    global _AUTO_EXPORT_DISABLED
    global _AUTO_EXPORT_SUPPORT_WARNED
    global _AUTO_EXPORT_DIRECTORY_HANDLE
    global _AUTO_EXPORT_LAST_FILENAME
    global _AUTO_EXPORT_SETUP_PROMPTED
    if auto and _AUTO_EXPORT_DISABLED:
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
    if auto and payload == _LAST_AUTO_EXPORT_SNAPSHOT:
        return

    now = datetime.now()
    proposed_filename = _build_export_filename(data, now=now)

    persistent_used = await _attempt_persistent_export(
        payload,
        proposed_filename,
        auto=auto,
        allow_prompt=not auto,
    )
    if persistent_used:
        return

    if auto:
        if not _supports_persistent_auto_export():
            if not _AUTO_EXPORT_SUPPORT_WARNED:
                console.warn("PySheet: browser does not support persistent auto-export; automatic downloads disabled")
                _AUTO_EXPORT_SUPPORT_WARNED = True
            _AUTO_EXPORT_DISABLED = True
            _AUTO_EXPORT_SETUP_PROMPTED = False
            return
        if not _AUTO_EXPORT_DISABLED:
            console.log("PySheet: auto-export paused. Use Export JSON to choose a folder for automatic saves.")
        _AUTO_EXPORT_DISABLED = True
        _AUTO_EXPORT_SETUP_PROMPTED = False
        return

    blob = Blob.new([payload], {"type": "application/json"})
    url = URL.createObjectURL(blob)
    link = document.createElement("a")
    link.href = url
    link.download = proposed_filename
    link.click()
    URL.revokeObjectURL(url)
    _LAST_AUTO_EXPORT_SNAPSHOT = payload
    if auto:
        console.log(f"PySheet: auto-exported character JSON (download) to {proposed_filename}")
    else:
        console.log(f"PySheet: exported character JSON to {proposed_filename}")


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
    update_calculations()
    if SPELL_LIBRARY_STATE.get("loaded"):
        target_id = ""
        if event is not None and hasattr(event, "target"):
            target = event.target
            target_id = getattr(target, "id", "")
        auto = target_id in {"class", "level"}
        apply_spell_filters(auto_select=auto)
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
