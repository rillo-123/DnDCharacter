"""PyScript driver for the PySheet D&D 5e character web app."""

import copy
import json
from math import floor

from js import Blob, URL, console, document, window
from pyodide.ffi import create_proxy

LOCAL_STORAGE_KEY = "pysheet.character.v1"

ABILITY_ORDER = ["str", "dex", "con", "int", "wis", "cha"]

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
    "cantrips": "spells_cantrips",
    "level_1": "spells_level_1",
    "level_2": "spells_level_2",
    "level_3": "spells_level_3",
    "level_4": "spells_level_4",
    "level_5": "spells_level_5",
    "level_6": "spells_level_6",
    "level_7": "spells_level_7",
    "level_8": "spells_level_8",
    "level_9": "spells_level_9",
}

DEFAULT_STATE = {
    "identity": {
        "name": "",
        "class": "Wizard 1",
        "race": "Human",
        "background": "Sage",
        "alignment": "Neutral Good",
        "player_name": "",
    },
    "level": 1,
    "inspiration": 0,
    "spell_ability": "int",
    "abilities": {
        ability: {"score": 10, "save_proficient": False} for ability in ABILITY_ORDER
    },
    "skills": {
        skill: {"proficient": False, "expertise": False} for skill in SKILLS
    },
    "combat": {
        "armor_class": 10,
        "speed": 30,
        "max_hp": 8,
        "current_hp": 8,
        "temp_hp": 0,
        "hit_dice": "1d6",
        "death_saves_success": 0,
        "death_saves_failure": 0,
    },
    "notes": {
        "equipment": "",
        "features": "",
        "attacks": "",
        "notes": "",
    },
    "spells": {key: "" for key in SPELL_FIELDS},
}

_EVENT_PROXIES = []


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


def ability_modifier(score: int) -> int:
    return floor((score - 10) / 2)


def format_bonus(value: int) -> str:
    return f"{value:+d}"


def compute_proficiency(level: int) -> int:
    level = max(1, min(20, level))
    return 2 + (level - 1) // 4


def gather_scores() -> dict:
    return {ability: get_numeric_value(f"{ability}-score", 10) for ability in ABILITY_ORDER}


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
    for skill_key, info in SKILLS.items():
        ability = info["ability"]
        mod = ability_modifier(scores[ability])
        proficient = get_checkbox(f"{skill_key}-prof")
        expertise = get_checkbox(f"{skill_key}-exp")
        multiplier = 0
        if expertise:
            multiplier = 2
        elif proficient:
            multiplier = 1
        total = mod + multiplier * proficiency
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


def collect_character_data() -> dict:
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
            "death_saves_success": get_numeric_value("death_saves_success", 0),
            "death_saves_failure": get_numeric_value("death_saves_failure", 0),
        },
        "notes": {
            "equipment": get_text_value("equipment"),
            "features": get_text_value("features"),
            "attacks": get_text_value("attacks"),
            "notes": get_text_value("notes"),
        },
        "spells": {
            key: get_text_value(element_id) for key, element_id in SPELL_FIELDS.items()
        },
    }

    for ability in ABILITY_ORDER:
        data["abilities"][ability] = {
            "score": get_numeric_value(f"{ability}-score", 10),
            "save_proficient": get_checkbox(f"{ability}-save-prof"),
        }

    for skill in SKILLS:
        data["skills"][skill] = {
            "proficient": get_checkbox(f"{skill}-prof"),
            "expertise": get_checkbox(f"{skill}-exp"),
        }

    return data


def populate_form(data: dict):
    identity = data.get("identity", {})
    set_form_value("name", identity.get("name", ""))
    set_form_value("class", identity.get("class", ""))
    set_form_value("race", identity.get("race", ""))
    set_form_value("background", identity.get("background", ""))
    set_form_value("alignment", identity.get("alignment", ""))
    set_form_value("player_name", identity.get("player_name", ""))

    set_form_value("level", data.get("level", 1))
    set_form_value("inspiration", data.get("inspiration", 0))
    set_form_value("spell_ability", data.get("spell_ability", "int"))

    for ability in ABILITY_ORDER:
        ability_state = data.get("abilities", {}).get(ability, {})
        set_form_value(f"{ability}-score", ability_state.get("score", 10))
        set_form_value(f"{ability}-save-prof", ability_state.get("save_proficient", False))

    for skill in SKILLS:
        skill_state = data.get("skills", {}).get(skill, {})
        set_form_value(f"{skill}-prof", skill_state.get("proficient", False))
        set_form_value(f"{skill}-exp", skill_state.get("expertise", False))

    combat = data.get("combat", {})
    set_form_value("armor_class", combat.get("armor_class", 10))
    set_form_value("speed", combat.get("speed", 30))
    set_form_value("max_hp", combat.get("max_hp", 8))
    set_form_value("current_hp", combat.get("current_hp", 8))
    set_form_value("temp_hp", combat.get("temp_hp", 0))
    set_form_value("hit_dice", combat.get("hit_dice", ""))
    set_form_value("death_saves_success", combat.get("death_saves_success", 0))
    set_form_value("death_saves_failure", combat.get("death_saves_failure", 0))

    notes = data.get("notes", {})
    set_form_value("equipment", notes.get("equipment", ""))
    set_form_value("features", notes.get("features", ""))
    set_form_value("attacks", notes.get("attacks", ""))
    set_form_value("notes", notes.get("notes", ""))

    spells = data.get("spells", {})
    for key, element_id in SPELL_FIELDS.items():
        set_form_value(element_id, spells.get(key, ""))

    update_calculations()


def save_character(_event=None):
    data = collect_character_data()
    window.localStorage.setItem(LOCAL_STORAGE_KEY, json.dumps(data))
    console.log("PySheet: character saved to localStorage")


def export_character(_event=None):
    data = collect_character_data()
    payload = json.dumps(data, indent=2)
    filename = (data.get("identity", {}).get("name") or "character").strip() or "character"
    blob = Blob.new([payload], {"type": "application/json"})
    url = URL.createObjectURL(blob)
    link = document.createElement("a")
    link.href = url
    link.download = f"{filename}.json"
    link.click()
    URL.revokeObjectURL(url)
    console.log("PySheet: exported character JSON")


def reset_character(_event=None):
    if not window.confirm("Reset the sheet to default values? This will clear saved data."):
        return
    window.localStorage.removeItem(LOCAL_STORAGE_KEY)
    populate_form(clone_default_state())
    console.log("PySheet: character reset to defaults")


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

    load_proxy = create_proxy(on_load)
    _EVENT_PROXIES.append(load_proxy)
    reader.onload = load_proxy
    reader.readAsText(file_obj)
    event.target.value = ""


def handle_input_event(_event):
    update_calculations()


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
