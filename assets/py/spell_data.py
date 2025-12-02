"""Spell library data, spell corrections, class mappings, and spell tables."""

# Fallback spell list (when Open5e API is unavailable)
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
        "source": "5e Core Rules",
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
        "source": "5e Core Rules",
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
        "duration": "Concentration, up to 1 round",
        "ritual": False,
        "concentration": True,
        "source": "5e Core Rules",
        "desc": [
            "A flash of light springs from your hand cloaked in momentary darkness. Roll a ranged spell attack against the target. On a hit, the target takes 4d6 radiant damage, and the next attack roll made against this target before the end of your next turn has advantage, thanks to the mystical dim light granting of this spell."
        ],
        "higher_level": "When you cast this spell using a spell slot of 2nd level or higher, the damage increases by 1d6 for each slot level above 1st.",
        "dnd_class": "Cleric",
        "document__title": "SRD",
    },
]

# Class to spell list mappings
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
            spell = dict(spell)  # Make a copy to avoid modifying original
            spell["dnd_class"] = ", ".join(correction["classes"])
    return spell


def is_spell_source_allowed(source: str) -> bool:
    """Check if a spell source is in our allowed list (PHB, TCE, XGE only)."""
    allowed = {"phb", "tce", "xge", "xgte"}
    return (source or "").lower() in allowed


# Spell casting progression tables
CLASS_CASTING_PROGRESSIONS = {
    "artificer": "artificer",
    "bard": "full",
    "cleric": "full",
    "druid": "full",
    "eldritch knight": "half",
    "arcane archer": "half",
    "monk": "full",
    "paladin": "half",
    "ranger": "half",
    "sorcerer": "full",
    "warlock": "warlock",
    "wizard": "full",
    "blood hunter": "full",
}

# Spell slot progressions by class type
SPELLCASTING_PROGRESSION_TABLES = {
    "full": {
        1: {1: 2},
        2: {1: 3},
        3: {1: 4, 2: 2},
        4: {1: 4, 2: 3},
        5: {1: 4, 2: 3, 3: 2},
        6: {1: 4, 2: 3, 3: 3},
        7: {1: 4, 2: 3, 3: 3, 4: 1},
        8: {1: 4, 2: 3, 3: 3, 4: 2},
        9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
        10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
        11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
        12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
        13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
        14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
        15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
        16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
        17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
        18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
        19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
        20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
    },
    "half": {
        1: {},
        2: {},
        3: {1: 2},
        4: {1: 2},
        5: {1: 3, 2: 0},
        6: {1: 3, 2: 0},
        7: {1: 3, 2: 1},
        8: {1: 3, 2: 1},
        9: {1: 3, 2: 2},
        10: {1: 3, 2: 2},
        11: {1: 3, 2: 3},
        12: {1: 3, 2: 3},
        13: {1: 3, 2: 3, 3: 1},
        14: {1: 3, 2: 3, 3: 1},
        15: {1: 3, 2: 3, 3: 2},
        16: {1: 3, 2: 3, 3: 2},
        17: {1: 3, 2: 3, 3: 3, 4: 1},
        18: {1: 3, 2: 3, 3: 3, 4: 1},
        19: {1: 3, 2: 3, 3: 3, 4: 2},
        20: {1: 3, 2: 3, 3: 3, 4: 2},
    },
    "artificer": {
        1: {1: 2},
        2: {1: 2},
        3: {1: 3, 2: 0},
        4: {1: 3, 2: 0},
        5: {1: 3, 2: 2},
        6: {1: 3, 2: 2},
        7: {1: 3, 2: 2, 3: 0},
        8: {1: 3, 2: 2, 3: 0},
        9: {1: 4, 2: 3, 3: 1},
        10: {1: 4, 2: 3, 3: 1},
        11: {1: 4, 2: 3, 3: 2},
        12: {1: 4, 2: 3, 3: 2},
        13: {1: 4, 2: 3, 3: 2, 4: 0},
        14: {1: 4, 2: 3, 3: 2, 4: 0},
        15: {1: 4, 2: 3, 3: 3, 4: 1},
        16: {1: 4, 2: 3, 3: 3, 4: 1},
        17: {1: 4, 2: 4, 3: 3, 4: 2},
        18: {1: 4, 2: 4, 3: 3, 4: 2},
        19: {1: 4, 2: 4, 3: 3, 4: 3},
        20: {1: 4, 2: 4, 3: 3, 4: 3},
    },
    "warlock": {
        1: {1: 1},
        2: {1: 2},
        3: {1: 2, 2: 1},
        4: {1: 3, 2: 1},
        5: {1: 3, 2: 1, 3: 1},
        6: {1: 3, 2: 2, 3: 1},
        7: {1: 3, 2: 2, 3: 2},
        8: {1: 3, 2: 2, 3: 2},
        9: {1: 3, 2: 3, 3: 2},
        10: {1: 3, 2: 3, 3: 3},
        11: {1: 3, 2: 3, 3: 3, 4: 1},
        12: {1: 3, 2: 3, 3: 3, 4: 1},
        13: {1: 3, 2: 3, 3: 3, 4: 2},
        14: {1: 3, 2: 3, 3: 3, 4: 2},
        15: {1: 3, 2: 3, 3: 3, 4: 3},
        16: {1: 3, 2: 3, 3: 3, 4: 3},
        17: {1: 3, 2: 4, 3: 3, 4: 3},
        18: {1: 3, 2: 4, 3: 3, 4: 3},
        19: {1: 3, 2: 4, 3: 3, 4: 3},
        20: {1: 3, 2: 4, 3: 3, 4: 3},
    },
}

# Standard (non-warlock) spell slot table
STANDARD_SLOT_TABLE = {
    1: {1: 2},
    2: {1: 3},
    3: {1: 4, 2: 2},
    4: {1: 4, 2: 3},
    5: {1: 4, 2: 3, 3: 2},
    6: {1: 4, 2: 3, 3: 3},
    7: {1: 4, 2: 3, 3: 3, 4: 1},
    8: {1: 4, 2: 3, 3: 3, 4: 2},
    9: {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    10: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    11: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    12: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    13: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    14: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    15: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    16: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    17: {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
    18: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
    19: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
    20: {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
}

# Warlock (Pact Magic) spell slot table
PACT_MAGIC_TABLE = {
    1: {1: 1},
    2: {1: 2},
    3: {1: 2, 2: 1},
    4: {1: 3, 2: 1},
    5: {1: 3, 2: 1, 3: 1},
    6: {1: 3, 2: 2, 3: 1},
    7: {1: 3, 2: 2, 3: 2},
    8: {1: 3, 2: 2, 3: 2},
    9: {1: 3, 2: 3, 3: 2},
    10: {1: 3, 2: 3, 3: 3},
    11: {1: 3, 2: 3, 3: 3, 4: 1},
    12: {1: 3, 2: 3, 3: 3, 4: 1},
    13: {1: 3, 2: 3, 3: 3, 4: 2},
    14: {1: 3, 2: 3, 3: 3, 4: 2},
    15: {1: 3, 2: 3, 3: 3, 4: 3},
    16: {1: 3, 2: 3, 3: 3, 4: 3},
    17: {1: 3, 2: 4, 3: 3, 4: 3},
    18: {1: 3, 2: 4, 3: 3, 4: 3},
    19: {1: 3, 2: 4, 3: 3, 4: 3},
    20: {1: 3, 2: 4, 3: 3, 4: 3},
}
