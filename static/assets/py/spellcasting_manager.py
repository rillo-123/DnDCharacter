"""Spellcasting management for D&D 5e characters.

Handles spellbook management, spell slots, prepared spells, and spell library integration.
"""

import copy
import json
import re
import sys
from html import escape
from typing import Union, Optional
from pathlib import Path

# Ensure __file__ is always set for diagnostics and tests
_module_path = Path(globals().get("__file__", Path.cwd() / "assets" / "py" / "spellcasting.py"))
try:
    _module_path = _module_path.resolve()
except Exception:
    pass
__file__ = str(_module_path)
sys.modules[__name__].__file__ = __file__

# Try to import PyScript/Pyodide components
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

try:
    from pyodide.ffi import create_proxy
except ImportError:
    # Mock for testing
    def create_proxy(func):
        return func

try:
    from pyodide.http import pyfetch
except ImportError:
    # Mock for testing
    async def pyfetch(url, *args, **kwargs):
        raise ImportError("pyfetch not available in test environment")

# Import spell data and character models
try:
    from spell_data import (
        LOCAL_SPELLS_FALLBACK,
        SPELL_CLASS_SYNONYMS,
        SPELL_CLASS_DISPLAY_NAMES,
        apply_spell_corrections,
        is_spell_source_allowed,
        STANDARD_SLOT_TABLE,
        PACT_MAGIC_TABLE,
        SUPPORTED_SPELL_CLASSES,
        SPELL_LIBRARY_STORAGE_KEY,
        SPELL_CACHE_VERSION,
        OPEN5E_SPELLS_ENDPOINT,
        OPEN5E_MAX_PAGES,
    )
except ImportError:
    # Fallback constants
    LOCAL_SPELLS_FALLBACK = []
    SPELL_CLASS_SYNONYMS = {}
    SPELL_CLASS_DISPLAY_NAMES = {}
    def apply_spell_corrections(spell): return spell
    def is_spell_source_allowed(source): return True
    STANDARD_SLOT_TABLE = {}
    PACT_MAGIC_TABLE = {}
    SUPPORTED_SPELL_CLASSES = {"artificer", "bard", "cleric", "druid", "paladin", "ranger", "sorcerer", "warlock", "wizard"}
    SPELL_LIBRARY_STORAGE_KEY = "pysheet_spell_cache"
    SPELL_CACHE_VERSION = 1
    OPEN5E_SPELLS_ENDPOINT = "https://api.open5e.com/spells/?limit=1000"
    OPEN5E_MAX_PAGES = 10
SPELL_LIBRARY_STATE = {
    "spells": [],
    "spell_map": {},
    "loaded": False,
    "loading": False,
    "class_options": [],
    "last_profile_signature": None,
}

_EVENT_PROXIES = []
MAX_SPELL_RENDER = 100


# ===================================================================
# Utility Functions (duplicated from character.py for self-containment)
# ===================================================================

def parse_int(value, default: int = 0) -> int:
    """Parse a value as integer or return default."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def clamp(value: int, minimum: Optional[int] = None, maximum: Optional[int] = None) -> int:
    """Clamp a value between minimum and maximum."""
    if minimum is not None and value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum
    return value


def is_truthy(value) -> bool:
    """Determine if a value is truthy in a D&D context."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        lower = value.strip().lower()
        return lower in {"true", "yes", "1"}
    return False


def normalize_class_token(token: Optional[str]) -> Union[str, None]:
    """Normalize a class name token to canonical form."""
    if not token:
        return None
    cleaned = token.replace("'", "'")
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


def get_element(element_id):
    """Get an element from the DOM."""
    # Defensive wrapper for test environments with minimal MockDocument
    if document is None:
        return None
    getter = getattr(document, 'getElementById', None)
    if not getter:
        return None
    return getter(element_id)


def get_text_value(element_id: str) -> str:
    """Get text value from form element."""
    element = get_element(element_id)
    if element is None:
        return ""
    return element.value or ""


def get_numeric_value(element_id: str, default: int = 0) -> int:
    """Get numeric value from form element."""
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


def format_spell_level_label(level: int) -> str:
    """Format spell level as human-readable label."""
    if level == 0:
        return "Cantrip"
    if level == 1:
        return "1st Level"
    if level == 2:
        return "2nd Level"
    if level == 3:
        return "3rd Level"
    return f"{level}th Level"


def compute_proficiency(level: int) -> int:
    """Compute proficiency bonus for a character level."""
    level = max(1, min(20, level))
    return 2 + (level - 1) // 4


def ability_modifier(score: int) -> int:
    """Compute ability modifier from ability score."""
    from math import floor
    return floor((score - 10) / 2)


def _coerce_spell_text(value) -> str:
    """Coerce a value to string for spell text."""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return " ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def _detect_saving_throw(spell: dict) -> tuple[bool, str | None]:
    """Detect if a spell calls for a REQUIRED saving throw and return (has_save, ability).
    
    Only matches when spell text says the target "must" make a save or "fails" one.
    This filters out spells like Bless that just mention saving throws as optional outcomes.
    """
    ability_names = {
        "strength": "STR",
        "dexterity": "DEX",
        "constitution": "CON",
        "intelligence": "INT",
        "wisdom": "WIS",
        "charisma": "CHA",
    }
    # Only match if the spell text says the target "must" make a save or "fails" one
    # Matches patterns like:
    #   "must succeed on a Dexterity saving throw"
    #   "must make a Wisdom saving throw"
    #   "if it fails a Dexterity saving throw"
    save_regex = re.compile(
        r"(?:must\s+(?:succeed\s+on\s+|make\s+)(?:a|an)\s+|if\s+it\s+fails\s+(?:a|an)\s+)"
        r"(strength|dexterity|constitution|intelligence|wisdom|charisma)\s+saving throw",
        re.IGNORECASE
    )
    candidates = []
    for field in ("dc", "saving_throw", "desc", "higher_level", "description", "description_html"):
        value = spell.get(field)
        if isinstance(value, (list, tuple)):
            value = " ".join(_coerce_spell_text(v) for v in value)
        candidates.append(_coerce_spell_text(value))
    for text in candidates:
        match = save_regex.search(text)
        if match:
            ability = match.group(1).lower()
            return True, ability_names.get(ability)
    return False, None


def _make_paragraphs(text: str) -> str:
    """Convert plain text to HTML paragraphs."""
    if not text:
        return ""
    lines = text.split("\n")
    paragraphs = []
    for line in lines:
        stripped = line.strip()
        if stripped:
            paragraphs.append(f"<p>{escape(stripped)}</p>")
    return "\n".join(paragraphs)


# ===================================================================
# SpellcastingManager Class
# ===================================================================

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

    def _normalize_prepared_entry(self, entry: dict) -> Optional[dict]:
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
            "is_domain_bonus": entry.get("is_domain_bonus", False) if entry else False,
        }

    def sort_prepared_spells(self):
        def _sort_key(item: dict):
            level = item.get("level", 0)
            name = item.get("name", "").lower()
            concentration = 1 if item.get("concentration") else 0
            return (level, name, concentration)

        self.prepared.sort(key=_sort_key)

    def load_state(self, state: Optional[dict]):
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
        
        # Recalculate domain bonus flags based on current domain setting
        # These will be set by character.py via integration functions
        domain = get_text_value("domain")
        if domain:
            # Domain bonus logic to be handled by character.py
            pass
        
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

    def is_spell_prepared(self, slug: Optional[str]) -> bool:
        if not slug:
            return False
        return slug in self.get_prepared_slug_set()

    # ------------------------------------------------------------------
    # spellbook manipulation
    # ------------------------------------------------------------------
    def add_spell(self, slug: str, is_domain_bonus: bool = False):
        """Add a spell to the prepared list."""
        console.log(f"DEBUG add_spell: slug={slug}, already_prepared={self.is_spell_prepared(slug)}, is_domain_bonus={is_domain_bonus}")
        if not slug or self.is_spell_prepared(slug):
            if slug:
                console.log(f"DEBUG add_spell: Skipping {slug} - already prepared")
            return
        record = get_spell_by_slug(slug)
        if record is None:
            console.warn(f"PySheet: unable to add spell '{slug}' – not in library")
            return
        
        console.log(f"DEBUG add_spell: Found spell record for {slug}")
        # Check if spell source is allowed
        source = record.get("source", "")
        console.log(f"DEBUG add_spell: Checking source for {slug}: source='{source}'")
        if not is_spell_source_allowed(source):
            console.warn(f"PySheet: spell '{slug}' is not from an allowed source (must be PHB, TCE, or XGE). Got: '{source}'")
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
                "desc": record.get("desc", ""),
                "higher_level": record.get("higher_level", ""),
                "classes": record.get("classes", []),
                "classes_display": record.get("classes_display", []),
                "is_domain_bonus": is_domain_bonus,
            }
        )
        console.log(f"DEBUG add_spell: Successfully added {slug}. Total prepared: {len(self.prepared)}")
        self.sort_prepared_spells()
        self.render_spellbook()
        self.render_spell_slots(self.compute_slot_summary())

    def remove_spell(self, slug: str):
        """Remove a spell from the prepared list."""
        if not slug:
            return
        
        before = len(self.prepared)
        self.prepared = [
            entry for entry in self.prepared if entry.get("slug") != slug
        ]
        if len(self.prepared) != before:
            self.render_spellbook()

    def can_cast_spell(self, spell_level: int) -> bool:
        """Check if a spell of given level can be cast (has available slots)."""
        if spell_level == 0:  # Cantrips don't use slots
            return True
        
        profile = {}  # Will be provided by character.py
        max_slots = self.compute_max_slots_for_level(spell_level, profile)
        used_slots = self.slots_used.get(spell_level, 0)
        
        return used_slots < max_slots
    
    def compute_max_slots_for_level(self, level: int, profile: Optional[dict] = None) -> int:
        """Get max spell slots available for a given level."""
        if level == 0:
            return 999  # Cantrips unlimited
        
        slot_summary = self.compute_slot_summary(profile)
        return slot_summary.get("levels", {}).get(level, 0)

    # ------------------------------------------------------------------
    # rendering helpers
    # ------------------------------------------------------------------
    
    def _enrich_spell_record(self, spell: dict) -> dict:
        """Enrich spell record with library data (description, properties, etc)."""
        record = spell.copy()
        slug = spell.get("slug", "")
        level = spell.get("level", 0)
        
        if not record.get("level_label"):
            record["level_label"] = format_spell_level_label(level)
        
        # Merge with library record if available
        lib_record = get_spell_by_slug(slug)
        if lib_record:
            for key in lib_record:
                if key not in record or not record.get(key):
                    record[key] = lib_record[key]
            # Ensure critical keys are present
            for critical_key in ["desc", "higher_level", "description_html", "description"]:
                if not record.get(critical_key) and lib_record.get(critical_key):
                    record[critical_key] = lib_record[critical_key]
        
        return record
    
    def _build_spellbook_mnemonics_and_tags(self, record: dict) -> tuple[str, str]:
        """Build mnemonics HTML and tags HTML for a spell card.
        
        Returns: (mnemonics_html, tags_html)
        """
        mnemonics = []
        if record.get("concentration"):
            mnemonics.append("<span class=\"spell-mnemonic\" title=\"Concentration\">Conc.</span>")
        if record.get("ritual"):
            mnemonics.append("<span class=\"spell-mnemonic\" title=\"Ritual\">Rit.</span>")
        if record.get("is_domain_bonus"):
            mnemonics.append("<span class=\"spell-mnemonic domain\" title=\"Domain Bonus\">Dom.</span>")
        
        # Detect saving throw requirement
        save_required, save_ability = _detect_saving_throw(record)
        if save_required and save_ability:
            label = f"Save: {save_ability}"
            title = f"Requires {save_ability} saving throw"
            mnemonics.append(f"<span class=\"spell-mnemonic save\" title=\"{escape(title)}\">{escape(label)}</span>")
        
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
                match = re.search(r'(\d+)\s*(?:feet|ft)', range_text)
                range_label = f"{match.group(1)}ft" if match else None
            
            if range_label:
                mnemonics.append(f"<span class=\"spell-mnemonic range\" title=\"Range: {escape(record.get('range', ''))}\">{ escape(range_label)}</span>")
        
        mnemonics_html = f"<span class=\"spell-mnemonics\">{''.join(mnemonics)}</span>" if mnemonics else ""
        
        # Build tags
        tag_parts = []
        if record.get("ritual"):
            tag_parts.append("<span class=\"spell-tag\">Ritual</span>")
        if record.get("concentration"):
            tag_parts.append("<span class=\"spell-tag\">Concentration</span>")
        tags_html = "".join(tag_parts)
        
        return mnemonics_html, tags_html
    
    def _build_spellbook_body_html(self, record: dict) -> str:
        """Build the body HTML (properties, classes, description) for a spell card."""
        # Build properties
        properties = []
        casting_time = record.get("casting_time") or ""
        if casting_time:
            properties.append(f"<div><dt>Casting Time</dt><dd>{escape(casting_time)}</dd></div>")
        range_text = record.get("range") or ""
        if range_text:
            properties.append(f"<div><dt>Range</dt><dd>{escape(range_text)}</dd></div>")
        components = record.get("components") or ""
        material = record.get("material") or ""
        if components:
            comp_text = escape(components)
            if material:
                comp_text = f"{comp_text} ({escape(material)})"
            properties.append(f"<div><dt>Components</dt><dd>{comp_text}</dd></div>")
        duration = record.get("duration") or ""
        if duration:
            properties.append(f"<div><dt>Duration</dt><dd>{escape(duration)}</dd></div>")
        properties_html = ("<dl class=\"spellbook-properties\">" + "".join(properties) + "</dl>") if properties else ""
        
        # Build classes display
        classes_display = record.get("classes_display") or []
        classes_html = (
            "<div class=\"spellbook-classes\"><strong>Classes: </strong>"
            + escape(", ".join(classes_display))
            + "</div>"
        ) if classes_display else ""
        
        # Build description
        description_html = record.get("description_html")
        if not description_html:
            desc_text = _coerce_spell_text(record.get("desc"))
            higher_text = _coerce_spell_text(record.get("higher_level"))
            desc_html = _make_paragraphs(desc_text)
            higher_html = _make_paragraphs(higher_text)
            if desc_html:
                description_html = desc_html
                if higher_html:
                    description_html += "<p class=\"spell-section-title\">At Higher Levels</p>" + higher_html
            else:
                description_text = record.get("description", "")
                if description_text:
                    description_html = _make_paragraphs(_coerce_spell_text(description_text))
                else:
                    description_html = "<p class=\"spellbook-description-empty\">No detailed description available.</p>"
        
        # Combine body sections
        body_sections = []
        if properties_html:
            body_sections.append(properties_html)
        if classes_html:
            body_sections.append(classes_html)
        body_sections.append(f"<div class=\"spellbook-description\">{description_html}</div>")
        
        return "<div class=\"spellbook-body\">" + "".join(body_sections) + "</div>"
    
    def render_spellbook(self):
        """Render the spellbook UI with all prepared spells."""
        container = get_element("spellbook-levels")
        empty_state = get_element("spellbook-empty-state")
        console.log(f"DEBUG: [render_spellbook] container={container is not None}, empty_state={empty_state is not None}, prepared={len(self.prepared)}")
        if container is None or empty_state is None:
            console.warn("DEBUG: [render_spellbook] Missing DOM elements, returning")
            return

        # Render slot tracker
        self.render_slots_tracker()

        if not self.prepared:
            console.log("DEBUG: [render_spellbook] No prepared spells, showing empty state")
            empty_state.style.display = "block"
            container.innerHTML = ""
            return

        console.log(f"DEBUG: [render_spellbook] Rendering {len(self.prepared)} prepared spells")
        console.log("💡 TIP: Click the 'Spells' tab at the top to see your prepared spellbook!")
        empty_state.style.display = "none"
        console.log("DEBUG: [render_spellbook] Set empty_state.style.display = 'none'")
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
                
                # Enrich spell record with library data
                record = self._enrich_spell_record(spell)
                
                # Build meta text (level and school)
                level_label = record.get("level_label") or format_spell_level_label(spell.get("level", level))
                school = record.get("school") or ""
                meta_parts = [part for part in [level_label, school] if part]
                meta_text = " · ".join(meta_parts)
                _meta_html = f"<span class=\"spellbook-meta\">{escape(meta_text)}</span>" if meta_text else ""
                _source_html = f"<span class=\"spellbook-source\">{escape(source)}</span>" if source else ""
                
                # Build mnemonics and tags
                mnemonics_html, tags_html = self._build_spellbook_mnemonics_and_tags(record)
                
                # Build body HTML
                body_html = self._build_spellbook_body_html(record)
                if tags_html:
                    body_html = f"<div class=\"spellbook-tags\">{tags_html}</div>" + body_html

                # Determine castability
                is_castable = self.can_cast_spell(level)
                castable_class = "" if is_castable else " uncastable"
                
                is_bonus_spell = record.get("is_domain_bonus", False)
                
                # Remove button (only if not a bonus spell)
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

        html_content = "".join(sections)
        console.log(f"DEBUG: [render_spellbook] Setting container.innerHTML with {len(html_content)} chars, {len(sections)} sections")
        console.log(f"DEBUG: [render_spellbook] First 200 chars of HTML: {html_content[:200]}")
        container.innerHTML = html_content
        
        # Verify the content was actually set
        console.log(f"DEBUG: [render_spellbook] After innerHTML set: container.innerHTML.length = {len(container.innerHTML)}")
        console.log(f"DEBUG: [render_spellbook] container.children.length = {container.children.length}")
        console.log(f"DEBUG: [render_spellbook] container textContent length = {len(container.textContent)}")
        
        # Force a style update to ensure visibility
        container.style.display = "block"
        console.log("DEBUG: [render_spellbook] Set container.style.display = 'block'")

        buttons = container.querySelectorAll("button[data-remove-spell]")
        console.log(f"DEBUG: [render_spellbook] Found {len(buttons)} remove buttons")
        for button in buttons:
            slug = button.getAttribute("data-remove-spell")
            if not slug:
                continue
            proxy = create_proxy(
                lambda event, s=slug: self.handle_remove_spell_click(event, s)
            )
            button.addEventListener("click", proxy)
            _EVENT_PROXIES.append(proxy)

    def handle_remove_spell_click(self, event, slug: str):
        """Handle spell removal button click."""
        if event is not None:
            event.stopPropagation()
            event.preventDefault()
        self.remove_spell(slug)

    def compute_slot_summary(self, profile: Optional[dict] = None) -> dict:
        """Compute available spell slots based on character level and progression."""
        # This will be enhanced by character.py integration
        effective_level = get_numeric_value("level", 1)
        
        slot_counts = STANDARD_SLOT_TABLE.get(
            effective_level, STANDARD_SLOT_TABLE.get(1, {})
        )
        # slot_counts is a dict like {1: 2, 2: 3, 3: 4, ...} mapping spell level to slot count
        level_slots = {level: slot_counts.get(level, 0) for level in range(1, 10)}

        pact_info = PACT_MAGIC_TABLE.get(effective_level, {"slots": 0, "level": 0})

        return {
            "levels": level_slots,
            "pact": pact_info,
            "effective_level": effective_level,
        }

    def _normalize_slot_usage(self, slot_summary: dict):
        """Clamp slot usage to available slots."""
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
                + '<span class="slot-tracker-label">Pact</span>'
                + f'<span class="slot-tracker-value">{pact_available}/{pact_max}</span>'
                + '</div>'
            )
        
        if tracker_items:
            container.innerHTML = '<div class="slot-tracker">' + "".join(tracker_items) + '</div>'
            container.style.display = "block"
        else:
            container.innerHTML = ""
            container.style.display = "none"

    def render_spell_slots(self, slot_summary: Optional[dict] = None):
        """Render the spell slot adjustment UI."""
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
                lambda event, lvl=level, d=delta: self.handle_slot_button(event, lvl, d)
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
                        lambda event, d=delta: self.handle_pact_slot_button(event, d)
                    )
                    button.addEventListener("click", proxy)
                    _EVENT_PROXIES.append(proxy)

    def handle_slot_button(self, event, level: int, delta: int):
        """Handle spell slot adjustment button click."""
        if event is not None:
            event.stopPropagation()
            event.preventDefault()
        self.adjust_spell_slot(level, delta)

    def handle_pact_slot_button(self, event, delta: int):
        """Handle pact slot adjustment button click."""
        if event is not None:
            event.stopPropagation()
            event.preventDefault()
        self.adjust_pact_slot(delta)

    # ------------------------------------------------------------------
    # slot adjustments
    # ------------------------------------------------------------------
    def adjust_spell_slot(self, level: int, delta: int):
        """Adjust spell slots for a given level."""
        slot_summary = self.compute_slot_summary()
        max_slots = slot_summary["levels"].get(level, 0)
        if max_slots <= 0:
            self.slots_used[level] = 0
            self.render_spell_slots(slot_summary)
            return
        current = self.slots_used.get(level, 0)
        current = clamp(current + delta, 0, max_slots)
        self.slots_used[level] = current
        self.render_spell_slots(slot_summary)

    def adjust_pact_slot(self, delta: int):
        """Adjust pact slots."""
        slot_summary = self.compute_slot_summary()
        pact_max = slot_summary.get("pact", {}).get("slots", 0)
        current = clamp(self.pact_used + delta, 0, pact_max)
        self.pact_used = current
        self.render_spell_slots(slot_summary)

    def reset_spell_slots(self):
        """Reset all spell slots to 0."""
        for level in range(1, 10):
            self.slots_used[level] = 0
        self.pact_used = 0
        self.render_spell_slots()
        self.render_spellbook()


# ===================================================================
# Spell Library Functions
# ===================================================================

def get_spell_by_slug(slug: Optional[str]) -> Union[dict, None]:
    """Get a spell from the library by slug."""
    if not slug:
        return None
    spell_map = SPELL_LIBRARY_STATE.get("spell_map") or {}
    spell_map_size = len(spell_map)
    spells_list_size = len(SPELL_LIBRARY_STATE.get("spells", []))
    
    if slug in spell_map:
        spell = spell_map[slug]
        console.log(f"DEBUG get_spell_by_slug: Found '{slug}' in spell_map (size={spell_map_size}, spells_list={spells_list_size})")
    else:
        spell = None
        console.log(f"DEBUG get_spell_by_slug: '{slug}' NOT in spell_map (size={spell_map_size}), checking spells list (size={spells_list_size})")
        for s in SPELL_LIBRARY_STATE.get("spells", []):
            if s.get("slug") == slug:
                spell = s
                console.log(f"DEBUG get_spell_by_slug: Found '{slug}' in spells list")
                break
        if spell is None:
            # Show first 5 spell_map keys for debugging
            keys_sample = list(spell_map.keys())[:5]
            console.log(f"DEBUG get_spell_by_slug: '{slug}' not found. Sample spell_map keys: {keys_sample}")
    
    # Try normalizing slug by removing source suffixes
    if spell is None and "-a5e" in slug:
        normalized_slug = slug.replace("-a5e", "")
        if normalized_slug in spell_map:
            spell = spell_map[normalized_slug]
            console.log(f"DEBUG get_spell_by_slug: Found normalized slug '{normalized_slug}' in spell_map")
        else:
            for s in SPELL_LIBRARY_STATE.get("spells", []):
                if s.get("slug") == normalized_slug:
                    spell = s
                    console.log(f"DEBUG get_spell_by_slug: Found normalized slug '{normalized_slug}' in spells list")
                    break
    
    # Normalize spell record: ensure level_int is set
    if spell and "level_int" not in spell and "level" in spell:
        spell["level_int"] = spell.get("level", 0)
    
    return spell


def sanitize_spell_record(raw: dict) -> Optional[dict]:
    """Sanitize and validate a spell record from the library."""
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
    
    # Apply known corrections
    return apply_spell_corrections(result)


def sanitize_spell_list(raw_spells: list[dict]) -> list[dict]:
    """Sanitize and deduplicate a list of spell records."""
    sanitized: list[dict] = []
    seen_slugs: set[str] = set()
    for spell in raw_spells:
        record = sanitize_spell_record(spell)
        if record is not None:
            slug = record.get("slug")
            if slug not in seen_slugs:
                sanitized.append(record)
                seen_slugs.add(slug)
    sanitized.sort(key=lambda item: (item["level_int"], item["name"].lower()))
    return sanitized


def rehydrate_cached_spell(record: dict) -> Optional[dict]:
    """Rehydrate a cached spell record."""
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


def load_spell_cache() -> Union[list[dict], None]:
    """Load cached spells from localStorage."""
    if window is None or not hasattr(window, "localStorage"):
        return None
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
    """Save spells to localStorage cache."""
    if window is None or not hasattr(window, "localStorage"):
        return
    payload = {"version": SPELL_CACHE_VERSION, "spells": spells}
    try:
        window.localStorage.setItem(SPELL_LIBRARY_STORAGE_KEY, json.dumps(payload))
    except Exception as exc:
        console.warn(f"PySheet: unable to store spell cache ({exc})")


async def fetch_open5e_spells() -> list[dict]:
    """Fetch spells from Open5e API."""
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


def set_spell_library_data(spells: list):
    """Populate spell library state and build searchable index with deduplication."""
    spell_list = spells or []
    
    # Deduplicate by slug to prevent duplicates in spell chooser
    seen_slugs = set()
    deduplicated = []
    for spell in spell_list:
        if isinstance(spell, dict):
            slug = spell.get("slug", "")
            if slug and slug not in seen_slugs:
                deduplicated.append(spell)
                seen_slugs.add(slug)
            elif not slug:
                # Keep spells without slug (shouldn't happen, but be safe)
                deduplicated.append(spell)
    
    SPELL_LIBRARY_STATE["spells"] = deduplicated
    SPELL_LIBRARY_STATE["spell_map"] = {}
    for spell in deduplicated:
        spell_slug = (spell.get("slug") or "").lower()
        if spell_slug:
            SPELL_LIBRARY_STATE["spell_map"][spell_slug] = spell
    
    console.log(f"DEBUG set_spell_library_data: Built spell_map with {len(SPELL_LIBRARY_STATE['spell_map'])} spells")
    
    # Log domain spell presence
    domain_spells_to_check = ["bless", "cure-wounds", "raise-dead", "mass-cure-wounds", "beacon-of-hope"]
    domain_present = []
    domain_missing = []
    for spell_slug in domain_spells_to_check:
        if spell_slug in SPELL_LIBRARY_STATE["spell_map"]:
            domain_present.append(spell_slug)
        else:
            domain_missing.append(spell_slug)
    console.log(f"DEBUG set_spell_library_data: Domain spells present: {domain_present}, missing: {domain_missing}")


def update_spell_library_status(message: str):
    """Update spell library status message."""
    status_el = get_element("spell-library-status")
    if status_el is not None:
        status_el.innerText = message


async def load_spell_library(_event=None):
    """Load spells from Open5e API or cache."""
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
            update_spell_library_status("Loaded spells from cache.")
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
            # Merge fallback spells
            console.log("PySheet: Merging fallback spells into Open5e list...")
            existing_slugs = {spell.get("slug") for spell in raw_spells if spell.get("slug")}
            merge_count = 0
            for fallback_spell in LOCAL_SPELLS_FALLBACK:
                fallback_slug = fallback_spell.get("slug")
                if fallback_slug not in existing_slugs:
                    raw_spells.append(fallback_spell)
                    merge_count += 1
            console.log(f"PySheet: Merged {merge_count} fallback spells")

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
        if raw_spells is not LOCAL_SPELLS_FALLBACK:
            save_spell_cache(sanitized)
        update_spell_library_status(status_message)
    except Exception as exc:
        console.error(f"PySheet: failed to load spell library - {exc}")
        update_spell_library_status("Unable to load spells. Check your connection and try again.")
    finally:
        SPELL_LIBRARY_STATE["loading"] = False
        if button is not None:
            button.disabled = False
